#!/usr/bin/env python3
"""
Google Calendar連携を有効化するスクリプト
"""

import json
import logging
import os
import sys
from pathlib import Path

def enable_calendar_in_config():

logger = logging.getLogger(__name__)

    """config.jsonのcalendar.enabledをtrueに設定"""

    project_root = Path("/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")
    config_path = project_root / "config.json"

    if not config_path.exists():
        logger.info(f"エラー: {config_path} が見つかりません")
        return False

    # config.jsonを読み込み
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # calendarセクションの初期化または更新
    if 'calendar' not in config:
        config['calendar'] = {}

    # 設定を更新
    original_enabled = config['calendar'].get('enabled', False)
    config['calendar']['enabled'] = True
    config['calendar']['calendar_id'] = config['calendar'].get('calendar_id', 'primary')
    config['calendar']['event_color_anime'] = config['calendar'].get('event_color_anime', '9')
    config['calendar']['event_color_manga'] = config['calendar'].get('event_color_manga', '10')

    # config.jsonに書き戻し
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    logger.info("=" * 70)
    logger.info("Google Calendar連携を有効化しました")
    logger.info("=" * 70)
    logger.info(f"設定ファイル: {config_path}")
    logger.info(f"変更前: calendar.enabled = {original_enabled}")
    logger.info(f"変更後: calendar.enabled = True")
    logger.info("")
    logger.info("現在の設定:")
    logger.info(f"  - calendar_id: {config['calendar']['calendar_id']}")
    logger.info(f"  - event_color_anime: {config['calendar']['event_color_anime']}")
    logger.info(f"  - event_color_manga: {config['calendar']['event_color_manga']}")
    logger.info("=" * 70)

    return True

def main():
    success = enable_calendar_in_config()

    if success:
        logger.info("\n次のステップ:")
        logger.info("1. credentials.json をプロジェクトルートに配置")
        logger.info("2. 必要なパッケージをインストール:")
        logger.info("   pip3 install google-auth google-auth-oauthlib google-api-python-client")
        logger.info("3. 初回認証:")
        logger.info("   python3 modules/calendar_integration.py")
        logger.info("4. 動作確認:")
        logger.info("   python3 check_calendar_status.py")
    else:
        logger.info("\nエラーが発生しました")
        sys.exit(1)

if __name__ == "__main__":
    main()
