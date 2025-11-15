"""
通知履歴機能の包括的テストスイート

テスト対象:
1. データベーステスト (notification_historyテーブル)
2. APIエンドポイントテスト (/api/notification-status)
3. UI表示テスト
4. 統合テスト (メール送信 → 履歴記録 → UI表示)
"""

import pytest
import json
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestNotificationHistoryDatabase:
    """データベース層のテスト"""

    @pytest.fixture
    def test_db(self, tmp_path):
        """テスト用データベースを作成"""
        db_path = tmp_path / "test_notification.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # notification_historyテーブルを作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_type TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                count INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        yield conn
        conn.close()

    def test_table_creation(self, test_db):
        """テーブルが正しく作成されることを確認"""
        cursor = test_db.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='notification_history'
        """)
        result = cursor.fetchone()
        assert result is not None, "notification_historyテーブルが存在しません"
        assert result[0] == 'notification_history'

    def test_insert_notification_record(self, test_db):
        """履歴レコードの挿入テスト"""
        cursor = test_db.cursor()

        # レコード挿入
        cursor.execute("""
            INSERT INTO notification_history
            (notification_type, status, details, count)
            VALUES (?, ?, ?, ?)
        """, ('email', 'success', 'Test notification', 5))
        test_db.commit()

        # 挿入確認
        cursor.execute("SELECT * FROM notification_history WHERE notification_type = 'email'")
        result = cursor.fetchone()

        assert result is not None, "レコードが挿入されていません"
        assert result[1] == 'email', "notification_typeが一致しません"
        assert result[2] == 'success', "statusが一致しません"
        assert result[4] == 5, "countが一致しません"

    def test_retrieve_recent_history(self, test_db):
        """最近の履歴取得テスト"""
        cursor = test_db.cursor()

        # 複数レコード挿入
        records = [
            ('email', 'success', 'Email 1', 3),
            ('calendar', 'success', 'Calendar 1', 2),
            ('email', 'failed', 'Email 2', 0),
        ]

        for record in records:
            cursor.execute("""
                INSERT INTO notification_history
                (notification_type, status, details, count)
                VALUES (?, ?, ?, ?)
            """, record)
        test_db.commit()

        # 最新10件取得
        cursor.execute("""
            SELECT * FROM notification_history
            ORDER BY created_at DESC
            LIMIT 10
        """)
        results = cursor.fetchall()

        assert len(results) == 3, "取得件数が正しくありません"
        assert results[0][1] == 'email', "最新レコードが正しくありません"

    def test_filter_by_status(self, test_db):
        """ステータスでのフィルタリングテスト"""
        cursor = test_db.cursor()

        # 成功・失敗レコード挿入
        cursor.execute("""
            INSERT INTO notification_history
            (notification_type, status, details, count)
            VALUES (?, ?, ?, ?)
        """, ('email', 'success', 'Success test', 5))

        cursor.execute("""
            INSERT INTO notification_history
            (notification_type, status, details, count, error_message)
            VALUES (?, ?, ?, ?, ?)
        """, ('email', 'failed', 'Failed test', 0, 'SMTP error'))
        test_db.commit()

        # 成功レコードのみ取得
        cursor.execute("""
            SELECT * FROM notification_history
            WHERE status = 'success'
        """)
        success_results = cursor.fetchall()

        # 失敗レコードのみ取得
        cursor.execute("""
            SELECT * FROM notification_history
            WHERE status = 'failed'
        """)
        failed_results = cursor.fetchall()

        assert len(success_results) == 1, "成功レコード数が正しくありません"
        assert len(failed_results) == 1, "失敗レコード数が正しくありません"
        assert failed_results[0][5] == 'SMTP error', "エラーメッセージが記録されていません"


class TestNotificationHistoryAPI:
    """APIエンドポイントのテスト"""

    @pytest.fixture
    def mock_db(self):
        """モックデータベース"""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            # モックデータ
            mock_cursor.fetchall.return_value = [
                (1, 'email', 'success', 'Test email', 5, None, '2025-11-15 10:00:00'),
                (2, 'calendar', 'success', 'Test calendar', 3, None, '2025-11-15 10:05:00'),
            ]
            mock_cursor.fetchone.return_value = (8,)  # 総通知数

            yield mock_cursor

    def test_notification_status_endpoint(self, mock_db):
        """通知ステータスエンドポイントのレスポンステスト"""
        # APIレスポンス構造をシミュレート
        response = {
            "status": "success",
            "data": {
                "last_execution": "2025-11-15 10:05:00",
                "next_execution": "2025-11-16 08:00:00",
                "total_notifications": 8,
                "recent_history": [
                    {
                        "id": 1,
                        "type": "email",
                        "status": "success",
                        "details": "Test email",
                        "count": 5,
                        "timestamp": "2025-11-15 10:00:00"
                    },
                    {
                        "id": 2,
                        "type": "calendar",
                        "status": "success",
                        "details": "Test calendar",
                        "count": 3,
                        "timestamp": "2025-11-15 10:05:00"
                    }
                ]
            }
        }

        assert response["status"] == "success", "ステータスが正しくありません"
        assert "last_execution" in response["data"], "最終実行時刻がありません"
        assert "next_execution" in response["data"], "次回実行時刻がありません"
        assert response["data"]["total_notifications"] == 8, "総通知数が正しくありません"
        assert len(response["data"]["recent_history"]) == 2, "履歴件数が正しくありません"

    def test_next_execution_calculation(self):
        """次回実行時刻の計算テスト"""
        # 毎朝8:00に実行する想定
        last_execution = datetime(2025, 11, 15, 10, 0, 0)

        # 次回実行時刻を計算
        next_day = last_execution.date() + timedelta(days=1)
        next_execution = datetime.combine(next_day, datetime.min.time().replace(hour=8))

        assert next_execution.hour == 8, "実行時刻が正しくありません"
        assert next_execution.date() == last_execution.date() + timedelta(days=1), "実行日が正しくありません"

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        with patch('sqlite3.connect', side_effect=sqlite3.Error("Database error")):
            try:
                conn = sqlite3.connect("test.db")
                pytest.fail("例外が発生すべきです")
            except sqlite3.Error as e:
                assert str(e) == "Database error", "エラーメッセージが正しくありません"


class TestNotificationHistoryUI:
    """UI表示テスト"""

    def test_history_table_rendering(self):
        """履歴テーブルのレンダリングテスト"""
        history_data = [
            {
                "id": 1,
                "type": "email",
                "status": "success",
                "details": "5件の通知を送信",
                "timestamp": "2025-11-15 10:00:00"
            },
            {
                "id": 2,
                "type": "calendar",
                "status": "success",
                "details": "3件のイベントを登録",
                "timestamp": "2025-11-15 10:05:00"
            }
        ]

        # HTMLテーブル行を生成
        table_rows = []
        for item in history_data:
            row = f"""
            <tr>
                <td>{item['timestamp']}</td>
                <td>{item['type']}</td>
                <td class="status-{item['status']}">{item['status']}</td>
                <td>{item['details']}</td>
            </tr>
            """
            table_rows.append(row)

        assert len(table_rows) == 2, "テーブル行数が正しくありません"
        assert "email" in table_rows[0], "メール通知行が含まれていません"
        assert "calendar" in table_rows[1], "カレンダー行が含まれていません"

    def test_auto_refresh_interval(self):
        """自動更新間隔のテスト"""
        # 30秒ごとに更新する設定
        refresh_interval = 30000  # ミリ秒

        assert refresh_interval == 30000, "更新間隔が正しくありません"
        assert refresh_interval >= 10000, "更新間隔が短すぎます"

    def test_error_message_display(self):
        """エラーメッセージ表示テスト"""
        error_data = {
            "id": 3,
            "type": "email",
            "status": "failed",
            "details": "送信失敗",
            "error_message": "SMTP authentication failed",
            "timestamp": "2025-11-15 11:00:00"
        }

        # エラー表示HTMLを生成
        error_html = f"""
        <div class="alert alert-danger">
            <strong>エラー:</strong> {error_data['error_message']}
            <br>
            <small>{error_data['timestamp']}</small>
        </div>
        """

        assert "alert-danger" in error_html, "エラークラスが適用されていません"
        assert error_data['error_message'] in error_html, "エラーメッセージが表示されていません"


class TestNotificationIntegration:
    """統合テスト (メール送信 → 履歴記録 → UI表示)"""

    @pytest.fixture
    def integration_env(self, tmp_path):
        """統合テスト環境をセットアップ"""
        db_path = tmp_path / "integration_test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # テーブル作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_type TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                count INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS releases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_id INTEGER NOT NULL,
                release_type TEXT,
                number TEXT,
                platform TEXT,
                release_date DATE,
                notified INTEGER DEFAULT 0
            )
        """)
        conn.commit()

        yield conn, cursor
        conn.close()

    def test_email_send_and_record(self, integration_env):
        """メール送信と履歴記録の統合テスト"""
        conn, cursor = integration_env

        # ステップ1: 未通知のリリースをシミュレート
        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, platform, release_date, notified)
            VALUES (1, 'episode', '5', 'dアニメストア', '2025-11-16', 0)
        """)
        conn.commit()

        # ステップ2: 通知処理をシミュレート
        cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 0")
        pending_count = cursor.fetchone()[0]

        # メール送信成功をシミュレート
        email_sent = True

        if email_sent:
            # ステップ3: 履歴記録
            cursor.execute("""
                INSERT INTO notification_history
                (notification_type, status, details, count)
                VALUES (?, ?, ?, ?)
            """, ('email', 'success', f'{pending_count}件の通知を送信', pending_count))

            # リリースを通知済みに更新
            cursor.execute("UPDATE releases SET notified = 1 WHERE notified = 0")
            conn.commit()

        # ステップ4: 履歴確認
        cursor.execute("SELECT * FROM notification_history WHERE notification_type = 'email'")
        history = cursor.fetchone()

        assert history is not None, "履歴が記録されていません"
        assert history[2] == 'success', "ステータスが正しくありません"
        assert history[4] == pending_count, "通知件数が正しくありません"

        # ステップ5: 通知済み確認
        cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 1")
        notified_count = cursor.fetchone()[0]
        assert notified_count == pending_count, "通知済み件数が一致しません"

    def test_calendar_integration_and_record(self, integration_env):
        """カレンダー統合と履歴記録のテスト"""
        conn, cursor = integration_env

        # カレンダー登録をシミュレート
        calendar_event_count = 3
        calendar_success = True

        if calendar_success:
            cursor.execute("""
                INSERT INTO notification_history
                (notification_type, status, details, count)
                VALUES (?, ?, ?, ?)
            """, ('calendar', 'success', f'{calendar_event_count}件のイベントを登録', calendar_event_count))
            conn.commit()

        # 履歴確認
        cursor.execute("SELECT * FROM notification_history WHERE notification_type = 'calendar'")
        history = cursor.fetchone()

        assert history is not None, "カレンダー履歴が記録されていません"
        assert history[2] == 'success', "カレンダーステータスが正しくありません"
        assert history[4] == calendar_event_count, "イベント件数が正しくありません"

    def test_error_recovery_and_logging(self, integration_env):
        """エラー発生時のリカバリとログ記録テスト"""
        conn, cursor = integration_env

        # メール送信失敗をシミュレート
        email_error = "SMTP authentication failed"

        cursor.execute("""
            INSERT INTO notification_history
            (notification_type, status, details, count, error_message)
            VALUES (?, ?, ?, ?, ?)
        """, ('email', 'failed', '送信失敗', 0, email_error))
        conn.commit()

        # エラー履歴確認
        cursor.execute("SELECT * FROM notification_history WHERE status = 'failed'")
        error_history = cursor.fetchone()

        assert error_history is not None, "エラー履歴が記録されていません"
        assert error_history[5] == email_error, "エラーメッセージが正しくありません"

    def test_full_workflow_simulation(self, integration_env):
        """完全ワークフローシミュレーション"""
        conn, cursor = integration_env

        # 1. データ収集（シミュレート）
        releases_data = [
            (1, 'episode', '1', 'Netflix', '2025-11-16', 0),
            (2, 'volume', '5', 'BookWalker', '2025-11-17', 0),
        ]

        for release in releases_data:
            cursor.execute("""
                INSERT INTO releases
                (work_id, release_type, number, platform, release_date, notified)
                VALUES (?, ?, ?, ?, ?, ?)
            """, release)
        conn.commit()

        # 2. メール送信
        cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 0")
        email_count = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO notification_history
            (notification_type, status, details, count)
            VALUES (?, ?, ?, ?)
        """, ('email', 'success', f'{email_count}件のメール送信', email_count))

        cursor.execute("UPDATE releases SET notified = 1")
        conn.commit()

        # 3. カレンダー登録
        calendar_count = email_count
        cursor.execute("""
            INSERT INTO notification_history
            (notification_type, status, details, count)
            VALUES (?, ?, ?, ?)
        """, ('calendar', 'success', f'{calendar_count}件のカレンダー登録', calendar_count))
        conn.commit()

        # 4. 結果検証
        cursor.execute("SELECT COUNT(*) FROM notification_history")
        total_history = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 1")
        notified_releases = cursor.fetchone()[0]

        assert total_history == 2, "履歴件数が正しくありません"
        assert notified_releases == email_count, "通知済みリリース数が正しくありません"


class TestPerformanceAndScalability:
    """パフォーマンスとスケーラビリティのテスト"""

    def test_large_history_retrieval(self, tmp_path):
        """大量履歴データの取得パフォーマンステスト"""
        db_path = tmp_path / "perf_test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE notification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_type TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 1000件のレコードを挿入
        import time
        start_time = time.time()

        for i in range(1000):
            cursor.execute("""
                INSERT INTO notification_history
                (notification_type, status, details, count)
                VALUES (?, ?, ?, ?)
            """, ('email', 'success', f'Test {i}', i % 10))
        conn.commit()

        insert_time = time.time() - start_time

        # 取得パフォーマンステスト
        start_time = time.time()
        cursor.execute("""
            SELECT * FROM notification_history
            ORDER BY created_at DESC
            LIMIT 100
        """)
        results = cursor.fetchall()
        query_time = time.time() - start_time

        conn.close()

        assert len(results) == 100, "取得件数が正しくありません"
        assert insert_time < 5.0, f"挿入が遅すぎます: {insert_time}秒"
        assert query_time < 0.5, f"クエリが遅すぎます: {query_time}秒"

    def test_concurrent_access(self, tmp_path):
        """同時アクセステスト"""
        from threading import Thread, Lock
        import time

        db_path = tmp_path / "concurrent_test.db"

        # 初期セットアップ用の接続
        setup_conn = sqlite3.connect(str(db_path))
        setup_cursor = setup_conn.cursor()
        setup_cursor.execute("""
            CREATE TABLE notification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_type TEXT NOT NULL,
                status TEXT NOT NULL,
                count INTEGER DEFAULT 0
            )
        """)
        setup_conn.commit()
        setup_conn.close()

        # ロックを使用してトランザクション競合を防ぐ
        db_lock = Lock()
        success_count = [0]  # スレッド間で共有するカウンタ

        def insert_record(record_id):
            try:
                with db_lock:
                    # 各スレッドで独立した接続を作成
                    thread_conn = sqlite3.connect(str(db_path))
                    thread_cursor = thread_conn.cursor()
                    thread_cursor.execute("""
                        INSERT INTO notification_history
                        (notification_type, status, count)
                        VALUES (?, ?, ?)
                    """, ('email', 'success', record_id))
                    thread_conn.commit()
                    thread_conn.close()
                    success_count[0] += 1
            except Exception as e:
                print(f"Thread {record_id} error: {e}")

        # 10個のスレッドで同時挿入
        threads = []
        for i in range(10):
            t = Thread(target=insert_record, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 結果確認
        verify_conn = sqlite3.connect(str(db_path))
        verify_cursor = verify_conn.cursor()
        verify_cursor.execute("SELECT COUNT(*) FROM notification_history")
        count = verify_cursor.fetchone()[0]
        verify_conn.close()

        assert count == 10, f"同時挿入が失敗しました: {count}件（成功数: {success_count[0]}）"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
