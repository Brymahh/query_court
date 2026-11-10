"""Read-only SQL safety validation."""

from sqlglot import ParseError, parse

from app.models import CheckStatus, SQLDialect, ValidationCheck

ALLOWED_ROOT_KEYS = frozenset(
    {
        "select",
        "union",
        "intersect",
        "except",
        "show",
        "describe",
    }
)

FORBIDDEN_NODE_KEYS = frozenset(
    {
        "insert",
        "update",
        "delete",
        "merge",
        "create",
        "alter",
        "drop",
        "truncate",
        "truncatetable",
        "copy",
        "command",
        "transaction",
    }
)


def sql_execution_validator(sql: str, dialect: SQLDialect) -> ValidationCheck:
    """Validate whether SQL is allowed by the read-only execution policy.

    Parameters
    ----------
    sql:
        SQL statement to inspect.
    dialect:
        SQL dialect used to parse the statement.

    Returns
    -------
    ValidationCheck
        Structured result indicating whether the SQL execution is allowed.
    """
    try:
        expressions = parse(sql, read=str(dialect))
    except ParseError as error:
        return ValidationCheck(
            name="execution_policy",
            status=CheckStatus.FAILED,
            evidence=f"SQL could not be parsed: {error}",
        )

    if not expressions:
        return ValidationCheck(
            name="execution_policy",
            status=CheckStatus.FAILED,
            evidence="A SQL statement is required.",
        )

    if len(expressions) != 1:
        return ValidationCheck(
            name="execution_policy",
            status=CheckStatus.FAILED,
            evidence="Only one SQL statement is allowed.",
        )

    # print(f"Parsed expressions: {expressions}")
    expression = expressions[0]
    root_key = str(expression.key)

    for node in expression.walk():
        node_key = str(node.key).lower()

        if node_key in FORBIDDEN_NODE_KEYS:
            display_name = "TRUNCATE" if node_key == "truncatetable" else node_key.upper()

            return ValidationCheck(
                name="execution_policy",
                status=CheckStatus.FAILED,
                evidence=(
                    f"Forbidden '{display_name}' operation detected. "
                    "The query cannot be executed under the read-only policy."
                ),
            )

    if root_key not in ALLOWED_ROOT_KEYS:
        return ValidationCheck(
            name="execution_policy",
            status=CheckStatus.FAILED,
            evidence=(
                f"Statement type '{root_key}' is not allowed by the read-only execution policy."
            ),
        )

    # for node in expression.walk():
    #     node_key = str(node.key).lower()

    #     if node_key in FORBIDDEN_NODE_KEYS:
    #         return ValidationCheck(
    #             name="execution_policy",
    #             status=CheckStatus.FAILED,
    #             evidence=(
    #                 f"Forbidden '{node_key.upper()}' operation detected. "
    #                 "The query cannot be executed under the read-only policy."
    #             ),
    #         )

    return ValidationCheck(
        name="execution_policy",
        status=CheckStatus.PASSED,
        evidence=(
            "The SQL contains one approved read operation and no "
            "forbidden mutation or DDL operations."
        ),
    )
