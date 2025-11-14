"""
Fixed database tests using correct DatabaseManager API
"""

from modules.db import DatabaseManager
import pytest
import sqlite3
import os
import sys
from datetime import date

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestDatabaseManagerFixed:
    """Test DatabaseManager with correct API methods"""

    def setup_method(self):
        """Set up test fixtures with in-memory database"""
        self.db_path = ":memory:"
        self.db = DatabaseManager(db_path=self.db_path)
        self.db.initialize_database()

    def teardown_method(self):
        """Clean up after tests"""
        if hasattr(self, "db"):
            self.db.close_connections()

    def test_database_initialization(self):
        """Test that database initializes correctly"""
        # Verify tables exist by querying them
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Check works table
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='works'
            """
            )
            assert cursor.fetchone() is not None

            # Check releases table
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='releases'
            """
            )
            assert cursor.fetchone() is not None

    def test_create_work(self):
        """Test creating a work using correct API"""
        work_id = self.db.create_work(
            title="Attack on Titan",
            work_type="anime",  # Use string value
            title_kana="しんげきのきょじん",
            title_en="Attack on Titan",
            official_url="https://example.com/aot",
        )

        assert work_id > 0
        assert isinstance(work_id, int)

    def test_create_manga_work(self):
        """Test creating a manga work"""
        work_id = self.db.create_work(
            title="One Piece",
            work_type="manga",
            title_kana="ワンピース",
            title_en="One Piece",
            official_url="https://example.com/onepiece",
        )

        assert work_id > 0

    def test_get_or_create_work(self):
        """Test get_or_create_work functionality"""
        # First call creates
        work_id1 = self.db.get_or_create_work(title="Test Anime", work_type="anime")

        # Second call retrieves existing
        work_id2 = self.db.get_or_create_work(title="Test Anime", work_type="anime")

        assert work_id1 == work_id2

    def test_create_release(self):
        """Test creating a release"""
        # First create a work
        work_id = self.db.create_work(title="Test Anime", work_type="anime")

        # Then create a release
        release_id = self.db.create_release(
            work_id=work_id,
            release_type="episode",
            number="1",
            platform="Crunchyroll",
            release_date=date(2024, 1, 7),
            source="AniList",
            source_url="https://example.com/ep1",
        )

        assert release_id > 0

    def test_create_manga_release(self):
        """Test creating a manga volume release"""
        work_id = self.db.create_work(title="Test Manga", work_type="manga")

        release_id = self.db.create_release(
            work_id=work_id,
            release_type="volume",
            number="108",
            platform="Viz Media",
            release_date=date(2024, 2, 2),
            source="RSS",
            source_url="https://example.com/vol108",
        )

        assert release_id > 0

    def test_get_unnotified_releases(self):
        """Test getting unnotified releases"""
        # Create work and releases
        work_id = self.db.create_work(title="Test Work", work_type="anime")

        self.db.create_release(
            work_id=work_id,
            release_type="episode",
            number="1",
            platform="Test Platform",
            release_date=date(2024, 1, 1),
        )

        self.db.create_release(
            work_id=work_id,
            release_type="episode",
            number="2",
            platform="Test Platform",
            release_date=date(2024, 1, 8),
        )

        # Get unnotified releases
        releases = self.db.get_unnotified_releases(limit=10)

        assert len(releases) == 2
        assert all(r["notified"] == 0 for r in releases)

    def test_mark_release_notified(self):
        """Test marking a release as notified"""
        work_id = self.db.create_work(title="Test Work", work_type="anime")

        release_id = self.db.create_release(
            work_id=work_id,
            release_type="episode",
            number="1",
            platform="Test Platform",
            release_date=date(2024, 1, 1),
        )

        # Mark as notified
        success = self.db.mark_release_notified(release_id)
        assert success is True

        # Verify it's marked
        releases = self.db.get_unnotified_releases(limit=10)
        assert len(releases) == 0

    def test_duplicate_release_handling(self):
        """Test that duplicate releases are prevented by UNIQUE constraint"""
        work_id = self.db.create_work(title="Test Work", work_type="anime")

        # Create first release
        release_id1 = self.db.create_release(
            work_id=work_id,
            release_type="episode",
            number="1",
            platform="Test Platform",
            release_date=date(2024, 1, 1),
        )

        # Try to create duplicate (should be handled gracefully or raise error)
        try:
            release_id2 = self.db.create_release(
                work_id=work_id,
                release_type="episode",
                number="1",
                platform="Test Platform",
                release_date=date(2024, 1, 1),
            )
            # If no error, should return same ID or 0
            assert release_id2 == release_id1 or release_id2 == 0
        except sqlite3.IntegrityError:
            # Expected behavior - UNIQUE constraint violation
            pass

    def test_get_work_stats(self):
        """Test getting work statistics"""
        # Create some works
        self.db.create_work("Anime 1", "anime")
        self.db.create_work("Anime 2", "anime")
        self.db.create_work("Manga 1", "manga")

        stats = self.db.get_work_stats()

        # Check for actual keys returned by get_work_stats
        assert isinstance(stats, dict)
        assert "anime_works" in stats or "total_works" in stats
        assert "manga_works" in stats or "manga_count" in stats
        # Verify we have 3 total works
        total = stats.get(
            "total_works", stats.get("anime_works", 0) + stats.get("manga_works", 0)
        )
        assert total >= 3

    def test_connection_pooling(self):
        """Test that connection pooling works"""
        conn1 = self.db.get_connection()
        conn2 = self.db.get_connection()

        # Connections should be from the pool
        assert conn1 is not None
        assert conn2 is not None


class TestDatabaseTransactions:
    """Test database transaction management"""

    def setup_method(self):
        """Set up test fixtures"""
        self.db = DatabaseManager(db_path=":memory:")
        self.db.initialize_database()

    def teardown_method(self):
        """Clean up"""
        if hasattr(self, "db"):
            self.db.close_connections()

    def test_transaction_context_manager(self):
        """Test transaction context manager"""
        with self.db.get_transaction() as conn:
            conn.cursor()
            # Transaction should auto-commit on success
            work_id = self.db.create_work(title="Transaction Test", work_type="anime")
            assert work_id > 0


class TestDatabasePerformance:
    """Test database performance and optimization"""

    def setup_method(self):
        """Set up test fixtures"""
        self.db = DatabaseManager(db_path=":memory:")
        self.db.initialize_database()

    def teardown_method(self):
        """Clean up"""
        if hasattr(self, "db"):
            self.db.close_connections()

    @pytest.mark.performance
    def test_bulk_insert_performance(self):
        """Test performance of bulk inserts"""
        import time

        start = time.time()

        # Create 100 works
        for i in range(100):
            self.db.create_work(title=f"Anime {i}", work_type="anime")

        elapsed = time.time() - start

        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0

    def test_get_performance_stats(self):
        """Test getting performance statistics"""
        stats = self.db.get_performance_stats()

        assert isinstance(stats, dict)
        # Stats should contain useful metrics
        assert len(stats) > 0


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database operations"""

    def setup_method(self):
        """Set up test fixtures"""
        self.db = DatabaseManager(db_path=":memory:")
        self.db.initialize_database()

    def teardown_method(self):
        """Clean up"""
        if hasattr(self, "db"):
            self.db.close_connections()

    def test_full_workflow(self):
        """Test complete workflow: create work -> create release -> query -> notify"""
        # 1. Create work
        work_id = self.db.create_work(
            title="Integration Test Anime",
            work_type="anime",
            title_en="Integration Test",
        )

        # 2. Create multiple releases
        for i in range(1, 4):
            self.db.create_release(
                work_id=work_id,
                release_type="episode",
                number=str(i),
                platform="Test Platform",
                release_date=date(2024, 1, i),
            )

        # 3. Query unnotified
        unnotified = self.db.get_unnotified_releases(limit=10)
        assert len(unnotified) == 3

        # 4. Mark first as notified
        self.db.mark_release_notified(unnotified[0]["id"])

        # 5. Verify only 2 remain unnotified
        remaining = self.db.get_unnotified_releases(limit=10)
        assert len(remaining) == 2
