from datetime import UTC, datetime

from app.models.user import User


def test_user_model_fields() -> None:
    user = User(
        id=1,
        email="test@example.com",
        password_hash="hashed",
        display_name="TestUser",
        email_verified=False,
    )
    assert user.email == "test@example.com"
    assert user.password_hash == "hashed"
    assert user.display_name == "TestUser"
    assert user.email_verified is False
    assert user.battle_net_id is None
    assert user.battletag is None


def test_user_model_with_bnet_fields() -> None:
    user = User(
        id=2,
        email="linked@example.com",
        password_hash="hashed",
        display_name="LinkedUser",
        email_verified=True,
        battle_net_id=12345678,
        battletag="Player#1234",
        last_login=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert user.battle_net_id == 12345678
    assert user.battletag == "Player#1234"
    assert user.email_verified is True
    assert user.last_login is not None


def test_user_table_name() -> None:
    assert User.__tablename__ == "users"
