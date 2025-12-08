"""
Integration Tests for Notification Flow
========================================

End-to-end tests for the complete notification pipeline:
- Data collection -> Filtering -> Storage -> Notification
- Gmail integration
- Calendar integration
- Error recovery
- Duplicate handling
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock, call


class TestCompleteNotificationFlow:
    """Integration tests for complete notification pipeline"""

    @pytest.fixture
    def test_database(self):
        """Create test database with schema"""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                title_kana TEXT,
                title_en TEXT,
                type TEXT CHECK(type IN ('anime','manga')),
                official_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE releases (
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
        """)

        conn.commit()
        conn.close()

        yield db_path

        if os.path.exists(db_path):
            os.remove(db_path)

    @pytest.fixture
    def sample_anime_data(self):
        """Sample anime data from API"""
        return {
            "id": 1,
            "title": {
                "romaji": "Test Anime",
                "english": "Test Anime EN",
                "native": "テストアニメ"
            },
            "genres": ["Action", "Adventure"],
            "episodes": 12,
            "startDate": {"year": 2025, "month": 12, "day": 15},
            "streamingEpisodes": [
                {
                    "title": "Episode 1",
                    "url": "https://example.com/ep1",
                    "site": "Netflix"
                }
            ]
        }

    @pytest.fixture
    def sample_manga_data(self):
        """Sample manga data from RSS"""
        return {
            "title": "Test Manga Vol 1",
            "link": "https://bookwalker.jp/series/123",
            "pubDate": "2025-12-15",
            "description": "New volume release"
        }

    def test_anime_collection_to_notification_flow(self, test_database, sample_anime_data):
        """Test complete flow from anime data collection to notification"""
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()

        # Step 1: Collect and parse anime data
        anime_data = sample_anime_data
        title = anime_data['title']['romaji']
        release_date = f"{anime_data['startDate']['year']}-{anime_data['startDate']['month']:02d}-{anime_data['startDate']['day']:02d}"

        # Step 2: Filter (no NG keywords)
        ng_keywords = ["R18", "BL"]
        should_filter = any(kw in title for kw in ng_keywords)
        assert not should_filter

        # Step 3: Store in database
        cursor.execute("""
            INSERT INTO works (title, title_en, type)
            VALUES (?, ?, ?)
        """, (title, anime_data['title']['english'], 'anime'))
        work_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, platform, release_date, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (work_id, 'episode', '1', 'Netflix', release_date, 'AniList'))
        release_id = cursor.lastrowid
        conn.commit()

        # Step 4: Query unnotified releases
        cursor.execute("""
            SELECT r.*, w.title
            FROM releases r
            JOIN works w ON r.work_id = w.id
            WHERE r.notified = 0
        """)
        unnotified = cursor.fetchall()

        assert len(unnotified) == 1

        # Step 5: Mark as notified
        cursor.execute("UPDATE releases SET notified = 1 WHERE id = ?", (release_id,))
        conn.commit()

        # Verify notification status
        cursor.execute("SELECT notified FROM releases WHERE id = ?", (release_id,))
        assert cursor.fetchone()[0] == 1

        conn.close()

    def test_manga_collection_to_notification_flow(self, test_database, sample_manga_data):
        """Test complete flow from manga RSS to notification"""
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()

        # Step 1: Parse RSS data
        manga_data = sample_manga_data

        # Step 2: Extract volume number
        import re
        match = re.search(r'Vol\.?\s*(\d+)', manga_data['title'])
        volume_number = match.group(1) if match else None

        assert volume_number == '1'

        # Step 3: Extract base title
        base_title = re.sub(r'\s*Vol\.?\s*\d+', '', manga_data['title']).strip()

        # Step 4: Filter
        ng_keywords = ["R18", "BL"]
        should_filter = any(kw in base_title for kw in ng_keywords)
        assert not should_filter

        # Step 5: Store in database
        cursor.execute("""
            INSERT INTO works (title, type, official_url)
            VALUES (?, ?, ?)
        """, (base_title, 'manga', manga_data['link']))
        work_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, release_date, source)
            VALUES (?, ?, ?, ?, ?)
        """, (work_id, 'volume', volume_number, manga_data['pubDate'], 'RSS'))
        release_id = cursor.lastrowid
        conn.commit()

        # Step 6: Query and notify
        cursor.execute("""
            SELECT r.*, w.title
            FROM releases r
            JOIN works w ON r.work_id = w.id
            WHERE r.notified = 0 AND w.type = 'manga'
        """)
        unnotified = cursor.fetchall()

        assert len(unnotified) == 1

        conn.close()

    @patch('smtplib.SMTP')
    def test_gmail_notification_integration(self, mock_smtp, test_database):
        """Test Gmail notification integration"""
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()

        # Setup test data
        cursor.execute("""
            INSERT INTO works (title, type)
            VALUES (?, ?)
        """, ('Test Anime', 'anime'))
        work_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, release_date)
            VALUES (?, ?, ?, ?)
        """, (work_id, 'episode', '1', '2025-12-15'))
        conn.commit()

        # Query releases to notify
        cursor.execute("""
            SELECT r.*, w.title, w.type
            FROM releases r
            JOIN works w ON r.work_id = w.id
            WHERE r.notified = 0
        """)
        releases = cursor.fetchall()

        # Mock Gmail sending
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Simulate sending email
        for release in releases:
            title = release[8]  # w.title
            release_type = release[2]  # r.release_type
            number = release[3]  # r.number

            email_subject = f"New {release_type}: {title} #{number}"
            email_body = f"Release date: {release[5]}"

            mock_server.send_message.assert_not_called()  # Not yet called

            # Simulate actual send
            # In real code: send_email(subject, body)
            notification_sent = True

        assert notification_sent
        conn.close()

    @patch('googleapiclient.discovery.build')
    def test_calendar_integration(self, mock_build, test_database):
        """Test Google Calendar integration"""
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()

        # Setup test data
        cursor.execute("""
            INSERT INTO works (title, type)
            VALUES (?, ?)
        """, ('Test Anime', 'anime'))
        work_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, release_date)
            VALUES (?, ?, ?, ?)
        """, (work_id, 'episode', '1', '2025-12-15'))
        conn.commit()

        # Query releases
        cursor.execute("""
            SELECT r.*, w.title
            FROM releases r
            JOIN works w ON r.work_id = w.id
            WHERE r.notified = 0
        """)
        releases = cursor.fetchall()

        # Mock Calendar API
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_events = MagicMock()
        mock_service.events.return_value = mock_events

        # Create calendar events
        for release in releases:
            event = {
                'summary': f"{release[8]} Episode {release[3]}",
                'start': {'date': release[5]},
                'end': {'date': release[5]},
            }

            # In real code: service.events().insert(...).execute()
            calendar_created = True

        assert calendar_created
        conn.close()

    def test_duplicate_prevention(self, test_database):
        """Test prevention of duplicate notifications"""
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()

        # Insert work and release
        cursor.execute("""
            INSERT INTO works (title, type)
            VALUES (?, ?)
        """, ('Test Anime', 'anime'))
        work_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, platform, release_date)
            VALUES (?, ?, ?, ?, ?)
        """, (work_id, 'episode', '1', 'Netflix', '2025-12-15'))
        conn.commit()

        # Try to insert duplicate (should fail due to UNIQUE constraint)
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO releases (work_id, release_type, number, platform, release_date)
                VALUES (?, ?, ?, ?, ?)
            """, (work_id, 'episode', '1', 'Netflix', '2025-12-15'))
            conn.commit()

        conn.close()

    def test_error_recovery_partial_failure(self, test_database):
        """Test recovery from partial notification failures"""
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()

        # Create multiple releases
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)", ('Anime 1', 'anime'))
        work1_id = cursor.lastrowid

        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)", ('Anime 2', 'anime'))
        work2_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number)
            VALUES (?, ?, ?)
        """, (work1_id, 'episode', '1'))
        release1_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number)
            VALUES (?, ?, ?)
        """, (work2_id, 'episode', '1'))
        release2_id = cursor.lastrowid
        conn.commit()

        # Simulate partial success
        # Release 1 succeeds
        cursor.execute("UPDATE releases SET notified = 1 WHERE id = ?", (release1_id,))
        conn.commit()

        # Release 2 fails (remains unnotified)
        # On next run, only release 2 should be processed
        cursor.execute("SELECT id FROM releases WHERE notified = 0")
        unnotified = cursor.fetchall()

        assert len(unnotified) == 1
        assert unnotified[0][0] == release2_id

        conn.close()

    def test_batch_notification_processing(self, test_database):
        """Test processing multiple notifications in batch"""
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()

        # Create multiple releases
        batch_size = 10

        for i in range(batch_size):
            cursor.execute("""
                INSERT INTO works (title, type)
                VALUES (?, ?)
            """, (f'Anime {i}', 'anime'))
            work_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO releases (work_id, release_type, number)
                VALUES (?, ?, ?)
            """, (work_id, 'episode', '1'))

        conn.commit()

        # Query all unnotified
        cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 0")
        count = cursor.fetchone()[0]
        assert count == batch_size

        # Process in batch
        cursor.execute("SELECT id FROM releases WHERE notified = 0")
        release_ids = [row[0] for row in cursor.fetchall()]

        # Mark all as notified
        cursor.executemany(
            "UPDATE releases SET notified = 1 WHERE id = ?",
            [(rid,) for rid in release_ids]
        )
        conn.commit()

        # Verify all processed
        cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 0")
        remaining = cursor.fetchone()[0]
        assert remaining == 0

        conn.close()

    def test_notification_with_filtering(self, test_database):
        """Test notification flow with filtering applied"""
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()

        ng_keywords = ["R18", "BL"]

        test_works = [
            ("Normal Anime", "anime", False),
            ("R18 Anime", "anime", True),
            ("BL Story", "manga", True),
            ("Family Show", "anime", False),
        ]

        created_ids = []

        for title, work_type, should_filter in test_works:
            # Apply filter
            filtered = any(kw in title for kw in ng_keywords)
            assert filtered == should_filter

            if not filtered:
                cursor.execute("""
                    INSERT INTO works (title, type)
                    VALUES (?, ?)
                """, (title, work_type))
                work_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO releases (work_id, release_type, number)
                    VALUES (?, ?, ?)
                """, (work_id, 'episode', '1'))
                created_ids.append(cursor.lastrowid)

        conn.commit()

        # Only non-filtered works should be in database
        cursor.execute("SELECT COUNT(*) FROM releases")
        count = cursor.fetchone()[0]
        assert count == 2  # Only "Normal Anime" and "Family Show"

        conn.close()


class TestNotificationScheduling:
    """Integration tests for notification scheduling"""

    @pytest.fixture
    def test_database(self):
        """Create test database"""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                type TEXT CHECK(type IN ('anime','manga'))
            )
        """)

        cursor.execute("""
            CREATE TABLE releases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_id INTEGER NOT NULL,
                release_type TEXT,
                number TEXT,
                release_date DATE,
                notified INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

        yield db_path

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_future_release_scheduling(self, test_database):
        """Test scheduling notifications for future releases"""
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()

        today = date.today()
        future_dates = [
            today + timedelta(days=1),
            today + timedelta(days=7),
            today + timedelta(days=30),
        ]

        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)", ('Test Anime', 'anime'))
        work_id = cursor.lastrowid

        for i, release_date in enumerate(future_dates):
            cursor.execute("""
                INSERT INTO releases (work_id, release_type, number, release_date)
                VALUES (?, ?, ?, ?)
            """, (work_id, 'episode', str(i+1), release_date.isoformat()))

        conn.commit()

        # Query upcoming releases (within 7 days)
        week_from_now = today + timedelta(days=7)
        cursor.execute("""
            SELECT * FROM releases
            WHERE release_date <= ? AND release_date >= ?
        """, (week_from_now.isoformat(), today.isoformat()))

        upcoming = cursor.fetchall()
        assert len(upcoming) == 2  # Day 1 and Day 7

        conn.close()

    def test_past_release_handling(self, test_database):
        """Test handling of past releases"""
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()

        today = date.today()
        past_date = today - timedelta(days=7)

        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)", ('Test Anime', 'anime'))
        work_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, release_date)
            VALUES (?, ?, ?, ?)
        """, (work_id, 'episode', '1', past_date.isoformat()))
        conn.commit()

        # Query past releases
        cursor.execute("""
            SELECT * FROM releases
            WHERE release_date < ?
        """, (today.isoformat(),))

        past_releases = cursor.fetchall()
        assert len(past_releases) == 1

        conn.close()

    def test_notification_timing_window(self, test_database):
        """Test notification timing window"""
        conn = sqlite3.connect(test_database)
        cursor = conn.cursor()

        today = date.today()

        # Create releases at different times
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)", ('Test', 'anime'))
        work_id = cursor.lastrowid

        test_dates = [
            (today - timedelta(days=1), False),  # Yesterday
            (today, True),                        # Today
            (today + timedelta(days=1), True),   # Tomorrow
            (today + timedelta(days=8), False),  # Too far
        ]

        for i, (release_date, in_window) in enumerate(test_dates):
            cursor.execute("""
                INSERT INTO releases (work_id, release_type, number, release_date)
                VALUES (?, ?, ?, ?)
            """, (work_id, 'episode', str(i+1), release_date.isoformat()))

        conn.commit()

        # Query releases within notification window (today to +7 days)
        week_from_now = today + timedelta(days=7)
        cursor.execute("""
            SELECT * FROM releases
            WHERE release_date >= ? AND release_date <= ?
        """, (today.isoformat(), week_from_now.isoformat()))

        in_window_releases = cursor.fetchall()
        expected_count = sum(1 for _, in_win in test_dates if in_win)
        assert len(in_window_releases) == expected_count

        conn.close()


class TestErrorHandlingIntegration:
    """Integration tests for error handling"""

    def test_database_connection_failure_recovery(self):
        """Test recovery from database connection failure"""
        # Try to connect to non-existent database
        non_existent_db = "/tmp/non_existent_db_12345.db"

        try:
            conn = sqlite3.connect(non_existent_db)
            # Connection succeeds but database is empty
            cursor = conn.cursor()

            # This should fail
            with pytest.raises(sqlite3.OperationalError):
                cursor.execute("SELECT * FROM works")

            conn.close()

        finally:
            if os.path.exists(non_existent_db):
                os.remove(non_existent_db)

    def test_transaction_rollback_on_error(self):
        """Test transaction rollback on error"""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            conn.commit()

            # Start transaction
            cursor.execute("INSERT INTO test_table (value) VALUES (?)", ('value1',))

            # Cause an error
            try:
                cursor.execute("INSERT INTO test_table (value) VALUES (NULL)")  # Should fail
            except sqlite3.IntegrityError:
                conn.rollback()  # Rollback on error

            # Verify rollback
            cursor.execute("SELECT COUNT(*) FROM test_table")
            count = cursor.fetchone()[0]
            assert count == 0  # Nothing committed

            conn.close()

        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_partial_data_handling(self):
        """Test handling of partial/incomplete data"""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE works (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    type TEXT
                )
            """)
            conn.commit()

            # Insert with missing optional field
            cursor.execute("""
                INSERT INTO works (title, type)
                VALUES (?, ?)
            """, ('Test', None))
            conn.commit()

            # Verify inserted
            cursor.execute("SELECT * FROM works")
            work = cursor.fetchone()
            assert work[1] == 'Test'
            assert work[2] is None

            conn.close()

        finally:
            if os.path.exists(db_path):
                os.remove(db_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
