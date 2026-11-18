from collections.abc import Sequence

from sqlglot import ParseError, exp, parse

from app.models import ReviewLevel, SchemaColumn, SchemaContext, SchemaTable, SQLDialect


def build_no_schema_context() -> SchemaContext:
    """Build context for a review with no schema information
        provided by the user.

    Returns
    -------
    SchemaContext
        Empty schema context with the no-schema review level.
    """
    return SchemaContext(
        level=ReviewLevel.NO_SCHEMA,
        tables=[],
    )


def build_partial_schema_context(tables: Sequence[SchemaTable]) -> SchemaContext:
    """Build context from user-provided partial schema details.

    Parameters
    ----------
    tables:
        Tables and columns supplied by the user.

    Returns
    -------
    SchemaContext
        Partial schema context.
    """
    return SchemaContext(
        level=ReviewLevel.PARTIAL_SCHEMA,
        tables=list(tables),
    )


def parse_ddl_context(
    ddl: str,
    dialect: SQLDialect,
) -> SchemaContext:
    """Parse DDL into normalized schema metadata.

    Parameters
    ----------
    ddl:
        Data Definition Language (DDL) text supplied by the user.
    dialect:
        SQL dialect used to parse the DDL.

    Returns
    -------
    SchemaContext
        Full schema context extracted from the DDL.

    Raises
    ------
    ValueError
        If the DDL cannot be parsed or contains unsupported statements.
    """
    try:
        expressions = parse(ddl, read=str(dialect))
    except ParseError as error:
        raise ValueError(
            f"Invalid {dialect} DDL: {error}",
        ) from error

    # print(f"Expressions: {expressions}")             # Godsgift remember to remove this!!!!
    tables: list[SchemaTable] = []

    for expression in expressions:
        # print(f"Expression: {expression}")             # Godsgift remember to remove this!!!!
        if expression is None:
            continue

        if expression.key != "create" or expression.args.get("kind") != "TABLE":
            raise ValueError(
                "Only CREATE TABLE statements are supported in DDL input.",
            )

        schema = expression.find(exp.Schema)
        # print(f'Schema: {schema}')             # Godsgift remember to remove this!!!!

        if schema is None:
            raise ValueError(
                "CREATE statement does not contain a table schema.",
            )

        table = schema.this
        # print(f'Table: {table}')             # Godsgift remember to remove this!!!!

        if not isinstance(table, exp.Table):
            raise ValueError(
                "CREATE statement does not define a table.",
            )

        columns: list[SchemaColumn] = []

        for column_definition in schema.expressions:
            if not isinstance(column_definition, exp.ColumnDef):
                continue

            data_type = column_definition.args.get("kind")

            if data_type is None:
                continue

            columns.append(
                SchemaColumn(
                    name=column_definition.name,
                    data_type=data_type.sql(dialect=str(dialect)),
                )
            )

        tables.append(
            SchemaTable(
                name=table.name,
                columns=columns,
            )
        )
    return SchemaContext(
        level=ReviewLevel.FULL_SCHEMA,
        tables=tables,
    )
