"""State contracts for the generator-critic workflow."""

from typing import TypedDict

from app.models import (
    AuditEvent,
    Critique,
    ReviewRequest,
    SQLDraft,
    Verdict,
)


class ReviewState(TypedDict, total=False):
    """State carried through one SQL review."""

    request: ReviewRequest
    round_number: int
    draft: SQLDraft
    critique: Critique
    verdict: Verdict
    events: list[AuditEvent]
