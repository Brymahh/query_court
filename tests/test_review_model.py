import pytest
from pydantic import ValidationError

from app.models.review import (
    CheckStatus,
    ReviewLevel,
    ReviewRequest,
    SQLDialect,
    SQLDraft,
    ValidationCheck,
    Verdict,
    VerdictStatus,
)


def test_review_request_accepts_no_schema() -> None:
    request = ReviewRequest(
        natural_language_request="Find customers from Ghana",
        dialect=SQLDialect.POSTGRES,
    )

    assert request.schema_context is None
    assert request.maximum_rounds == 3


def test_review_request_accepts_partial_schema() -> None:
    request = ReviewRequest(
        natural_language_request="Find customer names",
        dialect="postgres",
        schema_context={
            "level": "partial_schema",
            "tables": [
                {
                    "name": "customers",
                    "columns": [{"name": "name", "data_type": "text"}],
                }
            ],
        },
    )

    assert request.schema_context is not None
    assert request.schema_context.level is ReviewLevel.PARTIAL_SCHEMA


def test_invalid_request_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ReviewRequest(
            natural_language_request="",
            dialect="unsupported",
            maximum_rounds=0,
        )


def test_sql_draft_requires_positive_round_number() -> None:
    with pytest.raises(ValidationError):
        SQLDraft(sql="SELECT 1", dialect="postgres", round_number=0)


def test_verdict_preserves_structured_check_results() -> None:
    check = ValidationCheck(
        name="syntax",
        status=CheckStatus.PASSED,
        evidence="Parsed successfully as PostgreSQL",
    )

    verdict = Verdict(
        status=VerdictStatus.CONDITIONALLY_APPROVED,
        review_level=ReviewLevel.NO_SCHEMA,
        rationale="Syntax passed, but schema validation was unavailable.",
        checks=[check],
    )

    assert verdict.checks[0].status is CheckStatus.PASSED
