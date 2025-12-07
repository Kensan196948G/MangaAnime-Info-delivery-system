#!/usr/bin/env python3
"""
通知履歴機能のテストスクリプト

このスクリプトは、新しく実装された通知履歴機能をテストします：
1. データベースのnotification_historyテーブルの作成確認
2. 履歴レコードの作成
3. 履歴レコードの取得
4. 統計情報の取得
5. APIエンドポイントの動作確認（オプション）
"""

import sys
import os
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.db import DatabaseManager


def test_notification_history():
    """通知履歴機能の総合テスト"""

    print("=" * 80)
    print("通知履歴機能テスト開始")
    print("=" * 80)

    # データベースマネージャーの初期化
    db = DatabaseManager(db_path="./test_notification.db")

    try:
        # テスト1: テーブルの存在確認
        print("\n[テスト1] notification_historyテーブルの確認")
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='notification_history'"
            )
            table_exists = cursor.fetchone() is not None

        if table_exists:
            print("✓ notification_historyテーブルが存在します")
        else:
            print("✗ notification_historyテーブルが見つかりません")
            return False

        # テスト2: メール通知履歴の記録
        print("\n[テスト2] メール通知履歴の記録")
        email_history_id = db.record_notification_history(
            notification_type="email",
            success=True,
            error_message=None,
            releases_count=5
        )
        print(f"✓ メール通知履歴を記録しました (ID: {email_history_id})")

        # テスト3: カレンダー通知履歴の記録
        print("\n[テスト3] カレンダー通知履歴の記録")
        calendar_history_id = db.record_notification_history(
            notification_type="calendar",
            success=True,
            error_message=None,
            releases_count=3
        )
        print(f"✓ カレンダー通知履歴を記録しました (ID: {calendar_history_id})")

        # テスト4: エラー履歴の記録
        print("\n[テスト4] エラー履歴の記録")
        error_history_id = db.record_notification_history(
            notification_type="email",
            success=False,
            error_message="Gmail API認証エラー",
            releases_count=0
        )
        print(f"✓ エラー履歴を記録しました (ID: {error_history_id})")

        # テスト5: 履歴の取得
        print("\n[テスト5] 通知履歴の取得")
        all_history = db.get_notification_history(limit=10)
        print(f"✓ 全履歴: {len(all_history)}件")

        email_history = db.get_notification_history(notification_type="email", limit=10)
        print(f"✓ メール履歴: {len(email_history)}件")

        calendar_history = db.get_notification_history(notification_type="calendar", limit=10)
        print(f"✓ カレンダー履歴: {len(calendar_history)}件")

        # テスト6: 最終実行時刻の取得
        print("\n[テスト6] 最終実行時刻の取得")
        last_email_time = db.get_last_notification_time("email")
        last_calendar_time = db.get_last_notification_time("calendar")

        print(f"✓ メール最終実行: {last_email_time}")
        print(f"✓ カレンダー最終実行: {last_calendar_time}")

        # テスト7: 統計情報の取得
        print("\n[テスト7] 統計情報の取得")
        email_stats = db.get_notification_statistics(notification_type="email", days=7)
        calendar_stats = db.get_notification_statistics(notification_type="calendar", days=7)

        print(f"\nメール通知統計 (過去7日間):")
        print(f"  総実行回数: {email_stats['total_executions']}")
        print(f"  成功: {email_stats['success_count']}")
        print(f"  失敗: {email_stats['failure_count']}")
        print(f"  成功率: {email_stats['success_rate']}%")
        print(f"  処理リリース数: {email_stats['total_releases_processed']}")
        print(f"  最近のエラー数: {len(email_stats['recent_errors'])}")

        print(f"\nカレンダー登録統計 (過去7日間):")
        print(f"  総実行回数: {calendar_stats['total_executions']}")
        print(f"  成功: {calendar_stats['success_count']}")
        print(f"  失敗: {calendar_stats['failure_count']}")
        print(f"  成功率: {calendar_stats['success_rate']}%")
        print(f"  処理イベント数: {calendar_stats['total_releases_processed']}")

        # テスト8: 複数の履歴レコードを追加してテスト
        print("\n[テスト8] 複数の履歴レコードを追加")
        for i in range(5):
            db.record_notification_history(
                notification_type="email",
                success=True,
                error_message=None,
                releases_count=i + 1
            )
        print("✓ 5件の履歴を追加しました")

        # 再度統計を取得
        updated_stats = db.get_notification_statistics(notification_type="email", days=1)
        print(f"\n更新後のメール通知統計:")
        print(f"  総実行回数: {updated_stats['total_executions']}")
        print(f"  成功率: {updated_stats['success_rate']}%")

        print("\n" + "=" * 80)
        print("✓ すべてのテストが成功しました！")
        print("=" * 80)

        # 詳細履歴の表示
        print("\n[詳細] 最新の履歴レコード:")
        recent = db.get_notification_history(limit=5)
        for record in recent:
            status = "✓ 成功" if record['success'] else "✗ 失敗"
            print(f"  {record['executed_at']} | {record['notification_type']:8s} | {status} | {record['releases_count']}件")
            if record['error_message']:
                print(f"    エラー: {record['error_message']}")

        return True

    except Exception as e:
        print(f"\n✗ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close_connections()


def test_api_endpoint():
    """APIエンドポイントのテスト（オプション）"""
    print("\n" + "=" * 80)
    print("APIエンドポイントのテスト")
    print("=" * 80)

    try:
        import requests

        # Web アプリが起動していることを確認
        response = requests.get("http://localhost:3030/api/notification-status", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print("\n✓ APIエンドポイントが正常に動作しています")
            print(f"\nレスポンス:")
            import json
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"✗ APIエラー: HTTP {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("⚠ Web アプリが起動していません。")
        print("  python app/web_app.py を実行してからこのテストを再実行してください。")
        return None
    except Exception as e:
        print(f"✗ エラー: {e}")
        return False


if __name__ == "__main__":
    # データベース機能のテスト
    success = test_notification_history()

    # APIエンドポイントのテスト（オプション）
    print("\n")
    api_result = test_api_endpoint()

    # 終了ステータス
    if success:
        print("\n✓ データベース機能テスト: 成功")
    else:
        print("\n✗ データベース機能テスト: 失敗")
        sys.exit(1)

    if api_result is True:
        print("✓ APIエンドポイントテスト: 成功")
    elif api_result is False:
        print("✗ APIエンドポイントテスト: 失敗")
    else:
        print("- APIエンドポイントテスト: スキップ")

    print("\nテスト完了")
