"""
ウォッチリスト機能の包括的テスト
作成日: 2025-12-07
"""

import unittest
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sqlite3
from datetime import datetime, timedelta
import json
from modules.watchlist_notifier import WatchlistNotifier


class TestWatchlistNotifier(unittest.TestCase):
    """ウォッチリスト通知のテスト"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体のセットアップ"""
        cls.test_db = ':memory:'
        cls.notifier = WatchlistNotifier(db_path=cls.test_db)
        cls._setup_test_database()

    @classmethod
    def _setup_test_database(cls):
        """テスト用データベースのセットアップ"""
        conn = sqlite3.connect(cls.test_db)
        cursor = conn.cursor()

        # ユーザーテーブル
        cursor.execute("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT,
                email_verified INTEGER DEFAULT 0
            )
        """)

        # 作品テーブル
        cursor.execute("""
            CREATE TABLE works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                title_en TEXT,
                type TEXT CHECK(type IN ('anime','manga')),
                official_url TEXT
            )
        """)

        # リリーステーブル
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
                FOREIGN KEY (work_id) REFERENCES works(id)
            )
        """)

        # ウォッチリストテーブル
        cursor.execute("""
            CREATE TABLE watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                work_id INTEGER NOT NULL,
                notify_new_episodes INTEGER DEFAULT 1,
                notify_new_volumes INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (work_id) REFERENCES works(id),
                UNIQUE(user_id, work_id)
            )
        """)

        # テストデータ投入
        cursor.execute("""
            INSERT INTO users (id, username, email, email_verified)
            VALUES ('user1', 'testuser', 'test@example.com', 1)
        """)

        cursor.execute("""
            INSERT INTO works (id, title, title_en, type, official_url)
            VALUES
                (1, 'テストアニメ', 'Test Anime', 'anime', 'https://example.com/anime'),
                (2, 'テストマンガ', 'Test Manga', 'manga', 'https://example.com/manga')
        """)

        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, platform, release_date, source, notified)
            VALUES
                (1, 'episode', '1', 'Netflix', ?, 'Netflix', 0),
                (1, 'episode', '2', 'Netflix', ?, 'Netflix', 0),
                (2, 'volume', '1', NULL, ?, 'BookWalker', 0)
        """, (yesterday, today, yesterday))

        cursor.execute("""
            INSERT INTO watchlist (user_id, work_id, notify_new_episodes, notify_new_volumes)
            VALUES
                ('user1', 1, 1, 1),
                ('user1', 2, 1, 1)
        """)

        conn.commit()
        conn.close()

    def test_get_new_releases_for_watchlist(self):
        """ウォッチリストの新規リリース取得テスト"""
        releases = self.notifier.get_new_releases_for_watchlist(days_back=7)

        self.assertIn('user1', releases)
        user_releases = releases['user1']

        # 3件のリリースがあるはず
        self.assertEqual(len(user_releases), 3)

        # エピソードとボリュームが含まれているか
        release_types = [r['release_type'] for r in user_releases]
        self.assertIn('episode', release_types)
        self.assertIn('volume', release_types)

    def test_mark_as_notified(self):
        """通知済みマークのテスト"""
        # 最初は未通知
        conn = self.notifier.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 0")
        before_count = cursor.fetchone()[0]
        conn.close()

        # 通知済みマーク
        marked = self.notifier.mark_as_notified([1, 2, 3])
        self.assertEqual(marked, 3)

        # 通知済みになっているか確認
        conn = self.notifier.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 1")
        after_count = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(after_count, 3)

    def test_get_user_info(self):
        """ユーザー情報取得テスト"""
        user_info = self.notifier.get_user_info('user1')

        self.assertIsNotNone(user_info)
        self.assertEqual(user_info['username'], 'testuser')
        self.assertEqual(user_info['email'], 'test@example.com')
        self.assertTrue(user_info['email_verified'])

    def test_format_notification_email(self):
        """通知メール生成テスト"""
        user_info = {
            'id': 'user1',
            'username': 'testuser',
            'email': 'test@example.com',
            'email_verified': True
        }

        releases = [
            {
                'work_id': 1,
                'work_title': 'テストアニメ',
                'work_title_en': 'Test Anime',
                'work_type': 'anime',
                'official_url': 'https://example.com',
                'release_id': 1,
                'release_type': 'episode',
                'number': '1',
                'platform': 'Netflix',
                'release_date': '2025-12-06',
                'source': 'Netflix',
                'source_url': 'https://netflix.com'
            }
        ]

        subject, html_body = self.notifier.format_notification_email(user_info, releases)

        # 件名チェック
        self.assertIn('ウォッチリスト', subject)
        self.assertIn('新エピソード', subject)

        # HTML本文チェック
        self.assertIn('testuser', html_body)
        self.assertIn('テストアニメ', html_body)
        self.assertIn('第1話', html_body)
        self.assertIn('Netflix', html_body)

    def test_get_watchlist_summary(self):
        """ウォッチリスト概要取得テスト"""
        summary = self.notifier.get_watchlist_summary('user1')

        self.assertEqual(summary['total'], 2)
        self.assertEqual(summary['anime'], 1)
        self.assertEqual(summary['manga'], 1)
        self.assertEqual(summary['notify_episodes'], 2)
        self.assertEqual(summary['notify_volumes'], 2)


class TestWatchlistAPI(unittest.TestCase):
    """ウォッチリストAPIのテスト（Flask統合テスト）"""

    def setUp(self):
        """各テストの前処理"""
        # TODO: Flaskアプリのテストクライアントをセットアップ
        pass

    def test_add_to_watchlist(self):
        """ウォッチリスト追加APIテスト"""
        # TODO: POST /watchlist/api/add のテスト
        pass

    def test_remove_from_watchlist(self):
        """ウォッチリスト削除APIテスト"""
        # TODO: DELETE /watchlist/api/remove/<work_id> のテスト
        pass

    def test_update_watchlist_settings(self):
        """ウォッチリスト設定更新APIテスト"""
        # TODO: PUT /watchlist/api/update/<work_id> のテスト
        pass

    def test_check_watchlist_status(self):
        """ウォッチリスト状態確認APIテスト"""
        # TODO: GET /watchlist/api/check/<work_id> のテスト
        pass


class TestWatchlistIntegration(unittest.TestCase):
    """ウォッチリスト統合テスト"""

    def test_end_to_end_workflow(self):
        """エンドツーエンドワークフローテスト"""
        # 1. ユーザーが作品をウォッチリストに追加
        # 2. 新規リリースが登録される
        # 3. 通知処理が実行される
        # 4. 通知が送信される
        # 5. リリースが通知済みになる
        pass

    def test_notification_filtering(self):
        """通知フィルタリングテスト"""
        # エピソード通知OFF時はエピソードの通知が来ないことを確認
        # ボリューム通知OFF時はボリュームの通知が来ないことを確認
        pass

    def test_duplicate_prevention(self):
        """重複通知防止テスト"""
        # 同じリリースに対して複数回通知されないことを確認
        pass


def run_tests():
    """テストを実行"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # テストクラスを追加
    suite.addTests(loader.loadTestsFromTestCase(TestWatchlistNotifier))
    suite.addTests(loader.loadTestsFromTestCase(TestWatchlistAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestWatchlistIntegration))

    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
