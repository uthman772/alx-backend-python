import sqlite3
from contextlib import contextmanager

@contextmanager
def database_connection(db_path):
    """
    Context manager for SQLite database connection.
    Usage:
        with database_connection('example.db') as conn:
            # use conn
    """
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()