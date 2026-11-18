from unittest.mock import patch

from app.models import CheckStatus
from app.validation import validate_sql


def test_valid_postgres_sql_passes() -> None:
    result = validate_sql(
        "SELECT name FROM customers",
        "postgres",
    )

    assert result.name == "syntax"
    assert result.status is CheckStatus.PASSED
    assert "parsed successfully" in result.evidence


def test_invalid_postgres_sql_fails() -> None:
    result = validate_sql(
        "SELECT - FROM customers",
        "postgres",
    )

    assert result.name == "syntax"
    assert result.status is CheckStatus.FAILED
    assert "Invalid postgres SQL" in result.evidence


def test_unsupported_dialect_is_unavailable() -> None:
    result = validate_sql(
        "SELECT name FROM customers",
        "mysql",
    )

    assert result.name == "syntax"
    assert result.status is CheckStatus.UNAVAILABLE
    assert "not supported yet" in result.evidence


def test_selected_dialect_is_passed_to_sqlglot() -> None:
    with patch("app.validation.sql.parse_one") as parse_one_mock:
        validate_sql("SELECT 1", "postgres")

    parse_one_mock.assert_called_once_with(
        "SELECT 1",
        read="postgres",
    )
