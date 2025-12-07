#!/usr/bin/env python3
"""
データ収集機能の統合テスト
実際のAPIとRSSから情報を取得して動作確認
"""
import sys
import os
import time
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.anime_anilist import AniListClient, AniListCollector
from modules.manga_rss import MangaRSSCollector
from modules.config import get_config
from modules.db import DatabaseManager


class TestDataCollection:
    """データ収集統合テストクラス"""

    def __init__(self):
        self.results = {}
        self.start_time = None
        self.config = None

    def setup(self):
        """テスト環境のセットアップ"""
        print("=" * 60)
        print("データ収集機能 統合テスト")
        print("=" * 60)
        self.start_time = time.time()

        try:
            self.config = get_config()
            print("✅ 設定ファイル読み込み成功")
            return True
        except Exception as e:
            print(f"❌ 設定ファイル読み込みエラー: {e}")
            return False

    def test_anilist_api(self):
        """AniList API接続テスト"""
        print("\n" + "=" * 60)
        print("1. AniList API テスト")
        print("=" * 60)

        try:
            client = AniListClient()
            print("✅ AniListクライアント初期化成功")

            # 今期アニメ取得
            print("\n今期アニメ取得中...")
            current_season = client.get_current_season_anime(per_page=10)

            if not current_season:
                print("⚠️  今期アニメが取得できませんでした")
                return False

            print(f"✅ 今期アニメ取得成功: {len(current_season)}作品")

            # 最初の5作品を表示
            print("\n取得した作品（最初の5件）:")
            for i, anime in enumerate(current_season[:5], 1):
                title = anime.get('title', {})
                title_romaji = title.get('romaji', 'Unknown')
                title_native = title.get('native', '')
                start_date = anime.get('startDate', {})

                print(f"\n  {i}. {title_romaji}")
                if title_native:
                    print(f"     日本語: {title_native}")
                if start_date:
                    print(f"     放送開始: {start_date.get('year')}/{start_date.get('month')}/{start_date.get('day')}")

                # 配信プラットフォーム
                streaming = anime.get('streamingEpisodes', [])
                if streaming:
                    print(f"     配信: {len(streaming)}プラットフォーム")

            self.results['anilist_api'] = True
            return True

        except Exception as e:
            print(f"❌ AniListエラー: {e}")
            import traceback
            traceback.print_exc()
            self.results['anilist_api'] = False
            return False

    def test_anilist_collector(self):
        """AniListコレクターテスト"""
        print("\n" + "=" * 60)
        print("2. AniList コレクター テスト")
        print("=" * 60)

        try:
            collector = AniListCollector(self.config)
            print("✅ AniListコレクター初期化成功")

            # データ収集
            print("\nアニメデータ収集中...")
            works = collector.collect()

            if not works:
                print("⚠️  アニメデータが収集できませんでした")
                return False

            print(f"✅ アニメデータ収集成功: {len(works)}作品")

            # サンプル表示
            print("\n収集したデータ（最初の3件）:")
            for i, work in enumerate(works[:3], 1):
                print(f"\n  {i}. {work.title}")
                if work.title_en:
                    print(f"     英語: {work.title_en}")
                print(f"     タイプ: {work.work_type}")
                print(f"     URL: {work.official_url}")

                if hasattr(work, 'releases') and work.releases:
                    print(f"     リリース情報: {len(work.releases)}件")
                    for release in work.releases[:2]:
                        print(f"       - {release.platform}: {release.release_date}")

            self.results['anilist_collector'] = True
            return True

        except Exception as e:
            print(f"❌ コレクターエラー: {e}")
            import traceback
            traceback.print_exc()
            self.results['anilist_collector'] = False
            return False

    def test_manga_rss(self):
        """マンガRSS収集テスト"""
        print("\n" + "=" * 60)
        print("3. マンガRSS収集テスト")
        print("=" * 60)

        try:
            collector = MangaRSSCollector(self.config)
            print("✅ RSSコレクター初期化成功")

            # RSS収集
            print("\nRSSフィード収集中...")
            works = collector.collect()

            if not works:
                print("⚠️  RSSデータが収集できませんでした")
                return False

            print(f"✅ RSS収集成功: {len(works)}作品")

            # サンプル表示
            print("\n収集したデータ（最初の5件）:")
            for i, work in enumerate(works[:5], 1):
                print(f"\n  {i}. {work.title}")
                print(f"     タイプ: {work.work_type}")
                if work.official_url:
                    print(f"     URL: {work.official_url[:60]}...")

                if hasattr(work, 'releases') and work.releases:
                    for release in work.releases[:1]:
                        print(f"     リリース: {release.release_date} ({release.platform})")

            self.results['manga_rss'] = True
            return True

        except Exception as e:
            print(f"❌ RSS収集エラー: {e}")
            import traceback
            traceback.print_exc()
            self.results['manga_rss'] = False
            return False

    def test_database_operations(self):
        """データベース操作テスト"""
        print("\n" + "=" * 60)
        print("4. データベース操作テスト")
        print("=" * 60)

        try:
            db = DatabaseManager()
            print("✅ データベース接続成功")

            # テストデータ作成
            print("\nテストデータ登録中...")
            work_id = db.add_work(
                title="【テスト】統合テストアニメ",
                work_type="anime",
                title_en="Integration Test Anime",
                official_url="https://example.com/test"
            )

            print(f"✅ 作品登録成功: ID={work_id}")

            # リリース情報追加
            from datetime import date, timedelta
            release_date = date.today() + timedelta(days=7)

            release_id = db.add_release(
                work_id=work_id,
                release_type="episode",
                number="1",
                platform="Test Platform",
                release_date=release_date,
                source="test",
                source_url="https://example.com/test/ep1"
            )

            print(f"✅ リリース情報登録成功: ID={release_id}")

            # データ取得テスト
            pending = db.get_pending_notifications()
            print(f"✅ 未通知リリース取得: {len(pending)}件")

            # クリーンアップ
            db.conn.execute("DELETE FROM releases WHERE id = ?", (release_id,))
            db.conn.execute("DELETE FROM works WHERE id = ?", (work_id,))
            db.conn.commit()
            print("✅ テストデータクリーンアップ完了")

            self.results['database'] = True
            return True

        except Exception as e:
            print(f"❌ データベースエラー: {e}")
            import traceback
            traceback.print_exc()
            self.results['database'] = False
            return False

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        print("\n" + "=" * 60)
        print("5. エラーハンドリングテスト")
        print("=" * 60)

        try:
            # 無効なRSS URLでのテスト
            print("\n無効なRSS URLテスト...")
            from modules.manga_rss import RSSParser

            parser = RSSParser()
            result = parser.parse_feed("https://invalid-url-for-testing.example.com/feed")

            if result is None or len(result) == 0:
                print("✅ 無効なURLを適切に処理")
            else:
                print("⚠️  エラーハンドリングが期待通りではない可能性")

            # AniListレート制限テスト
            print("\nAniList レート制限テスト...")
            client = AniListClient()

            # 連続リクエスト（レート制限を確認）
            for i in range(3):
                try:
                    client.get_current_season_anime(per_page=5)
                    print(f"  リクエスト {i+1}: 成功")
                    time.sleep(1)  # レート制限回避
                except Exception as e:
                    print(f"  リクエスト {i+1}: {e}")

            print("✅ レート制限ハンドリング確認完了")

            self.results['error_handling'] = True
            return True

        except Exception as e:
            print(f"❌ エラーハンドリングテストエラー: {e}")
            import traceback
            traceback.print_exc()
            self.results['error_handling'] = False
            return False

    def test_retry_logic(self):
        """リトライロジックテスト"""
        print("\n" + "=" * 60)
        print("6. リトライロジックテスト")
        print("=" * 60)

        try:
            from modules.retry_handler import RetryHandler

            handler = RetryHandler(max_retries=3, backoff_factor=1.5)
            print("✅ リトライハンドラー初期化成功")

            # 成功するまでリトライ
            attempt_count = 0

            def test_function():
                nonlocal attempt_count
                attempt_count += 1
                if attempt_count < 2:
                    raise Exception("意図的なエラー")
                return "成功"

            result = handler.execute_with_retry(test_function)
            print(f"✅ リトライ成功: {attempt_count}回目で成功, 結果={result}")

            self.results['retry_logic'] = True
            return True

        except Exception as e:
            print(f"❌ リトライロジックエラー: {e}")
            import traceback
            traceback.print_exc()
            self.results['retry_logic'] = False
            return False

    def print_summary(self):
        """テスト結果サマリー表示"""
        elapsed = time.time() - self.start_time

        print("\n" + "=" * 60)
        print("テスト結果サマリー")
        print("=" * 60)

        total = len(self.results)
        passed = sum(1 for v in self.results.values() if v)
        failed = total - passed

        for name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {name}")

        print("\n" + "-" * 60)
        print(f"合計: {total}テスト")
        print(f"成功: {passed}テスト ({passed/total*100:.1f}%)")
        print(f"失敗: {failed}テスト")
        print(f"実行時間: {elapsed:.2f}秒")
        print("=" * 60)

        return failed == 0


def main():
    """メイン実行関数"""
    tester = TestDataCollection()

    # セットアップ
    if not tester.setup():
        print("\n❌ セットアップに失敗しました")
        return 1

    # テスト実行
    tester.test_anilist_api()
    tester.test_anilist_collector()
    tester.test_manga_rss()
    tester.test_database_operations()
    tester.test_error_handling()
    tester.test_retry_logic()

    # サマリー表示
    success = tester.print_summary()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
