"""Persistence operations for review sessions."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from app.models import (
    AuditEvent,
    ReviewRequest,
    ValidationCheck,
    Verdict,
)
from app.persistence.database import Database


class ReviewRepository:
    """Persist review sessions and their audit records."""

    def __init__(self, database: Database) -> None:
        """Create a review repository.

        Parameters
        ----------
        database:
            Database connection manager.
        """
        self._database = database

    async def create_session(
        self,
        request: ReviewRequest,
        retention_expires_at: datetime,
    ) -> UUID:
        """Create a review session and return its identifier."""
        session_id = uuid4()

        review_level = (
            request.schema_context.level.value
            if request.schema_context is not None
            else "no_schema"
        )

        async with await self._database.connect() as connection:
            await connection.execute(
                """
                INSERT INTO sessions (
                    id,
                    natural_language_request,
                    dialect,
                    review_level,
                    retention_expires_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    session_id,
                    request.natural_language_request,
                    str(request.dialect),
                    review_level,
                    retention_expires_at,
                ),
            )

        return session_id

    async def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        round_number: int | None = None,
    ) -> UUID:
        """Store one user, generator, critic, or system message."""
        message_id = uuid4()

        async with await self._database.connect() as connection:
            await connection.execute(
                """
                INSERT INTO messages (
                    id,
                    session_id,
                    role,
                    content,
                    round_number
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    message_id,
                    session_id,
                    role,
                    content,
                    round_number,
                ),
            )

        return message_id

    async def add_checks(
        self,
        session_id: UUID,
        checks: Sequence[ValidationCheck],
    ) -> None:
        """Store validation evidence produced by the critic."""
        async with await self._database.connect() as connection:
            for check in checks:
                await connection.execute(
                    """
                    INSERT INTO validation_checks (
                        id,
                        session_id,
                        name,
                        status,
                        evidence
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        uuid4(),
                        session_id,
                        check.name,
                        check.status.value,
                        check.evidence,
                    ),
                )

    async def add_verdict(
        self,
        session_id: UUID,
        verdict: Verdict,
    ) -> UUID:
        """Store the final review verdict."""
        verdict_id = uuid4()

        async with await self._database.connect() as connection:
            await connection.execute(
                """
                INSERT INTO verdicts (
                    id,
                    session_id,
                    status,
                    review_level,
                    rationale,
                    final_sql
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    verdict_id,
                    session_id,
                    verdict.status.value,
                    verdict.review_level.value,
                    verdict.rationale,
                    verdict.final_sql,
                ),
            )

        return verdict_id

    async def add_audit_event(
        self,
        session_id: UUID,
        event: AuditEvent,
    ) -> UUID:
        """Store one workflow audit event."""
        event_id = uuid4()

        async with await self._database.connect() as connection:
            await connection.execute(
                """
                INSERT INTO audit_events (
                    id,
                    session_id,
                    event_type,
                    message,
                    round_number,
                    event_data
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    event_id,
                    session_id,
                    event.event_type.value,
                    event.message,
                    event.round_number,
                    Jsonb(event.data),
                ),
            )

        return event_id
