#!/usr/bin/env python3
"""
Google Calendar連携のdry-runテスト
実際にはイベントを作成せず、処理フローを確認
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """設定ファイルを読み込み"""
    config_path = Path("/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config.json")

    if not config_path.exists():
        logger.error(f"config.jsonが見つかりません: {config_path}")
        return None

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_mock_releases():
    """テスト用のモックリリースデータを作成"""
    today = datetime.now()

    releases = [
        {
            'title': '葬送のフリーレン',
            'type': 'anime',
            'release_type': 'episode',
            'number': '10',
            'platform': 'dアニメストア',
            'release_date': (today + timedelta(days=1)).strftime('%Y-%m-%d'),
            'source_url': 'https://example.com/frieren'
        },
        {
            'title': 'SPY×FAMILY',
            'type': 'anime',
            'release_type': 'episode',
            'number': '5',
            'platform': 'Netflix',
            'release_date': (today + timedelta(days=2)).strftime('%Y-%m-%d'),
            'source_url': 'https://example.com/spyfamily'
        },
        {
            'title': 'チェンソーマン',
            'type': 'manga',
            'release_type': 'volume',
            'number': '15',
            'platform': '',
            'release_date': (today + timedelta(days=7)).strftime('%Y-%m-%d'),
            'source_url': 'https://example.com/chainsaw'
        },
        {
            'title': '呪術廻戦',
            'type': 'manga',
            'release_type': 'volume',
            'number': '25',
            'platform': '',
            'release_date': (today + timedelta(days=14)).strftime('%Y-%m-%d'),
            'source_url': 'https://example.com/jujutsu'
        }
    ]

    return releases

def dry_run_calendar_sync(releases, config):
    """
    カレンダー同期のdry-run
    実際にはAPIを呼ばず、処理フローのみ確認
    """

    print("\n" + "=" * 70)
    print("Google Calendar連携 - Dry-Run テスト")
    print("=" * 70)

    # 設定確認
    calendar_config = config.get('calendar', {})
    enabled = calendar_config.get('enabled', False)

    print(f"\n[設定確認]")
    print(f"  - calendar.enabled: {enabled}")
    print(f"  - calendar_id: {calendar_config.get('calendar_id', 'primary')}")
    print(f"  - event_color_anime: {calendar_config.get('event_color_anime', '9')}")
    print(f"  - event_color_manga: {calendar_config.get('event_color_manga', '10')}")

    if not enabled:
        print("\n⚠️  警告: カレンダー連携が無効です")
        print("有効化するには: python3 enable_calendar.py")
        return

    # リリース情報の処理
    print(f"\n[リリース情報処理]")
    print(f"処理対象: {len(releases)}件")

    color_anime = calendar_config.get('event_color_anime', '9')
    color_manga = calendar_config.get('event_color_manga', '10')

    for i, release in enumerate(releases, 1):
        work_title = release.get('title', '不明な作品')
        release_type = release.get('release_type', '')
        number = release.get('number', '')
        platform = release.get('platform', '')
        release_date = release.get('release_date')
        work_type = release.get('type', 'anime')

        # イベントタイトル生成
        if release_type == 'episode':
            title = f"{work_title} 第{number}話"
            if platform:
                title += f" ({platform})"
        else:
            title = f"{work_title} 第{number}巻"

        # 説明文生成
        description = f"作品: {work_title}\n"
        if platform:
            description += f"配信: {platform}\n"
        if release.get('source_url'):
            description += f"URL: {release['source_url']}\n"

        # カラーID決定
        color_id = color_anime if work_type == 'anime' else color_manga

        # 情報表示
        print(f"\n  [{i}] {title}")
        print(f"      日付: {release_date}")
        print(f"      種別: {work_type}")
        print(f"      カラーID: {color_id}")
        print(f"      説明: {description.strip()}")
        print(f"      → [DRY-RUN] イベント作成をスキップ")

    print("\n" + "=" * 70)
    print(f"Dry-Run完了: {len(releases)}件のイベントを確認")
    print("=" * 70)
    print("\n実際の同期を実行するには:")
    print("  1. credentials.json を配置")
    print("  2. 初回認証を実行")
    print("  3. メインスクリプトで sync_releases_to_calendar() を呼び出し")

def main():
    print("Google Calendar連携 - Dry-Run テスト開始")

    # 設定読み込み
    config = load_config()
    if not config:
        print("エラー: 設定ファイルの読み込みに失敗しました")
        return

    # モックデータ作成
    releases = create_mock_releases()

    # Dry-Run実行
    dry_run_calendar_sync(releases, config)

if __name__ == "__main__":
    main()
