"""LangGraph generator-critic workflow."""

from typing import Any, Protocol

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.models import (
    AuditEvent,
    AuditEventType,
    CheckStatus,
    Critique,
    ReviewLevel,
    ReviewRequest,
    SQLDraft,
    Verdict,
    VerdictStatus,
)
from app.workflow.state import ReviewState


class SQLGenerator(Protocol):
    """Interface required from a SQL generator."""

    def generate(
        self, request: ReviewRequest, previous_critique: Critique | None, round_number: int
    ) -> SQLDraft:
        """Generate an SQL draft for the given request and round number."""
        ...


class SQLCritic(Protocol):
    """Interface required from a SQL critic."""

    def review(self, request: ReviewRequest, draft: SQLDraft) -> Critique:
        """Review a SQL draft."""
        ...


def _generate_node(state: ReviewState, generator: SQLGenerator) -> dict[str, object]:
    """Generate a SQL draft for the current review round."""
    request = state["request"]
    round_number = state.get("round_number", 0) + 1
    previous_critique = state.get("critique")

    draft = generator.generate(
        request=request, previous_critique=previous_critique, round_number=round_number
    )

    event = AuditEvent(
        event_type=AuditEventType.DRAFT_CREATED,
        message="Generator created a SQL draft.",
        round_number=round_number,
    )

    events = [*state.get("events", []), event]

    return {
        "draft": draft,
        "round_number": round_number,
        "events": events,
    }


def _critique_node(state: ReviewState, critic: SQLCritic) -> dict[str, object]:
    """Critique the current SQL draft."""
    request = state["request"]
    draft = state["draft"]

    critique = critic.review(request=request, draft=draft)

    event = AuditEvent(
        event_type=AuditEventType.CRITIQUE_CREATED,
        message="Critic evaluated the SQL draft.",
        round_number=state["round_number"],
    )

    events = [*state.get("events", []), event]

    return {
        "critique": critique,
        "events": events,
    }


def _create_verdict_node(state: ReviewState) -> dict[str, object]:
    """Create the final verdict from the critic checks."""
    request = state["request"]
    draft = state["draft"]
    critique = state["critique"]

    has_failed_check = any(check.status is CheckStatus.FAILED for check in critique.checks)

    has_unavailable_check = any(
        check.status is CheckStatus.UNAVAILABLE for check in critique.checks
    )

    if has_failed_check:
        status = VerdictStatus.REJECTED
    elif has_unavailable_check:
        status = VerdictStatus.CONDITIONALLY_APPROVED
    else:
        status = VerdictStatus.APPROVED

    review_level = (
        request.schema_context.level
        if request.schema_context is not None
        else ReviewLevel.NO_SCHEMA
    )

    verdict = Verdict(
        status=status,
        review_level=review_level,
        rationale=critique.summary,
        checks=critique.checks,
        final_sql=draft.sql,
    )

    event = AuditEvent(
        event_type=AuditEventType.VERDICT_ISSUED,
        message=f"Review finished with status '{status.value}'.",
        round_number=state["round_number"],
    )

    events = [*state.get("events", []), event]

    return {
        "verdict": verdict,
        "events": events,
    }


def _route_after_critique(state: ReviewState) -> str:
    """Choose revision or final verdict after a critique."""
    request = state["request"]
    critique = state["critique"]
    round_number = state["round_number"]

    needs_revision = critique.requested_revision is not None and any(
        check.status is CheckStatus.FAILED for check in critique.checks
    )

    if needs_revision and round_number < request.maximum_rounds:
        return "revise"

    return "finish"


def build_review_graph(
    generator: SQLGenerator, critic: SQLCritic
) -> CompiledStateGraph[Any, Any, Any, Any]:
    """Build the compiled generator-critic workflow.

    Parameters
    ----------
    generator:
        Object responsible for creating SQL drafts.
    critic:
        Object responsible for reviewing SQL drafts.

    Returns
    -------
    CompiledStateGraph
        Compiled LangGraph workflow.
    """
    graph = StateGraph(ReviewState)

    graph.add_node("generate", lambda state: _generate_node(state, generator))
    graph.add_node("critique", lambda state: _critique_node(state, critic))
    graph.add_node("verdict", _create_verdict_node)

    graph.add_edge(START, "generate")
    graph.add_edge("generate", "critique")
    graph.add_conditional_edges(
        "critique",
        _route_after_critique,
        {
            "revise": "generate",
            "finish": "verdict",
        },
    )
    graph.add_edge("verdict", END)
    return graph.compile()
