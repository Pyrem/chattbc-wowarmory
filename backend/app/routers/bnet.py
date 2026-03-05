"""Battle.net OAuth linking endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.character import Character
from app.models.user import User
from app.schemas.bnet import (
    BNetAuthorizeResponse,
    BNetLinkedCharacterResponse,
    BNetStatusResponse,
)
from app.services.bnet_linking import (
    BNetAlreadyLinkedError,
    BNetTokenError,
    exchange_code,
    fetch_bnet_user,
    fetch_wow_characters,
    generate_state,
    get_authorize_url,
    link_account,
    sync_characters,
    unlink_account,
)

router = APIRouter(prefix="/api/auth/bnet", tags=["bnet"])

# In-memory state store (per-process). In production, use Redis.
_pending_states: dict[str, int] = {}


@router.get("/authorize", response_model=BNetAuthorizeResponse)
async def authorize(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Generate Battle.net OAuth authorization URL."""
    state = generate_state()
    _pending_states[state] = current_user.id
    url = get_authorize_url(state)
    return {"authorize_url": url, "state": state}


@router.get("/callback", response_model=BNetStatusResponse)
async def callback(
    code: str,
    state: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Handle Battle.net OAuth callback."""
    user_id = _pending_states.pop(state, None)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        token_data = await exchange_code(code)
    except BNetTokenError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    access_token = token_data["access_token"]

    try:
        bnet_user = await fetch_bnet_user(access_token)
    except BNetTokenError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    bnet_id = bnet_user.get("id")
    battletag = bnet_user.get("battletag", "")

    if bnet_id is None:
        raise HTTPException(status_code=502, detail="No Battle.net ID returned")

    try:
        await link_account(user, bnet_id, battletag, db)
    except BNetAlreadyLinkedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    # Sync character ownership
    characters = await fetch_wow_characters(access_token)
    linked_count = await sync_characters(user, characters, db)

    return {
        "linked": True,
        "battletag": battletag,
        "characters_linked": linked_count,
    }


@router.delete("/unlink", response_model=BNetStatusResponse)
async def unlink(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Unlink Battle.net account."""
    if current_user.battle_net_id is None:
        raise HTTPException(status_code=400, detail="No Battle.net account linked")

    await unlink_account(current_user, db)
    return {"linked": False, "battletag": None, "characters_linked": 0}


@router.get("/characters", response_model=list[BNetLinkedCharacterResponse])
async def linked_characters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List characters linked to the current user."""
    result = await db.execute(select(Character).where(Character.user_id == current_user.id))
    chars = result.scalars().all()
    return [
        {
            "name": c.name,
            "realm": c.realm,
            "class_name": c.class_,
            "level": c.level,
            "faction": c.faction,
        }
        for c in chars
    ]
