#!/usr/bin/env python3
"""
Annict API接続テストスクリプト

このスクリプトは以下をテストします：
1. Personal Access Tokenの有効性
2. 現在シーズンの作品情報取得
3. 放送予定情報取得
4. APIレスポンスデータの確認
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.anime_annict import AnnictAPIClient, collect_annict_data, AnnictAPIError


def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent.parent / 'config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


async def test_annict_connection():
    """Test Annict API connection and data retrieval"""
    logger.info("=" * 80)
    logger.info("🔍 Annict API 接続テスト")
    logger.info("=" * 80)

    # Load config
    try:
        config_data = load_config()
        annict_config = config_data.get('apis', {}).get('annict', {})
    except Exception as e:
        logger.info(f"❌ config.json読み込みエラー: {str(e)}")
        return False

    # Check if enabled
    if not annict_config.get('enabled', False):
        logger.info("\n⚠️  Annict APIが無効になっています")
        logger.info("   config.jsonで 'enabled: true' に設定してください")
        return False

    # Check access token
    access_token = annict_config.get('access_token', '')
    if not access_token:
        logger.info("\n⚠️  Personal Access Tokenが設定されていません")
        logger.info("\n📝 設定手順:")
        logger.info("   1. https://annict.com/settings/apps にアクセス")
        logger.info("   2. Personal Access Tokenを作成")
        logger.info("   3. config.jsonの 'access_token' に貼り付け")
        logger.info("\n詳細: docs/ANNICT_SETUP.md を参照")
        return False

    logger.info(f"\n✅ 設定確認:")
    logger.info(f"   Base URL: {annict_config.get('base_url')}")
    logger.info(f"   Token: {'*' * 10}{access_token[-4:] if len(access_token) > 4 else '****'}")
    logger.info(f"   Rate Limit: {annict_config.get('rate_limit', {}).get('requests_per_minute', 60)} req/min")

    # Test API connection
    logger.info("\n" + "=" * 80)
    logger.info("📡 API接続テスト")
    logger.info("=" * 80)

    try:
        async with AnnictAPIClient(annict_config) as client:
            # Test 1: Get current season works
            logger.info("\n🎬 テスト1: 現在シーズンの作品取得")
            logger.info("-" * 80)

            current_season = client._get_current_season()
            logger.info(f"   対象シーズン: {current_season}")

            works = await client.get_current_season_works(per_page=10)
            logger.info(f"   ✅ 取得成功: {len(works)}件の作品")

            if works:
                logger.info(f"\n   📺 サンプル作品:")
                sample = works[0]
                logger.info(f"      - ID: {sample.get('id')}")
                logger.info(f"      - タイトル: {sample.get('title')}")
                logger.info(f"      - かな: {sample.get('title_kana', 'N/A')}")
                logger.info(f"      - メディア: {sample.get('media_text', 'N/A')}")
                logger.info(f"      - エピソード数: {sample.get('episodes_count', 'N/A')}")
                logger.info(f"      - 視聴者数: {sample.get('watchers_count', 0):,}")
                logger.info(f"      - 公式サイト: {sample.get('official_site_url', 'N/A')}")

            # Test 2: Get programs
            logger.info("\n📅 テスト2: 放送予定取得")
            logger.info("-" * 80)

            start_date = datetime.now()
            programs = await client.get_programs(start_date=start_date, per_page=10)
            logger.info(f"   ✅ 取得成功: {len(programs)}件の放送予定")

            if programs:
                logger.info(f"\n   📡 サンプル放送予定:")
                sample = programs[0]
                logger.info(f"      - 放送日時: {sample.get('started_at', 'N/A')}")
                logger.info(f"      - 作品: {sample.get('work', {}).get('title', 'N/A')}")
                logger.info(f"      - チャンネル: {sample.get('channel', {}).get('name', 'N/A')}")
                logger.info(f"      - エピソード: {sample.get('episode', {}).get('number_text', 'N/A')}")
                logger.info(f"      - 再放送: {'はい' if sample.get('is_rebroadcast') else 'いいえ'}")

            # Test 3: Data normalization
            logger.info("\n🔄 テスト3: データ正規化")
            logger.info("-" * 80)

            if works:
                normalized = client.normalize_work_data(works[0])
                logger.info(f"   ✅ 正規化成功")
                logger.info(f"      - Source: {normalized.get('source')}")
                logger.info(f"      - Type: {normalized.get('type')}")
                logger.info(f"      - Title: {normalized.get('title')}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ すべてのテストが成功しました！")
        logger.info("=" * 80)
        logger.info("\n💡 次のステップ:")
        logger.info("   - collection_api.py でAnnict統合を実装")
        logger.info("   - スケジュール収集にAnnictデータを含める")
        logger.info("   - Web UIで収集状況を確認")

        return True

    except AnnictAPIError as e:
        logger.info(f"\n❌ Annict APIエラー: {str(e)}")
        logger.info("\n💡 トラブルシューティング:")
        logger.info("   - Personal Access Tokenが正しいか確認")
        logger.info("   - https://annict.com/settings/apps でトークンを再確認")
        logger.info("   - トークンの有効期限が切れていないか確認")
        return False

    except Exception as e:
        logger.info(f"\n❌ 予期しないエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_collection():
    """Test full data collection using collect_annict_data function"""
    logger.info("\n" + "=" * 80)
    logger.info("📦 完全データ収集テスト")
    logger.info("=" * 80)

    config_data = load_config()
    annict_config = config_data.get('apis', {}).get('annict', {})

    result = await collect_annict_data(annict_config)

    logger.info(f"\n📊 収集結果:")
    logger.info(f"   Works: {len(result.get('works', []))} 件")
    logger.info(f"   Programs: {len(result.get('programs', []))} 件")
    logger.info(f"   Episodes: {len(result.get('episodes', []))} 件")

    if result.get('works'):
        logger.info(f"\n📺 収集された作品（最初の3件）:")
        for i, work in enumerate(result['works'][:3], 1):
            logger.info(f"   {i}. {work.get('title')} ({work.get('season', 'N/A')})")


def main():
    """Main test function"""
import logging

logger = logging.getLogger(__name__)

    logger.info("\n")

logger = logging.getLogger(__name__)

    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 20 + "Annict API 統合テストスイート" + " " * 27 + "║")
    logger.info("╚" + "=" * 78 + "╝")

    # Run basic connection test
    success = asyncio.run(test_annict_connection())

    if success:
        # Run full collection test
        asyncio.run(test_full_collection())

        logger.info("\n" + "=" * 80)
        logger.info("✨ テスト完了！Annict APIは正常に動作しています")
        logger.info("=" * 80)
        sys.exit(0)
    else:
        logger.info("\n" + "=" * 80)
        logger.info("⚠️  テスト失敗。上記のエラーメッセージを確認してください")
        logger.info("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
