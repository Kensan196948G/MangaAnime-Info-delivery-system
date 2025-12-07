#!/usr/bin/env python3
"""
Google Calendar連携機能の状態確認スクリプト
"""

import os
import sys
import json
from pathlib import Path

def main():
    print("=" * 70)
    print("Google Calendar連携機能 - 状態確認")
    print("=" * 70)

    # プロジェクトルート
    project_root = Path("/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")

    # 1. config.jsonの確認
    print("\n[1] config.json の確認")
    config_path = project_root / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            calendar_config = config.get('calendar', {})
            print(f"  - ファイル: 存在 ✓")
            print(f"  - enabled: {calendar_config.get('enabled', False)}")
            print(f"  - calendar_id: {calendar_config.get('calendar_id', 'primary')}")
            print(f"  - event_color_anime: {calendar_config.get('event_color_anime', '9')}")
            print(f"  - event_color_manga: {calendar_config.get('event_color_manga', '10')}")
    else:
        print(f"  - ファイル: 見つかりません ✗")

    # 2. カレンダーモジュールの確認
    print("\n[2] カレンダーモジュールの確認")
    modules_dir = project_root / "modules"
    calendar_files = [
        "calendar_integration.py",
        "calendar_template.py",
        "calendar.py"
    ]

    found_module = None
    for filename in calendar_files:
        filepath = modules_dir / filename
        if filepath.exists():
            print(f"  - {filename}: 存在 ✓")
            found_module = filepath

            # ファイルの内容を少し確認
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                has_create_event = 'create_calendar_event' in content or 'create_event' in content
                has_sync = 'sync_releases' in content
                has_get_service = 'get_calendar_service' in content or 'get_service' in content

                print(f"    - create_event関数: {'あり ✓' if has_create_event else 'なし ✗'}")
                print(f"    - sync_releases関数: {'あり ✓' if has_sync else 'なし ✗'}")
                print(f"    - get_service関数: {'あり ✓' if has_get_service else 'なし ✗'}")
        else:
            print(f"  - {filename}: 見つかりません")

    # 3. 認証ファイルの確認
    print("\n[3] Google OAuth認証ファイルの確認")
    credentials_path = project_root / "credentials.json"
    token_path = project_root / "token.json"

    print(f"  - credentials.json: {'存在 ✓' if credentials_path.exists() else '見つかりません ✗'}")
    print(f"  - token.json: {'存在 ✓' if token_path.exists() else '見つかりません ✗'}")

    # 4. 依存パッケージの確認
    print("\n[4] 依存パッケージの確認")
    try:
        import google.oauth2.credentials
        print("  - google-auth: インストール済み ✓")
    except ImportError:
        print("  - google-auth: 未インストール ✗")

    try:
        import google_auth_oauthlib.flow
        print("  - google-auth-oauthlib: インストール済み ✓")
    except ImportError:
        print("  - google-auth-oauthlib: 未インストール ✗")

    try:
        from googleapiclient.discovery import build
        print("  - google-api-python-client: インストール済み ✓")
    except ImportError:
        print("  - google-api-python-client: 未インストール ✗")

    # 5. まとめと推奨アクション
    print("\n" + "=" * 70)
    print("推奨アクション")
    print("=" * 70)

    if not config_path.exists():
        print("❌ config.jsonが見つかりません。作成が必要です。")
    elif not calendar_config.get('enabled', False):
        print("⚠️  calendar.enabledがfalseです。trueに変更してください。")
    else:
        print("✓ config.jsonの設定OK")

    if found_module:
        print(f"✓ カレンダーモジュール発見: {found_module.name}")
    else:
        print("❌ カレンダーモジュールが見つかりません。実装が必要です。")

    if not credentials_path.exists():
        print("❌ credentials.jsonが見つかりません。")
        print("   Google Cloud Consoleから取得して配置してください。")
        print("   https://console.cloud.google.com/apis/credentials")

    if not token_path.exists():
        print("⚠️  token.jsonが見つかりません。")
        print("   初回認証後に自動生成されます。")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
