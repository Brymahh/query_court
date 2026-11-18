"""Server-Sent Events helpers for review streaming."""

import json
from collections.abc import AsyncIterator
from typing import Protocol

from app.models import AuditEvent, AuditEventType, ReviewRequest


class ReviewEventSource(Protocol):
    """Source of events produced by a review workflow."""

    def stream(
        self,
        request: ReviewRequest,
    ) -> AsyncIterator[AuditEvent]:
        """Stream typed review events."""
        ...


def encode_sse_event(event: AuditEvent) -> str:
    """Encode one review event as an SSE message.

    Parameters
    ----------
    event:
        Typed review event to encode.

    Returns
    -------
    str
        SSE-formatted event text.
    """
    payload = json.dumps(event.model_dump(mode="json"))

    return f"event: {event.event_type.value}\ndata: {payload}\n\n"


async def stream_review_events(
    source: ReviewEventSource,
    request: ReviewRequest,
) -> AsyncIterator[str]:
    """Stream workflow events in SSE format.

    Parameters
    ----------
    source:
        Review workflow event source.
    request:
        User review request.

    Yields
    ------
    str
        SSE-formatted event messages.
    """
    yield encode_sse_event(
        AuditEvent(
            event_type=AuditEventType.REQUEST_RECEIVED,
            message="Query request received. Processing started...",
        )
    )

    async for event in source.stream(request):
        yield encode_sse_event(event)
