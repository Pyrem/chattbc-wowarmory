from typing import Any

from pydantic import BaseModel


class GuildResponse(BaseModel):
    """Full guild data returned by the guild endpoint."""

    guild: dict[str, Any]
    roster: dict[str, Any]
