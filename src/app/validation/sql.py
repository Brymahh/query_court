"""Dialect-aware SQL syntax validation."""

from sqlglot import ParseError, parse_one

from app.models import CheckStatus, SQLDialect, ValidationCheck

SUPPORTED_DIALECTS = frozenset({"postgres"})


def validate_sql(sql: str, dialect: SQLDialect) -> ValidationCheck:
    """Validate SQL syntax for the selected dialect.

    Parameters
    ----------
    sql:
        SQL statement to validate.
    dialect:
        SQL dialect selected by the user.

    Returns
    -------
    ValidationCheck
        Structured result describing whether parsing succeeded.
    """
    dialect_name = str(dialect)

    if dialect_name not in SUPPORTED_DIALECTS:
        return ValidationCheck(
            name="syntax",
            status=CheckStatus.UNAVAILABLE,
            evidence=(
                f"Dialect '{dialect_name}' is not supported yet. PostgreSQL is currently supported."
            ),
        )

    try:
        parse_one(sql, read=dialect_name)
    except ParseError as error:
        return ValidationCheck(
            name="syntax",
            status=CheckStatus.FAILED,
            evidence=f"Invalid {dialect_name} SQL: {error}",
        )

    return ValidationCheck(
        name="syntax",
        status=CheckStatus.PASSED,
        evidence=f"SQL parsed successfully as {dialect_name}.",
    )
