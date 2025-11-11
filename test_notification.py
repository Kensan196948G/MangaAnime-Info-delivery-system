#!/usr/bin/env python3
"""
通知機能テスト用スクリプト
未通知のリリースを1件取得してテスト通知を送信
"""

import sys
import logging
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.config import get_config
from modules.db import DatabaseManager
from modules.logger import setup_logging
from modules.mailer import GmailNotifier, EmailTemplateGenerator
from modules.calendar import GoogleCalendarManager


def main():
    print("🧪 通知機能テストを開始します...")

    # 設定と初期化
    config = get_config()
    setup_logging(config)
    logger = logging.getLogger(__name__)

    # データベース接続
    db = DatabaseManager(config.get_db_path())

    # 未通知リリースを1件取得
    unnotified_releases = db.get_unnotified_releases(limit=1)

    if not unnotified_releases:
        print("❌ 未通知リリースがありません")
        return 1

    # テスト対象リリース
    test_release = unnotified_releases[0]
    print(f"📧 テスト対象: {test_release}")

    try:
        # Gmail通知テスト
        print("📧 Gmail認証とテスト通知を実行中...")
        mailer = GmailNotifier(config)
        email_generator = EmailTemplateGenerator(config)

        if mailer.authenticate():
            print("✅ Gmail認証成功")

            # テスト用リリース情報を作成
            test_releases = [
                {
                    "title": "テスト作品",
                    "number": "1",
                    "platform": "テストプラットフォーム",
                    "release_date": "2025-08-09",
                    "official_url": "https://example.com",
                    "type": "anime",
                }
            ]

            # メール生成と送信
            notification = email_generator.generate_release_notification(test_releases)

            if mailer.send_notification(notification):
                print("✅ テストメール送信成功")
            else:
                print("❌ テストメール送信失敗")
        else:
            print("❌ Gmail認証失敗")
            return 1

        # Googleカレンダーテスト
        print("📅 Googleカレンダー認証とテストイベント作成中...")
        calendar = GoogleCalendarManager(config)

        if calendar.authenticate():
            print("✅ Googleカレンダー認証成功")

            # テストイベント作成
            results = calendar.bulk_create_release_events(test_releases)
            created_count = len([v for v in results.values() if v])

            if created_count > 0:
                print(f"✅ テストカレンダーイベント作成成功: {created_count} 件")
            else:
                print("❌ テストカレンダーイベント作成失敗")
        else:
            print("❌ Googleカレンダー認証失敗")
            return 1

        print("🎉 すべてのテストが成功しました！")
        return 0

    except Exception as e:
        print(f"❌ テスト中にエラーが発生: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
