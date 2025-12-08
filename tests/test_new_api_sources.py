#!/usr/bin/env python3
"""
新規追加API・RSSソースの動作確認テストスクリプト

このスクリプトは以下をテストします:
1. Kitsu API（アニメ・マンガ）
2. MangaDex API
3. MangaUpdates API
"""

import asyncio
import logging
import json
import sys
from datetime import datetime

# Add modules to path
sys.path.insert(0, "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")

from modules.anime_kitsu import collect_kitsu_anime, collect_kitsu_manga
from modules.manga_mangadex import collect_mangadex_manga, collect_mangadex_chapters
from modules.manga_mangaupdates import (
    collect_mangaupdates_releases,
    search_mangaupdates_series,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("test_new_api_sources.log"),
    ],
)


class APITestRunner:
    """API動作確認テストランナー"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {"total": 0, "passed": 0, "failed": 0},
        }

    async def test_kitsu_anime(self):
        """Kitsu API アニメデータ取得テスト"""
        test_name = "Kitsu API - Anime Collection"
        logger.info(f"Starting: {test_name}")

        config = {
            "base_url": "https://kitsu.io/api/edge",
            "timeout_seconds": 30,
            "rate_limit": {"requests_per_minute": 90, "retry_delay_seconds": 3},
        }

        try:
            anime_data = await collect_kitsu_anime(config)

            self.results["tests"][test_name] = {
                "status": "PASSED" if len(anime_data) > 0 else "FAILED",
                "items_collected": len(anime_data),
                "sample_data": anime_data[0] if anime_data else None,
                "error": None,
            }

            logger.info(f"✅ {test_name} - Collected {len(anime_data)} items")
            return True

        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "FAILED",
                "items_collected": 0,
                "sample_data": None,
                "error": str(e),
            }
            logger.error(f"❌ {test_name} - Error: {str(e)}")
            return False

    async def test_kitsu_manga(self):
        """Kitsu API マンガデータ取得テスト"""
        test_name = "Kitsu API - Manga Collection"
        logger.info(f"Starting: {test_name}")

        config = {
            "base_url": "https://kitsu.io/api/edge",
            "timeout_seconds": 30,
            "rate_limit": {"requests_per_minute": 90, "retry_delay_seconds": 3},
        }

        try:
            manga_data = await collect_kitsu_manga(config)

            self.results["tests"][test_name] = {
                "status": "PASSED" if len(manga_data) > 0 else "FAILED",
                "items_collected": len(manga_data),
                "sample_data": manga_data[0] if manga_data else None,
                "error": None,
            }

            logger.info(f"✅ {test_name} - Collected {len(manga_data)} items")
            return True

        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "FAILED",
                "items_collected": 0,
                "sample_data": None,
                "error": str(e),
            }
            logger.error(f"❌ {test_name} - Error: {str(e)}")
            return False

    async def test_mangadex_manga(self):
        """MangaDex API マンガデータ取得テスト"""
        test_name = "MangaDex API - Manga Collection"
        logger.info(f"Starting: {test_name}")

        config = {
            "base_url": "https://api.mangadex.org",
            "timeout_seconds": 30,
            "rate_limit": {"requests_per_minute": 40, "retry_delay_seconds": 5},
        }

        try:
            manga_data = await collect_mangadex_manga(config)

            self.results["tests"][test_name] = {
                "status": "PASSED" if len(manga_data) > 0 else "FAILED",
                "items_collected": len(manga_data),
                "sample_data": manga_data[0] if manga_data else None,
                "error": None,
            }

            logger.info(f"✅ {test_name} - Collected {len(manga_data)} items")
            return True

        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "FAILED",
                "items_collected": 0,
                "sample_data": None,
                "error": str(e),
            }
            logger.error(f"❌ {test_name} - Error: {str(e)}")
            return False

    async def test_mangadex_chapters(self):
        """MangaDex API チャプター更新取得テスト"""
        test_name = "MangaDex API - Chapter Updates"
        logger.info(f"Starting: {test_name}")

        config = {
            "base_url": "https://api.mangadex.org",
            "timeout_seconds": 30,
            "rate_limit": {"requests_per_minute": 40, "retry_delay_seconds": 5},
        }

        try:
            chapter_data = await collect_mangadex_chapters(config, hours=24)

            self.results["tests"][test_name] = {
                "status": "PASSED" if len(chapter_data) > 0 else "FAILED",
                "items_collected": len(chapter_data),
                "sample_data": chapter_data[0] if chapter_data else None,
                "error": None,
            }

            logger.info(f"✅ {test_name} - Collected {len(chapter_data)} items")
            return True

        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "FAILED",
                "items_collected": 0,
                "sample_data": None,
                "error": str(e),
            }
            logger.error(f"❌ {test_name} - Error: {str(e)}")
            return False

    async def test_mangaupdates_releases(self):
        """MangaUpdates API リリース情報取得テスト"""
        test_name = "MangaUpdates API - Latest Releases"
        logger.info(f"Starting: {test_name}")

        config = {
            "base_url": "https://api.mangaupdates.com/v1",
            "timeout_seconds": 30,
            "rate_limit": {"requests_per_minute": 30, "retry_delay_seconds": 5},
        }

        try:
            releases = await collect_mangaupdates_releases(config, pages=1)

            self.results["tests"][test_name] = {
                "status": "PASSED" if len(releases) > 0 else "FAILED",
                "items_collected": len(releases),
                "sample_data": releases[0] if releases else None,
                "error": None,
            }

            logger.info(f"✅ {test_name} - Collected {len(releases)} items")
            return True

        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "FAILED",
                "items_collected": 0,
                "sample_data": None,
                "error": str(e),
            }
            logger.error(f"❌ {test_name} - Error: {str(e)}")
            return False

    async def test_mangaupdates_search(self):
        """MangaUpdates API 検索テスト"""
        test_name = "MangaUpdates API - Series Search"
        logger.info(f"Starting: {test_name}")

        config = {
            "base_url": "https://api.mangaupdates.com/v1",
            "timeout_seconds": 30,
            "rate_limit": {"requests_per_minute": 30, "retry_delay_seconds": 5},
        }

        try:
            results = await search_mangaupdates_series(config, "One Piece")

            self.results["tests"][test_name] = {
                "status": "PASSED" if len(results) > 0 else "FAILED",
                "items_collected": len(results),
                "sample_data": results[0] if results else None,
                "error": None,
            }

            logger.info(f"✅ {test_name} - Found {len(results)} results")
            return True

        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "FAILED",
                "items_collected": 0,
                "sample_data": None,
                "error": str(e),
            }
            logger.error(f"❌ {test_name} - Error: {str(e)}")
            return False

    async def run_all_tests(self):
        """全テストを実行"""
        logger.info("=" * 80)
        logger.info("Starting API Sources Test Suite")
        logger.info("=" * 80)

        tests = [
            self.test_kitsu_anime(),
            self.test_kitsu_manga(),
            self.test_mangadex_manga(),
            self.test_mangadex_chapters(),
            self.test_mangaupdates_releases(),
            self.test_mangaupdates_search(),
        ]

        # 順次実行（レート制限を考慮）
        test_results = []
        for i, test in enumerate(tests):
            result = await test
            test_results.append(result)

            # テスト間に待機時間を設ける
            if i < len(tests) - 1:
                logger.info("Waiting 3 seconds before next test...")
                await asyncio.sleep(3)

        # 統計計算
        self.results["summary"]["total"] = len(test_results)
        self.results["summary"]["passed"] = sum(1 for r in test_results if r)
        self.results["summary"]["failed"] = sum(1 for r in test_results if not r)
        self.results["summary"]["success_rate"] = (
            f"{(self.results['summary']['passed'] / self.results['summary']['total'] * 100):.1f}%"
        )

        # 結果を保存
        self.save_results()

        # サマリー表示
        self.print_summary()

    def save_results(self):
        """テスト結果をJSONファイルに保存"""
        filename = f"test_new_api_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        logger.info(f"Test results saved to: {filename}")

    def print_summary(self):
        """テストサマリーを表示"""
        logger.info("=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {self.results['summary']['total']}")
        logger.info(f"Passed: {self.results['summary']['passed']}")
        logger.info(f"Failed: {self.results['summary']['failed']}")
        logger.info(f"Success Rate: {self.results['summary']['success_rate']}")
        logger.info("=" * 80)

        for test_name, result in self.results["tests"].items():
            status_emoji = "✅" if result["status"] == "PASSED" else "❌"
            logger.info(
                f"{status_emoji} {test_name}: {result['status']} ({result['items_collected']} items)"
            )

        logger.info("=" * 80)


async def main():
    """メイン実行関数"""
    runner = APITestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
