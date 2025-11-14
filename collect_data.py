#!/usr/bin/env python3
"""
データ収集スクリプト - AniList APIとRSSからデータを取得してDBに保存
"""

import sys
import logging
from datetime import datetime, timedelta
import random

# モジュールのインポート
from modules import get_config, get_db
from modules.anime_anilist import AniListCollector
from modules.manga_rss import MangaRSSCollector
from modules.filter_logic import ContentFilter
from modules.data_normalizer import DataNormalizer

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """メイン処理"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 データ収集を開始します")
        logger.info("=" * 60)

        # 設定とDBの初期化
        logger.info("設定ファイルを読み込み中...")
        config = get_config("config.json")

        logger.info("データベースを初期化中...")
        db = get_db()

        # フィルターと正規化の初期化
        content_filter = ContentFilter(config)
        normalizer = DataNormalizer(config)

        # 収集したデータ
        all_data = []

        # AniList APIからデータ収集
        logger.info("\n📡 AniList APIからアニメ情報を収集中...")
        try:
            anilist_collector = AniListCollector(config)
            anilist_data = anilist_collector.collect_upcoming_anime(limit=50)
            logger.info(f"✅ AniList: {len(anilist_data)}件のアニメ情報を取得")
            all_data.extend(anilist_data)
        except Exception as e:
            logger.error(f"❌ AniList収集エラー: {e}")

        # RSSフィードからデータ収集
        logger.info("\n📡 RSSフィードからマンガ情報を収集中...")
        try:
            rss_collector = MangaRSSCollector(config)
            rss_data = rss_collector.collect_all_feeds()
            logger.info(f"✅ RSS: {len(rss_data)}件のマンガ情報を取得")
            all_data.extend(rss_data)
        except Exception as e:
            logger.error(f"❌ RSS収集エラー: {e}")

        if not all_data:
            logger.warning("⚠️ データが取得できませんでした")
            return

        logger.info(f"\n📊 合計 {len(all_data)}件のデータを取得")

        # データのフィルタリング
        logger.info("\n🔍 NGワードフィルタリング中...")
        filtered_data = content_filter.filter_data(all_data)
        logger.info(f"✅ フィルタリング完了: {len(filtered_data)}件が残存")

        # データの正規化
        logger.info("\n⚙️ データ正規化中...")
        normalized_data = normalizer.normalize_batch(filtered_data)
        logger.info(f"✅ 正規化完了: {len(normalized_data)}件")

        # データベースへ保存
        logger.info("\n💾 データベースへ保存中...")
        saved_works = 0
        saved_releases = 0

        for item in normalized_data:
            try:
                # 作品情報を保存
                work_data = {
                    'title': item.get('title', '不明'),
                    'title_kana': item.get('title_kana'),
                    'title_en': item.get('title_en'),
                    'type': item.get('type', 'anime'),
                    'official_url': item.get('official_url')
                }
                work_id = db.insert_work(**work_data)

                if work_id:
                    saved_works += 1

                    # リリース情報を保存
                    releases = item.get('releases', [])
                    for release in releases:
                        release_data = {
                            'work_id': work_id,
                            'release_type': release.get('release_type', 'episode'),
                            'number': release.get('number'),
                            'platform': release.get('platform', '不明'),
                            'release_date': release.get('release_date'),
                            'source': release.get('source', 'unknown'),
                            'source_url': release.get('source_url')
                        }
                        if db.insert_release(**release_data):
                            saved_releases += 1

            except Exception as e:
                logger.error(f"データ保存エラー: {e}")
                continue

        logger.info(f"✅ 保存完了: 作品{saved_works}件、リリース{saved_releases}件")

        # 統計情報を表示
        logger.info("\n📊 データベース統計:")
        stats = db.get_work_stats()
        logger.info(f"  - 総作品数: {stats.get('total_works', 0)}件")
        logger.info(f"  - アニメ: {stats.get('anime_count', 0)}件")
        logger.info(f"  - マンガ: {stats.get('manga_count', 0)}件")
        logger.info(f"  - 総リリース数: {stats.get('total_releases', 0)}件")

        logger.info("\n" + "=" * 60)
        logger.info("✅ データ収集が完了しました")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
