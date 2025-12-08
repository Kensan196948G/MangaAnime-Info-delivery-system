#!/usr/bin/env python3
"""
Googleカレンダー同期スクリプト
Phase 17: カレンダー統合実装

機能:
- 全未同期リリースをGoogleカレンダーに登録
- バッチ処理によるレート制限対策
- 進捗表示
- エラーハンドリング

使用例:
    # 全件同期
    python3 scripts/sync_calendar.py

    # 件数制限
    python3 scripts/sync_calendar.py --limit 100

    # ドライラン
    python3 scripts/sync_calendar.py --dry-run
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import argparse
from modules.calendar_sync_manager import CalendarSyncManager
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Googleカレンダー同期')
    parser.add_argument('--limit', type=int, help='同期件数制限')
    parser.add_argument('--batch-size', type=int, default=20, help='バッチサイズ')
    parser.add_argument('--dry-run', action='store_true', help='ドライラン（同期せず確認のみ）')
    parser.add_argument('--calendar-id', default='primary', help='カレンダーID')
    args = parser.parse_args()

    print("="*70)
    print("🗓️  Googleカレンダー同期スクリプト")
    print("="*70)

    if args.dry_run:
        print("⚠️  ドライランモード（実際には同期しません）")

    # マネージャー初期化
    manager = CalendarSyncManager(calendar_id=args.calendar_id)

    # 現在の統計
    stats = manager.get_sync_stats()
    print(f"\n【現在の同期状況】")
    print(f"  総リリース数: {stats['total']}")
    print(f"  同期済み: {stats['synced']}件（{stats['sync_rate']}%）")
    print(f"  未同期: {stats['unsynced']}件")

    if stats['unsynced'] == 0:
        print("\n✅ 全てのリリースが既に同期されています")
        return

    # 同期件数確認
    to_sync = args.limit if args.limit else stats['unsynced']
    print(f"\n📧 同期予定: {to_sync}件")

    # バッチ数計算
    batch_count = (to_sync + args.batch_size - 1) // args.batch_size
    print(f"📦 バッチ数: {batch_count}バッチ（{args.batch_size}件/バッチ）")

    # 推定時間
    estimated_minutes = (to_sync * 1.5 + batch_count * 5) / 60
    print(f"⏱️  推定時間: 約{estimated_minutes:.1f}分")

    if not args.dry_run:
        # 確認プロンプト
        if sys.stdin.isatty():
            response = input(f"\n▶️  {to_sync}件の同期を開始しますか？ (y/N): ")
            if response.lower() != 'y':
                print("キャンセルしました")
                return
        else:
            print("\n▶️  自動実行モード: 同期を開始します...")

        # 同期実行
        print("\n" + "="*70)
        result = manager.sync_unsynced_releases(
            limit=args.limit,
            batch_size=args.batch_size
        )
        print("="*70)

        # 結果表示
        print(f"\n【同期結果】")
        print(f"  ✅ 成功: {result['success']}件")
        print(f"  ❌ 失敗: {result['failed']}件")
        print(f"  ⏭️  スキップ: {result['skipped']}件")
        print(f"  📊 合計: {result['total']}件")

        # 最新統計
        final_stats = manager.get_sync_stats()
        print(f"\n【最新の同期状況】")
        print(f"  同期済み: {final_stats['synced']}件（{final_stats['sync_rate']}%）")
        print(f"  未同期: {final_stats['unsynced']}件")

    else:
        # ドライラン: 対象リリース表示のみ
        print("\n【ドライラン: 同期対象リリース】")
        releases = manager.get_unsynced_releases(limit=min(to_sync, 10))

        for i, release in enumerate(releases, 1):
            title = release['title_kana'] or release['title']
            print(f"  {i}. {title} - {release['release_date']}")

        if to_sync > 10:
            print(f"  ... 他{to_sync - 10}件")

    print("\n" + "="*70)
    print("✅ 完了")
    print("="*70)


if __name__ == "__main__":
    main()
