from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.models import ReviewRequest
from app.persistence import Database, ReviewRepository


@pytest.mark.asyncio
async def test_create_session_returns_uuid() -> None:
    connection = AsyncMock()
    connection.__aenter__.return_value = connection

    with patch.object(
        Database,
        "connect",
        new_callable=AsyncMock,
        return_value=connection,
    ):
        repository = ReviewRepository(
            Database("postgresql://test"),
        )

        session_id = await repository.create_session(
            request=ReviewRequest(
                natural_language_request="Find customer names",
                dialect="postgres",
            ),
            retention_expires_at=datetime.now(UTC) + timedelta(days=30),
        )

    args = connection.execute.await_args.args
    assert args[1][2] == "postgres"
    assert isinstance(session_id, UUID)
    connection.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_message_returns_uuid() -> None:
    connection = AsyncMock()
    connection.__aenter__.return_value = connection

    with patch.object(
        Database,
        "connect",
        new_callable=AsyncMock,
        return_value=connection,
    ):
        repository = ReviewRepository(
            Database("postgresql://test"),
        )

        message_id = await repository.add_message(
            session_id=UUID("00000000-0000-0000-0000-000000000001"),
            role="generator",
            content="SELECT name FROM customers",
            round_number=1,
        )

    assert isinstance(message_id, UUID)
    connection.execute.assert_awaited_once()
