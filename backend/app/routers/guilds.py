from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_guild_service
from app.schemas.guild import GuildResponse
from app.services.guild_service import GuildService

router = APIRouter(prefix="/api/guilds", tags=["guilds"])


@router.get("/{realm}/{name}", response_model=GuildResponse)
async def get_guild(
    realm: str,
    name: str,
    db: AsyncSession = Depends(get_db),
    guild_service: GuildService = Depends(get_guild_service),
) -> dict[str, Any]:
    """Fetch guild data via cache pipeline. 404 if unknown."""
    return await guild_service.get_guild(realm, name, db)
