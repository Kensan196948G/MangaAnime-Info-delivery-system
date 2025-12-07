"""
監査ログデータベースモジュールのテスト - 完全版
SQLiteベースの監査ログシステムの包括的テスト
"""
import pytest
import tempfile
import os
import json
from datetime import datetime, timedelta
from modules.audit_log_db import AuditLoggerDB
from modules.audit_log import AuditEventType, AuditLog


@pytest.fixture
def temp_db():
    """テスト用一時データベース"""
    fd, path = tempfile.mkstemp(suffix='.db')
    # データベース初期化のためにusersテーブルを作成
    import sqlite3
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_id TEXT,
            username TEXT,
            ip_address TEXT DEFAULT 'unknown',
            user_agent TEXT DEFAULT 'unknown',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            details TEXT DEFAULT '{}',
            success INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

    yield path
    os.close(fd)
    os.unlink(path)


@pytest.fixture
def memory_logger():
    """メモリ内データベースロガー"""
    # メモリDBでもusersテーブルが必要
    import sqlite3
    conn = sqlite3.connect(':memory:')
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_id TEXT,
            username TEXT,
            ip_address TEXT DEFAULT 'unknown',
            user_agent TEXT DEFAULT 'unknown',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            details TEXT DEFAULT '{}',
            success INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

    return AuditLoggerDB(db_path=":memory:")


@pytest.fixture
def populated_logger(memory_logger):
    """テストデータが投入されたロガー"""
    # ログイン成功
    memory_logger.log_event(
        AuditEventType.AUTH_LOGIN_SUCCESS,
        user_id='user-1',
        username='alice',
        ip_address='192.168.1.100',
        user_agent='Mozilla/5.0',
        success=True
    )

    # ログイン失敗
    memory_logger.log_event(
        AuditEventType.AUTH_LOGIN_FAILURE,
        username='bob',
        ip_address='192.168.1.101',
        user_agent='curl/7.68.0',
        details={'reason': 'invalid_password'},
        success=False
    )

    # ユーザー作成
    memory_logger.log_event(
        AuditEventType.USER_CREATE,
        user_id='admin-1',
        username='admin',
        ip_address='127.0.0.1',
        details={'new_username': 'charlie'},
        success=True
    )

    return memory_logger


class TestAuditLoggerDBInitialization:
    """AuditLoggerDB初期化テスト"""

    def test_init_with_memory_db(self, memory_logger):
        """メモリDBで初期化"""
        assert memory_logger.db_path == ":memory:"

    def test_init_with_file_db(self, temp_db):
        """ファイルDBで初期化"""
        logger = AuditLoggerDB(db_path=temp_db)
        assert logger.db_path == temp_db
        assert os.path.exists(temp_db)

    def test_connection_context_manager(self, memory_logger):
        """接続コンテキストマネージャのテスト"""
        with memory_logger.get_connection() as conn:
            assert conn is not None
            cursor = conn.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1


class TestAuditLoggerDBEventLogging:
    """イベントログ記録テスト"""

    def test_log_simple_event(self, memory_logger):
        """シンプルなイベント記録"""
        memory_logger.log_event(
            AuditEventType.AUTH_LOGIN_SUCCESS,
            user_id='user-123',
            username='testuser',
            ip_address='192.168.1.1',
            user_agent='TestAgent/1.0'
        )

        logs = memory_logger.get_logs(limit=1)
        assert len(logs) == 1
        assert logs[0].event_type == AuditEventType.AUTH_LOGIN_SUCCESS
        assert logs[0].username == 'testuser'
        assert logs[0].user_id == 'user-123'

    def test_log_event_with_details(self, memory_logger):
        """詳細情報付きイベント記録"""
        details = {
            'action': 'password_change',
            'old_value': 'hidden',
            'new_value': 'hidden'
        }

        memory_logger.log_event(
            AuditEventType.AUTH_PASSWORD_CHANGE,
            user_id='user-456',
            username='alice',
            details=details
        )

        logs = memory_logger.get_logs(limit=1)
        assert len(logs) == 1
        assert logs[0].details == details

    def test_log_failed_event(self, memory_logger):
        """失敗イベントの記録"""
        memory_logger.log_event(
            AuditEventType.AUTH_LOGIN_FAILURE,
            username='attacker',
            ip_address='10.0.0.1',
            details={'reason': 'invalid_credentials'},
            success=False
        )

        logs = memory_logger.get_logs(limit=1)
        assert logs[0].success is False

    def test_log_event_without_user(self, memory_logger):
        """ユーザー情報なしのイベント記録"""
        memory_logger.log_event(
            AuditEventType.API_CALL,
            ip_address='1.2.3.4',
            details={'endpoint': '/api/status'}
        )

        logs = memory_logger.get_logs(limit=1)
        assert logs[0].user_id is None
        assert logs[0].username is None

    def test_log_multiple_events(self, memory_logger):
        """複数イベントの記録"""
        for i in range(10):
            memory_logger.log_event(
                AuditEventType.API_CALL,
                user_id=f'user-{i}',
                username=f'user{i}'
            )

        logs = memory_logger.get_logs(limit=100)
        assert len(logs) == 10


class TestAuditLoggerDBLogRetrieval:
    """ログ取得テスト"""

    def test_get_logs_basic(self, populated_logger):
        """基本的なログ取得"""
        logs = populated_logger.get_logs(limit=100)
        assert len(logs) == 3

    def test_get_logs_with_limit(self, populated_logger):
        """制限付きログ取得"""
        logs = populated_logger.get_logs(limit=2)
        assert len(logs) == 2

    def test_get_logs_filter_by_event_type(self, populated_logger):
        """イベントタイプでフィルタ"""
        logs = populated_logger.get_logs(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS
        )
        assert len(logs) == 1
        assert logs[0].event_type == AuditEventType.AUTH_LOGIN_SUCCESS

    def test_get_logs_filter_by_user_id(self, populated_logger):
        """ユーザーIDでフィルタ"""
        logs = populated_logger.get_logs(user_id='user-1')
        assert len(logs) == 1
        assert logs[0].user_id == 'user-1'

    def test_get_logs_filter_by_success(self, populated_logger):
        """成功/失敗でフィルタ"""
        # 成功イベントのみ
        success_logs = populated_logger.get_logs(success=True)
        assert all(log.success for log in success_logs)
        assert len(success_logs) == 2

        # 失敗イベントのみ
        failure_logs = populated_logger.get_logs(success=False)
        assert all(not log.success for log in failure_logs)
        assert len(failure_logs) == 1

    def test_get_logs_multiple_filters(self, memory_logger):
        """複数フィルタの組み合わせ"""
        # テストデータ作成
        memory_logger.log_event(
            AuditEventType.AUTH_LOGIN_SUCCESS,
            user_id='user-1',
            username='alice'
        )
        memory_logger.log_event(
            AuditEventType.AUTH_LOGIN_FAILURE,
            user_id='user-1',
            username='alice',
            success=False
        )
        memory_logger.log_event(
            AuditEventType.AUTH_LOGIN_SUCCESS,
            user_id='user-2',
            username='bob'
        )

        # user-1 かつ 成功イベント
        logs = memory_logger.get_logs(
            user_id='user-1',
            success=True
        )
        assert len(logs) == 1
        assert logs[0].user_id == 'user-1'
        assert logs[0].success is True

    def test_get_logs_ordered_by_timestamp(self, memory_logger):
        """ログが時刻順（降順）で取得されることを確認"""
        # 3つのイベントを記録
        for i in range(3):
            memory_logger.log_event(
                AuditEventType.API_CALL,
                details={'index': i}
            )

        logs = memory_logger.get_logs(limit=10)

        # 最新が先頭
        assert logs[0].details['index'] == 2
        assert logs[1].details['index'] == 1
        assert logs[2].details['index'] == 0


class TestAuditLoggerDBStatistics:
    """統計情報テスト"""

    def test_get_statistics_basic(self, populated_logger):
        """基本的な統計情報取得"""
        stats = populated_logger.get_statistics()

        assert stats['total_logs'] == 3
        assert stats['success_count'] == 2
        assert stats['failure_count'] == 1
        assert stats['success_rate'] > 0

    def test_get_statistics_empty_db(self, memory_logger):
        """空のDBでの統計情報"""
        stats = memory_logger.get_statistics()

        assert stats['total_logs'] == 0
        assert stats['success_count'] == 0
        assert stats['failure_count'] == 0
        assert stats['success_rate'] == 0

    def test_get_statistics_success_rate(self, memory_logger):
        """成功率の計算"""
        # 成功3回、失敗1回
        for i in range(3):
            memory_logger.log_event(
                AuditEventType.AUTH_LOGIN_SUCCESS,
                success=True
            )
        memory_logger.log_event(
            AuditEventType.AUTH_LOGIN_FAILURE,
            success=False
        )

        stats = memory_logger.get_statistics()
        assert stats['success_rate'] == 75.0  # 3/4 = 75%

    def test_get_statistics_event_type_counts(self, populated_logger):
        """イベントタイプ別集計"""
        stats = populated_logger.get_statistics()

        event_counts = stats['event_type_counts']
        assert 'auth.login.success' in event_counts
        assert 'auth.login.failure' in event_counts
        assert 'user.create' in event_counts


class TestAuditLoggerDBRecentFailures:
    """最近の失敗ログ取得テスト"""

    def test_get_recent_failures(self, populated_logger):
        """最近の失敗ログを取得"""
        failures = populated_logger.get_recent_failures(limit=10)

        assert len(failures) == 1
        assert failures[0].success is False
        assert failures[0].event_type == AuditEventType.AUTH_LOGIN_FAILURE

    def test_get_recent_failures_by_username(self, memory_logger):
        """特定ユーザーの失敗ログを取得"""
        # 異なるユーザーの失敗ログ
        memory_logger.log_event(
            AuditEventType.AUTH_LOGIN_FAILURE,
            username='alice',
            success=False
        )
        memory_logger.log_event(
            AuditEventType.AUTH_LOGIN_FAILURE,
            username='bob',
            success=False
        )
        memory_logger.log_event(
            AuditEventType.AUTH_LOGIN_FAILURE,
            username='alice',
            success=False
        )

        # Aliceの失敗のみ
        failures = memory_logger.get_recent_failures(username='alice', limit=10)
        assert len(failures) == 2
        assert all(f.username == 'alice' for f in failures)

    def test_get_recent_failures_limit(self, memory_logger):
        """失敗ログの取得制限"""
        # 10個の失敗ログ
        for i in range(10):
            memory_logger.log_event(
                AuditEventType.AUTH_LOGIN_FAILURE,
                username=f'user{i}',
                success=False
            )

        failures = memory_logger.get_recent_failures(limit=5)
        assert len(failures) == 5

    def test_get_recent_failures_no_failures(self, memory_logger):
        """失敗ログがない場合"""
        # 成功ログのみ
        memory_logger.log_event(
            AuditEventType.AUTH_LOGIN_SUCCESS,
            success=True
        )

        failures = memory_logger.get_recent_failures(limit=10)
        assert len(failures) == 0


class TestAuditLoggerDBEdgeCases:
    """エッジケースと例外処理テスト"""

    def test_log_event_with_unicode(self, memory_logger):
        """Unicode文字を含むイベント"""
        memory_logger.log_event(
            AuditEventType.USER_CREATE,
            username='ユーザー太郎',
            details={'note': '日本語テスト'}
        )

        logs = memory_logger.get_logs(limit=1)
        assert logs[0].username == 'ユーザー太郎'
        assert logs[0].details['note'] == '日本語テスト'

    def test_log_event_with_special_characters(self, memory_logger):
        """特殊文字を含むイベント"""
        memory_logger.log_event(
            AuditEventType.API_CALL,
            username='user@example.com',
            details={'data': '<script>alert("XSS")</script>'}
        )

        logs = memory_logger.get_logs(limit=1)
        assert logs[0].username == 'user@example.com'

    def test_log_event_with_complex_details(self, memory_logger):
        """複雑な詳細情報"""
        complex_details = {
            'nested': {
                'level1': {
                    'level2': 'value'
                }
            },
            'array': [1, 2, 3],
            'boolean': True,
            'null_value': None
        }

        memory_logger.log_event(
            AuditEventType.CONFIG_UPDATE,
            details=complex_details
        )

        logs = memory_logger.get_logs(limit=1)
        assert logs[0].details == complex_details

    def test_log_event_with_empty_details(self, memory_logger):
        """空の詳細情報"""
        memory_logger.log_event(
            AuditEventType.AUTH_LOGOUT,
            details={}
        )

        logs = memory_logger.get_logs(limit=1)
        assert logs[0].details == {}

    def test_log_event_with_none_details(self, memory_logger):
        """None詳細情報"""
        memory_logger.log_event(
            AuditEventType.AUTH_LOGOUT,
            details=None
        )

        logs = memory_logger.get_logs(limit=1)
        assert logs[0].details == {}


class TestAuditLoggerDBTransaction:
    """トランザクション処理テスト"""

    def test_context_manager_commit(self, memory_logger):
        """成功時のコミット"""
        with memory_logger.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (event_type, username, success)
                VALUES (?, ?, ?)
                """,
                ('test.event', 'testuser', 1)
            )

        # コミットされているので取得できる
        with memory_logger.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM audit_logs")
            count = cursor.fetchone()[0]
            assert count > 0

    def test_context_manager_rollback(self, memory_logger):
        """エラー時のロールバック"""
        initial_count = 0
        with memory_logger.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM audit_logs")
            initial_count = cursor.fetchone()[0]

        try:
            with memory_logger.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO audit_logs (event_type, username, success)
                    VALUES (?, ?, ?)
                    """,
                    ('test.event', 'testuser', 1)
                )
                # エラーを発生させる
                raise ValueError("Test error")
        except ValueError:
            pass

        # ロールバックされているので件数は変わらない
        with memory_logger.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM audit_logs")
            count = cursor.fetchone()[0]
            assert count == initial_count


class TestAuditLoggerDBAllEventTypes:
    """全イベントタイプのテスト"""

    def test_log_all_auth_events(self, memory_logger):
        """認証関連の全イベント"""
        auth_events = [
            AuditEventType.AUTH_LOGIN_SUCCESS,
            AuditEventType.AUTH_LOGIN_FAILURE,
            AuditEventType.AUTH_LOGOUT,
            AuditEventType.AUTH_SESSION_REFRESH,
            AuditEventType.AUTH_PASSWORD_RESET,
            AuditEventType.AUTH_PASSWORD_CHANGE
        ]

        for event in auth_events:
            memory_logger.log_event(event, username='testuser')

        logs = memory_logger.get_logs(limit=100)
        assert len(logs) == len(auth_events)

    def test_log_all_user_events(self, memory_logger):
        """ユーザー管理関連の全イベント"""
        user_events = [
            AuditEventType.USER_CREATE,
            AuditEventType.USER_DELETE,
            AuditEventType.USER_UPDATE,
            AuditEventType.USER_PERMISSION_CHANGE
        ]

        for event in user_events:
            memory_logger.log_event(event, username='admin')

        logs = memory_logger.get_logs(limit=100)
        assert len(logs) == len(user_events)

    def test_log_all_api_events(self, memory_logger):
        """API関連の全イベント"""
        api_events = [
            AuditEventType.API_CALL,
            AuditEventType.API_KEY_GENERATE,
            AuditEventType.API_KEY_REVOKE
        ]

        for event in api_events:
            memory_logger.log_event(event, username='apiuser')

        logs = memory_logger.get_logs(limit=100)
        assert len(logs) == len(api_events)


class TestAuditLoggerDBPerformance:
    """パフォーマンステスト"""

    def test_log_many_events_performance(self, memory_logger):
        """大量イベント記録のパフォーマンス"""
        import time

        start_time = time.time()

        # 1000件のイベント記録
        for i in range(1000):
            memory_logger.log_event(
                AuditEventType.API_CALL,
                user_id=f'user-{i % 100}',
                details={'index': i}
            )

        elapsed = time.time() - start_time

        # 1000件が5秒以内に記録できることを確認
        assert elapsed < 5.0

        # 全件取得できることを確認
        logs = memory_logger.get_logs(limit=2000)
        assert len(logs) == 1000

    def test_query_performance_with_filter(self, memory_logger):
        """フィルタ付きクエリのパフォーマンス"""
        # テストデータ作成
        for i in range(500):
            memory_logger.log_event(
                AuditEventType.AUTH_LOGIN_SUCCESS if i % 2 == 0 else AuditEventType.AUTH_LOGIN_FAILURE,
                user_id=f'user-{i % 50}',
                success=(i % 2 == 0)
            )

        import time
        start_time = time.time()

        # フィルタクエリ
        logs = memory_logger.get_logs(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            success=True,
            limit=100
        )

        elapsed = time.time() - start_time

        # 1秒以内に完了することを確認
        assert elapsed < 1.0
        assert len(logs) > 0


class TestAuditLoggerDBIntegration:
    """統合テスト"""

    def test_full_audit_workflow(self, memory_logger):
        """完全な監査ワークフロー"""
        # 1. ユーザーログイン成功
        memory_logger.log_event(
            AuditEventType.AUTH_LOGIN_SUCCESS,
            user_id='user-1',
            username='alice',
            ip_address='192.168.1.100'
        )

        # 2. 設定変更
        memory_logger.log_event(
            AuditEventType.CONFIG_UPDATE,
            user_id='user-1',
            username='alice',
            details={'setting': 'email_notification', 'value': True}
        )

        # 3. データ収集
        memory_logger.log_event(
            AuditEventType.DATA_COLLECTION,
            user_id='user-1',
            username='alice',
            details={'items_collected': 42}
        )

        # 4. ログアウト
        memory_logger.log_event(
            AuditEventType.AUTH_LOGOUT,
            user_id='user-1',
            username='alice'
        )

        # 検証
        logs = memory_logger.get_logs(user_id='user-1', limit=100)
        assert len(logs) == 4

        stats = memory_logger.get_statistics()
        assert stats['total_logs'] == 4
        assert stats['success_count'] == 4


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
