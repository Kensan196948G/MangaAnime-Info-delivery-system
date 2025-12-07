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
    print("=" * 80)
    print("🔍 Annict API 接続テスト")
    print("=" * 80)

    # Load config
    try:
        config_data = load_config()
        annict_config = config_data.get('apis', {}).get('annict', {})
    except Exception as e:
        print(f"❌ config.json読み込みエラー: {str(e)}")
        return False

    # Check if enabled
    if not annict_config.get('enabled', False):
        print("\n⚠️  Annict APIが無効になっています")
        print("   config.jsonで 'enabled: true' に設定してください")
        return False

    # Check access token
    access_token = annict_config.get('access_token', '')
    if not access_token:
        print("\n⚠️  Personal Access Tokenが設定されていません")
        print("\n📝 設定手順:")
        print("   1. https://annict.com/settings/apps にアクセス")
        print("   2. Personal Access Tokenを作成")
        print("   3. config.jsonの 'access_token' に貼り付け")
        print("\n詳細: docs/ANNICT_SETUP.md を参照")
        return False

    print(f"\n✅ 設定確認:")
    print(f"   Base URL: {annict_config.get('base_url')}")
    print(f"   Token: {'*' * 10}{access_token[-4:] if len(access_token) > 4 else '****'}")
    print(f"   Rate Limit: {annict_config.get('rate_limit', {}).get('requests_per_minute', 60)} req/min")

    # Test API connection
    print("\n" + "=" * 80)
    print("📡 API接続テスト")
    print("=" * 80)

    try:
        async with AnnictAPIClient(annict_config) as client:
            # Test 1: Get current season works
            print("\n🎬 テスト1: 現在シーズンの作品取得")
            print("-" * 80)

            current_season = client._get_current_season()
            print(f"   対象シーズン: {current_season}")

            works = await client.get_current_season_works(per_page=10)
            print(f"   ✅ 取得成功: {len(works)}件の作品")

            if works:
                print(f"\n   📺 サンプル作品:")
                sample = works[0]
                print(f"      - ID: {sample.get('id')}")
                print(f"      - タイトル: {sample.get('title')}")
                print(f"      - かな: {sample.get('title_kana', 'N/A')}")
                print(f"      - メディア: {sample.get('media_text', 'N/A')}")
                print(f"      - エピソード数: {sample.get('episodes_count', 'N/A')}")
                print(f"      - 視聴者数: {sample.get('watchers_count', 0):,}")
                print(f"      - 公式サイト: {sample.get('official_site_url', 'N/A')}")

            # Test 2: Get programs
            print("\n📅 テスト2: 放送予定取得")
            print("-" * 80)

            start_date = datetime.now()
            programs = await client.get_programs(start_date=start_date, per_page=10)
            print(f"   ✅ 取得成功: {len(programs)}件の放送予定")

            if programs:
                print(f"\n   📡 サンプル放送予定:")
                sample = programs[0]
                print(f"      - 放送日時: {sample.get('started_at', 'N/A')}")
                print(f"      - 作品: {sample.get('work', {}).get('title', 'N/A')}")
                print(f"      - チャンネル: {sample.get('channel', {}).get('name', 'N/A')}")
                print(f"      - エピソード: {sample.get('episode', {}).get('number_text', 'N/A')}")
                print(f"      - 再放送: {'はい' if sample.get('is_rebroadcast') else 'いいえ'}")

            # Test 3: Data normalization
            print("\n🔄 テスト3: データ正規化")
            print("-" * 80)

            if works:
                normalized = client.normalize_work_data(works[0])
                print(f"   ✅ 正規化成功")
                print(f"      - Source: {normalized.get('source')}")
                print(f"      - Type: {normalized.get('type')}")
                print(f"      - Title: {normalized.get('title')}")

        print("\n" + "=" * 80)
        print("✅ すべてのテストが成功しました！")
        print("=" * 80)
        print("\n💡 次のステップ:")
        print("   - collection_api.py でAnnict統合を実装")
        print("   - スケジュール収集にAnnictデータを含める")
        print("   - Web UIで収集状況を確認")

        return True

    except AnnictAPIError as e:
        print(f"\n❌ Annict APIエラー: {str(e)}")
        print("\n💡 トラブルシューティング:")
        print("   - Personal Access Tokenが正しいか確認")
        print("   - https://annict.com/settings/apps でトークンを再確認")
        print("   - トークンの有効期限が切れていないか確認")
        return False

    except Exception as e:
        print(f"\n❌ 予期しないエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_collection():
    """Test full data collection using collect_annict_data function"""
    print("\n" + "=" * 80)
    print("📦 完全データ収集テスト")
    print("=" * 80)

    config_data = load_config()
    annict_config = config_data.get('apis', {}).get('annict', {})

    result = await collect_annict_data(annict_config)

    print(f"\n📊 収集結果:")
    print(f"   Works: {len(result.get('works', []))} 件")
    print(f"   Programs: {len(result.get('programs', []))} 件")
    print(f"   Episodes: {len(result.get('episodes', []))} 件")

    if result.get('works'):
        print(f"\n📺 収集された作品（最初の3件）:")
        for i, work in enumerate(result['works'][:3], 1):
            print(f"   {i}. {work.get('title')} ({work.get('season', 'N/A')})")


def main():
    """Main test function"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Annict API 統合テストスイート" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")

    # Run basic connection test
    success = asyncio.run(test_annict_connection())

    if success:
        # Run full collection test
        asyncio.run(test_full_collection())

        print("\n" + "=" * 80)
        print("✨ テスト完了！Annict APIは正常に動作しています")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("⚠️  テスト失敗。上記のエラーメッセージを確認してください")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
