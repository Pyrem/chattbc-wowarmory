from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_character_service
from app.models.character import Character
from app.schemas.character import CharacterOwnerResponse, CharacterResponse
from app.services.character_service import CharacterService

router = APIRouter(prefix="/api/characters", tags=["characters"])


@router.get("/{realm}/{name}", response_model=CharacterResponse)
async def get_character(
    realm: str,
    name: str,
    db: AsyncSession = Depends(get_db),
    character_service: CharacterService = Depends(get_character_service),
) -> dict[str, Any]:
    """Fetch character data via cache pipeline. 404 if unknown."""
    return await character_service.get_character(realm, name, db)


@router.get("/{realm}/{name}/owner", response_model=CharacterOwnerResponse)
async def get_character_owner(
    realm: str,
    name: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Check if a character has a verified owner."""
    result = await db.execute(
        select(Character).where(
            Character.name == name.lower(),
            Character.realm == realm.lower(),
        )
    )
    char = result.scalar_one_or_none()
    return {"verified": char is not None and char.user_id is not None}
