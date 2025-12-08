#!/usr/bin/env python3
"""
Google Calendar API 初回認証セットアップ
Phase 17: カレンダー統合実装

前提条件:
1. Google Cloud Consoleでプロジェクト作成済み
2. Calendar API有効化済み
3. OAuth2認証情報（Desktop app）作成済み
4. auth/calendar_credentials.json 配置済み

実行後:
- auth/calendar_token.json が生成される
- Googleカレンダーへのアクセス権限取得完了
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print("❌ 必要なライブラリがインストールされていません")
    print("\n以下のコマンドでインストールしてください:")
    print("pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# 必要なスコープ
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# 認証ファイルパス
CREDENTIALS_FILE = 'auth/calendar_credentials.json'
TOKEN_FILE = 'auth/calendar_token.json'

def main():
    print("="*70)
    print("🗓️  Google Calendar API 初回認証セットアップ")
    print("="*70)
    print(f"\n📋 必要なファイル:")
    print(f"  - 認証情報: {CREDENTIALS_FILE}")
    print(f"  - トークン出力先: {TOKEN_FILE}")
    print(f"\n🔑 スコープ:")
    print(f"  - {SCOPES[0]}")
    print("="*70)

    # 認証情報ファイル確認
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"\n❌ エラー: {CREDENTIALS_FILE} が見つかりません")
        print("\n📝 以下の手順で作成してください:")
        print("1. https://console.cloud.google.com/ にアクセス")
        print("2. プロジェクト作成（まだの場合）")
        print("3. Calendar API を有効化")
        print("4. 認証情報 → OAuth client ID 作成（Desktop app）")
        print("5. JSONをダウンロードして auth/calendar_credentials.json に保存")
        sys.exit(1)

    # 既存トークン確認
    if os.path.exists(TOKEN_FILE):
        print(f"\n⚠️  既存のトークンファイルが見つかりました: {TOKEN_FILE}")
        response = input("上書きしますか？ (y/N): ")
        if response.lower() != 'y':
            print("キャンセルしました")
            sys.exit(0)

    # 認証フロー開始
    print("\n🌐 ブラウザが開きます...")
    print("   Googleアカウントで認証してください")
    print("   （ブラウザが開かない場合は、表示されるURLを手動で開いてください）")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES
        )

        # ローカルサーバーで認証（ポート8080）
        creds = flow.run_local_server(port=8080)

        # トークン保存
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

        print(f"\n✅ 認証成功！")
        print(f"  トークン保存: {TOKEN_FILE}")

        # テスト: カレンダーリスト取得
        print("\n📅 利用可能なカレンダー一覧:")
        service = build('calendar', 'v3', credentials=creds)

        calendar_list = service.calendarList().list().execute()

        for i, calendar in enumerate(calendar_list.get('items', []), 1):
            calendar_id = calendar['id']
            summary = calendar['summary']
            primary = " [PRIMARY]" if calendar.get('primary', False) else ""

            print(f"  {i}. {summary}{primary}")
            print(f"     ID: {calendar_id}")

        print("\n" + "="*70)
        print("✅ セットアップ完了！")
        print("="*70)
        print("\n次のステップ:")
        print("  1. modules/calendar_api.py の実装")
        print("  2. modules/calendar_sync_manager.py の実装")
        print("  3. scripts/sync_calendar.py の作成")

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print("\nトラブルシューティング:")
        print("  - ポート8080が使用中でないか確認")
        print("  - ファイアウォール設定を確認")
        print("  - 認証情報ファイルの内容を確認")
        sys.exit(1)

if __name__ == "__main__":
    main()
