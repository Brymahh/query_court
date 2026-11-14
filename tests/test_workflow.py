from dataclasses import dataclass

from app.models import (
    CheckStatus,
    Critique,
    ReviewRequest,
    SQLDraft,
    ValidationCheck,
    VerdictStatus,
)
from app.workflow.graph import build_review_graph


@dataclass
class FakeGenerator:
    """Fake generator used by workflow tests."""

    calls: int = 0

    def generate(
        self,
        request: ReviewRequest,
        previous_critique: Critique | None,
        round_number: int,
    ) -> SQLDraft:
        self.calls += 1

        if round_number == 1:
            sql = "SELECT FROM customers"
        else:
            sql = "SELECT name FROM customers"

        return SQLDraft(
            sql=sql,
            dialect=request.dialect,
            round_number=round_number,
        )


@dataclass
class FakeCritic:
    """Fake critic used by workflow tests."""

    calls: int = 0

    def review(
        self,
        request: ReviewRequest,
        draft: SQLDraft,
    ) -> Critique:
        self.calls += 1

        if self.calls == 1:
            return Critique(
                summary="The SQL has invalid syntax.",
                requested_revision="Return a valid SELECT statement.",
                checks=[
                    ValidationCheck(
                        name="syntax",
                        status=CheckStatus.FAILED,
                        evidence="The SQL is missing a projection.",
                    )
                ],
            )

        return Critique(
            summary="The SQL passed all available checks.",
            requested_revision=None,
            checks=[
                ValidationCheck(
                    name="syntax",
                    status=CheckStatus.PASSED,
                    evidence="The SQL is valid.",
                )
            ],
        )


def test_workflow_revises_failed_sql() -> None:
    generator = FakeGenerator()
    critic = FakeCritic()

    graph = build_review_graph(generator, critic)

    result = graph.invoke(
        {
            "request": ReviewRequest(
                natural_language_request="Find customer names",
                dialect="postgres",
                maximum_rounds=3,
            )
        }
    )

    assert result["round_number"] == 2
    assert generator.calls == 2
    assert critic.calls == 2
    assert result["verdict"].status is VerdictStatus.APPROVED
    assert result["verdict"].final_sql == "SELECT name FROM customers"


def test_workflow_stops_at_round_limit() -> None:
    class AlwaysFailingCritic:
        def review(
            self,
            request: ReviewRequest,
            draft: SQLDraft,
        ) -> Critique:
            return Critique(
                summary="The SQL is invalid.",
                requested_revision="Fix the SQL.",
                checks=[
                    ValidationCheck(
                        name="syntax",
                        status=CheckStatus.FAILED,
                        evidence="Invalid SQL.",
                    )
                ],
            )

    generator = FakeGenerator()
    critic = AlwaysFailingCritic()

    graph = build_review_graph(generator, critic)

    result = graph.invoke(
        {
            "request": ReviewRequest(
                natural_language_request="Find customer names",
                dialect="postgres",
                maximum_rounds=2,
            )
        }
    )

    assert result["round_number"] == 2
    assert result["verdict"].status is VerdictStatus.REJECTED
