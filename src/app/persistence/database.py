"""Asynchronous PostgreSQL connection management."""

import psycopg
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row


class Database:
    """Create asynchronous PostgreSQL connections."""

    def __init__(self, database_url: str) -> None:
        """Store the database connection URL.

        Parameters
        ----------
        database_url:
            PostgreSQL connection string.
        """
        self._database_url = database_url

    async def connect(self) -> AsyncConnection[DictRow]:
        """Open an asynchronous PostgreSQL connection.

        Returns
        -------
        AsyncConnection
            Open database connection using dictionary rows.
        """
        return await psycopg.AsyncConnection.connect(
            self._database_url,
            row_factory=dict_row,
        )
