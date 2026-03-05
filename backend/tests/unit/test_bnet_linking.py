"""Unit tests for Battle.net linking service."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.bnet_linking import (
    BNetAlreadyLinkedError,
    generate_state,
    get_authorize_url,
    link_account,
    sync_characters,
    unlink_account,
)


class TestGenerateState:
    def test_returns_string(self) -> None:
        state = generate_state()
        assert isinstance(state, str)
        assert len(state) > 20

    def test_unique(self) -> None:
        states = {generate_state() for _ in range(10)}
        assert len(states) == 10


class TestGetAuthorizeUrl:
    def test_contains_required_params(self) -> None:
        url = get_authorize_url("test-state")
        assert "oauth.battle.net/authorize" in url
        assert "state=test-state" in url
        assert "response_type=code" in url
        assert "scope=wow.profile" in url


class TestLinkAccount:
    @pytest.mark.asyncio
    async def test_links_successfully(self) -> None:
        user = MagicMock()
        user.id = 1
        user.battle_net_id = None

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)
        db.commit = AsyncMock()

        await link_account(user, 12345, "Player#1234", db)

        assert user.battle_net_id == 12345
        assert user.battletag == "Player#1234"
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_already_linked_to_other(self) -> None:
        user = MagicMock()
        user.id = 1

        other_user = MagicMock()
        other_user.id = 2

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = other_user
        db.execute = AsyncMock(return_value=result)

        with pytest.raises(BNetAlreadyLinkedError):
            await link_account(user, 12345, "Player#1234", db)


class TestUnlinkAccount:
    @pytest.mark.asyncio
    async def test_clears_fields(self) -> None:
        user = MagicMock()
        user.id = 1
        user.battle_net_id = 12345
        user.battletag = "Player#1234"

        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()

        await unlink_account(user, db)

        assert user.battle_net_id is None
        assert user.battletag is None
        db.commit.assert_awaited_once()


class TestSyncCharacters:
    @pytest.mark.asyncio
    async def test_links_matching_characters(self) -> None:
        user = MagicMock()
        user.id = 1

        db_char = MagicMock()
        db_char.user_id = None

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = db_char
        db.execute = AsyncMock(return_value=result)
        db.commit = AsyncMock()

        characters = [
            {"name": "Testchar", "realm": {"slug": "faerlina"}},
        ]

        linked = await sync_characters(user, characters, db)

        assert linked == 1
        assert db_char.user_id == 1

    @pytest.mark.asyncio
    async def test_skips_unknown_characters(self) -> None:
        user = MagicMock()
        user.id = 1

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)
        db.commit = AsyncMock()

        characters = [
            {"name": "Nobody", "realm": {"slug": "faerlina"}},
        ]

        linked = await sync_characters(user, characters, db)

        assert linked == 0
