#!/usr/bin/env python3
"""
RSS Feed Testing Script

テスト対象のRSSフィード一覧から動作するものを特定し、結果をレポートします。
"""

import requests
import feedparser
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
from urllib.parse import urlparse
import time

# テスト対象のRSSフィード一覧
ANIME_FEEDS = [
    {
        "name": "Anime News Network",
        "url": "https://animenewsnetwork.com/all/rss",
        "category": "anime"
    },
    {
        "name": "MyAnimeList News",
        "url": "https://myanimelist.net/rss/news.xml",
        "category": "anime"
    },
    {
        "name": "Crunchyroll News",
        "url": "https://feeds.feedburner.com/crunchyroll/animenews",
        "category": "anime"
    },
    {
        "name": "Tokyo Otaku Mode",
        "url": "https://otakumode.com/news/feed",
        "category": "anime"
    },
    {
        "name": "Anime UK News",
        "url": "https://animeuknews.net/feed",
        "category": "anime"
    },
    {
        "name": "Anime Trending",
        "url": "https://anitrendz.net/news/feed",
        "category": "anime"
    },
    {
        "name": "Otaku News",
        "url": "https://otakunews.com/rss/rss.xml",
        "category": "anime"
    }
]

MANGA_FEEDS = [
    {
        "name": "マンバ",
        "url": "https://manba.co.jp/feed",
        "category": "manga"
    },
    {
        "name": "マンバ通信",
        "url": "https://manba.co.jp/manba_magazines/feed",
        "category": "manga"
    },
    {
        "name": "マンバ クチコミ",
        "url": "https://manba.co.jp/topics/feed",
        "category": "manga"
    },
    {
        "name": "マンバ 無料キャンペーン",
        "url": "https://manba.co.jp/free_campaigns/feed",
        "category": "manga"
    },
    {
        "name": "マンバ公式note",
        "url": "https://note.com/manba/rss",
        "category": "manga"
    },
    {
        "name": "LEED Cafe",
        "url": "https://leedcafe.com/feed",
        "category": "manga"
    },
    {
        "name": "少年ジャンプ+",
        "url": "https://shonenjumpplus.com/rss",
        "category": "manga"
    },
    {
        "name": "マガポケ",
        "url": "https://pocket.shonenmagazine.com/feed",
        "category": "manga"
    },
    {
        "name": "comix.fyi",
        "url": "https://comix.fyi/rss",
        "category": "manga"
    }
]

class RSSFeedTester:
    """RSSフィードテスト用クラス"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.results = {
            "anime": [],
            "manga": [],
            "summary": {}
        }

    def test_feed(self, feed_info: Dict[str, str], timeout: int = 30) -> Dict[str, Any]:
        """
        単一のRSSフィードをテスト

        Args:
            feed_info: フィード情報
            timeout: タイムアウト秒数

        Returns:
            テスト結果
        """
        result = {
            "name": feed_info["name"],
            "url": feed_info["url"],
            "category": feed_info["category"],
            "status": "unknown",
            "http_code": None,
            "is_valid_xml": False,
            "is_valid_rss": False,
            "item_count": 0,
            "error": None,
            "sample_items": [],
            "response_time": 0,
            "timestamp": datetime.now().isoformat()
        }

        try:
            # HTTP GETリクエスト
            start_time = time.time()
            response = self.session.get(feed_info["url"], timeout=timeout)
            result["response_time"] = round(time.time() - start_time, 2)
            result["http_code"] = response.status_code

            # ステータスコード確認
            if response.status_code == 200:
                result["status"] = "http_ok"

                # XML/RSS パース
                feed = feedparser.parse(response.content)

                # 有効なRSS形式かどうか
                if feed.version:
                    result["is_valid_xml"] = True
                    result["is_valid_rss"] = True
                    result["status"] = "valid_rss"

                    # エントリ数
                    result["item_count"] = len(feed.entries)

                    # サンプルアイテム（最初の3件）
                    for i, entry in enumerate(feed.entries[:3]):
                        sample = {
                            "title": entry.get("title", ""),
                            "link": entry.get("link", ""),
                            "published": entry.get("published", "")
                        }
                        result["sample_items"].append(sample)
                else:
                    result["status"] = "invalid_xml"
                    result["error"] = "Valid RSS/XML not found"

            elif response.status_code == 404:
                result["status"] = "not_found"
                result["error"] = "404 Not Found"
            elif response.status_code >= 500:
                result["status"] = "server_error"
                result["error"] = f"HTTP {response.status_code}"
            else:
                result["status"] = "http_error"
                result["error"] = f"HTTP {response.status_code}"

        except requests.Timeout:
            result["status"] = "timeout"
            result["error"] = f"Timeout after {timeout}s"
        except requests.ConnectionError as e:
            result["status"] = "connection_error"
            result["error"] = str(e)
        except requests.RequestException as e:
            result["status"] = "request_error"
            result["error"] = str(e)
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def run_tests(self):
        """すべてのフィードをテスト"""
        print("[INFO] RSS Feed テストを開始します...\n")

        # アニメフィードのテスト
        print("=" * 80)
        print("アニメ情報RSSフィードのテスト")
        print("=" * 80)
        for feed_info in ANIME_FEEDS:
            print(f"[TEST] {feed_info['name']:<30} ... ", end="", flush=True)
            result = self.test_feed(feed_info)
            self.results["anime"].append(result)

            status_symbol = "✓" if result["is_valid_rss"] else "✗"
            print(f"{status_symbol} ({result['status']}) - {result['item_count']} items - {result['response_time']}s")

            if result["error"]:
                print(f"  エラー: {result['error']}")
            time.sleep(0.5)  # レート制限対策

        # マンガフィードのテスト
        print("\n" + "=" * 80)
        print("マンガ情報RSSフィードのテスト")
        print("=" * 80)
        for feed_info in MANGA_FEEDS:
            print(f"[TEST] {feed_info['name']:<30} ... ", end="", flush=True)
            result = self.test_feed(feed_info)
            self.results["manga"].append(result)

            status_symbol = "✓" if result["is_valid_rss"] else "✗"
            print(f"{status_symbol} ({result['status']}) - {result['item_count']} items - {result['response_time']}s")

            if result["error"]:
                print(f"  エラー: {result['error']}")
            time.sleep(0.5)  # レート制限対策

        self._generate_summary()

    def _generate_summary(self):
        """テスト結果のサマリーを生成"""
        anime_valid = sum(1 for r in self.results["anime"] if r["is_valid_rss"])
        manga_valid = sum(1 for r in self.results["manga"] if r["is_valid_rss"])

        self.results["summary"] = {
            "anime_total": len(self.results["anime"]),
            "anime_valid": anime_valid,
            "anime_valid_rate": f"{(anime_valid/len(self.results['anime'])*100):.1f}%",
            "manga_total": len(self.results["manga"]),
            "manga_valid": manga_valid,
            "manga_valid_rate": f"{(manga_valid/len(self.results['manga'])*100):.1f}%",
            "total_valid": anime_valid + manga_valid,
            "total_feeds": len(self.results["anime"]) + len(self.results["manga"])
        }

    def print_summary(self):
        """テスト結果のサマリーを表示"""
        print("\n" + "=" * 80)
        print("テスト結果サマリー")
        print("=" * 80)
        s = self.results["summary"]
        print(f"アニメフィード:  {s['anime_valid']}/{s['anime_total']} 有効 ({s['anime_valid_rate']})")
        print(f"マンガフィード:  {s['manga_valid']}/{s['manga_total']} 有効 ({s['manga_valid_rate']})")
        print(f"合計:            {s['total_valid']}/{s['total_feeds']} 有効")
        print("=" * 80)

    def get_valid_feeds(self) -> Dict[str, List[Dict]]:
        """有効なフィードのみを返す"""
        valid_feeds = {
            "anime": [r for r in self.results["anime"] if r["is_valid_rss"]],
            "manga": [r for r in self.results["manga"] if r["is_valid_rss"]]
        }
        return valid_feeds

    def save_results(self, filename: str = "rss_test_results.json"):
        """テスト結果をJSONファイルに保存"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n[INFO] テスト結果を {filename} に保存しました")

    def save_report(self, filename: str = "rss_test_report.md"):
        """テスト結果をMarkdownレポートとして保存"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# RSSフィード テスト結果レポート\n\n")
            f.write(f"**テスト実施日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            s = self.results["summary"]
            f.write("## テスト結果サマリー\n\n")
            f.write(f"- **アニメフィード**: {s['anime_valid']}/{s['anime_total']} 有効 ({s['anime_valid_rate']})\n")
            f.write(f"- **マンガフィード**: {s['manga_valid']}/{s['manga_total']} 有効 ({s['manga_valid_rate']})\n")
            f.write(f"- **合計**: {s['total_valid']}/{s['total_feeds']} 有効\n\n")

            # 有効なフィード
            f.write("## 有効なRSSフィード\n\n")
            valid_feeds = self.get_valid_feeds()

            f.write("### アニメ情報フィード\n\n")
            for result in valid_feeds["anime"]:
                f.write(f"- **{result['name']}**\n")
                f.write(f"  - URL: {result['url']}\n")
                f.write(f"  - エントリ数: {result['item_count']}\n")
                f.write(f"  - レスポンス時間: {result['response_time']}s\n\n")

            f.write("### マンガ情報フィード\n\n")
            for result in valid_feeds["manga"]:
                f.write(f"- **{result['name']}**\n")
                f.write(f"  - URL: {result['url']}\n")
                f.write(f"  - エントリ数: {result['item_count']}\n")
                f.write(f"  - レスポンス時間: {result['response_time']}s\n\n")

            # 無効なフィード
            f.write("## テスト結果（全体）\n\n")
            f.write("### アニメ情報フィード\n\n")
            f.write("| 名前 | URL | ステータス | エラー | エントリ数 |\n")
            f.write("|------|-----|----------|--------|----------|\n")
            for result in self.results["anime"]:
                status_mark = "✓" if result["is_valid_rss"] else "✗"
                error_msg = result["error"] if result["error"] else "-"
                f.write(f"| {status_mark} {result['name']} | {result['url']} | {result['status']} | {error_msg} | {result['item_count']} |\n")

            f.write("\n### マンガ情報フィード\n\n")
            f.write("| 名前 | URL | ステータス | エラー | エントリ数 |\n")
            f.write("|------|-----|----------|--------|----------|\n")
            for result in self.results["manga"]:
                status_mark = "✓" if result["is_valid_rss"] else "✗"
                error_msg = result["error"] if result["error"] else "-"
                f.write(f"| {status_mark} {result['name']} | {result['url']} | {result['status']} | {error_msg} | {result['item_count']} |\n")

        print(f"[INFO] レポートを {filename} に保存しました")


def main():
    """メイン処理"""
    tester = RSSFeedTester()
    tester.run_tests()
    tester.print_summary()
    tester.save_results()
    tester.save_report()

    # 有効なフィードを表示
    print("\n有効なフィード一覧（config.json更新用）:\n")
    valid_feeds = tester.get_valid_feeds()

    print("【アニメフィード】")
    for feed in valid_feeds["anime"]:
        print(f'  "url": "{feed["url"]}",  // {feed["name"]}')

    print("\n【マンガフィード】")
    for feed in valid_feeds["manga"]:
        print(f'  "url": "{feed["url"]}",  // {feed["name"]}')


if __name__ == "__main__":
    main()
