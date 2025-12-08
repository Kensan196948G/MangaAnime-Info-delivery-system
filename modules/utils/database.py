"""
Database connection utilities for MangaAnime Info Delivery System.

Provides unified database connection helpers that eliminate code duplication
across the application.
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Optional
from pathlib import Path

# Default database path
DEFAULT_DB_PATH = os.getenv('DATABASE_PATH', './data/db.sqlite3')


def get_db_path(custom_path: Optional[str] = None) -> str:
    """
    Get the database path with environment variable support.

    Priority:
    1. custom_path parameter
    2. DATABASE_PATH environment variable
    3. Default path (./data/db.sqlite3)

    Args:
        custom_path: Optional custom database path

    Returns:
        Resolved database path
    """
    if custom_path:
        return custom_path

    return os.getenv('DATABASE_PATH', './data/db.sqlite3')


def ensure_db_directory(db_path: str) -> None:
    """
    Ensure the database directory exists.

    Args:
        db_path: Path to database file
    """
    db_dir = os.path.dirname(os.path.abspath(db_path))
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)


@contextmanager
def get_db_connection(db_path: Optional[str] = None, row_factory: bool = True):
    """
    Get a database connection with automatic cleanup.

    Unified connection helper that replaces all scattered sqlite3.connect() calls.
    Uses context manager for automatic connection cleanup.

    Args:
        db_path: Optional database path (uses DEFAULT_DB_PATH if None)
        row_factory: Whether to enable Row factory for dict-like access

    Yields:
        sqlite3.Connection: Database connection

    Example:
        >>> with get_db_connection() as conn:
        ...     cursor = conn.execute("SELECT * FROM works")
        ...     results = cursor.fetchall()
    """
    path = get_db_path(db_path)
    ensure_db_directory(path)

    conn = sqlite3.connect(path)

    if row_factory:
        conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_simple_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Get a simple database connection without context manager.

    Note: Caller is responsible for closing the connection.
    Use get_db_connection() context manager when possible.

    Args:
        db_path: Optional database path

    Returns:
        sqlite3.Connection with Row factory enabled

    Example:
        >>> conn = get_simple_connection()
        >>> try:
        ...     cursor = conn.execute("SELECT * FROM works")
        ... finally:
        ...     conn.close()
    """
    path = get_db_path(db_path)
    ensure_db_directory(path)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_db_manager(db_path: Optional[str] = None):
    """
    Get a DatabaseManager instance (singleton pattern).

    Args:
        db_path: Optional database path

    Returns:
        DatabaseManager instance from modules.db
    """
    from modules.db import DatabaseManager

    path = get_db_path(db_path)

    # Singleton pattern - reuse existing instance if available
    if not hasattr(get_db_manager, '_instances'):
        get_db_manager._instances = {}

    if path not in get_db_manager._instances:
        get_db_manager._instances[path] = DatabaseManager(path)

    return get_db_manager._instances[path]


def execute_query(
    query: str,
    params: Optional[tuple] = None,
    db_path: Optional[str] = None,
    fetch_one: bool = False,
    fetch_all: bool = True
):
    """
    Execute a database query with automatic connection management.

    Args:
        query: SQL query string
        params: Optional query parameters
        db_path: Optional database path
        fetch_one: Return single result
        fetch_all: Return all results

    Returns:
        Query results or None

    Example:
        >>> results = execute_query("SELECT * FROM works WHERE type = ?", ("anime",))
        >>> single = execute_query("SELECT * FROM works WHERE id = ?", (1,), fetch_one=True)
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, params or ())

        if fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        else:
            return cursor


def check_table_exists(table_name: str, db_path: Optional[str] = None) -> bool:
    """
    Check if a table exists in the database.

    Args:
        table_name: Name of the table to check
        db_path: Optional database path

    Returns:
        True if table exists, False otherwise
    """
    query = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """
    result = execute_query(query, (table_name,), db_path, fetch_one=True)
    return result is not None


def get_table_info(table_name: str, db_path: Optional[str] = None) -> list:
    """
    Get table schema information.

    Args:
        table_name: Name of the table
        db_path: Optional database path

    Returns:
        List of column information dicts
    """
    query = f"PRAGMA table_info({table_name})"
    return execute_query(query, db_path=db_path, fetch_all=True)


def get_database_stats(db_path: Optional[str] = None) -> dict:
    """
    Get database statistics.

    Args:
        db_path: Optional database path

    Returns:
        Dict with database statistics
    """
    path = get_db_path(db_path)

    stats = {
        'path': path,
        'exists': os.path.exists(path),
        'size_bytes': os.path.getsize(path) if os.path.exists(path) else 0,
    }

    if stats['exists']:
        with get_db_connection(db_path) as conn:
            # Get table count
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"
            )
            stats['table_count'] = cursor.fetchone()['count']

            # Get table names
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            stats['tables'] = [row['name'] for row in cursor.fetchall()]

    return stats
