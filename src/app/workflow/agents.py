"""Generator and critic adapters for the review workflow."""

from app.models import (
    CheckStatus,
    Critique,
    ReviewRequest,
    SQLDraft,
    ValidationCheck,
)
from app.prompts import load_prompts
from app.providers.base import ModelProvider
from app.validation import sql_execution_validator, validate_sql


class SQLGeneratorAgent:
    """Generate SQL drafts using a model provider."""

    def __init__(self, provider: ModelProvider) -> None:
        """Store the model provider."""
        self._provider = provider

    def generate(
        self, request: ReviewRequest, previous_critique: Critique | None, round_number: int
    ) -> SQLDraft:
        """Generate one SQL draft."""
        revision = ""

        if previous_critique is not None:
            checks = "\n".join(
                f"{check.name}: {check.status.value} - {check.evidence}"
                for check in previous_critique.checks
            )
            revision = (
                f"\nPrevious critique:\n{previous_critique.summary}\n"
                f"\nRequested revision:\n"
                f"{previous_critique.requested_revision}\n"
                f"\nValidation checks:\n{checks}\n"
                "\nRevise the SQL accordingly."
            )
            # revision = (
            #     f"\nPrevious critique: \n{previous_critique.summary}\n"
            #     "Revise the SQL draft based on the critique."
            # )

        generator_prompt = load_prompts().generator.format(dialect=str(request.dialect))

        prompt = (
            f"Generate {request.dialect} SQL for this request:\n"
            f"{request.natural_language_request}\n"
            f"{revision}"
            "Return SQL only."
        )

        sql = self._provider.complete(
            system_prompt=generator_prompt,
            user_prompt=prompt,
        )

        return SQLDraft(
            sql=sql.strip(),
            dialect=request.dialect,
            round_number=round_number,
        )


class SQLCriticAgent:
    """Review SQL using deterministic validators and a model provider."""

    def __init__(self, provider: ModelProvider) -> None:
        """Store the model provider."""
        self._provider = provider

    def review(
        self,
        request: ReviewRequest,
        draft: SQLDraft,
    ) -> Critique:
        """Produce a critique from deterministic validation results."""
        syntax_check = validate_sql(
            draft.sql,
            request.dialect,
        )

        safety_check = sql_execution_validator(
            draft.sql,
            request.dialect,
        )

        checks: list[ValidationCheck] = [
            syntax_check,
            safety_check,
        ]

        failed = any(check.status is CheckStatus.FAILED for check in checks)

        evidence = "\n".join(
            f"{check.name}: {check.status.value} - {check.evidence}" for check in checks
        )

        critic_prompt = load_prompts().critic

        summary = self._provider.complete(
            system_prompt=critic_prompt,
            user_prompt=(f"SQL:\n{draft.sql}\n\nValidation evidence:\n{evidence}"),
        )

        return Critique(
            summary=summary.strip(),
            requested_revision=("Correct the failed validation checks." if failed else None),
            checks=checks,
        )
