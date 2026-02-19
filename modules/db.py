"""
Database module for Anime/Manga information delivery system.

This module provides SQLite database management functionality including:
- Connection management and initialization
- Table creation based on the schema in CLAUDE.md
- CRUD operations for works and releases
- Duplicate prevention and data integrity
- Transaction management

Database Schema:
- works: Stores anime/manga titles with metadata
- releases: Stores episode/volume release information
"""

import hashlib
import logging
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional


class DatabaseManager:
    """
    SQLite database manager for the anime/manga information system.

    Provides thread-safe database operations with proper connection management,
    transaction handling, data integrity enforcement, and connection pooling.
    """

    def __init__(self, db_path: str = "./db.sqlite3", max_connections: int = 5):
        """
        Initialize database manager with enhanced connection management.

        Args:
            db_path: Path to SQLite database file
            max_connections: Maximum number of concurrent connections
        """
        self.db_path = db_path
        self.max_connections = max_connections
        self.logger = logging.getLogger(__name__)
        self._local = threading.local()
        self._connection_pool = []
        self._pool_lock = threading.Lock()
        self._connection_refs = (
            set()
        )  # Use regular set instead of WeakSet due to sqlite3 limitation

        # Performance monitoring
        self._query_count = 0
        self._error_count = 0
        self._start_time = time.time()
        self._slow_query_threshold = 1.0  # Log queries taking > 1 second
        self._transaction_count = 0
        self._rollback_count = 0

        # Connection pool health monitoring
        self._pool_hits = 0  # Connections reused from pool
        self._pool_misses = 0  # New connections created
        self._pool_evictions = 0  # Connections removed from pool

        # Connection quality tracking
        self._connection_ages = {}  # Track connection creation times
        self._max_connection_age = 3600  # 1 hour max connection age

        # Ensure database directory exists
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # Initialize database schema
        self.initialize_database()

        # Validate database integrity
        self._validate_database_integrity()

    def _create_connection(self) -> sqlite3.Connection:
        """
        Create a new database connection with optimized settings.

        Returns:
            Configured SQLite connection
        """
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0,
            isolation_level=None,  # Enable autocommit mode for better performance
        )
        conn.row_factory = sqlite3.Row

        # Optimize SQLite settings
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for better concurrency
        conn.execute("PRAGMA synchronous = NORMAL")  # Balance between performance and safety
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA mmap_size = 268435456")  # 256MB memory map

        return conn

    @contextmanager
    def get_connection(self):
        """
        Get database connection with enhanced error handling and monitoring.

        Uses connection pooling for better performance in multi-threaded environment.
        """
        connection = None
        start_time = time.time()
        pool_hit = False

        try:
            # Try to get connection from thread-local storage first
            if not hasattr(self._local, "connection") or self._local.connection is None:
                connection = self._get_pooled_connection()
                self._local.connection = connection
            else:
                connection = self._local.connection
                pool_hit = True

            # Test connection validity and age
            if not self._is_connection_valid(connection):
                self.logger.debug("Invalid connection detected, creating new one")
                if connection:
                    self._close_connection_safely(connection)
                connection = self._create_connection()
                self._local.connection = connection
                pool_hit = False

            # Update statistics
            if pool_hit:
                self._pool_hits += 1
            else:
                self._pool_misses += 1

            self._query_count += 1
            yield connection

        except sqlite3.Error as e:
            self._error_count += 1
            self._rollback_count += 1
            if connection:
                try:
                    connection.rollback()
                except:
                    pass
            self.logger.error(f"Database operation failed: {e}")
            raise
        except Exception as e:
            self._error_count += 1
            if connection:
                try:
                    connection.rollback()
                except:
                    pass
            self.logger.error(f"Unexpected database error: {e}")
            raise
        finally:
            query_time = time.time() - start_time
            if query_time > self._slow_query_threshold:
                self.logger.warning(f"Slow database query: {query_time:.2f}s")

    def _get_pooled_connection(self) -> sqlite3.Connection:
        """Get connection from pool or create new one."""
        with self._pool_lock:
            # Clean up old connections first
            self._cleanup_old_connections()

            # Try to get from pool
            while self._connection_pool:
                connection = self._connection_pool.pop()
                if self._is_connection_valid(connection):
                    self._pool_hits += 1
                    return connection
                else:
                    self._close_connection_safely(connection)
                    self._pool_evictions += 1

            # Create new connection
            self._pool_misses += 1
            connection = self._create_connection()
            self._connection_ages[id(connection)] = time.time()
            return connection

    def _is_connection_valid(self, connection: sqlite3.Connection) -> bool:
        """Check if connection is valid and not too old."""
        if not connection:
            return False

        try:
            # Test basic functionality
            connection.execute("SELECT 1").fetchone()

            # Check age
            conn_id = id(connection)
            if conn_id in self._connection_ages:
                age = time.time() - self._connection_ages[conn_id]
                if age > self._max_connection_age:
                    self.logger.debug(f"Connection too old: {age:.1f}s")
                    return False

            return True

        except sqlite3.Error:
            return False

    def _cleanup_old_connections(self):
        """Remove old connections from pool."""
        current_time = time.time()
        valid_connections = []

        for connection in self._connection_pool:
            conn_id = id(connection)
            if (
                conn_id in self._connection_ages
                and current_time - self._connection_ages[conn_id] < self._max_connection_age
            ):
                if self._is_connection_valid(connection):
                    valid_connections.append(connection)
                    continue

            # Close invalid/old connection
            self._close_connection_safely(connection)
            if conn_id in self._connection_ages:
                del self._connection_ages[conn_id]
            self._pool_evictions += 1

        self._connection_pool = valid_connections

    def _close_connection_safely(self, connection: sqlite3.Connection):
        """Safely close a connection."""
        try:
            conn_id = id(connection)
            if conn_id in self._connection_ages:
                del self._connection_ages[conn_id]
            connection.close()
        except Exception as e:
            self.logger.debug(f"Error closing connection: {e}")

    @contextmanager
    def get_transaction(self):
        """
        Get database connection with explicit transaction management.

        Provides ACID transaction guarantees with automatic rollback on failure.
        """
        start_time = time.time()

        with self.get_connection() as conn:
            try:
                # Begin transaction explicitly
                conn.execute("BEGIN")
                self._transaction_count += 1

                yield conn

                # Commit if successful
                conn.commit()

                transaction_time = time.time() - start_time
                if transaction_time > self._slow_query_threshold:
                    self.logger.warning(f"Slow transaction: {transaction_time:.2f}s")

            except Exception:
                # Rollback on any error
                try:
                    conn.rollback()
                    self._rollback_count += 1
                except Exception as rollback_error:
                    self.logger.error(f"Rollback failed: {rollback_error}")
                raise

    def initialize_database(self):
        """
        Initialize database with required tables and indexes.

        Creates tables based on the schema defined in CLAUDE.md:
        - works: Stores anime/manga metadata
        - releases: Stores episode/volume release information
        - settings: Stores system settings
        """
        with self.get_connection() as conn:
            try:
                # Create works table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS works (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        title_kana TEXT,
                        title_en TEXT,
                        type TEXT CHECK(type IN ('anime','manga')),
                        official_url TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create releases table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS releases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        work_id INTEGER NOT NULL,
                        release_type TEXT CHECK(release_type IN ('episode','volume')),
                        number TEXT,
                        platform TEXT,
                        release_date DATE,
                        source TEXT,
                        source_url TEXT,
                        notified INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (work_id) REFERENCES works (id) ON DELETE CASCADE,
                        UNIQUE(work_id, release_type, number, platform, release_date)
                    )
                """)

                # Create settings table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE NOT NULL,
                        value TEXT,
                        value_type TEXT CHECK(value_type IN ('string','integer','boolean','json')),
                        description TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create notification_history table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS notification_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        notification_type TEXT CHECK(notification_type IN ('email','calendar')),
                        executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        success INTEGER DEFAULT 1,
                        error_message TEXT,
                        releases_count INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_works_title ON works(title)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_works_type ON works(type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_releases_work_id ON releases(work_id)")
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_releases_date ON releases(release_date)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_releases_notified ON releases(notified)"
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)")
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_notification_history_type ON notification_history(notification_type)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_notification_history_executed_at ON notification_history(executed_at)"
                )

                # Create pending_calendar_events table for development-mode calendar testing
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS pending_calendar_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        start_datetime TEXT NOT NULL,
                        end_datetime TEXT,
                        event_type TEXT CHECK(event_type IN ('anime','manga')),
                        work_id INTEGER,
                        release_id INTEGER,
                        synced INTEGER DEFAULT 0,
                        google_event_id TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_pending_calendar_events_synced "
                    "ON pending_calendar_events(synced)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_pending_calendar_events_event_type "
                    "ON pending_calendar_events(event_type)"
                )

                # calendar_events table (used by web UI)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS calendar_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        work_id INTEGER NOT NULL,
                        release_id INTEGER,
                        event_title TEXT NOT NULL,
                        event_date DATE,
                        description TEXT,
                        calendar_id TEXT,
                        event_id TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (work_id) REFERENCES works(id),
                        FOREIGN KEY (release_id) REFERENCES releases(id)
                    )
                    """)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_calendar_events_date "
                    "ON calendar_events(event_date)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_calendar_events_work "
                    "ON calendar_events(work_id)"
                )

                # collection_stats table (used by web UI dashboard)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS collection_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_id TEXT NOT NULL UNIQUE,
                        source_type TEXT CHECK(source_type IN ('api', 'rss', 'scraper')),
                        source_name TEXT,
                        items_collected INTEGER DEFAULT 0,
                        success_rate REAL DEFAULT 100.0,
                        avg_response_time REAL DEFAULT 0.0,
                        total_attempts INTEGER DEFAULT 0,
                        last_run DATETIME,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """)

                conn.commit()

                # Initialize default settings
                self._initialize_default_settings(conn)

                self.logger.info("Database initialized successfully")

            except sqlite3.Error as e:
                conn.rollback()
                self.logger.error(f"Failed to initialize database: {e}")
                raise

    def _initialize_default_settings(self, conn):
        """Initialize default settings if they don't exist."""
        default_settings = [
            (
                "notification_email",
                "kensan1969@gmail.com",
                "string",
                "デフォルト通知先メールアドレス",
            ),
            ("check_interval_hours", "1", "integer", "チェック間隔（時間）"),
            ("email_notifications_enabled", "true", "boolean", "メール通知を有効化"),
            ("calendar_enabled", "false", "boolean", "カレンダー登録を有効化"),
            ("max_notifications_per_day", "50", "integer", "1日あたりの最大通知数"),
        ]

        for key, value, value_type, description in default_settings:
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO settings (key, value, value_type, description)
                    VALUES (?, ?, ?, ?)
                """,
                    (key, value, value_type, description),
                )
            except sqlite3.Error:
                # Setting already exists, skip
                pass

        conn.commit()

    def generate_work_id_hash(self, title: str, work_type: str) -> str:
        """
        Generate unique hash for work identification.

        Args:
            title: Work title
            work_type: 'anime' or 'manga'

        Returns:
            SHA-256 hash string for work identification
        """
        combined = f"{title.lower().strip()}_{work_type}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]

    def create_work(
        self,
        title: str,
        work_type: str,
        title_kana: Optional[str] = None,
        title_en: Optional[str] = None,
        official_url: Optional[str] = None,
    ) -> int:
        """
        Create new work entry.

        Args:
            title: Work title (required)
            work_type: 'anime' or 'manga' (required)
            title_kana: Katakana reading (optional)
            title_en: English title (optional)
            official_url: Official website URL (optional)

        Returns:
            work_id of created work

        Raises:
            ValueError: If work_type is invalid
            sqlite3.Error: Database operation failed
        """
        if work_type not in ("anime", "manga"):
            raise ValueError(f"Invalid work_type: {work_type}. Must be 'anime' or 'manga'")

        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO works (title, title_kana, title_en, type, official_url)
                VALUES (?, ?, ?, ?, ?)
            """,
                (title, title_kana, title_en, work_type, official_url),
            )

            work_id = cursor.lastrowid
            conn.commit()

            self.logger.info(f"Created work: {title} (ID: {work_id}, Type: {work_type})")
            return work_id

    def get_work_by_title(
        self, title: str, work_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get work by title and optional type.

        Args:
            title: Work title to search for
            work_type: Optional work type filter ('anime' or 'manga')

        Returns:
            Work data as dictionary or None if not found
        """
        with self.get_connection() as conn:
            if work_type:
                cursor = conn.execute(
                    """
                    SELECT * FROM works WHERE title = ? AND type = ?
                """,
                    (title, work_type),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM works WHERE title = ?
                """,
                    (title,),
                )

            row = cursor.fetchone()
            return dict(row) if row else None

    def get_or_create_work(self, title: str, work_type: str, **kwargs) -> int:
        """
        Get existing work or create new one.

        Args:
            title: Work title
            work_type: 'anime' or 'manga'
            **kwargs: Additional fields for work creation

        Returns:
            work_id of existing or newly created work
        """
        existing_work = self.get_work_by_title(title, work_type)
        if existing_work:
            return existing_work["id"]

        return self.create_work(title, work_type, **kwargs)

    def create_release(
        self,
        work_id: int,
        release_type: str,
        number: Optional[str] = None,
        platform: Optional[str] = None,
        release_date: Optional[str] = None,
        source: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> int:
        """
        Create new release entry.

        Args:
            work_id: ID of associated work
            release_type: 'episode' or 'volume'
            number: Episode/volume number (optional)
            platform: Release platform (optional)
            release_date: Release date in YYYY-MM-DD format (optional)
            source: Data source name (optional)
            source_url: Source URL (optional)

        Returns:
            release_id of created release

        Raises:
            ValueError: If release_type is invalid
            sqlite3.IntegrityError: Duplicate release (handled by UNIQUE constraint)
        """
        if release_type not in ("episode", "volume"):
            raise ValueError(f"Invalid release_type: {release_type}. Must be 'episode' or 'volume'")

        with self.get_connection() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO releases (work_id, release_type, number, platform,
                                        release_date, source, source_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        work_id,
                        release_type,
                        number,
                        platform,
                        release_date,
                        source,
                        source_url,
                    ),
                )

                release_id = cursor.lastrowid
                conn.commit()

                self.logger.info(f"Created release: Work ID {work_id}, {release_type} {number}")
                return release_id

            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e):
                    self.logger.debug(
                        f"Duplicate release ignored: Work ID {work_id}, {release_type} {number}"
                    )
                    # Return existing release ID
                    cursor = conn.execute(
                        """
                        SELECT id FROM releases
                        WHERE work_id=? AND release_type=? AND number=? AND platform=? AND release_date=?
                    """,
                        (work_id, release_type, number, platform, release_date),
                    )
                    row = cursor.fetchone()
                    return row[0] if row else None
                else:
                    raise

    def get_unnotified_releases(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get releases that haven't been notified yet.

        Args:
            limit: Maximum number of releases to return (optional)

        Returns:
            List of release dictionaries with work information joined
        """
        with self.get_connection() as conn:
            query = """
                SELECT r.*, w.title, w.title_kana, w.title_en, w.type, w.official_url
                FROM releases r
                JOIN works w ON r.work_id = w.id
                WHERE r.notified = 0
                ORDER BY r.release_date ASC, r.created_at ASC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def mark_release_notified(self, release_id: int) -> bool:
        """
        Mark release as notified.

        Args:
            release_id: ID of release to mark as notified

        Returns:
            True if successful, False if release not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE releases SET notified = 1 WHERE id = ?
            """,
                (release_id,),
            )

            conn.commit()
            success = cursor.rowcount > 0

            if success:
                self.logger.info(f"Marked release {release_id} as notified")
            else:
                self.logger.warning(f"Release {release_id} not found for notification update")

            return success

    def get_work_stats(self) -> Dict[str, int]:
        """
        Get database statistics.

        Returns:
            Dictionary with counts of works by type and total releases
        """
        with self.get_connection() as conn:
            stats = {}

            # Count works by type
            cursor = conn.execute("""
                SELECT type, COUNT(*) FROM works GROUP BY type
            """)
            for row in cursor.fetchall():
                stats[f"{row[0]}_works"] = row[1]

            # Count total releases
            cursor = conn.execute("SELECT COUNT(*) FROM releases")
            stats["total_releases"] = cursor.fetchone()[0]

            # Count unnotified releases
            cursor = conn.execute("SELECT COUNT(*) FROM releases WHERE notified = 0")
            stats["unnotified_releases"] = cursor.fetchone()[0]

            return stats

    def cleanup_old_releases(self, days: int = 90) -> int:
        """
        Clean up old notified releases.

        Args:
            days: Remove releases older than this many days

        Returns:
            Number of releases deleted
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM releases
                WHERE notified = 1
                AND created_at < date('now', '-{} days')
            """.format(days))

            deleted_count = cursor.rowcount
            conn.commit()

            self.logger.info(f"Cleaned up {deleted_count} old releases")
            return deleted_count

    def _validate_database_integrity(self):
        """
        Validate database integrity and perform maintenance if needed.
        """
        try:
            with self.get_connection() as conn:
                # Check database integrity
                result = conn.execute("PRAGMA integrity_check").fetchone()
                if result[0] != "ok":
                    self.logger.warning(f"Database integrity check failed: {result[0]}")

                # Analyze database for optimization
                conn.execute("ANALYZE")

                self.logger.debug("Database integrity validation completed")
        except Exception as e:
            self.logger.error(f"Database integrity validation failed: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get database performance statistics.

        Returns:
            Dictionary with comprehensive performance metrics
        """
        uptime = time.time() - self._start_time

        # Calculate connection pool efficiency
        total_connection_requests = self._pool_hits + self._pool_misses
        pool_hit_rate = (
            self._pool_hits / total_connection_requests if total_connection_requests > 0 else 0
        )

        return {
            # Basic metrics
            "uptime_seconds": uptime,
            "total_queries": self._query_count,
            "total_errors": self._error_count,
            "total_transactions": self._transaction_count,
            "total_rollbacks": self._rollback_count,
            # Performance ratios
            "queries_per_second": self._query_count / uptime if uptime > 0 else 0,
            "error_rate": (self._error_count / self._query_count if self._query_count > 0 else 0),
            "rollback_rate": (
                self._rollback_count / self._transaction_count if self._transaction_count > 0 else 0
            ),
            # Connection pool metrics
            "active_connections": 1 if hasattr(self._local, "connection") else 0,
            "pool_size": len(self._connection_pool),
            "max_pool_size": self.max_connections,
            "pool_hit_rate": pool_hit_rate,
            "pool_hits": self._pool_hits,
            "pool_misses": self._pool_misses,
            "pool_evictions": self._pool_evictions,
            # Health indicators
            "health_score": self._calculate_health_score(),
            "performance_grade": self._calculate_performance_grade(),
            "connection_ages_tracked": len(self._connection_ages),
            "slow_query_threshold": self._slow_query_threshold,
        }

    def _calculate_health_score(self) -> float:
        """
        Calculate overall database health score (0.0 to 1.0).

        Returns:
            Health score from 0.0 (unhealthy) to 1.0 (perfect health)
        """
        if self._query_count == 0:
            return 1.0  # Perfect score for new database

        # Base score calculation
        error_penalty = min(self._error_count / self._query_count, 0.5)  # Max 50% penalty
        rollback_penalty = min(
            self._rollback_count / max(self._transaction_count, 1), 0.3
        )  # Max 30% penalty

        # Connection pool efficiency bonus
        total_requests = self._pool_hits + self._pool_misses
        pool_bonus = (self._pool_hits / max(total_requests, 1)) * 0.1  # Up to 10% bonus

        health_score = 1.0 - error_penalty - rollback_penalty + pool_bonus
        return max(0.0, min(1.0, health_score))

    def _calculate_performance_grade(self) -> str:
        """
        Calculate performance grade based on metrics.

        Returns:
            Performance grade: 'A', 'B', 'C', 'D', or 'F'
        """
        health_score = self._calculate_health_score()

        if health_score >= 0.9:
            return "A"  # Excellent
        elif health_score >= 0.8:
            return "B"  # Good
        elif health_score >= 0.7:
            return "C"  # Fair
        elif health_score >= 0.6:
            return "D"  # Poor
        else:
            return "F"  # Failing

    def optimize_database(self):
        """
        Perform database optimization operations.
        """
        try:
            with self.get_connection() as conn:
                self.logger.info("Starting database optimization...")

                # Vacuum to reclaim space and defragment
                conn.execute("VACUUM")

                # Update statistics for query optimizer
                conn.execute("ANALYZE")

                # Rebuild indexes if needed
                conn.execute("REINDEX")

                self.logger.info("Database optimization completed")
        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value from the database.

        Args:
            key: Setting key
            default: Default value if setting doesn't exist

        Returns:
            Setting value with proper type conversion
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT value, value_type FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()

            if not row:
                return default

            value, value_type = row["value"], row["value_type"]

            # Convert value based on type
            if value_type == "integer":
                return int(value)
            elif value_type == "boolean":
                return value.lower() in ("true", "1", "yes")
            elif value_type == "json":
                import json

                return json.loads(value)
            else:
                return value

    def set_setting(self, key: str, value: Any, value_type: str = "string", description: str = ""):
        """
        Set a setting value in the database.

        Args:
            key: Setting key
            value: Setting value
            value_type: Type of value ('string', 'integer', 'boolean', 'json')
            description: Optional description
        """
        # Convert value to string for storage
        if value_type == "json":
            import json

            value_str = json.dumps(value)
        elif value_type == "boolean":
            value_str = "true" if value else "false"
        else:
            value_str = str(value)

        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value, value_type, description, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    value_type = excluded.value_type,
                    description = excluded.description,
                    updated_at = CURRENT_TIMESTAMP
            """,
                (key, value_str, value_type, description),
            )
            conn.commit()

    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all settings from the database.

        Returns:
            Dictionary of all settings with proper type conversion
        """
        settings = {}
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT key, value, value_type FROM settings")
            for row in cursor.fetchall():
                key, value, value_type = row["key"], row["value"], row["value_type"]

                # Convert value based on type
                if value_type == "integer":
                    settings[key] = int(value)
                elif value_type == "boolean":
                    settings[key] = value.lower() in ("true", "1", "yes")
                elif value_type == "json":
                    import json

                    settings[key] = json.loads(value)
                else:
                    settings[key] = value

        return settings

    def update_settings(self, settings: Dict[str, Any]):
        """
        Update multiple settings at once.

        Args:
            settings: Dictionary of settings to update
        """
        with self.get_connection() as conn:
            for key, value in settings.items():
                # Determine value type
                if isinstance(value, bool):
                    value_type = "boolean"
                    value_str = "true" if value else "false"
                elif isinstance(value, int):
                    value_type = "integer"
                    value_str = str(value)
                elif isinstance(value, (dict, list)):
                    import json

                    value_type = "json"
                    value_str = json.dumps(value)
                else:
                    value_type = "string"
                    value_str = str(value)

                conn.execute(
                    """
                    INSERT INTO settings (key, value, value_type, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        value_type = excluded.value_type,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    (key, value_str, value_type),
                )

            conn.commit()

    def record_notification_history(
        self,
        notification_type: str,
        success: bool = True,
        error_message: Optional[str] = None,
        releases_count: int = 0,
    ) -> int:
        """
        Record notification execution history.

        Args:
            notification_type: 'email' or 'calendar'
            success: Whether the notification was successful
            error_message: Error message if failed
            releases_count: Number of releases processed

        Returns:
            ID of created history record
        """
        if notification_type not in ("email", "calendar"):
            raise ValueError(
                f"Invalid notification_type: {notification_type}. Must be 'email' or 'calendar'"
            )

        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO notification_history (notification_type, success, error_message, releases_count)
                VALUES (?, ?, ?, ?)
            """,
                (notification_type, 1 if success else 0, error_message, releases_count),
            )

            history_id = cursor.lastrowid
            conn.commit()

            self.logger.info(
                f"Recorded {notification_type} notification history (ID: {history_id}, Success: {success}, Count: {releases_count})"
            )
            return history_id

    def get_notification_history(
        self, notification_type: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get notification execution history.

        Args:
            notification_type: Filter by type ('email' or 'calendar'), None for all
            limit: Maximum number of records to return

        Returns:
            List of history records
        """
        with self.get_connection() as conn:
            if notification_type:
                cursor = conn.execute(
                    """
                    SELECT * FROM notification_history
                    WHERE notification_type = ?
                    ORDER BY executed_at DESC
                    LIMIT ?
                """,
                    (notification_type, limit),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM notification_history
                    ORDER BY executed_at DESC
                    LIMIT ?
                """,
                    (limit,),
                )

            return [dict(row) for row in cursor.fetchall()]

    def get_last_notification_time(self, notification_type: str) -> Optional[datetime]:
        """
        Get the last successful notification execution time.

        Args:
            notification_type: 'email' or 'calendar'

        Returns:
            Datetime of last execution, or None if no history
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT executed_at FROM notification_history
                WHERE notification_type = ? AND success = 1
                ORDER BY executed_at DESC
                LIMIT 1
            """,
                (notification_type,),
            )

            row = cursor.fetchone()
            if row:
                return datetime.fromisoformat(row["executed_at"])
            return None

    def get_notification_statistics(
        self, notification_type: Optional[str] = None, days: int = 7
    ) -> Dict[str, Any]:
        """
        Get notification statistics.

        Args:
            notification_type: Filter by type, None for all
            days: Number of days to analyze

        Returns:
            Dictionary with statistics
        """
        with self.get_connection() as conn:
            where_clause = ""
            params = []

            if notification_type:
                where_clause = "WHERE notification_type = ? AND"
                params.append(notification_type)
            else:
                where_clause = "WHERE"

            # Total executions
            cursor = conn.execute(
                f"""
                SELECT COUNT(*) as total FROM notification_history
                {where_clause} executed_at >= datetime('now', '-{days} days')
            """,
                params,
            )
            total = cursor.fetchone()["total"]

            # Success count
            cursor = conn.execute(
                f"""
                SELECT COUNT(*) as success_count FROM notification_history
                {where_clause} success = 1 AND executed_at >= datetime('now', '-{days} days')
            """,
                params,
            )
            success_count = cursor.fetchone()["success_count"]

            # Failure count
            cursor = conn.execute(
                f"""
                SELECT COUNT(*) as failure_count FROM notification_history
                {where_clause} success = 0 AND executed_at >= datetime('now', '-{days} days')
            """,
                params,
            )
            failure_count = cursor.fetchone()["failure_count"]

            # Total releases processed
            cursor = conn.execute(
                f"""
                SELECT SUM(releases_count) as total_releases FROM notification_history
                {where_clause} success = 1 AND executed_at >= datetime('now', '-{days} days')
            """,
                params,
            )
            total_releases = cursor.fetchone()["total_releases"] or 0

            # Recent errors
            error_params = params + [5]  # limit to 5 recent errors
            cursor = conn.execute(
                f"""
                SELECT executed_at, error_message, releases_count FROM notification_history
                {where_clause} success = 0 AND executed_at >= datetime('now', '-{days} days')
                ORDER BY executed_at DESC
                LIMIT ?
            """,
                error_params,
            )
            recent_errors = [dict(row) for row in cursor.fetchall()]

            # Calculate success rate
            success_rate = (success_count / total * 100) if total > 0 else 0.0

            return {
                "total_executions": total,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": round(success_rate, 2),
                "total_releases_processed": total_releases,
                "recent_errors": recent_errors,
                "period_days": days,
                "notification_type": notification_type or "all",
            }

    def execute_wal_checkpoint(self) -> dict:
        """
        Execute WAL checkpoint to consolidate WAL file into main database.

        This should be called periodically to prevent WAL file from growing too large
        and to ensure data durability.

        Returns:
            dict: Checkpoint result with busy, log, and checkpointed page counts
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                result = cursor.fetchone()
                checkpoint_info = {
                    "busy": result[0],
                    "log_pages": result[1],
                    "checkpointed_pages": result[2],
                    "success": result[0] == 0,
                    "timestamp": datetime.now().isoformat(),
                }
                self.logger.info(
                    f"WAL checkpoint executed: busy={result[0]}, "
                    f"log={result[1]}, checkpointed={result[2]}"
                )
                return checkpoint_info
        except Exception as e:
            self.logger.error(f"WAL checkpoint failed: {e}")
            return {"success": False, "error": str(e)}

    def check_integrity(self) -> dict:
        """
        Check database integrity.

        Returns:
            dict: Integrity check result
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("PRAGMA integrity_check;")
                result = cursor.fetchone()[0]
                is_valid = result == "ok"
                return {
                    "valid": is_valid,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as e:
            self.logger.error(f"Integrity check failed: {e}")
            return {"valid": False, "error": str(e)}

    def save_calendar_event(self, event_data: dict) -> Optional[int]:
        """
        Save a calendar event to pending_calendar_events table.

        Args:
            event_data: Dictionary with event fields:
                - title (required): Event title
                - description: Event description
                - start_datetime (required): ISO format datetime string
                - end_datetime: ISO format datetime string
                - event_type: 'anime' or 'manga'
                - work_id: Associated work ID
                - release_id: Associated release ID

        Returns:
            ID of inserted record, or None on failure
        """
        required_fields = ("title", "start_datetime")
        for field in required_fields:
            if not event_data.get(field):
                self.logger.error(f"save_calendar_event: missing required field '{field}'")
                return None

        event_type = event_data.get("event_type")
        if event_type and event_type not in ("anime", "manga"):
            self.logger.error(f"save_calendar_event: invalid event_type '{event_type}'")
            return None

        with self.get_connection() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO pending_calendar_events
                        (title, description, start_datetime, end_datetime,
                         event_type, work_id, release_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_data["title"],
                        event_data.get("description"),
                        event_data["start_datetime"],
                        event_data.get("end_datetime"),
                        event_type,
                        event_data.get("work_id"),
                        event_data.get("release_id"),
                    ),
                )
                event_id = cursor.lastrowid
                conn.commit()
                self.logger.info(f"Saved calendar event: '{event_data['title']}' (ID: {event_id})")
                return event_id
            except sqlite3.Error as e:
                self.logger.error(f"Failed to save calendar event: {e}")
                return None

    def get_pending_calendar_events(self, synced: bool = False) -> List[dict]:
        """
        Retrieve calendar events from pending_calendar_events table.

        Args:
            synced: If False (default), return only unsynced events.
                    If True, return only already-synced events.

        Returns:
            List of event dictionaries ordered by start_datetime ascending
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM pending_calendar_events
                WHERE synced = ?
                ORDER BY start_datetime ASC
                """,
                (1 if synced else 0,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def mark_calendar_event_synced(self, event_id: int, google_event_id: str) -> bool:
        """
        Mark a pending calendar event as synced to Google Calendar.

        Args:
            event_id: Local database ID of the pending_calendar_events row
            google_event_id: Google Calendar event ID returned by the API

        Returns:
            True if the row was updated, False if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE pending_calendar_events
                SET synced = 1, google_event_id = ?
                WHERE id = ?
                """,
                (google_event_id, event_id),
            )
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                self.logger.info(
                    f"Marked calendar event {event_id} as synced "
                    f"(google_event_id={google_event_id})"
                )
            else:
                self.logger.warning(f"Calendar event {event_id} not found for sync update")
            return success

    def close_connections(self):
        """Close all database connections and clean up resources."""
        # Execute WAL checkpoint before closing
        try:
            self.execute_wal_checkpoint()
        except Exception as e:
            self.logger.warning(f"WAL checkpoint before close failed: {e}")

        with self._pool_lock:
            # Close pooled connections
            for conn in self._connection_pool:
                try:
                    conn.close()
                except:
                    pass
            self._connection_pool.clear()

        # Close thread-local connections
        if hasattr(self._local, "connection"):
            try:
                self._local.connection.close()
            except:
                pass
            delattr(self._local, "connection")

        # Clear connection references
        self._connection_refs.clear()

        self.logger.info("All database connections closed")


# Global database instance
db = DatabaseManager()


def get_db() -> DatabaseManager:
    """Get the global database manager instance."""
    return db
