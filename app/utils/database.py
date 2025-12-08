"""
Database utility functions for the Flask web application.
"""

import sqlite3

# Default database path
DATABASE_PATH = "db.sqlite3"


def get_db_connection(db_path: str = None):
    """
    Get database connection with row factory for dict-like access.

    Args:
        db_path: Optional path to database file

    Returns:
        sqlite3.Connection with Row factory
    """
    path = db_path or DATABASE_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn
