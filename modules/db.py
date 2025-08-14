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

import sqlite3
import logging
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
import threading
import os
import time
from concurrent.futures import ThreadPoolExecutor


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
        self._connection_refs = set()  # Use regular set instead of WeakSet due to sqlite3 limitation
        
        # Performance monitoring
        self._query_count = 0
        self._error_count = 0
        self._start_time = time.time()
        
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
            isolation_level=None  # Enable autocommit mode for better performance
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
        
        try:
            # Try to get connection from thread-local storage first
            if not hasattr(self._local, 'connection') or self._local.connection is None:
                with self._pool_lock:
                    if self._connection_pool:
                        connection = self._connection_pool.pop()
                        self._local.connection = connection
                    else:
                        connection = self._create_connection()
                        self._local.connection = connection
            else:
                connection = self._local.connection
            
            # Test connection validity
            try:
                connection.execute("SELECT 1").fetchone()
            except sqlite3.Error:
                # Connection is stale, create new one
                connection.close()
                connection = self._create_connection()
                self._local.connection = connection
            
            self._query_count += 1
            yield connection
            
        except sqlite3.Error as e:
            self._error_count += 1
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
            if query_time > 1.0:  # Log slow queries
                self.logger.warning(f"Slow database query: {query_time:.2f}s")
    
    def initialize_database(self):
        """
        Initialize database with required tables and indexes.
        
        Creates tables based on the schema defined in CLAUDE.md:
        - works: Stores anime/manga metadata
        - releases: Stores episode/volume release information
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
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_works_title ON works(title)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_works_type ON works(type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_releases_work_id ON releases(work_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_releases_date ON releases(release_date)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_releases_notified ON releases(notified)")
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
            except sqlite3.Error as e:
                conn.rollback()
                self.logger.error(f"Failed to initialize database: {e}")
                raise
    
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
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]
    
    def create_work(self, title: str, work_type: str, 
                   title_kana: Optional[str] = None,
                   title_en: Optional[str] = None,
                   official_url: Optional[str] = None) -> int:
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
        if work_type not in ('anime', 'manga'):
            raise ValueError(f"Invalid work_type: {work_type}. Must be 'anime' or 'manga'")
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO works (title, title_kana, title_en, type, official_url)
                VALUES (?, ?, ?, ?, ?)
            """, (title, title_kana, title_en, work_type, official_url))
            
            work_id = cursor.lastrowid
            conn.commit()
            
            self.logger.info(f"Created work: {title} (ID: {work_id}, Type: {work_type})")
            return work_id
    
    def get_work_by_title(self, title: str, work_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
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
                cursor = conn.execute("""
                    SELECT * FROM works WHERE title = ? AND type = ?
                """, (title, work_type))
            else:
                cursor = conn.execute("""
                    SELECT * FROM works WHERE title = ?
                """, (title,))
            
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
            return existing_work['id']
        
        return self.create_work(title, work_type, **kwargs)
    
    def create_release(self, work_id: int, release_type: str,
                      number: Optional[str] = None,
                      platform: Optional[str] = None,
                      release_date: Optional[str] = None,
                      source: Optional[str] = None,
                      source_url: Optional[str] = None) -> int:
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
        if release_type not in ('episode', 'volume'):
            raise ValueError(f"Invalid release_type: {release_type}. Must be 'episode' or 'volume'")
        
        with self.get_connection() as conn:
            try:
                cursor = conn.execute("""
                    INSERT INTO releases (work_id, release_type, number, platform, 
                                        release_date, source, source_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (work_id, release_type, number, platform, release_date, source, source_url))
                
                release_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Created release: Work ID {work_id}, {release_type} {number}")
                return release_id
                
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e):
                    self.logger.debug(f"Duplicate release ignored: Work ID {work_id}, {release_type} {number}")
                    # Return existing release ID
                    cursor = conn.execute("""
                        SELECT id FROM releases 
                        WHERE work_id=? AND release_type=? AND number=? AND platform=? AND release_date=?
                    """, (work_id, release_type, number, platform, release_date))
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
            cursor = conn.execute("""
                UPDATE releases SET notified = 1 WHERE id = ?
            """, (release_id,))
            
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
            stats['total_releases'] = cursor.fetchone()[0]
            
            # Count unnotified releases
            cursor = conn.execute("SELECT COUNT(*) FROM releases WHERE notified = 0")
            stats['unnotified_releases'] = cursor.fetchone()[0]
            
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
            Dictionary with performance metrics
        """
        uptime = time.time() - self._start_time
        return {
            'uptime_seconds': uptime,
            'total_queries': self._query_count,
            'total_errors': self._error_count,
            'queries_per_second': self._query_count / uptime if uptime > 0 else 0,
            'error_rate': self._error_count / self._query_count if self._query_count > 0 else 0,
            'active_connections': 1 if hasattr(self._local, 'connection') else 0,
            'pool_size': len(self._connection_pool)
        }
    
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
    
    def close_connections(self):
        """Close all database connections and clean up resources."""
        with self._pool_lock:
            # Close pooled connections
            for conn in self._connection_pool:
                try:
                    conn.close()
                except:
                    pass
            self._connection_pool.clear()
        
        # Close thread-local connections
        if hasattr(self._local, 'connection'):
            try:
                self._local.connection.close()
            except:
                pass
            delattr(self._local, 'connection')
        
        # Clear connection references
        self._connection_refs.clear()
        
        self.logger.info("All database connections closed")


# Global database instance
db = DatabaseManager()


def get_db() -> DatabaseManager:
    """Get the global database manager instance."""
    return db