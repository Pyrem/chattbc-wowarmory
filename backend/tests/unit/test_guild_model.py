"""Unit tests for Guild model."""

from app.models.guild import Guild


def test_guild_table_name() -> None:
    assert Guild.__tablename__ == "guilds"


def test_guild_has_progression_json_column() -> None:
    assert "progression_json" in Guild.__table__.columns
