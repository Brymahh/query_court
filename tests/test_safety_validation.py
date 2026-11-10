from app.models import CheckStatus
from app.validation import sql_execution_validator


def test_select_statement_is_allowed() -> None:
    result = sql_execution_validator(
        "SELECT name FROM customers",
        "postgres",
    )

    assert result.name == "execution_policy"
    assert result.status is CheckStatus.PASSED


def test_union_statement_is_allowed() -> None:
    result = sql_execution_validator(
        "SELECT name FROM customers UNION SELECT name FROM archived_customers",
        "postgres",
    )

    assert result.status is CheckStatus.PASSED


def test_insert_statement_is_rejected() -> None:
    result = sql_execution_validator(
        "INSERT INTO customers (name) VALUES ('Ada')",
        "postgres",
    )

    assert result.status is CheckStatus.FAILED
    assert "INSERT" in result.evidence


def test_update_statement_is_rejected() -> None:
    result = sql_execution_validator(
        "UPDATE customers SET name = 'Ada'",
        "postgres",
    )

    assert result.status is CheckStatus.FAILED
    assert "UPDATE" in result.evidence


def test_delete_statement_is_rejected() -> None:
    result = sql_execution_validator(
        "DELETE FROM customers",
        "postgres",
    )

    assert result.status is CheckStatus.FAILED
    assert "DELETE" in result.evidence


def test_drop_statement_is_rejected() -> None:
    result = sql_execution_validator(
        "DROP TABLE customers",
        "postgres",
    )

    assert result.status is CheckStatus.FAILED
    assert "DROP" in result.evidence


def test_nested_delete_inside_cte_is_rejected() -> None:
    result = sql_execution_validator(
        """
        WITH gone AS (
            DELETE FROM customers
            RETURNING *
        )
        SELECT * FROM gone
        """,
        "postgres",
    )

    assert result.status is CheckStatus.FAILED
    assert "DELETE" in result.evidence


def test_truncate_statement_is_rejected() -> None:
    result = sql_execution_validator(
        "TRUNCATE TABLE customers",
        "postgres",
    )

    assert result.status is CheckStatus.FAILED
    assert "TRUNCATE" in result.evidence


def test_multiple_statements_are_rejected() -> None:
    result = sql_execution_validator(
        "SELECT 1; DROP TABLE customers",
        "postgres",
    )

    assert result.status is CheckStatus.FAILED
    assert "Only one SQL statement" in result.evidence


def test_invalid_sql_is_rejected() -> None:
    result = sql_execution_validator(
        "SELECT FROM",
        "postgres",
    )

    assert result.status is CheckStatus.FAILED
    assert "could not be parsed" in result.evidence
