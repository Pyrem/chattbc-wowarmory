"""Battle.net OAuth linking service.

Handles Authorization Code flow for character ownership verification.
Uses a separate OAuth client from the developer API client.
"""

from __future__ import annotations

import secrets
from typing import Any

import httpx
import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.character import Character
from app.models.user import User

logger = structlog.get_logger()

AUTHORIZE_URL = "https://oauth.battle.net/authorize"
TOKEN_URL = "https://oauth.battle.net/token"
USERINFO_URL = "https://oauth.battle.net/userinfo"
PROFILE_API = "https://us.api.blizzard.com/profile/user/wow"


class BNetLinkingError(Exception):
    """Base error for Battle.net linking failures."""


class BNetStateError(BNetLinkingError):
    """CSRF state mismatch."""


class BNetTokenError(BNetLinkingError):
    """Failed to exchange authorization code for token."""


class BNetAlreadyLinkedError(BNetLinkingError):
    """This Battle.net account is already linked to another user."""


def generate_state() -> str:
    """Generate a random state string for CSRF protection."""
    return secrets.token_urlsafe(32)


def get_authorize_url(state: str) -> str:
    """Build the Blizzard OAuth authorization URL."""
    params = {
        "client_id": settings.bnet_oauth_client_id,
        "redirect_uri": settings.bnet_oauth_redirect_uri,
        "response_type": "code",
        "scope": "wow.profile",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{AUTHORIZE_URL}?{query}"


async def exchange_code(code: str) -> dict[str, Any]:
    """Exchange authorization code for access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.bnet_oauth_redirect_uri,
            },
            auth=(settings.bnet_oauth_client_id, settings.bnet_oauth_client_secret),
        )
    if resp.status_code != 200:
        logger.error("bnet_token_exchange_failed", status=resp.status_code)
        raise BNetTokenError("Failed to exchange code for token")
    data: dict[str, Any] = resp.json()
    return data


async def fetch_bnet_user(access_token: str) -> dict[str, Any]:
    """Fetch Battle.net user info (bnet_id, battletag)."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code != 200:
        raise BNetTokenError("Failed to fetch user info")
    data: dict[str, Any] = resp.json()
    return data


async def fetch_wow_characters(access_token: str) -> list[dict[str, Any]]:
    """Fetch the user's WoW character list from Profile API."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            PROFILE_API,
            headers={"Authorization": f"Bearer {access_token}"},
            params={"namespace": f"profile-classic-{settings.blizzard_region}"},
        )
    if resp.status_code != 200:
        logger.warning("bnet_character_fetch_failed", status=resp.status_code)
        return []
    data: dict[str, Any] = resp.json()
    accounts: list[dict[str, Any]] = data.get("wow_accounts", [])
    characters: list[dict[str, Any]] = []
    for account in accounts:
        characters.extend(account.get("characters", []))
    return characters


async def link_account(
    user: User,
    bnet_id: int,
    battletag: str,
    db: AsyncSession,
) -> None:
    """Link a Battle.net account to a user. Raises if already linked to another."""
    existing = await db.execute(select(User).where(User.battle_net_id == bnet_id))
    existing_user = existing.scalar_one_or_none()
    if existing_user is not None and existing_user.id != user.id:
        raise BNetAlreadyLinkedError("This Battle.net account is linked to another user")

    user.battle_net_id = bnet_id
    user.battletag = battletag
    await db.commit()


async def unlink_account(user: User, db: AsyncSession) -> None:
    """Unlink Battle.net account and remove character ownership."""
    await db.execute(update(Character).where(Character.user_id == user.id).values(user_id=None))
    user.battle_net_id = None
    user.battletag = None
    await db.commit()


async def sync_characters(
    user: User,
    characters: list[dict[str, Any]],
    db: AsyncSession,
) -> int:
    """Set user_id on matching Character records.

    Returns the number of characters linked.
    """
    linked = 0
    for char in characters:
        char_name = char.get("name", "").lower()
        realm_data = char.get("realm", {})
        realm_slug = realm_data.get("slug", "").lower()

        if not char_name or not realm_slug:
            continue

        result = await db.execute(
            select(Character).where(
                Character.name == char_name,
                Character.realm == realm_slug,
            )
        )
        db_char = result.scalar_one_or_none()
        if db_char is not None:
            db_char.user_id = user.id
            linked += 1

    await db.commit()
    return linked
