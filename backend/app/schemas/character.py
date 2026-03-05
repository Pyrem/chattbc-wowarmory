from typing import Any

from pydantic import BaseModel


class CharacterResponse(BaseModel):
    """Full character data returned by the character endpoint."""

    profile: dict[str, Any]
    equipment: dict[str, Any]
    specializations: dict[str, Any]
    statistics: dict[str, Any]
    pvp: dict[str, Any]
    reputations: dict[str, Any]


class CharacterOwnerResponse(BaseModel):
    """Whether a character has a verified owner."""

    verified: bool
