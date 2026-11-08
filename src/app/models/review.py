"""Typed contracts shared by the SQL review workflow."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ReviewModel(BaseModel):
    """Base configuration for review-domain models."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SQLDialect(StrEnum):
    """SQL dialect selected for generation and validation."""

    POSTGRES = "postgres"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    SQL_SERVER = "sql_server"
    SNOWFLAKE = "snowflake"


class ReviewLevel(StrEnum):
    """Amount of database evidence available to a review."""

    NO_SCHEMA = "no_schema"
    PARTIAL_SCHEMA = "partial_schema"
    FULL_SCHEMA = "full_schema"
    SANDBOX = "sandbox"


class CheckStatus(StrEnum):
    """Outcome of one deterministic validation check."""

    PASSED = "passed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    WARNING = "warning"


class VerdictStatus(StrEnum):
    """Overall decision produced by the critic."""

    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    REJECTED = "rejected"
    UNABLE_TO_VERIFY = "unable_to_verify"


class AuditEventType(StrEnum):
    """Lifecycle event recorded during a review."""

    REQUEST_RECEIVED = "request_received"
    DRAFT_CREATED = "draft_created"
    CRITIQUE_CREATED = "critique_created"
    VERDICT_ISSUED = "verdict_issued"


class SchemaColumn(ReviewModel):
    """Column metadata supplied for schema-aware review."""

    name: str = Field(min_length=1)
    data_type: str = Field(min_length=1)
    nullable: bool = True


class SchemaTable(ReviewModel):
    """Table metadata supplied for schema-aware review."""

    name: str = Field(min_length=1)
    columns: list[SchemaColumn] = Field(default_factory=list)


class SchemaContext(ReviewModel):
    """Database context available to the critic."""

    level: ReviewLevel
    tables: list[SchemaTable] = Field(default_factory=list)


class ReviewRequest(ReviewModel):
    """User request that starts an SQL review."""

    natural_language_request: str = Field(min_length=1)
    dialect: SQLDialect
    schema_context: SchemaContext | None = None
    maximum_rounds: int = Field(default=3, ge=1, le=10)


class SQLDraft(ReviewModel):
    """SQL statement produced by the generator for one review round."""

    sql: str = Field(min_length=1)
    dialect: SQLDialect
    round_number: int = Field(ge=1)


class ValidationCheck(ReviewModel):
    """One deterministic result produced by a critic tool."""

    name: str = Field(min_length=1)
    status: CheckStatus
    evidence: str = Field(min_length=1)


class Critique(ReviewModel):
    """Critic explanation and requested generator revision."""

    summary: str = Field(min_length=1)
    requested_revision: str | None = None
    checks: list[ValidationCheck] = Field(default_factory=list)


class Verdict(ReviewModel):
    """Final critic decision for a review."""

    status: VerdictStatus
    review_level: ReviewLevel
    rationale: str = Field(min_length=1)
    checks: list[ValidationCheck] = Field(default_factory=list)
    final_sql: str | None = None


class AuditEvent(ReviewModel):
    """Structured event emitted during a review lifecycle."""

    event_type: AuditEventType
    message: str = Field(min_length=1)
    round_number: int | None = Field(default=None, ge=1)
