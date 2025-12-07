#!/usr/bin/env python3
"""
Config.json バリデーションスクリプト

整合性チェックと修正を実施します。
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
BACKUP_PATH = PROJECT_ROOT / "config.json.bak"


def load_config() -> Dict[str, Any]:
    """現在のconfig.jsonを読み込み"""
    if not CONFIG_PATH.exists():
        print(f"エラー: {CONFIG_PATH} が見つかりません")
        sys.exit(1)

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_inconsistencies(config: Dict[str, Any]) -> List[Tuple[str, str, Any, Any]]:
    """設定の矛盾をチェック"""
    issues = []

    # メール通知の矛盾チェック
    if 'email_notifications_enabled' in config and 'notifications' in config:
        top_level = config.get('email_notifications_enabled')
        nested = config.get('notifications', {}).get('email', {}).get('enabled')

        if top_level != nested:
            issues.append((
                'email_notifications',
                'トップレベルとnotifications.emailで異なる値',
                top_level,
                nested
            ))

    # カレンダーの矛盾チェック
    if 'calendar_enabled' in config:
        top_level = config.get('calendar_enabled')
        nested = config.get('notifications', {}).get('calendar', {}).get('enabled')
        settings_level = config.get('settings', {}).get('calendar_enabled')

        if top_level != nested or top_level != settings_level:
            issues.append((
                'calendar_enabled',
                '複数箇所で異なる値',
                f"top:{top_level}, nested:{nested}, settings:{settings_level}",
                None
            ))

    # 重複設定のチェック
    email_locations = []
    if 'notification_email' in config:
        email_locations.append('トップレベル')
    if 'settings' in config and 'notification_email' in config['settings']:
        email_locations.append('settings')
    if 'notifications' in config and 'email' in config['notifications']:
        email_locations.append('notifications.email')

    if len(email_locations) > 1:
        issues.append((
            'notification_email',
            f'{len(email_locations)}箇所に重複',
            ', '.join(email_locations),
            None
        ))

    return issues


def create_fixed_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """整合性のある新しい設定を生成"""

    # メールアドレスを取得（優先順位: notifications > settings > トップレベル）
    email_to = (
        old_config.get('notifications', {}).get('email', {}).get('to') or
        old_config.get('settings', {}).get('notification_email') or
        old_config.get('notification_email', 'your-email@gmail.com')
    )

    # カレンダーIDを取得
    calendar_id = (
        old_config.get('notifications', {}).get('calendar', {}).get('calendar_id') or
        old_config.get('settings', {}).get('calendar_id') or
        old_config.get('calendar_id', 'primary')
    )

    # 送信時刻を取得
    send_time = (
        old_config.get('settings', {}).get('notification_time') or
        old_config.get('notification_time', '08:00')
    )

    # NGキーワードを取得
    ng_keywords = old_config.get('ng_keywords', [])

    # ソースを取得
    anime_sources = old_config.get('anime_sources', [])
    manga_sources = old_config.get('manga_sources', [])
    streaming_sources = old_config.get('streaming_sources', [])

    # 新しい設定を構築
    new_config = {
        "notifications": {
            "email": {
                "enabled": True,
                "to": email_to,
                "subject_prefix": "[アニメ・マンガ情報]",
                "send_time": send_time
            },
            "calendar": {
                "enabled": True,
                "calendar_id": calendar_id,
                "event_title_format": "{title} {type} {number}",
                "color_by_genre": True,
                "reminder_minutes": [1440, 60]
            }
        },
        "filters": {
            "ng_keywords": ng_keywords,
            "min_rating": None,
            "excluded_genres": []
        },
        "sources": {
            "anime": anime_sources,
            "manga": manga_sources,
            "streaming": streaming_sources
        },
        "database": {
            "path": "db.sqlite3",
            "backup_enabled": True,
            "backup_interval_days": 7
        },
        "logging": {
            "level": "INFO",
            "file": "logs/system.log",
            "max_bytes": 10485760,
            "backup_count": 5
        },
        "scheduling": {
            "cron_expression": "0 8 * * *",
            "timezone": "Asia/Tokyo"
        }
    }

    return new_config


def main():
    """メイン処理"""
    print("=" * 60)
    print("Config.json 整合性チェック")
    print("=" * 60)

    # 設定を読み込み
    print(f"\n[1] 設定ファイル読み込み: {CONFIG_PATH}")
    config = load_config()
    print("✓ 読み込み成功")

    # 矛盾をチェック
    print("\n[2] 矛盾のチェック")
    issues = check_inconsistencies(config)

    if not issues:
        print("✓ 矛盾は検出されませんでした")
        return 0

    print(f"⚠ {len(issues)}件の問題を検出:")
    for key, desc, val1, val2 in issues:
        print(f"  - {key}: {desc}")
        print(f"    値1: {val1}")
        if val2 is not None:
            print(f"    値2: {val2}")

    # バックアップ作成
    print(f"\n[3] バックアップ作成: {BACKUP_PATH}")
    with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print("✓ バックアップ作成完了")

    # 修正版を生成
    print("\n[4] 整合性のある設定を生成")
    new_config = create_fixed_config(config)
    print("✓ 新しい設定を生成")

    # 保存
    print(f"\n[5] 修正版を保存: {CONFIG_PATH}")
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(new_config, f, ensure_ascii=False, indent=2)
    print("✓ 保存完了")

    # サマリー表示
    print("\n" + "=" * 60)
    print("修正完了")
    print("=" * 60)
    print("\n主な変更点:")
    print("  • メール通知: 一貫して有効化")
    print("  • カレンダー: 一貫して有効化")
    print("  • 重複設定を統合")
    print("  • 論理的な階層構造に再編成")
    print("\n詳細なレポート:")
    print(f"  {PROJECT_ROOT}/docs/CONFIG_MIGRATION_REPORT.md")
    print("\nバックアップファイル:")
    print(f"  {BACKUP_PATH}")
    print("\n" + "=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
