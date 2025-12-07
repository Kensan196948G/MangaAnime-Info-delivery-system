#!/usr/bin/env python3
"""
Google API接続テストスクリプト

このスクリプトは以下をテストします:
1. Google Calendar APIへの接続
2. Gmail APIへの接続
3. 基本的な操作の動作確認

使用方法:
    python3 scripts/test_google_apis.py
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta


def check_credentials_file():
    """credentials.jsonの存在確認"""
    credentials_path = project_root / 'credentials.json'

    if not credentials_path.exists():
        print("❌ エラー: credentials.json が見つかりません")
        print(f"   期待されるパス: {credentials_path}")
        print("\n📘 解決方法:")
        print("   1. docs/GOOGLE_API_SETUP.md の手順に従ってcredentials.jsonを取得")
        print("   2. プロジェクトルートに配置してください")
        print(f"      cp ~/Downloads/credentials.json {project_root}/")
        return False

    print(f"✅ credentials.json が見つかりました: {credentials_path}")
    return True


def test_calendar_api():
    """Google Calendar API接続テスト"""
    print("\n" + "="*60)
    print("Google Calendar API テスト")
    print("="*60)

    try:
        # calendar_integration モジュールをインポート
        from modules.calendar_integration import GoogleCalendarIntegration

        # インスタンス作成（初回は認証フローが起動）
        calendar = GoogleCalendarIntegration()
        print("✅ カレンダーサービスの初期化成功")

        # 今後のイベントを取得
        print("\n📅 今後のイベントを取得中...")
        events = calendar.get_upcoming_events(max_results=10)

        if events:
            print(f"✅ {len(events)}件のイベントを取得しました\n")
            print("今後のイベント:")
            for event in events[:5]:  # 最大5件表示
                start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))
                summary = event.get('summary', '(タイトルなし)')
                print(f"  - {start}: {summary}")
        else:
            print("📝 イベントが見つかりませんでした（カレンダーが空です）")

        # テストイベントの作成
        print("\n📝 テストイベントを作成中...")
        test_event = {
            'summary': 'API接続テスト - 削除してOK',
            'description': 'このイベントはAPI接続テストで自動作成されました。削除して問題ありません。',
            'start': {
                'dateTime': (datetime.now() + timedelta(days=1)).isoformat(),
                'timeZone': 'Asia/Tokyo',
            },
            'end': {
                'dateTime': (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
                'timeZone': 'Asia/Tokyo',
            },
        }

        created_event = calendar.add_event(test_event)
        if created_event:
            print(f"✅ テストイベント作成成功")
            print(f"   イベントID: {created_event.get('id')}")
            print(f"   タイトル: {created_event.get('summary')}")

            # 作成したイベントを削除
            print("\n🗑️  テストイベントを削除中...")
            if calendar.delete_event(created_event.get('id')):
                print("✅ テストイベント削除成功")
            else:
                print("⚠️  テストイベント削除失敗（手動で削除してください）")

        print("\n✅ Google Calendar API テスト完了")
        return True

    except FileNotFoundError as e:
        print(f"❌ モジュールが見つかりません: {e}")
        print("   modules/calendar_integration.py が存在するか確認してください")
        return False
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        print(f"   エラータイプ: {type(e).__name__}")

        if "credentials" in str(e).lower():
            print("\n📘 解決方法:")
            print("   credentials.jsonの設定を確認してください")
            print("   詳細: docs/GOOGLE_API_SETUP.md を参照")

        return False


def test_gmail_api():
    """Gmail API接続テスト"""
    print("\n" + "="*60)
    print("Gmail API テスト")
    print("="*60)

    try:
        # mailer モジュールをインポート
        from modules.mailer import GmailNotifier

        # インスタンス作成
        mailer = GmailNotifier()
        print("✅ Gmailサービスの初期化成功")

        # プロフィール情報取得
        print("\n📧 ユーザープロフィール取得中...")
        profile = mailer.get_profile()

        if profile:
            print(f"✅ プロフィール取得成功")
            print(f"   メールアドレス: {profile.get('emailAddress')}")
            print(f"   メッセージ総数: {profile.get('messagesTotal', 'N/A')}")
            print(f"   スレッド総数: {profile.get('threadsTotal', 'N/A')}")

        # ドラフト作成テスト（送信はしない）
        print("\n📝 ドラフト作成テスト中...")
        test_subject = "API接続テスト - 送信されません"
        test_body = """
        <html>
          <body>
            <h2>Gmail API 接続テスト</h2>
            <p>このメールはテスト用のドラフトです。実際には送信されません。</p>
            <p>作成日時: {}</p>
          </body>
        </html>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # ドラフトとして保存
        draft = mailer.create_draft(
            to=profile.get('emailAddress'),
            subject=test_subject,
            body=test_body
        )

        if draft:
            print(f"✅ ドラフト作成成功")
            print(f"   ドラフトID: {draft.get('id')}")
            print("   ※Gmailのドラフトフォルダを確認してください")
            print("   ※不要な場合は手動で削除してください")

        print("\n✅ Gmail API テスト完了")
        return True

    except FileNotFoundError as e:
        print(f"❌ モジュールが見つかりません: {e}")
        print("   modules/mailer.py が存在するか確認してください")
        return False
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        print(f"   エラータイプ: {type(e).__name__}")

        if "credentials" in str(e).lower():
            print("\n📘 解決方法:")
            print("   credentials.jsonの設定を確認してください")
            print("   詳細: docs/GOOGLE_API_SETUP.md を参照")

        return False


def main():
    """メイン処理"""
    print("="*60)
    print("Google API 接続テストスクリプト")
    print("="*60)
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"プロジェクトルート: {project_root}")

    # 1. credentials.jsonの確認
    if not check_credentials_file():
        sys.exit(1)

    # 2. Calendar APIテスト
    calendar_result = test_calendar_api()

    # 3. Gmail APIテスト
    gmail_result = test_gmail_api()

    # 結果サマリー
    print("\n" + "="*60)
    print("テスト結果サマリー")
    print("="*60)
    print(f"Google Calendar API: {'✅ 成功' if calendar_result else '❌ 失敗'}")
    print(f"Gmail API:          {'✅ 成功' if gmail_result else '❌ 失敗'}")

    if calendar_result and gmail_result:
        print("\n🎉 すべてのテストが成功しました！")
        print("システムは正常に動作しています。")
        sys.exit(0)
    else:
        print("\n⚠️  一部のテストが失敗しました")
        print("エラーメッセージを確認して問題を解決してください")
        print("詳細: docs/GOOGLE_API_SETUP.md")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  ユーザーによって中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
