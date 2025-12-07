"""
管理者ダッシュボード テストスイート

統計情報取得、セキュリティアラート、アカウントロック解除の動作確認
"""

import unittest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestAdminDashboard(unittest.TestCase):
    """管理者ダッシュボード機能のテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 一時データベース作成
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # テーブル作成
        self.create_test_tables()
        self.insert_test_data()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def create_test_tables(self):
        """テスト用テーブル作成"""
        # ユーザーテーブル
        self.cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                locked_until DATETIME,
                failed_attempts INTEGER DEFAULT 0,
                last_login DATETIME
            )
        ''')

        # 監査ログテーブル
        self.cursor.execute('''
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action TEXT NOT NULL,
                username TEXT,
                ip_address TEXT,
                details TEXT
            )
        ''')

        # APIキーテーブル
        self.cursor.execute('''
            CREATE TABLE api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_name TEXT NOT NULL,
                key_prefix TEXT NOT NULL,
                key_hash TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    def insert_test_data(self):
        """テストデータ投入"""
        # ユーザーデータ
        users = [
            ('admin', 'admin@example.com', 'hash123', 1, None, 0,
             datetime.now().isoformat()),
            ('user1', 'user1@example.com', 'hash456', 0, None, 0,
             (datetime.now() - timedelta(hours=2)).isoformat()),
            ('locked_user', 'locked@example.com', 'hash789', 0,
             (datetime.now() + timedelta(hours=1)).isoformat(), 5, None),
        ]

        for user in users:
            self.cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_admin,
                                 locked_until, failed_attempts, last_login)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', user)

        # 監査ログデータ
        now = datetime.now()
        logs = [
            (now.isoformat(), 'login_success', 'admin', '127.0.0.1', None),
            ((now - timedelta(minutes=5)).isoformat(), 'login_failed',
             'user1', '192.168.1.100', 'Invalid password'),
            ((now - timedelta(minutes=10)).isoformat(), 'login_failed',
             'user1', '192.168.1.100', 'Invalid password'),
            ((now - timedelta(minutes=15)).isoformat(), 'api_request',
             'api_user', '10.0.0.5', 'API key: ak_test123'),
        ]

        for log in logs:
            self.cursor.execute('''
                INSERT INTO audit_logs (timestamp, action, username, ip_address, details)
                VALUES (?, ?, ?, ?, ?)
            ''', log)

        # APIキーデータ
        api_keys = [
            ('Production API', 'ak_prod', 'hashed_key_prod', 1),
            ('Development API', 'ak_dev', 'hashed_key_dev', 1),
            ('Inactive API', 'ak_old', 'hashed_key_old', 0),
        ]

        for key in api_keys:
            self.cursor.execute('''
                INSERT INTO api_keys (key_name, key_prefix, key_hash, is_active)
                VALUES (?, ?, ?, ?)
            ''', key)

        self.conn.commit()

    # ========================
    # 統計情報テスト
    # ========================

    def test_total_users_count(self):
        """総ユーザー数の取得"""
        self.cursor.execute('SELECT COUNT(*) FROM users')
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 3)

    def test_active_users_count(self):
        """アクティブユーザー数の取得（24時間以内にログイン）"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM users
            WHERE last_login > datetime('now', '-1 day')
        ''')
        count = self.cursor.fetchone()[0]
        self.assertGreaterEqual(count, 1)  # 少なくとも admin

    def test_locked_accounts_count(self):
        """ロック中アカウント数の取得"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM users
            WHERE locked_until > datetime('now')
        ''')
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 1)  # locked_user

    def test_active_api_keys_count(self):
        """アクティブAPIキー数の取得"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM api_keys WHERE is_active = 1
        ''')
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 2)

    def test_audit_logs_24h_count(self):
        """24時間以内の監査ログ数"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM audit_logs
            WHERE timestamp > datetime('now', '-1 day')
        ''')
        count = self.cursor.fetchone()[0]
        self.assertGreaterEqual(count, 1)

    def test_failed_logins_count(self):
        """失敗ログイン数の取得"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM audit_logs
            WHERE action = 'login_failed'
            AND timestamp > datetime('now', '-1 day')
        ''')
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 2)

    # ========================
    # ロック中アカウントテスト
    # ========================

    def test_get_locked_accounts(self):
        """ロック中アカウント一覧取得"""
        self.cursor.execute('''
            SELECT username, locked_until FROM users
            WHERE locked_until > datetime('now')
        ''')
        accounts = self.cursor.fetchall()
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0][0], 'locked_user')

    def test_unlock_account(self):
        """アカウントロック解除"""
        # ロック解除
        self.cursor.execute('''
            UPDATE users
            SET locked_until = NULL, failed_attempts = 0
            WHERE username = 'locked_user'
        ''')
        self.conn.commit()

        # 確認
        self.cursor.execute('''
            SELECT locked_until, failed_attempts FROM users
            WHERE username = 'locked_user'
        ''')
        result = self.cursor.fetchone()
        self.assertIsNone(result[0])  # locked_until
        self.assertEqual(result[1], 0)  # failed_attempts

    # ========================
    # セキュリティアラートテスト
    # ========================

    def test_brute_force_detection(self):
        """ブルートフォース攻撃検出"""
        # 1時間以内に5回以上の失敗ログインを挿入
        now = datetime.now()
        for i in range(6):
            self.cursor.execute('''
                INSERT INTO audit_logs (timestamp, action, username, ip_address)
                VALUES (?, 'login_failed', 'attacker', '192.168.1.200')
            ''', ((now - timedelta(minutes=i)).isoformat(),))

        self.conn.commit()

        # 検出
        self.cursor.execute('''
            SELECT username, ip_address, COUNT(*) as attempts
            FROM audit_logs
            WHERE action = 'login_failed'
            AND timestamp > datetime('now', '-1 hour')
            GROUP BY username, ip_address
            HAVING attempts >= 5
        ''')

        results = self.cursor.fetchall()
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0][0], 'attacker')
        self.assertGreaterEqual(results[0][2], 5)

    def test_high_api_usage_detection(self):
        """高API使用量検出"""
        # 1時間以内に100回以上のAPIリクエストを挿入
        now = datetime.now()
        for i in range(105):
            self.cursor.execute('''
                INSERT INTO audit_logs (timestamp, action, details)
                VALUES (?, 'api_request', 'ak_test123')
            ''', ((now - timedelta(minutes=i % 60)).isoformat(),))

        self.conn.commit()

        # 検出
        self.cursor.execute('''
            SELECT details, COUNT(*) as count
            FROM audit_logs
            WHERE action = 'api_request'
            AND timestamp > datetime('now', '-1 hour')
            GROUP BY details
            HAVING count > 100
        ''')

        results = self.cursor.fetchall()
        self.assertGreater(len(results), 0)
        self.assertGreater(results[0][1], 100)

    # ========================
    # 監査ログ統計テスト
    # ========================

    def test_action_statistics(self):
        """アクション別統計"""
        self.cursor.execute('''
            SELECT action, COUNT(*) as count
            FROM audit_logs
            GROUP BY action
            ORDER BY count DESC
        ''')

        stats = self.cursor.fetchall()
        self.assertGreater(len(stats), 0)

        # login_failed が最も多いはず
        actions = [stat[0] for stat in stats]
        self.assertIn('login_failed', actions)

    def test_hourly_statistics(self):
        """時間別統計"""
        self.cursor.execute('''
            SELECT
                strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                COUNT(*) as count
            FROM audit_logs
            WHERE timestamp > datetime('now', '-1 day')
            GROUP BY hour
            ORDER BY hour
        ''')

        stats = self.cursor.fetchall()
        self.assertGreater(len(stats), 0)

    # ========================
    # API使用統計テスト
    # ========================

    def test_api_usage_statistics(self):
        """API使用統計"""
        self.cursor.execute('''
            SELECT
                ak.key_name,
                ak.key_prefix,
                COUNT(al.id) as request_count
            FROM api_keys ak
            LEFT JOIN audit_logs al
                ON al.details LIKE '%' || ak.key_prefix || '%'
                AND al.action = 'api_request'
            WHERE ak.is_active = 1
            GROUP BY ak.id
            ORDER BY request_count DESC
        ''')

        usage = self.cursor.fetchall()
        self.assertGreater(len(usage), 0)


class TestDashboardEdgeCases(unittest.TestCase):
    """エッジケースのテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # 空のテーブル作成
        self.cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                locked_until DATETIME,
                last_login DATETIME
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME,
                action TEXT,
                username TEXT,
                ip_address TEXT
            )
        ''')

        self.conn.commit()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_empty_database(self):
        """空のデータベースでの動作"""
        self.cursor.execute('SELECT COUNT(*) FROM users')
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 0)

    def test_no_locked_accounts(self):
        """ロック中アカウントがない場合"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM users
            WHERE locked_until > datetime('now')
        ''')
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 0)

    def test_no_audit_logs(self):
        """監査ログがない場合"""
        self.cursor.execute('SELECT COUNT(*) FROM audit_logs')
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 0)


def run_tests():
    """テスト実行"""
    # テストスイート作成
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # テストクラス追加
    suite.addTests(loader.loadTestsFromTestCase(TestAdminDashboard))
    suite.addTests(loader.loadTestsFromTestCase(TestDashboardEdgeCases))

    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
