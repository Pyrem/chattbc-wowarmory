"""Search service for characters and guilds in the database."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character
from app.models.guild import Guild


async def search(
    query: str,
    db: AsyncSession,
    result_type: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search characters and guilds by name prefix (case-insensitive).

    Args:
        query: Search string (minimum 2 characters).
        db: Database session.
        result_type: Filter to "character" or "guild". None means both.
        limit: Maximum results per type.

    Returns:
        List of search result dicts.
    """
    results: list[dict[str, Any]] = []
    pattern = f"{query.lower()}%"

    if result_type in (None, "character"):
        stmt = (
            select(Character)
            .where(func.lower(Character.name).like(pattern))
            .order_by(Character.name)
            .limit(limit)
        )
        rows = await db.execute(stmt)
        for char in rows.scalars():
            results.append(
                {
                    "type": "character",
                    "name": char.name,
                    "realm": char.realm,
                    "url": f"/character/{char.realm}/{char.name.lower()}",
                    "detail": f"Level {char.level} {char.race} {char.class_} — {char.faction}",
                }
            )

    if result_type in (None, "guild"):
        guild_stmt = (
            select(Guild)
            .where(func.lower(Guild.name).like(pattern))
            .order_by(Guild.name)
            .limit(limit)
        )
        guild_rows = await db.execute(guild_stmt)
        for guild in guild_rows.scalars():
            member_info = f", {guild.member_count} members" if guild.member_count else ""
            results.append(
                {
                    "type": "guild",
                    "name": guild.name,
                    "realm": guild.realm,
                    "url": f"/guild/{guild.realm}/{guild.name.lower()}",
                    "detail": f"{guild.faction}{member_info}",
                }
            )

    return results
