from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Character(Base):
    __tablename__ = "characters"
    __table_args__ = (UniqueConstraint("name", "realm", name="uq_character_name_realm"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    realm: Mapped[str] = mapped_column(String(100), nullable=False)
    class_: Mapped[str] = mapped_column("class", String(30), nullable=False)
    race: Mapped[str] = mapped_column(String(30), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    faction: Mapped[str] = mapped_column(String(10), nullable=False)
    guild_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_synced: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CharacterSnapshot(Base):
    __tablename__ = "character_snapshots"
    __table_args__ = (Index("ix_snapshot_character_time", "character_id", "snapshot_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id"), nullable=False)
    gear_json: Mapped[dict] = mapped_column(JSONB, nullable=False)  # type: ignore[type-arg]
    talents_json: Mapped[dict] = mapped_column(JSONB, nullable=False)  # type: ignore[type-arg]
    stats_json: Mapped[dict] = mapped_column(JSONB, nullable=False)  # type: ignore[type-arg]
    arena_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # type: ignore[type-arg]
    reputation_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # type: ignore[type-arg]
    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
