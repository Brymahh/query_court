from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from app.main import create_app
from app.models import (
    AuditEvent,
    AuditEventType,
    ReviewRequest,
)


class FakeReviewEventSource:
    """Fake event source for SSE tests."""

    def stream(
        self,
        request: ReviewRequest,
    ) -> AsyncIterator[AuditEvent]:
        """Yield deterministic review events."""
        del request

        async def generate() -> AsyncIterator[AuditEvent]:
            yield AuditEvent(
                event_type=AuditEventType.DRAFT_CREATED,
                message="Generator created a SQL draft.",
                round_number=1,
                data={
                    "sql": "SELECT name FROM customers",
                    "dialect": "postgres",
                },
            )

            yield AuditEvent(
                event_type=AuditEventType.VERDICT_ISSUED,
                message="Review finished.",
                round_number=1,
                data={
                    "status": "approved",
                },
            )

        return generate()


def test_review_stream_returns_sse_events() -> None:
    client = TestClient(create_app(FakeReviewEventSource()))

    response = client.post(
        "/reviews/stream",
        json={
            "natural_language_request": "Find customer names",
            "dialect": "postgres",
            "maximum_rounds": 3,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: request_received" in response.text
    assert "event: draft_created" in response.text
    assert "SELECT name FROM customers" in response.text
    assert "event: verdict_issued" in response.text


def test_review_stream_returns_503_without_workflow() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/reviews/stream",
        json={
            "natural_language_request": "Find customer names",
            "dialect": "postgres",
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Review workflow is not configured."}
