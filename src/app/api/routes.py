"""HTTP routes for the review API."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models import ReviewRequest
from app.streaming import ReviewEventSource, stream_review_events


def create_review_router(
    event_source: ReviewEventSource | None,
) -> APIRouter:
    """Create review routes with an optional workflow event source.

    Parameters
    ----------
    event_source:
        Workflow that produces review events.

    Returns
    -------
    APIRouter
        Configured FastAPI router.
    """
    router = APIRouter()

    @router.post("/reviews/stream")
    async def stream_review(
        review_request: ReviewRequest,
    ) -> StreamingResponse:
        """Stream a review as Server-Sent Events."""
        if event_source is None:
            raise HTTPException(
                status_code=503,
                detail="Review workflow is not configured.",
            )

        return StreamingResponse(
            stream_review_events(event_source, review_request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return router
