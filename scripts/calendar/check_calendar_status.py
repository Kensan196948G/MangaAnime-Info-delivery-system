#!/usr/bin/env python3
"""
Google Calendar連携機能の状態確認スクリプト
"""

import os
import logging
import sys
import json
from pathlib import Path

def main():

logger = logging.getLogger(__name__)

    logger.info("=" * 70)
    logger.info("Google Calendar連携機能 - 状態確認")
    logger.info("=" * 70)

    # プロジェクトルート
    project_root = Path("/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")

    # 1. config.jsonの確認
    logger.info("\n[1] config.json の確認")
    config_path = project_root / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            calendar_config = config.get('calendar', {})
            logger.info(f"  - ファイル: 存在 ✓")
            logger.info(f"  - enabled: {calendar_config.get('enabled', False)}")
            logger.info(f"  - calendar_id: {calendar_config.get('calendar_id', 'primary')}")
            logger.info(f"  - event_color_anime: {calendar_config.get('event_color_anime', '9')}")
            logger.info(f"  - event_color_manga: {calendar_config.get('event_color_manga', '10')}")
    else:
        logger.info(f"  - ファイル: 見つかりません ✗")

    # 2. カレンダーモジュールの確認
    logger.info("\n[2] カレンダーモジュールの確認")
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
            logger.info(f"  - {filename}: 存在 ✓")
            found_module = filepath

            # ファイルの内容を少し確認
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                has_create_event = 'create_calendar_event' in content or 'create_event' in content
                has_sync = 'sync_releases' in content
                has_get_service = 'get_calendar_service' in content or 'get_service' in content

                logger.info(f"    - create_event関数: {'あり ✓' if has_create_event else 'なし ✗'}")
                logger.info(f"    - sync_releases関数: {'あり ✓' if has_sync else 'なし ✗'}")
                logger.info(f"    - get_service関数: {'あり ✓' if has_get_service else 'なし ✗'}")
        else:
            logger.info(f"  - {filename}: 見つかりません")

    # 3. 認証ファイルの確認
    logger.info("\n[3] Google OAuth認証ファイルの確認")
    credentials_path = project_root / "credentials.json"
    token_path = project_root / "token.json"

    logger.info(f"  - credentials.json: {'存在 ✓' if credentials_path.exists() else '見つかりません ✗'}")
    logger.info(f"  - token.json: {'存在 ✓' if token_path.exists() else '見つかりません ✗'}")

    # 4. 依存パッケージの確認
    logger.info("\n[4] 依存パッケージの確認")
    try:
        import google.oauth2.credentials
        logger.info("  - google-auth: インストール済み ✓")
    except ImportError:
        logger.info("  - google-auth: 未インストール ✗")

    try:
        import google_auth_oauthlib.flow
        logger.info("  - google-auth-oauthlib: インストール済み ✓")
    except ImportError:
        logger.info("  - google-auth-oauthlib: 未インストール ✗")

    try:
        from googleapiclient.discovery import build
        logger.info("  - google-api-python-client: インストール済み ✓")
    except ImportError:
        logger.info("  - google-api-python-client: 未インストール ✗")

    # 5. まとめと推奨アクション
    logger.info("\n" + "=" * 70)
    logger.info("推奨アクション")
    logger.info("=" * 70)

    if not config_path.exists():
        logger.info("❌ config.jsonが見つかりません。作成が必要です。")
    elif not calendar_config.get('enabled', False):
        logger.info("⚠️  calendar.enabledがfalseです。trueに変更してください。")
    else:
        logger.info("✓ config.jsonの設定OK")

    if found_module:
        logger.info(f"✓ カレンダーモジュール発見: {found_module.name}")
    else:
        logger.info("❌ カレンダーモジュールが見つかりません。実装が必要です。")

    if not credentials_path.exists():
        logger.info("❌ credentials.jsonが見つかりません。")
        logger.info("   Google Cloud Consoleから取得して配置してください。")
        logger.info("   https://console.cloud.google.com/apis/credentials")

    if not token_path.exists():
        logger.info("⚠️  token.jsonが見つかりません。")
        logger.info("   初回認証後に自動生成されます。")

    logger.info("\n" + "=" * 70)

if __name__ == "__main__":
    main()
