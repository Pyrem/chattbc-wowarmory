from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Guild(Base):
    __tablename__ = "guilds"
    __table_args__ = (UniqueConstraint("name", "realm", name="uq_guild_name_realm"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    realm: Mapped[str] = mapped_column(String(100), nullable=False)
    faction: Mapped[str] = mapped_column(String(10), nullable=False)
    member_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    progression_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # type: ignore[type-arg]
    last_synced: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
