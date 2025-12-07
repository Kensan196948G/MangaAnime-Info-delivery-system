"""
監査ログDB版のテストスクリプト
作成日: 2025-12-07
目的: AuditLoggerDBクラスの動作確認
"""

import os
import sys
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.audit_log_db import AuditLoggerDB


class TestAuditLogDB:
    """監査ログDB版のテストクラス"""

    def __init__(self):
        # テスト用の一時データベース
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3')
        self.db_path = self.temp_db.name
        self.logger = AuditLoggerDB(db_path=self.db_path, auto_migrate=True)

    def cleanup(self):
        """テスト後のクリーンアップ"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_basic_logging(self):
        """基本的なログ記録テスト"""
        print("\n[TEST] 基本的なログ記録...")

        # ログ記録
        log_id = self.logger.log_event(
            event_type="test_event",
            user_id="test_user",
            username="Test User",
            ip_address="192.168.1.100",
            user_agent="Test Agent",
            details={"action": "test"},
            success=True
        )

        assert log_id > 0, "ログIDが取得できませんでした"
        print(f"  ✓ ログID: {log_id}")

        # ログ取得
        logs = self.logger.get_logs(limit=1)
        assert len(logs) > 0, "ログが取得できませんでした"
        assert logs[0]['event_type'] == 'test_event'
        print(f"  ✓ ログ取得成功: {logs[0]['event_type']}")

    def test_filtering(self):
        """フィルタリングテスト"""
        print("\n[TEST] フィルタリング...")

        # 複数ログ記録
        for i in range(5):
            self.logger.log_event(
                event_type="login_success" if i % 2 == 0 else "login_failure",
                user_id=f"user{i}",
                username=f"User {i}",
                success=(i % 2 == 0)
            )

        # イベントタイプフィルタ
        success_logs = self.logger.get_logs(event_type="login_success")
        failure_logs = self.logger.get_logs(event_type="login_failure")

        print(f"  ✓ 成功ログ: {len(success_logs)} 件")
        print(f"  ✓ 失敗ログ: {len(failure_logs)} 件")

        # 成功フラグフィルタ
        all_success = self.logger.get_logs(success=True)
        all_failure = self.logger.get_logs(success=False)

        print(f"  ✓ 全成功ログ: {len(all_success)} 件")
        print(f"  ✓ 全失敗ログ: {len(all_failure)} 件")

    def test_statistics(self):
        """統計情報テスト"""
        print("\n[TEST] 統計情報...")

        # テストデータ投入
        for i in range(10):
            self.logger.log_event(
                event_type="api_request",
                user_id=f"user{i % 3}",
                endpoint="/api/test",
                method="GET",
                status_code=200 if i % 2 == 0 else 500,
                response_time_ms=50 + i * 10,
                success=(i % 2 == 0)
            )

        stats = self.logger.get_statistics()

        print(f"  ✓ 総ログ数: {stats['total_logs']}")
        print(f"  ✓ 成功数: {stats['success_count']}")
        print(f"  ✓ 失敗数: {stats['failure_count']}")
        print(f"  ✓ 平均レスポンス時間: {stats['avg_response_time_ms']}ms")

        assert stats['total_logs'] > 0
        assert 'event_statistics' in stats

    def test_user_activity(self):
        """ユーザーアクティビティテスト"""
        print("\n[TEST] ユーザーアクティビティ...")

        # テストデータ投入
        test_user = "activity_user"
        for i in range(5):
            self.logger.log_event(
                event_type="page_view",
                user_id=test_user,
                username="Activity User",
                details={"page": f"page_{i}"}
            )

        activity = self.logger.get_user_activity(user_id=test_user, days=30)

        print(f"  ✓ ユーザーID: {activity['user_id']}")
        print(f"  ✓ 総アクション数: {activity['total_actions']}")
        print(f"  ✓ エラー数: {activity['error_count']}")

        assert activity['total_actions'] >= 5

    def test_security_alerts(self):
        """セキュリティアラートテスト"""
        print("\n[TEST] セキュリティアラート...")

        # 同一IPから複数失敗
        suspicious_ip = "203.0.113.100"
        for i in range(7):
            self.logger.log_event(
                event_type="login_failure",
                ip_address=suspicious_ip,
                user_agent="Suspicious Bot",
                success=False,
                error_message="Invalid credentials"
            )

        alerts = self.logger.get_security_alerts(threshold=5, hours=24)

        print(f"  ✓ アラート件数: {len(alerts)}")
        if alerts:
            alert = alerts[0]
            print(f"  ✓ 検出IP: {alert['ip_address']}")
            print(f"  ✓ 失敗回数: {alert['failure_count']}")

        assert len(alerts) > 0, "セキュリティアラートが検出されませんでした"

    def test_date_filtering(self):
        """日付範囲フィルタリングテスト"""
        print("\n[TEST] 日付範囲フィルタリング...")

        # 異なる時期のログを記録
        now = datetime.now()
        past = now - timedelta(days=10)

        # 過去のログをシミュレート（手動INSERT）
        with self.logger._get_connection() as conn:
            conn.execute("""
                INSERT INTO audit_logs (event_type, user_id, timestamp, success)
                VALUES (?, ?, ?, ?)
            """, ("old_event", "old_user", past.isoformat(), 1))

        # 最近のログ
        self.logger.log_event(
            event_type="new_event",
            user_id="new_user"
        )

        # 日付範囲指定
        start_date = now - timedelta(days=1)
        recent_logs = self.logger.get_logs(
            start_date=start_date,
            limit=100
        )

        print(f"  ✓ 最近のログ: {len(recent_logs)} 件")

        # 古いログも含む
        all_logs = self.logger.get_logs(limit=100)
        print(f"  ✓ 全ログ: {len(all_logs)} 件")

        assert len(recent_logs) >= 1
        assert len(all_logs) >= 2

    def test_cleanup(self):
        """クリーンアップテスト"""
        print("\n[TEST] クリーンアップ...")

        # 古いログを手動挿入
        old_date = (datetime.now() - timedelta(days=100)).isoformat()

        with self.logger._get_connection() as conn:
            for i in range(5):
                conn.execute("""
                    INSERT INTO audit_logs (event_type, timestamp, success)
                    VALUES (?, ?, ?)
                """, (f"old_event_{i}", old_date, 1))

        # 現在のログ
        self.logger.log_event(event_type="current_event")

        # クリーンアップ前のカウント
        stats_before = self.logger.get_statistics()
        print(f"  ✓ クリーンアップ前: {stats_before['total_logs']} 件")

        # クリーンアップ実行
        deleted = self.logger.cleanup_old_logs(days=90, keep_critical=False)
        print(f"  ✓ 削除件数: {deleted}")

        # クリーンアップ後のカウント
        stats_after = self.logger.get_statistics()
        print(f"  ✓ クリーンアップ後: {stats_after['total_logs']} 件")

        assert stats_after['total_logs'] < stats_before['total_logs']

    def test_memory_migration(self):
        """メモリログ移行テスト"""
        print("\n[TEST] メモリログ移行...")

        # メモリログをシミュレート
        memory_logs = [
            {
                'event_type': 'memory_event_1',
                'user_id': 'user1',
                'username': 'User 1',
                'ip_address': '192.168.1.1',
                'success': True,
                'details': {'source': 'memory'}
            },
            {
                'event_type': 'memory_event_2',
                'user_id': 'user2',
                'username': 'User 2',
                'ip_address': '192.168.1.2',
                'success': False,
                'error_message': 'Test error'
            }
        ]

        # 移行実行
        migrated_count = self.logger.migrate_from_memory(memory_logs)
        print(f"  ✓ 移行件数: {migrated_count}")

        # 移行確認
        logs = self.logger.get_logs(limit=10)
        migrated_events = [log['event_type'] for log in logs
                          if log['event_type'].startswith('memory_event')]

        print(f"  ✓ 移行確認: {len(migrated_events)} 件")

        assert migrated_count == len(memory_logs)
        assert len(migrated_events) == len(memory_logs)

    def test_json_details(self):
        """JSON詳細情報テスト"""
        print("\n[TEST] JSON詳細情報...")

        # 複雑なJSON
        complex_details = {
            "action": "update",
            "resource": {
                "type": "article",
                "id": 123,
                "changes": {
                    "title": {"old": "旧タイトル", "new": "新タイトル"},
                    "tags": ["Python", "Database", "SQLite"]
                }
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0"
            }
        }

        # ログ記録
        log_id = self.logger.log_event(
            event_type="complex_event",
            user_id="test_user",
            details=complex_details
        )

        # ログ取得
        logs = self.logger.get_logs(limit=1)
        retrieved_details = logs[0]['details']

        print(f"  ✓ 詳細情報保存成功")
        print(f"  ✓ アクション: {retrieved_details['action']}")
        print(f"  ✓ リソースID: {retrieved_details['resource']['id']}")

        assert retrieved_details['action'] == complex_details['action']
        assert retrieved_details['resource']['id'] == 123

    def run_all_tests(self):
        """全テスト実行"""
        print("=" * 60)
        print("監査ログDB版 テストスイート")
        print("=" * 60)

        try:
            self.test_basic_logging()
            self.test_filtering()
            self.test_statistics()
            self.test_user_activity()
            self.test_security_alerts()
            self.test_date_filtering()
            self.test_cleanup()
            self.test_memory_migration()
            self.test_json_details()

            print("\n" + "=" * 60)
            print("✅ すべてのテストが成功しました！")
            print("=" * 60)

        except AssertionError as e:
            print(f"\n❌ テスト失敗: {e}")
            return False
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()

        return True


def main():
    """メイン処理"""
    tester = TestAuditLogDB()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
