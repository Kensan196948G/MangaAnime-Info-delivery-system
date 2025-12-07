#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データ収集統合実行スクリプト
作成日: 2025-12-06
目的: アニメ・マンガ情報を各種APIから一括収集
"""

import os
import sys
import json
import logging
from datetime import datetime

# プロジェクトルートをパスに追加
PROJECT_ROOT = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "app"))

# ログ設定
log_dir = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f"data_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_config():
    """設定ファイル確認"""
    config_path = os.path.join(PROJECT_ROOT, "config.json")
    if not os.path.exists(config_path):
        logger.error(f"設定ファイルが見つかりません: {config_path}")
        return None

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    logger.info("✓ 設定ファイル読み込み完了")
    return config

def collect_anime_anilist():
    """AniList APIからアニメ情報収集"""
    logger.info("=" * 60)
    logger.info("AniList APIからアニメ情報収集開始")
    logger.info("=" * 60)

    try:
        # パッケージとしてインポート（相対インポート対応）
        from modules import anime_anilist

        # 収集実行
        logger.info("AniList APIからデータ取得中...")

        # fetch_and_store関数がある場合はそれを使用、なければCollectorクラスを使用
        if hasattr(anime_anilist, 'fetch_and_store'):
            result = anime_anilist.fetch_and_store()
        elif hasattr(anime_anilist, 'AniListCollector'):
            collector = anime_anilist.AniListCollector()
            result = collector.collect()
        else:
            logger.warning("AniListモジュールに適切な収集関数が見つかりません")
            return False

        logger.info(f"✓ AniList収集完了: {result if result else '詳細は個別ログ参照'}")
        return True

    except ImportError as e:
        logger.error(f"モジュールインポートエラー: {e}")
        logger.info("anime_anilist.pyまたは依存モジュールの問題です。")
        return False
    except Exception as e:
        logger.error(f"AniList収集エラー: {e}", exc_info=True)
        return False

def collect_anime_syoboi():
    """しょぼいカレンダーAPIからアニメ情報収集"""
    logger.info("=" * 60)
    logger.info("しょぼいカレンダーAPIからアニメ情報収集開始")
    logger.info("=" * 60)

    try:
        # パッケージとしてインポート
        from modules import anime_syoboi

        logger.info("しょぼいカレンダーAPIからデータ取得中...")

        if hasattr(anime_syoboi, 'fetch_and_store'):
            result = anime_syoboi.fetch_and_store()
        elif hasattr(anime_syoboi, 'SyoboiCollector'):
            collector = anime_syoboi.SyoboiCollector()
            result = collector.collect()
        else:
            logger.warning("しょぼいカレンダーモジュールに適切な収集関数が見つかりません")
            return False

        logger.info(f"✓ しょぼいカレンダー収集完了: {result if result else '詳細は個別ログ参照'}")
        return True

    except ImportError as e:
        logger.error(f"モジュールインポートエラー: {e}")
        logger.info("anime_syoboi.pyまたは依存モジュールの問題です。")
        return False
    except Exception as e:
        logger.error(f"しょぼいカレンダー収集エラー: {e}", exc_info=True)
        return False

def collect_manga_rss():
    """RSSフィードからマンガ情報収集"""
    logger.info("=" * 60)
    logger.info("RSSフィードからマンガ情報収集開始")
    logger.info("=" * 60)

    try:
        # パッケージとしてインポート
        from modules import manga_rss

        logger.info("RSSフィードからデータ取得中...")

        if hasattr(manga_rss, 'fetch_and_store'):
            result = manga_rss.fetch_and_store()
        elif hasattr(manga_rss, 'RSSCollector'):
            collector = manga_rss.RSSCollector()
            result = collector.collect()
        else:
            logger.warning("マンガRSSモジュールに適切な収集関数が見つかりません")
            return False

        logger.info(f"✓ マンガRSS収集完了: {result if result else '詳細は個別ログ参照'}")
        return True

    except ImportError as e:
        logger.error(f"モジュールインポートエラー: {e}")
        logger.info("manga_rss.pyまたは依存モジュールの問題です。")
        return False
    except Exception as e:
        logger.error(f"マンガRSS収集エラー: {e}", exc_info=True)
        return False

def collect_streaming_info():
    """配信プラットフォーム情報収集"""
    logger.info("=" * 60)
    logger.info("配信プラットフォーム情報収集開始")
    logger.info("=" * 60)

    try:
        modules_path = os.path.join(PROJECT_ROOT, "modules")
        streaming_module = os.path.join(modules_path, "streaming_collector.py")

        if not os.path.exists(streaming_module):
            logger.info("配信情報モジュールが見つかりません。スキップします。")
            return False

        sys.path.insert(0, modules_path)
        import streaming_collector

        logger.info("配信プラットフォーム情報取得中...")
        result = streaming_collector.fetch_and_store()

        logger.info(f"✓ 配信情報収集完了: {result if result else '詳細は個別ログ参照'}")
        return True

    except ImportError as e:
        logger.info(f"配信情報モジュールインポートエラー（スキップ）: {e}")
        return False
    except Exception as e:
        logger.error(f"配信情報収集エラー: {e}", exc_info=True)
        return False

def main():
    """メイン処理"""
    logger.info("=" * 60)
    logger.info("データ収集統合実行開始")
    logger.info("=" * 60)
    logger.info(f"プロジェクトルート: {PROJECT_ROOT}")
    logger.info(f"開始日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # 設定ファイル確認
    config = check_config()
    if not config:
        logger.error("設定ファイルの読み込みに失敗しました。処理を中断します。")
        sys.exit(1)

    results = {
        "anilist": False,
        "syoboi": False,
        "manga_rss": False,
        "streaming": False
    }

    # 各ソースから収集
    results["anilist"] = collect_anime_anilist()
    results["syoboi"] = collect_anime_syoboi()
    results["manga_rss"] = collect_manga_rss()
    results["streaming"] = collect_streaming_info()

    # 結果サマリー
    logger.info("")
    logger.info("=" * 60)
    logger.info("データ収集結果サマリー")
    logger.info("=" * 60)

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for source, success in results.items():
        status = "✓ 成功" if success else "✗ 失敗/スキップ"
        logger.info(f"  {source:20s}: {status}")

    logger.info("")
    logger.info(f"成功: {success_count}/{total_count}")
    logger.info(f"終了日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 検証スクリプト実行を推奨
    logger.info("")
    logger.info("次のステップ:")
    logger.info("  python3 scripts/verify_data_collection.py")
    logger.info("")

    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    sys.exit(main())
