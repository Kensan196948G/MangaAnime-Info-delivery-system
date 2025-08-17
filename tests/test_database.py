#!/usr/bin/env python3
"""
Unit tests for database operations
"""

import pytest
import sqlite3
import tempfile
from datetime import datetime
from unittest.mock import patch, Mock


# Test database manager functionality
class TestDatabaseManager:
    """Test database management operations."""

    @pytest.mark.db
    def test_database_initialization(self, temp_db):
        """Test database initialization and schema creation."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Verify tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert "works" in tables
        assert "releases" in tables

        # Verify works table schema
        cursor.execute("PRAGMA table_info(works)")
        works_columns = [row[1] for row in cursor.fetchall()]
        expected_works_columns = [
            "id",
            "title",
            "title_kana",
            "title_en",
            "type",
            "official_url",
            "created_at",
        ]

        for col in expected_works_columns:
            assert col in works_columns

        # Verify releases table schema
        cursor.execute("PRAGMA table_info(releases)")
        releases_columns = [row[1] for row in cursor.fetchall()]
        expected_releases_columns = [
            "id",
            "work_id",
            "release_type",
            "number",
            "platform",
            "release_date",
            "source",
            "source_url",
            "notified",
            "created_at",
        ]

        for col in expected_releases_columns:
            assert col in releases_columns

        conn.close()

    @pytest.mark.db
    def test_insert_work(self, temp_db, sample_work_data):
        """Test work insertion with proper data validation."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        work = sample_work_data[0]
        cursor.execute(
            """
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                work["title"],
                work["title_kana"],
                work["title_en"],
                work["type"],
                work["official_url"],
            ),
        )

        work_id = cursor.lastrowid
        conn.commit()

        # Verify insertion
        cursor.execute("SELECT * FROM works WHERE id = ?", (work_id,))
        result = cursor.fetchone()

        assert result is not None
        assert result[1] == work["title"]  # title
        assert result[2] == work["title_kana"]  # title_kana
        assert result[3] == work["title_en"]  # title_en
        assert result[4] == work["type"]  # type
        assert result[5] == work["official_url"]  # official_url

        conn.close()

    @pytest.mark.db
    def test_insert_release(self, temp_db, sample_work_data, sample_release_data):
        """Test release insertion with foreign key relationships."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # First insert a work
        work = sample_work_data[0]
        cursor.execute(
            """
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                work["title"],
                work["title_kana"],
                work["title_en"],
                work["type"],
                work["official_url"],
            ),
        )

        work_id = cursor.lastrowid
        conn.commit()

        # Now insert a release
        release = sample_release_data[0]
        release["work_id"] = work_id

        cursor.execute(
            """
            INSERT INTO releases (work_id, release_type, number, platform, release_date, source, source_url, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                release["work_id"],
                release["release_type"],
                release["number"],
                release["platform"],
                release["release_date"],
                release["source"],
                release["source_url"],
                release["notified"],
            ),
        )

        release_id = cursor.lastrowid
        conn.commit()

        # Verify insertion
        cursor.execute(
            """
            SELECT r.*, w.title 
            FROM releases r 
            JOIN works w ON r.work_id = w.id 
            WHERE r.id = ?
        """,
            (release_id,),
        )
        result = cursor.fetchone()

        assert result is not None
        assert result[1] == work_id  # work_id
        assert result[2] == release["release_type"]  # release_type
        assert result[3] == release["number"]  # number
        assert result[-1] == work["title"]  # joined title

        conn.close()

    @pytest.mark.db
    def test_unique_constraint_enforcement(
        self, temp_db, sample_work_data, sample_release_data
    ):
        """Test unique constraint on releases table."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Insert work
        work = sample_work_data[0]
        cursor.execute(
            """
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                work["title"],
                work["title_kana"],
                work["title_en"],
                work["type"],
                work["official_url"],
            ),
        )

        work_id = cursor.lastrowid
        conn.commit()

        # Insert first release
        release = sample_release_data[0]
        release["work_id"] = work_id

        cursor.execute(
            """
            INSERT INTO releases (work_id, release_type, number, platform, release_date, source, source_url, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                release["work_id"],
                release["release_type"],
                release["number"],
                release["platform"],
                release["release_date"],
                release["source"],
                release["source_url"],
                release["notified"],
            ),
        )
        conn.commit()

        # Try to insert duplicate - should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO releases (work_id, release_type, number, platform, release_date, source, source_url, notified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    release["work_id"],
                    release["release_type"],
                    release["number"],
                    release["platform"],
                    release["release_date"],
                    release["source"],
                    release["source_url"],
                    release["notified"],
                ),
            )
            conn.commit()

        conn.close()

    @pytest.mark.db
    def test_type_constraint_enforcement(self, temp_db):
        """Test type constraints on works and releases tables."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Test invalid work type
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO works (title, type) VALUES (?, ?)
            """,
                ("Test Title", "invalid_type"),
            )
            conn.commit()

        # Test invalid release type
        cursor.execute(
            """
            INSERT INTO works (title, type) VALUES (?, ?)
        """,
            ("Test Title", "anime"),
        )
        work_id = cursor.lastrowid
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO releases (work_id, release_type) VALUES (?, ?)
            """,
                (work_id, "invalid_release_type"),
            )
            conn.commit()

        conn.close()

    @pytest.mark.db
    def test_query_unnotified_releases(
        self, temp_db, sample_work_data, sample_release_data
    ):
        """Test querying unnotified releases."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Insert work
        work = sample_work_data[0]
        cursor.execute(
            """
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                work["title"],
                work["title_kana"],
                work["title_en"],
                work["type"],
                work["official_url"],
            ),
        )

        work_id = cursor.lastrowid
        conn.commit()

        # Insert multiple releases with different notification status
        releases = sample_release_data[:2]
        for i, release in enumerate(releases):
            release["work_id"] = work_id
            release["notified"] = i  # First one unnotified (0), second one notified (1)

            cursor.execute(
                """
                INSERT INTO releases (work_id, release_type, number, platform, release_date, source, source_url, notified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    release["work_id"],
                    release["release_type"],
                    f"episode_{i}",
                    release["platform"],
                    release["release_date"],
                    release["source"],
                    release["source_url"],
                    release["notified"],
                ),
            )

        conn.commit()

        # Query unnotified releases
        cursor.execute(
            """
            SELECT r.*, w.title 
            FROM releases r 
            JOIN works w ON r.work_id = w.id 
            WHERE r.notified = 0
        """
        )
        unnotified = cursor.fetchall()

        assert len(unnotified) == 1
        assert unnotified[0][8] == 0  # notified column should be 0

        conn.close()

    @pytest.mark.db
    def test_update_notification_status(
        self, temp_db, sample_work_data, sample_release_data
    ):
        """Test updating notification status after sending notifications."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Insert work and release
        work = sample_work_data[0]
        cursor.execute(
            """
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                work["title"],
                work["title_kana"],
                work["title_en"],
                work["type"],
                work["official_url"],
            ),
        )

        work_id = cursor.lastrowid

        release = sample_release_data[0]
        release["work_id"] = work_id
        cursor.execute(
            """
            INSERT INTO releases (work_id, release_type, number, platform, release_date, source, source_url, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                release["work_id"],
                release["release_type"],
                release["number"],
                release["platform"],
                release["release_date"],
                release["source"],
                release["source_url"],
                release["notified"],
            ),
        )

        release_id = cursor.lastrowid
        conn.commit()

        # Update notification status
        cursor.execute("UPDATE releases SET notified = 1 WHERE id = ?", (release_id,))
        conn.commit()

        # Verify update
        cursor.execute("SELECT notified FROM releases WHERE id = ?", (release_id,))
        result = cursor.fetchone()

        assert result[0] == 1

        conn.close()


class TestDatabasePerformance:
    """Test database performance and optimization."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_bulk_insert_performance(self, temp_db):
        """Test bulk insert performance with large datasets."""
        import time

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Generate large dataset
        works_data = []
        for i in range(1000):
            works_data.append(
                (
                    f"Test Title {i}",
                    f"テストタイトル{i}",
                    f"Test Title EN {i}",
                    "anime" if i % 2 == 0 else "manga",
                    f"https://example.com/{i}",
                )
            )

        # Measure bulk insert time
        start_time = time.time()
        cursor.executemany(
            """
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (?, ?, ?, ?, ?)
        """,
            works_data,
        )
        conn.commit()
        end_time = time.time()

        insert_time = end_time - start_time

        # Verify all records inserted
        cursor.execute("SELECT COUNT(*) FROM works")
        count = cursor.fetchone()[0]

        assert count == 1000
        assert insert_time < 5.0  # Should complete within 5 seconds

        conn.close()

    @pytest.mark.performance
    def test_query_performance_with_indexes(self, temp_db):
        """Test query performance and verify indexes are effective."""
        import time

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Insert test data
        for i in range(100):
            cursor.execute(
                """
                INSERT INTO works (title, type) VALUES (?, ?)
            """,
                (f"Test Title {i}", "anime"),
            )

            work_id = cursor.lastrowid

            for j in range(10):
                cursor.execute(
                    """
                    INSERT INTO releases (work_id, release_type, number, release_date, notified)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (work_id, "episode", str(j + 1), "2024-01-01", 0 if j < 5 else 1),
                )

        conn.commit()

        # Test query performance
        start_time = time.time()
        cursor.execute(
            """
            SELECT r.*, w.title 
            FROM releases r 
            JOIN works w ON r.work_id = w.id 
            WHERE r.notified = 0 
            ORDER BY r.release_date DESC
        """
        )
        results = cursor.fetchall()
        end_time = time.time()

        query_time = end_time - start_time

        assert len(results) == 500  # 100 works * 5 unnotified releases each
        assert query_time < 1.0  # Should complete within 1 second

        conn.close()
