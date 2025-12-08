"""
Unit Tests for Database Operations
===================================

Tests for SQLite database operations including:
- Connection management
- CRUD operations
- Transaction handling
- Error handling
- Data integrity
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, date
from pathlib import Path


class TestDatabaseOperations:
    """Test suite for database operations"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        # Initialize test database schema
        conn = sqlite3.connect(path)
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
                UNIQUE(work_id, release_type, number, platform, release_date),
                FOREIGN KEY (work_id) REFERENCES works(id)
            )
        """)

        conn.commit()
        conn.close()

        yield path

        # Cleanup
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def db_connection(self, temp_db):
        """Provide a database connection"""
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        yield conn
        conn.close()

    def test_connection_creation(self, temp_db):
        """Test database connection can be created"""
        conn = sqlite3.connect(temp_db)
        assert conn is not None
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert 'works' in tables
        assert 'releases' in tables
        conn.close()

    def test_insert_work(self, db_connection):
        """Test inserting a new work"""
        cursor = db_connection.cursor()
        cursor.execute("""
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (?, ?, ?, ?, ?)
        """, ('僕のヒーローアカデミア', 'ぼくのひーろーあかでみあ',
              'My Hero Academia', 'anime', 'https://example.com'))
        db_connection.commit()

        cursor.execute("SELECT * FROM works WHERE title = ?", ('僕のヒーローアカデミア',))
        work = cursor.fetchone()

        assert work is not None
        assert work['title'] == '僕のヒーローアカデミア'
        assert work['type'] == 'anime'
        assert work['id'] is not None

    def test_insert_duplicate_work(self, db_connection):
        """Test handling duplicate work insertions"""
        cursor = db_connection.cursor()

        # Insert first work
        cursor.execute("""
            INSERT INTO works (title, type)
            VALUES (?, ?)
        """, ('テストアニメ', 'anime'))
        db_connection.commit()

        # Insert second work with same title (should succeed - no unique constraint)
        cursor.execute("""
            INSERT INTO works (title, type)
            VALUES (?, ?)
        """, ('テストアニメ', 'anime'))
        db_connection.commit()

        cursor.execute("SELECT COUNT(*) as count FROM works WHERE title = ?",
                      ('テストアニメ',))
        count = cursor.fetchone()['count']
        assert count == 2  # Both inserts succeed

    def test_insert_release(self, db_connection):
        """Test inserting a new release"""
        cursor = db_connection.cursor()

        # First create a work
        cursor.execute("""
            INSERT INTO works (title, type)
            VALUES (?, ?)
        """, ('テストマンガ', 'manga'))
        work_id = cursor.lastrowid
        db_connection.commit()

        # Insert release
        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, platform, release_date, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (work_id, 'volume', '1', 'BookWalker', '2025-12-15', 'RSS'))
        db_connection.commit()

        cursor.execute("SELECT * FROM releases WHERE work_id = ?", (work_id,))
        release = cursor.fetchone()

        assert release is not None
        assert release['release_type'] == 'volume'
        assert release['number'] == '1'
        assert release['notified'] == 0

    def test_unique_constraint_on_releases(self, db_connection):
        """Test UNIQUE constraint on releases table"""
        cursor = db_connection.cursor()

        # Create work
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      ('テストアニメ', 'anime'))
        work_id = cursor.lastrowid
        db_connection.commit()

        # Insert first release
        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, platform, release_date)
            VALUES (?, ?, ?, ?, ?)
        """, (work_id, 'episode', '1', 'Netflix', '2025-12-15'))
        db_connection.commit()

        # Try to insert duplicate - should raise IntegrityError
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO releases (work_id, release_type, number, platform, release_date)
                VALUES (?, ?, ?, ?, ?)
            """, (work_id, 'episode', '1', 'Netflix', '2025-12-15'))
            db_connection.commit()

    def test_foreign_key_constraint(self, db_connection):
        """Test foreign key constraint on releases"""
        cursor = db_connection.cursor()

        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        # Try to insert release with non-existent work_id
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO releases (work_id, release_type, number)
                VALUES (?, ?, ?)
            """, (99999, 'episode', '1'))
            db_connection.commit()

    def test_type_check_constraint_works(self, db_connection):
        """Test CHECK constraint on works.type"""
        cursor = db_connection.cursor()

        # Valid types should work
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      ('Valid Anime', 'anime'))
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      ('Valid Manga', 'manga'))
        db_connection.commit()

        # Invalid type should raise error
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                          ('Invalid', 'movie'))
            db_connection.commit()

    def test_type_check_constraint_releases(self, db_connection):
        """Test CHECK constraint on releases.release_type"""
        cursor = db_connection.cursor()

        # Create work
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      ('Test', 'anime'))
        work_id = cursor.lastrowid
        db_connection.commit()

        # Valid release_type
        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number)
            VALUES (?, ?, ?)
        """, (work_id, 'episode', '1'))
        db_connection.commit()

        # Invalid release_type
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO releases (work_id, release_type, number)
                VALUES (?, ?, ?)
            """, (work_id, 'chapter', '1'))
            db_connection.commit()

    def test_update_notified_status(self, db_connection):
        """Test updating notified status"""
        cursor = db_connection.cursor()

        # Create work and release
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      ('Test Anime', 'anime'))
        work_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number)
            VALUES (?, ?, ?)
        """, (work_id, 'episode', '1'))
        release_id = cursor.lastrowid
        db_connection.commit()

        # Update notified status
        cursor.execute("UPDATE releases SET notified = 1 WHERE id = ?",
                      (release_id,))
        db_connection.commit()

        # Verify update
        cursor.execute("SELECT notified FROM releases WHERE id = ?",
                      (release_id,))
        notified = cursor.fetchone()['notified']
        assert notified == 1

    def test_delete_work_cascade(self, db_connection):
        """Test deleting a work"""
        cursor = db_connection.cursor()

        # Create work and release
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      ('To Delete', 'anime'))
        work_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number)
            VALUES (?, ?, ?)
        """, (work_id, 'episode', '1'))
        db_connection.commit()

        # Delete work
        cursor.execute("DELETE FROM works WHERE id = ?", (work_id,))
        db_connection.commit()

        # Verify work deleted
        cursor.execute("SELECT * FROM works WHERE id = ?", (work_id,))
        assert cursor.fetchone() is None

        # Note: Without ON DELETE CASCADE, releases remain orphaned
        # This tests current schema behavior

    def test_query_by_date_range(self, db_connection):
        """Test querying releases by date range"""
        cursor = db_connection.cursor()

        # Create work
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      ('Test', 'anime'))
        work_id = cursor.lastrowid

        # Insert releases with different dates
        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, release_date)
            VALUES (?, ?, ?, ?)
        """, (work_id, 'episode', '1', '2025-12-10'))

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, release_date)
            VALUES (?, ?, ?, ?)
        """, (work_id, 'episode', '2', '2025-12-20'))

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, release_date)
            VALUES (?, ?, ?, ?)
        """, (work_id, 'episode', '3', '2025-12-30'))
        db_connection.commit()

        # Query date range
        cursor.execute("""
            SELECT * FROM releases
            WHERE release_date BETWEEN ? AND ?
        """, ('2025-12-15', '2025-12-31'))

        results = cursor.fetchall()
        assert len(results) == 2
        assert all(r['release_date'] >= '2025-12-15' for r in results)

    def test_join_works_and_releases(self, db_connection):
        """Test JOIN query between works and releases"""
        cursor = db_connection.cursor()

        # Create multiple works with releases
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      ('Anime 1', 'anime'))
        work1_id = cursor.lastrowid

        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      ('Manga 1', 'manga'))
        work2_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number)
            VALUES (?, ?, ?)
        """, (work1_id, 'episode', '1'))

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number)
            VALUES (?, ?, ?)
        """, (work2_id, 'volume', '1'))
        db_connection.commit()

        # JOIN query
        cursor.execute("""
            SELECT w.title, w.type, r.release_type, r.number
            FROM works w
            JOIN releases r ON w.id = r.work_id
            WHERE w.type = 'anime'
        """)

        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0]['title'] == 'Anime 1'
        assert results[0]['release_type'] == 'episode'

    def test_transaction_rollback(self, db_connection):
        """Test transaction rollback"""
        cursor = db_connection.cursor()

        # Start transaction
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      ('Rollback Test', 'anime'))

        # Rollback
        db_connection.rollback()

        # Verify not inserted
        cursor.execute("SELECT * FROM works WHERE title = ?",
                      ('Rollback Test',))
        assert cursor.fetchone() is None

    def test_null_handling(self, db_connection):
        """Test handling of NULL values"""
        cursor = db_connection.cursor()

        # Insert with minimal required fields
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      ('Minimal', 'anime'))
        work_id = cursor.lastrowid
        db_connection.commit()

        cursor.execute("SELECT * FROM works WHERE id = ?", (work_id,))
        work = cursor.fetchone()

        assert work['title_kana'] is None
        assert work['title_en'] is None
        assert work['official_url'] is None

    def test_datetime_default(self, db_connection):
        """Test that created_at has default timestamp"""
        cursor = db_connection.cursor()

        before = datetime.now()

        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      ('Time Test', 'anime'))
        work_id = cursor.lastrowid
        db_connection.commit()

        after = datetime.now()

        cursor.execute("SELECT created_at FROM works WHERE id = ?", (work_id,))
        created_at_str = cursor.fetchone()['created_at']

        assert created_at_str is not None
        # Note: Comparing strings since SQLite stores as TEXT by default

    def test_batch_insert(self, db_connection):
        """Test batch insertion of multiple records"""
        cursor = db_connection.cursor()

        works_data = [
            ('Anime A', 'anime'),
            ('Anime B', 'anime'),
            ('Manga A', 'manga'),
            ('Manga B', 'manga'),
        ]

        cursor.executemany("""
            INSERT INTO works (title, type) VALUES (?, ?)
        """, works_data)
        db_connection.commit()

        cursor.execute("SELECT COUNT(*) as count FROM works")
        count = cursor.fetchone()['count']
        assert count == 4

    def test_query_unnotified_releases(self, db_connection):
        """Test querying unnotified releases"""
        cursor = db_connection.cursor()

        # Create work
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      ('Test', 'anime'))
        work_id = cursor.lastrowid

        # Insert releases with different notified status
        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, notified)
            VALUES (?, ?, ?, ?)
        """, (work_id, 'episode', '1', 0))

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, notified)
            VALUES (?, ?, ?, ?)
        """, (work_id, 'episode', '2', 1))

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, notified)
            VALUES (?, ?, ?, ?)
        """, (work_id, 'episode', '3', 0))
        db_connection.commit()

        # Query unnotified
        cursor.execute("SELECT * FROM releases WHERE notified = 0")
        unnotified = cursor.fetchall()

        assert len(unnotified) == 2
        assert all(r['notified'] == 0 for r in unnotified)

    def test_empty_string_vs_null(self, db_connection):
        """Test differentiation between empty string and NULL"""
        cursor = db_connection.cursor()

        # Insert with empty string
        cursor.execute("""
            INSERT INTO works (title, title_en, type)
            VALUES (?, ?, ?)
        """, ('Test', '', 'anime'))
        work_id = cursor.lastrowid
        db_connection.commit()

        cursor.execute("SELECT title_en FROM works WHERE id = ?", (work_id,))
        title_en = cursor.fetchone()['title_en']

        assert title_en == ''  # Empty string, not NULL


class TestDatabaseEdgeCases:
    """Edge case tests for database operations"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        conn = sqlite3.connect(path)
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

        yield path

        if os.path.exists(path):
            os.remove(path)

    def test_very_long_title(self, temp_db):
        """Test handling very long titles"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        long_title = 'あ' * 1000  # 1000 character title
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      (long_title, 'anime'))
        conn.commit()

        cursor.execute("SELECT title FROM works")
        retrieved_title = cursor.fetchone()[0]
        assert retrieved_title == long_title

        conn.close()

    def test_special_characters_in_title(self, temp_db):
        """Test special characters in titles"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        special_titles = [
            "Test's Anime",
            'Test "Quoted" Manga',
            'Test\nNewline',
            'Test\tTab',
            'Test\\Backslash',
            'Test 😀 Emoji',
            'Test ½ Special',
        ]

        for title in special_titles:
            cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                          (title, 'anime'))
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM works")
        count = cursor.fetchone()[0]
        assert count == len(special_titles)

        conn.close()

    def test_sql_injection_prevention(self, temp_db):
        """Test that parameterized queries prevent SQL injection"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        malicious_input = "'; DROP TABLE works; --"

        # This should insert the malicious string as data, not execute it
        cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                      (malicious_input, 'anime'))
        conn.commit()

        # Verify table still exists and data is inserted
        cursor.execute("SELECT title FROM works WHERE type = 'anime'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == malicious_input

        conn.close()

    def test_concurrent_access(self, temp_db):
        """Test concurrent database access"""
        import threading

        def insert_work(db_path, title):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                          (title, 'anime'))
            conn.commit()
            conn.close()

        threads = []
        for i in range(10):
            t = threading.Thread(target=insert_work, args=(temp_db, f'Anime {i}'))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM works")
        count = cursor.fetchone()[0]
        assert count == 10
        conn.close()

    def test_zero_and_negative_ids(self, temp_db):
        """Test behavior with zero and negative IDs in queries"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Query with ID 0
        cursor.execute("SELECT * FROM works WHERE id = 0")
        assert cursor.fetchone() is None

        # Query with negative ID
        cursor.execute("SELECT * FROM works WHERE id = -1")
        assert cursor.fetchone() is None

        conn.close()

    def test_unicode_characters(self, temp_db):
        """Test various Unicode characters"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        unicode_titles = [
            '日本語タイトル',
            '한국어 제목',
            '中文标题',
            'Русский заголовок',
            'العربية عنوان',
            '🎌🎎🎏',
        ]

        for title in unicode_titles:
            cursor.execute("INSERT INTO works (title, type) VALUES (?, ?)",
                          (title, 'anime'))
        conn.commit()

        cursor.execute("SELECT title FROM works")
        retrieved = [row[0] for row in cursor.fetchall()]

        for original in unicode_titles:
            assert original in retrieved

        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
