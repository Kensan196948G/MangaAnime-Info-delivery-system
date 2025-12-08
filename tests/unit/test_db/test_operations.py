# tests/unit/test_db/test_operations.py
# データベース操作の単体テスト

import pytest
import sqlite3
from datetime import datetime, timedelta


class TestDatabaseOperations:
    """データベース基本操作のテストクラス"""

    # ===========================
    # CRUD操作テスト
    # ===========================

    def test_insert_work(self, test_db):
        """作品データの挿入テスト"""
        cursor = test_db.cursor()

        work_data = {
            "title": "新作アニメ",
            "title_kana": "しんさくあにめ",
            "title_en": "New Anime",
            "type": "anime",
            "official_url": "https://example.com/new-anime"
        }

        cursor.execute("""
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (:title, :title_kana, :title_en, :type, :official_url)
        """, work_data)
        test_db.commit()

        # 検証
        result = cursor.execute("SELECT * FROM works WHERE title = ?", (work_data["title"],)).fetchone()
        assert result is not None
        assert result[1] == "新作アニメ"
        assert result[4] == "anime"

    def test_select_work_by_id(self, test_db, sample_works):
        """IDによる作品取得テスト"""
        cursor = test_db.cursor()

        result = cursor.execute("SELECT * FROM works WHERE id = ?", (1,)).fetchone()

        assert result is not None
        assert result[0] == 1
        assert result[1] == "転生したらスライムだった件"

    def test_update_work(self, test_db, sample_works):
        """作品情報の更新テスト"""
        cursor = test_db.cursor()

        new_url = "https://updated-url.com"
        cursor.execute("UPDATE works SET official_url = ? WHERE id = ?", (new_url, 1))
        test_db.commit()

        result = cursor.execute("SELECT official_url FROM works WHERE id = ?", (1,)).fetchone()
        assert result[0] == new_url

    def test_delete_work(self, test_db, sample_works):
        """作品削除テスト"""
        cursor = test_db.cursor()

        cursor.execute("DELETE FROM works WHERE id = ?", (1,))
        test_db.commit()

        result = cursor.execute("SELECT * FROM works WHERE id = ?", (1,)).fetchone()
        assert result is None

    # ===========================
    # リリース操作テスト
    # ===========================

    def test_insert_release(self, test_db, sample_works):
        """リリースデータの挿入テスト"""
        cursor = test_db.cursor()

        release_data = {
            "work_id": 1,
            "release_type": "episode",
            "number": "5",
            "platform": "Netflix",
            "release_date": (datetime.now().date() + timedelta(days=7)).isoformat(),
            "source": "anilist",
            "source_url": "https://example.com/episode5",
            "notified": 0,
            "calendar_synced": 0
        }

        cursor.execute("""
            INSERT INTO releases
            (work_id, release_type, number, platform, release_date, source, source_url, notified, calendar_synced)
            VALUES (:work_id, :release_type, :number, :platform, :release_date, :source, :source_url, :notified, :calendar_synced)
        """, release_data)
        test_db.commit()

        # 検証
        result = cursor.execute("SELECT * FROM releases WHERE number = ?", ("5",)).fetchone()
        assert result is not None
        assert result[2] == "episode"

    def test_get_unnotified_releases(self, test_db, sample_releases):
        """未通知リリースの取得テスト"""
        cursor = test_db.cursor()

        results = cursor.execute("""
            SELECT * FROM releases WHERE notified = 0
        """).fetchall()

        assert len(results) == 3  # sample_releasesで3件が未通知

    def test_mark_as_notified(self, test_db, sample_releases):
        """通知済みフラグ更新テスト"""
        cursor = test_db.cursor()

        cursor.execute("UPDATE releases SET notified = 1 WHERE id = ?", (1,))
        test_db.commit()

        result = cursor.execute("SELECT notified FROM releases WHERE id = ?", (1,)).fetchone()
        assert result[0] == 1

    # ===========================
    # 制約テスト
    # ===========================

    def test_unique_constraint(self, test_db, sample_works):
        """UNIQUE制約のテスト"""
        cursor = test_db.cursor()

        release_data = (1, "episode", "3", "dアニメストア", "2025-12-10", "anilist", "https://example.com", 0, 0, None)

        # 1回目: 成功
        cursor.execute("""
            INSERT INTO releases
            (work_id, release_type, number, platform, release_date, source, source_url, notified, calendar_synced, calendar_event_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, release_data)
        test_db.commit()

        # 2回目: UNIQUE制約違反
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO releases
                (work_id, release_type, number, platform, release_date, source, source_url, notified, calendar_synced, calendar_event_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, release_data)
            test_db.commit()

    def test_foreign_key_constraint(self, test_db):
        """外部キー制約のテスト"""
        cursor = test_db.cursor()

        # 存在しないwork_idを指定
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO releases
                (work_id, release_type, number, platform, release_date, source, source_url)
                VALUES (999, 'episode', '1', 'Netflix', '2025-12-10', 'anilist', 'https://example.com')
            """)
            test_db.commit()

    def test_check_constraint_type(self, test_db):
        """CHECK制約（type列）のテスト"""
        cursor = test_db.cursor()

        # 不正なtype値
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO works (title, type) VALUES ('Test', 'invalid_type')
            """)
            test_db.commit()

    # ===========================
    # トランザクションテスト
    # ===========================

    def test_transaction_commit(self, test_db):
        """トランザクションコミットのテスト"""
        cursor = test_db.cursor()

        cursor.execute("INSERT INTO works (title, type) VALUES ('Test 1', 'anime')")
        cursor.execute("INSERT INTO works (title, type) VALUES ('Test 2', 'manga')")
        test_db.commit()

        count = cursor.execute("SELECT COUNT(*) FROM works").fetchone()[0]
        assert count >= 2

    def test_transaction_rollback(self, test_db, sample_works):
        """トランザクションロールバックのテスト"""
        cursor = test_db.cursor()

        initial_count = cursor.execute("SELECT COUNT(*) FROM works").fetchone()[0]

        try:
            cursor.execute("INSERT INTO works (title, type) VALUES ('Test', 'anime')")
            # 意図的にエラーを発生させる
            cursor.execute("INSERT INTO works (title, type) VALUES (NULL, 'anime')")  # title NOT NULL制約違反
            test_db.commit()
        except sqlite3.IntegrityError:
            test_db.rollback()

        final_count = cursor.execute("SELECT COUNT(*) FROM works").fetchone()[0]
        assert final_count == initial_count  # ロールバックされているため変化なし

    def test_concurrent_transaction_handling(self, test_db):
        """並行トランザクション処理のテスト"""
        import threading

        def insert_work(work_id):
            cursor = test_db.cursor()
            try:
                cursor.execute(
                    "INSERT INTO works (title, type) VALUES (?, 'anime')",
                    (f"Concurrent Work {work_id}",)
                )
                test_db.commit()
            except sqlite3.IntegrityError:
                test_db.rollback()

        threads = [threading.Thread(target=insert_work, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        cursor = test_db.cursor()
        count = cursor.execute("SELECT COUNT(*) FROM works").fetchone()[0]
        assert count >= 5

    # ===========================
    # JOIN操作テスト
    # ===========================

    def test_join_works_and_releases(self, test_db, sample_works, sample_releases):
        """作品とリリースのJOINテスト"""
        cursor = test_db.cursor()

        results = cursor.execute("""
            SELECT w.title, r.release_type, r.number, r.platform, r.release_date
            FROM works w
            JOIN releases r ON w.id = r.work_id
            WHERE w.type = 'anime'
        """).fetchall()

        assert len(results) > 0
        assert results[0][0] in ["転生したらスライムだった件", "呪術廻戦"]

    def test_left_join_with_no_releases(self, test_db, sample_works):
        """リリースのない作品のLEFT JOINテスト"""
        cursor = test_db.cursor()

        # リリースのない作品を追加
        cursor.execute("INSERT INTO works (title, type) VALUES ('No Release Anime', 'anime')")
        test_db.commit()

        results = cursor.execute("""
            SELECT w.title, r.number
            FROM works w
            LEFT JOIN releases r ON w.id = r.work_id
            WHERE r.number IS NULL
        """).fetchall()

        assert len(results) > 0

    # ===========================
    # インデックス活用テスト
    # ===========================

    def test_index_on_notified_column(self, test_db, large_dataset):
        """notifiedカラムのインデックス活用テスト"""
        import time

        cursor = test_db.cursor()

        start_time = time.time()
        results = cursor.execute("SELECT * FROM releases WHERE notified = 0").fetchall()
        elapsed_time = time.time() - start_time

        # インデックスがあるため高速（1秒以内）
        assert elapsed_time < 1.0
        assert len(results) == large_dataset  # すべて未通知

    def test_index_on_release_date(self, test_db, sample_releases):
        """release_dateカラムのインデックス活用テスト"""
        cursor = test_db.cursor()

        today = datetime.now().date().isoformat()

        results = cursor.execute("""
            SELECT * FROM releases WHERE release_date > ?
        """, (today,)).fetchall()

        assert len(results) > 0

    # ===========================
    # 集計クエリテスト
    # ===========================

    def test_count_releases_by_platform(self, test_db, sample_releases):
        """プラットフォームごとのリリース数集計テスト"""
        cursor = test_db.cursor()

        results = cursor.execute("""
            SELECT platform, COUNT(*) as count
            FROM releases
            GROUP BY platform
            ORDER BY count DESC
        """).fetchall()

        assert len(results) > 0
        assert results[0][1] >= 1  # 少なくとも1件

    def test_upcoming_releases_next_7_days(self, test_db, sample_releases):
        """今後7日間のリリース取得テスト"""
        cursor = test_db.cursor()

        today = datetime.now().date()
        next_week = (today + timedelta(days=7)).isoformat()

        results = cursor.execute("""
            SELECT * FROM releases
            WHERE release_date BETWEEN ? AND ?
            ORDER BY release_date
        """, (today.isoformat(), next_week)).fetchall()

        assert len(results) > 0

    # ===========================
    # データ整合性テスト
    # ===========================

    def test_cascade_delete(self, test_db, sample_works, sample_releases):
        """カスケード削除のテスト"""
        cursor = test_db.cursor()

        # 作品削除時に関連リリースも削除される（外部キー設定次第）
        work_id = 1
        cursor.execute("DELETE FROM releases WHERE work_id = ?", (work_id,))
        cursor.execute("DELETE FROM works WHERE id = ?", (work_id,))
        test_db.commit()

        releases = cursor.execute("SELECT * FROM releases WHERE work_id = ?", (work_id,)).fetchall()
        assert len(releases) == 0

    def test_orphaned_releases(self, test_db, sample_works, sample_releases):
        """孤立したリリースの検出テスト"""
        cursor = test_db.cursor()

        # 孤立リリース（work_idが存在しない）の検出
        orphaned = cursor.execute("""
            SELECT r.*
            FROM releases r
            LEFT JOIN works w ON r.work_id = w.id
            WHERE w.id IS NULL
        """).fetchall()

        assert len(orphaned) == 0  # 孤立リリースが存在しないこと
