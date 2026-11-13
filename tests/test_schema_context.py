import pytest

from app.models import ReviewLevel, SchemaColumn, SchemaTable
from app.schema import (
    build_no_schema_context,
    build_partial_schema_context,
    parse_ddl_context,
)


def test_build_no_schema_context() -> None:
    context = build_no_schema_context()

    assert context.level is ReviewLevel.NO_SCHEMA
    assert context.tables == []


def test_build_partial_schema_context() -> None:
    tables = [
        SchemaTable(
            name="customers",
            columns=[
                SchemaColumn(name="id", data_type="INTEGER"),
                SchemaColumn(name="name", data_type="TEXT"),
            ],
        )
    ]

    context = build_partial_schema_context(tables)

    assert context.level is ReviewLevel.PARTIAL_SCHEMA
    assert len(context.tables) == 1
    assert context.tables[0].name == "customers"
    assert len(context.tables[0].columns) == 2


def test_parse_postgres_ddl_context() -> None:
    ddl = """
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        country TEXT
    );
    """

    context = parse_ddl_context(ddl, "postgres")

    assert context.level is ReviewLevel.FULL_SCHEMA
    assert len(context.tables) == 1
    assert context.tables[0].name == "customers"

    column_names = {column.name for column in context.tables[0].columns}

    assert column_names == {"id", "name", "country"}


def test_parse_multiple_tables() -> None:
    ddl = """
    CREATE TABLE customers (
        id INTEGER,
        name TEXT
    );

    CREATE TABLE orders (
        id INTEGER,
        customer_id INTEGER
    );
    """

    context = parse_ddl_context(ddl, "postgres")

    assert context.level is ReviewLevel.FULL_SCHEMA
    assert {table.name for table in context.tables} == {
        "customers",
        "orders",
    }


def test_invalid_ddl_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid postgres DDL"):
        parse_ddl_context(
            "CREATE TABLE customers (",
            "postgres",
        )


def test_non_table_ddl_is_rejected() -> None:
    with pytest.raises(ValueError, match="CREATE TABLE"):
        parse_ddl_context(
            "CREATE INDEX customer_name_idx ON customers (name)",
            "postgres",
        )
