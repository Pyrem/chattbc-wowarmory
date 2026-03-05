"""Unit tests for Character and CharacterSnapshot models."""

from app.models.character import Character, CharacterSnapshot


def test_character_table_name() -> None:
    assert Character.__tablename__ == "characters"


def test_character_snapshot_table_name() -> None:
    assert CharacterSnapshot.__tablename__ == "character_snapshots"


def test_character_class_column_name() -> None:
    col = Character.__table__.columns["class"]
    assert col.name == "class"
