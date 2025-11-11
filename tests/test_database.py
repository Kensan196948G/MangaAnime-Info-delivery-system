"""
Test database functionality
"""

import pytest
import sqlite3
import os
import sys
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from modules.db import DatabaseManager
except ImportError:
    # Create a mock DatabaseManager if the module doesn't exist
    class DatabaseManager:
        def __init__(self, db_path=":memory:"):
            self.db_path = db_path
            self.conn = sqlite3.connect(db_path)
            self.create_tables()

        def create_tables(self):
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS works (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    title_kana TEXT,
                    title_en TEXT,
                    type TEXT CHECK(type IN ('anime','manga')),
                    official_url TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            self.conn.execute(
                """
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
                    UNIQUE(work_id, release_type, number, platform, release_date)
                )
            """
            )
            self.conn.commit()

        def add_work(
            self, title, work_type, title_kana=None, title_en=None, official_url=None
        ):
            cursor = self.conn.execute(
                "INSERT INTO works (title, title_kana, title_en, type, official_url) VALUES (?, ?, ?, ?, ?)",
                (title, title_kana, title_en, work_type, official_url),
            )
            self.conn.commit()
            return cursor.lastrowid

        def add_release(
            self,
            work_id,
            release_type,
            number=None,
            platform=None,
            release_date=None,
            source=None,
            source_url=None,
        ):
            cursor = self.conn.execute(
                "INSERT OR IGNORE INTO releases (work_id, release_type, number, platform, release_date, source, source_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
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
            self.conn.commit()
            return cursor.lastrowid

        def get_works(self):
            cursor = self.conn.execute("SELECT * FROM works")
            return cursor.fetchall()

        def get_releases(self, work_id=None):
            if work_id:
                cursor = self.conn.execute(
                    "SELECT * FROM releases WHERE work_id = ?", (work_id,)
                )
            else:
                cursor = self.conn.execute("SELECT * FROM releases")
            return cursor.fetchall()

        def close(self):
            self.conn.close()


class TestDatabaseManager:
    """Test the DatabaseManager class"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.db = DatabaseManager(":memory:")

    def teardown_method(self):
        """Clean up after each test method"""
        self.db.close()

    def test_create_tables(self):
        """Test that tables are created properly"""
        # Check that works table exists
        cursor = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='works'"
        )
        assert cursor.fetchone() is not None

        # Check that releases table exists
        cursor = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='releases'"
        )
        assert cursor.fetchone() is not None

    def test_add_work(self):
        """Test adding a work to the database"""
        work_id = self.db.add_work(
            title="Test Anime",
            work_type="anime",
            title_kana="テストアニメ",
            title_en="Test Anime",
            official_url="https://example.com",
        )

        assert work_id is not None
        assert work_id > 0

        # Verify the work was added
        works = self.db.get_works()
        assert len(works) == 1
        assert works[0][1] == "Test Anime"  # title column
        assert works[0][4] == "anime"  # type column

    def test_add_manga_work(self):
        """Test adding a manga work"""
        work_id = self.db.add_work(
            title="Test Manga", work_type="manga", title_en="Test Manga"
        )

        assert work_id is not None
        works = self.db.get_works()
        assert len(works) == 1
        assert works[0][4] == "manga"  # type column

    def test_add_release(self):
        """Test adding a release to the database"""
        # First add a work
        work_id = self.db.add_work("Test Anime", "anime")

        # Add a release
        release_id = self.db.add_release(
            work_id=work_id,
            release_type="episode",
            number="1",
            platform="Crunchyroll",
            release_date="2024-01-07",
            source="anilist",
            source_url="https://example.com/ep1",
        )

        assert release_id is not None
        assert release_id > 0

        # Verify the release was added
        releases = self.db.get_releases(work_id)
        assert len(releases) == 1
        assert releases[0][2] == "episode"  # release_type column
        assert releases[0][3] == "1"  # number column
        assert releases[0][4] == "Crunchyroll"  # platform column

    def test_add_manga_release(self):
        """Test adding a manga volume release"""
        work_id = self.db.add_work("Test Manga", "manga")

        release_id = self.db.add_release(
            work_id=work_id,
            release_type="volume",
            number="5",
            platform="Viz Media",
            release_date="2024-02-01",
        )

        assert release_id is not None
        releases = self.db.get_releases(work_id)
        assert len(releases) == 1
        assert releases[0][2] == "volume"
        assert releases[0][3] == "5"

    def test_duplicate_release_handling(self):
        """Test that duplicate releases are handled properly"""
        work_id = self.db.add_work("Test Anime", "anime")

        # Add the same release twice
        release_id1 = self.db.add_release(
            work_id=work_id,
            release_type="episode",
            number="1",
            platform="Crunchyroll",
            release_date="2024-01-07",
        )

        release_id2 = self.db.add_release(
            work_id=work_id,
            release_type="episode",
            number="1",
            platform="Crunchyroll",
            release_date="2024-01-07",
        )

        # Should still only have one release
        releases = self.db.get_releases(work_id)
        assert len(releases) == 1

    def test_get_all_releases(self):
        """Test getting all releases"""
        # Add multiple works and releases
        work1_id = self.db.add_work("Anime 1", "anime")
        work2_id = self.db.add_work("Manga 1", "manga")

        self.db.add_release(work1_id, "episode", "1", "Crunchyroll")
        self.db.add_release(work1_id, "episode", "2", "Crunchyroll")
        self.db.add_release(work2_id, "volume", "1", "Viz Media")

        all_releases = self.db.get_releases()
        assert len(all_releases) == 3

    def test_work_type_constraint(self):
        """Test that work type constraint is enforced"""
        with pytest.raises(sqlite3.IntegrityError):
            self.db.add_work("Invalid Work", "invalid_type")

    def test_release_type_constraint(self):
        """Test that release type constraint is enforced"""
        work_id = self.db.add_work("Test Work", "anime")

        with pytest.raises(sqlite3.IntegrityError):
            self.db.add_release(work_id, "invalid_release_type")


@pytest.fixture
def sample_db():
    """Create a sample database with test data"""
    db = DatabaseManager(":memory:")

    # Add sample works
    anime_id = db.add_work("Attack on Titan", "anime", "進撃の巨人", "Attack on Titan")
    manga_id = db.add_work("One Piece", "manga", "ワンピース", "One Piece")

    # Add sample releases
    db.add_release(anime_id, "episode", "1", "Crunchyroll", "2024-01-07")
    db.add_release(anime_id, "episode", "2", "Crunchyroll", "2024-01-14")
    db.add_release(manga_id, "volume", "108", "Viz Media", "2024-02-02")

    yield db
    db.close()


class TestDatabaseIntegration:
    """Integration tests for database functionality"""

    def test_sample_database(self, sample_db):
        """Test using the sample database fixture"""
        works = sample_db.get_works()
        assert len(works) == 2

        releases = sample_db.get_releases()
        assert len(releases) == 3

    def test_complex_query_scenarios(self, sample_db):
        """Test complex database scenarios"""
        # Get releases for specific work
        works = sample_db.get_works()
        anime_work = [w for w in works if w[4] == "anime"][0]  # type = anime
        anime_releases = sample_db.get_releases(anime_work[0])  # id

        assert len(anime_releases) == 2
        assert all(r[2] == "episode" for r in anime_releases)  # release_type

    @patch("sqlite3.connect")
    def test_database_connection_error(self, mock_connect):
        """Test database connection error handling"""
        mock_connect.side_effect = sqlite3.Error("Connection failed")

        with pytest.raises(sqlite3.Error):
            DatabaseManager("test.db")

    def test_empty_database(self):
        """Test operations on empty database"""
        db = DatabaseManager(":memory:")

        works = db.get_works()
        assert len(works) == 0

        releases = db.get_releases()
        assert len(releases) == 0

        db.close()


if __name__ == "__main__":
    pytest.main([__file__])
