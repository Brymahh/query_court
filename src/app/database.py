import psycopg


def check_database_connection(database_url: str) -> bool:
    """Check whether PostgreSQL accepts a connection.

    Parameters
    ----------
    database_url:
        PostgreSQL connection string.

    Returns
    -------
    bool
        True when a connection and test query succeed; otherwise False.
    """
    try:
        with psycopg.connect(database_url, connect_timeout=3) as connection:
            connection.execute("SELECT 1")
        return True
    except psycopg.Error:
        return False
