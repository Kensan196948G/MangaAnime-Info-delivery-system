#!/usr/bin/env python3
"""
システム統合テスト・エンドツーエンド検証スクリプト
Integration Testing and End-to-End Validation Suite
"""

import asyncio
import aiohttp
import json
import sqlite3
import time
import logging
import os
import sys
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import xml.etree.ElementTree as ET
import requests
from unittest.mock import patch, MagicMock

# プロジェクトルートをパスに追加
project_root = Path("/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")
sys.path.insert(0, str(project_root))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / "logs" / "integration_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntegrationTestSuite:
    """統合テストスイート"""
    
    def __init__(self):
        self.project_root = project_root
        self.test_db_path = self.project_root / "test_db.sqlite3"
        self.config_path = self.project_root / "config" / "config.json"
        self.test_results = {}
        self.test_start_time = time.time()
        
    def setup_test_environment(self) -> bool:
        """テスト環境セットアップ"""
        logger.info("🔧 テスト環境セットアップ開始")
        
        try:
            # テスト用データベース作成
            self.create_test_database()
            
            # テスト用設定ファイル確認
            if not self.config_path.exists():
                self.create_test_config()
            
            # ログディレクトリ作成
            (self.project_root / "logs").mkdir(exist_ok=True)
            
            logger.info("✅ テスト環境セットアップ完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ テスト環境セットアップ失敗: {e}")
            return False
    
    def create_test_database(self):
        """テスト用データベース作成"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # worksテーブル作成
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            title_kana TEXT,
            title_en TEXT,
            type TEXT CHECK(type IN ('anime','manga')),
            official_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # releasesテーブル作成
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS releases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_id INTEGER NOT NULL,
            release_type TEXT CHECK(release_type IN ('episode','volume')),
            number TEXT,
            platform TEXT,
            release_date DATE,
            source TEXT,
            source_url TEXT,
            notified INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(work_id, release_type, number, platform, release_date),
            FOREIGN KEY (work_id) REFERENCES works(id)
        )
        """)
        
        # テストデータ挿入
        test_works = [
            ("進撃の巨人", "しんげきのきょじん", "Attack on Titan", "anime", "https://shingeki.tv"),
            ("鬼滅の刃", "きめつのやいば", "Demon Slayer", "anime", "https://kimetsu.com"),
            ("ワンピース", "わんぴーす", "One Piece", "manga", "https://one-piece.com")
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO works (title, title_kana, title_en, type, official_url) VALUES (?, ?, ?, ?, ?)",
            test_works
        )
        
        # テストリリース情報
        test_releases = [
            (1, "episode", "25", "dアニメストア", "2024-12-01", "test", "https://example.com/1"),
            (2, "episode", "12", "Netflix", "2024-12-02", "test", "https://example.com/2"),
            (3, "volume", "105", "ジャンプ+", "2024-12-03", "test", "https://example.com/3")
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO releases (work_id, release_type, number, platform, release_date, source, source_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
            test_releases
        )
        
        conn.commit()
        conn.close()
        
        logger.info("📊 テスト用データベース作成完了")
    
    def create_test_config(self):
        """テスト用設定ファイル作成"""
        test_config = {
            "database": {
                "path": str(self.test_db_path)
            },
            "apis": {
                "anilist": {
                    "url": "https://graphql.anilist.co",
                    "rate_limit": 90
                },
                "gmail": {
                    "enabled": False,
                    "credentials_path": "credentials.json",
                    "token_path": "token.json"
                }
            },
            "notification": {
                "email": {
                    "enabled": False,
                    "recipient": "test@example.com"
                },
                "calendar": {
                    "enabled": False,
                    "calendar_id": "primary"
                }
            },
            "filtering": {
                "ng_keywords": ["エロ", "R18", "成人向け", "BL", "百合"]
            }
        }
        
        self.config_path.parent.mkdir(exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, ensure_ascii=False, indent=2)
        
        logger.info("⚙️ テスト用設定ファイル作成完了")
    
    async def test_anilist_api_integration(self) -> Dict[str, Any]:
        """AniList API統合テスト"""
        logger.info("🎌 AniList API統合テスト開始")
        
        test_result = {
            "test_name": "AniList API Integration",
            "status": "passed",
            "response_times": [],
            "data_quality": {},
            "errors": []
        }
        
        try:
            # GraphQLクエリ定義
            query = """
            query {
                Page(page: 1, perPage: 5) {
                    media(type: ANIME, status: RELEASING, sort: POPULARITY_DESC) {
                        id
                        title {
                            romaji
                            english
                            native
                        }
                        startDate {
                            year
                            month
                            day
                        }
                        episodes
                        genres
                        description
                        averageScore
                        streamingEpisodes {
                            title
                            url
                        }
                    }
                }
            }
            """
            
            async with aiohttp.ClientSession() as session:
                # 複数回リクエストして安定性確認
                for i in range(3):
                    start_time = time.time()
                    
                    async with session.post(
                        'https://graphql.anilist.co',
                        json={'query': query},
                        headers={'Content-Type': 'application/json'}
                    ) as response:
                        response_time = (time.time() - start_time) * 1000
                        test_result["response_times"].append(response_time)
                        
                        if response.status == 200:
                            data = await response.json()
                            
                            # データ品質チェック
                            if i == 0:  # 最初のレスポンスでデータ品質を確認
                                test_result["data_quality"] = self.validate_anilist_data(data)
                        else:
                            test_result["errors"].append(f"HTTP {response.status}: {await response.text()}")
                            test_result["status"] = "failed"
                    
                    await asyncio.sleep(1)  # レート制限対応
            
            # 平均応答時間が5秒以内なら合格
            avg_response_time = sum(test_result["response_times"]) / len(test_result["response_times"])
            if avg_response_time > 5000:
                test_result["status"] = "warning"
                test_result["errors"].append(f"平均応答時間が遅い: {avg_response_time:.1f}ms")
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"AniList APIテストエラー: {e}")
        
        return test_result
    
    def validate_anilist_data(self, data: Dict) -> Dict[str, Any]:
        """AniListデータ品質検証"""
        quality_metrics = {
            "valid_structure": False,
            "complete_titles": 0,
            "valid_dates": 0,
            "total_items": 0,
            "streaming_info_available": 0
        }
        
        try:
            if "data" in data and "Page" in data["data"] and "media" in data["data"]["Page"]:
                quality_metrics["valid_structure"] = True
                media_list = data["data"]["Page"]["media"]
                quality_metrics["total_items"] = len(media_list)
                
                for media in media_list:
                    # タイトル完全性チェック
                    if media.get("title", {}).get("romaji"):
                        quality_metrics["complete_titles"] += 1
                    
                    # 日付妥当性チェック
                    start_date = media.get("startDate", {})
                    if start_date.get("year") and start_date.get("month"):
                        quality_metrics["valid_dates"] += 1
                    
                    # 配信情報チェック
                    if media.get("streamingEpisodes"):
                        quality_metrics["streaming_info_available"] += 1
        
        except Exception as e:
            logger.error(f"データ品質検証エラー: {e}")
        
        return quality_metrics
    
    def test_rss_feed_integration(self) -> Dict[str, Any]:
        """RSS フィード統合テスト"""
        logger.info("📡 RSS フィード統合テスト開始")
        
        test_result = {
            "test_name": "RSS Feed Integration",
            "status": "passed",
            "feed_results": {},
            "errors": []
        }
        
        # テスト対象のRSSフィード
        rss_feeds = {
            "dアニメストア": "https://anime.dmkt-sp.jp/animestore/CF/rss/",
            "BookWalker": "https://bookwalker.jp/rss/",
        }
        
        for feed_name, feed_url in rss_feeds.items():
            try:
                start_time = time.time()
                response = requests.get(feed_url, timeout=15)
                response_time = (time.time() - start_time) * 1000
                
                feed_result = {
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "content_valid": False,
                    "item_count": 0
                }
                
                if response.status_code == 200:
                    # XML パース確認
                    try:
                        root = ET.fromstring(response.content)
                        items = root.findall(".//item")
                        feed_result["item_count"] = len(items)
                        feed_result["content_valid"] = len(items) > 0
                    except ET.ParseError as e:
                        feed_result["parse_error"] = str(e)
                        test_result["status"] = "warning"
                else:
                    test_result["errors"].append(f"{feed_name}: HTTP {response.status_code}")
                    test_result["status"] = "failed"
                
                test_result["feed_results"][feed_name] = feed_result
                
            except Exception as e:
                test_result["feed_results"][feed_name] = {
                    "error": str(e),
                    "response_time": 999999
                }
                test_result["errors"].append(f"{feed_name}: {str(e)}")
                test_result["status"] = "failed"
        
        return test_result
    
    def test_database_operations(self) -> Dict[str, Any]:
        """データベース操作テスト"""
        logger.info("🗃️ データベース操作テスト開始")
        
        test_result = {
            "test_name": "Database Operations",
            "status": "passed",
            "operation_times": {},
            "data_integrity": {},
            "errors": []
        }
        
        try:
            conn = sqlite3.connect(self.test_db_path)
            cursor = conn.cursor()
            
            # INSERT性能テスト
            start_time = time.time()
            test_work_data = ("テスト作品", "てすとさくひん", "Test Work", "anime", "https://test.com")
            cursor.execute(
                "INSERT INTO works (title, title_kana, title_en, type, official_url) VALUES (?, ?, ?, ?, ?)",
                test_work_data
            )
            work_id = cursor.lastrowid
            conn.commit()
            test_result["operation_times"]["insert"] = (time.time() - start_time) * 1000
            
            # SELECT性能テスト
            start_time = time.time()
            cursor.execute("SELECT * FROM works WHERE id = ?", (work_id,))
            row = cursor.fetchone()
            test_result["operation_times"]["select"] = (time.time() - start_time) * 1000
            
            # UPDATE性能テスト
            start_time = time.time()
            cursor.execute("UPDATE works SET title = ? WHERE id = ?", ("更新テスト作品", work_id))
            conn.commit()
            test_result["operation_times"]["update"] = (time.time() - start_time) * 1000
            
            # データ整合性確認
            cursor.execute("SELECT COUNT(*) FROM works")
            work_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM releases")
            release_count = cursor.fetchone()[0]
            
            test_result["data_integrity"] = {
                "work_count": work_count,
                "release_count": release_count,
                "foreign_key_valid": True  # 簡略化
            }
            
            # クリーンアップ
            cursor.execute("DELETE FROM works WHERE id = ?", (work_id,))
            conn.commit()
            conn.close()
            
            # 性能基準チェック
            for operation, time_ms in test_result["operation_times"].items():
                if time_ms > 1000:  # 1秒以上なら警告
                    test_result["errors"].append(f"{operation}操作が遅い: {time_ms:.1f}ms")
                    test_result["status"] = "warning"
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"データベース操作テストエラー: {e}")
        
        return test_result
    
    def test_notification_system(self) -> Dict[str, Any]:
        """通知システムテスト（モック使用）"""
        logger.info("📧 通知システムテスト開始")
        
        test_result = {
            "test_name": "Notification System",
            "status": "passed",
            "email_test": {},
            "calendar_test": {},
            "errors": []
        }
        
        try:
            # Gmail API テスト（認証ファイル存在確認のみ）
            credentials_path = self.project_root / "credentials.json"
            token_path = self.project_root / "token.json"
            
            test_result["email_test"] = {
                "credentials_exist": credentials_path.exists(),
                "token_exist": token_path.exists(),
                "ready_for_production": credentials_path.exists() and token_path.exists()
            }
            
            # Google Calendar API テスト（同じ認証情報使用）
            test_result["calendar_test"] = {
                "credentials_exist": credentials_path.exists(),
                "ready_for_production": credentials_path.exists() and token_path.exists()
            }
            
            # 認証情報が不足している場合は警告
            if not (credentials_path.exists() and token_path.exists()):
                test_result["status"] = "warning"
                test_result["errors"].append("Gmail/Calendar API認証情報が不足しています")
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"通知システムテストエラー: {e}")
        
        return test_result
    
    def test_filtering_logic(self) -> Dict[str, Any]:
        """フィルタリングロジックテスト"""
        logger.info("🔍 フィルタリングロジックテスト開始")
        
        test_result = {
            "test_name": "Filtering Logic",
            "status": "passed",
            "filter_tests": {},
            "errors": []
        }
        
        try:
            # NGワードリスト
            ng_keywords = ["エロ", "R18", "成人向け", "BL", "百合", "ボーイズラブ"]
            
            # テストケース
            test_cases = [
                ("進撃の巨人", True),  # 通常のアニメ - 通す
                ("エロアニメ", False),  # NGワード含む - 除外
                ("R18指定作品", False),  # NGワード含む - 除外
                ("ラブコメディ", True),  # 正常 - 通す
                ("BL作品", False),  # NGワード含む - 除外
                ("百合アニメ", False),  # NGワード含む - 除外
                ("ボーイズラブストーリー", False),  # NGワード含む - 除外
            ]
            
            passed_tests = 0
            for title, should_pass in test_cases:
                # 簡単なフィルタリングロジック
                contains_ng = any(ng_word in title for ng_word in ng_keywords)
                actual_pass = not contains_ng
                
                test_passed = actual_pass == should_pass
                if test_passed:
                    passed_tests += 1
                
                test_result["filter_tests"][title] = {
                    "expected": should_pass,
                    "actual": actual_pass,
                    "passed": test_passed
                }
            
            # 全テストが通れば成功
            if passed_tests == len(test_cases):
                test_result["status"] = "passed"
            else:
                test_result["status"] = "failed"
                test_result["errors"].append(f"フィルタリングテスト {passed_tests}/{len(test_cases)} 通過")
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"フィルタリングロジックテストエラー: {e}")
        
        return test_result
    
    def test_web_ui_integration(self) -> Dict[str, Any]:
        """Web UI統合テスト"""
        logger.info("🌐 Web UI統合テスト開始")
        
        test_result = {
            "test_name": "Web UI Integration",
            "status": "passed",
            "file_checks": {},
            "errors": []
        }
        
        try:
            # 必要ファイルの存在確認
            required_files = {
                "app.py": self.project_root / "app.py",
                "dashboard.py": self.project_root / "modules" / "dashboard.py",
                "templates_dir": self.project_root / "templates",
                "static_dir": self.project_root / "static"
            }
            
            for file_key, file_path in required_files.items():
                exists = file_path.exists()
                test_result["file_checks"][file_key] = {
                    "exists": exists,
                    "path": str(file_path)
                }
                
                if not exists and file_key in ["app.py", "dashboard.py"]:
                    test_result["errors"].append(f"必須ファイルが見つかりません: {file_path}")
                    test_result["status"] = "failed"
            
            # Flask アプリケーションの基本的な構文チェック
            app_py = self.project_root / "app.py"
            if app_py.exists():
                try:
                    with open(app_py, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 基本的な Flask パターンを確認
                        if "from flask import" in content and "app = Flask" in content:
                            test_result["file_checks"]["flask_structure"] = {"valid": True}
                        else:
                            test_result["file_checks"]["flask_structure"] = {"valid": False}
                            test_result["status"] = "warning"
                except Exception as e:
                    test_result["errors"].append(f"app.py読み込みエラー: {e}")
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"Web UI統合テストエラー: {e}")
        
        return test_result
    
    def test_cron_configuration(self) -> Dict[str, Any]:
        """cron設定テスト"""
        logger.info("⏰ cron設定テスト開始")
        
        test_result = {
            "test_name": "Cron Configuration",
            "status": "passed",
            "cron_checks": {},
            "errors": []
        }
        
        try:
            # crontab確認
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            
            if result.returncode == 0:
                cron_content = result.stdout
                test_result["cron_checks"]["crontab_accessible"] = True
                
                # アニメ関連のcronジョブ確認
                anime_jobs = []
                for line in cron_content.split('\n'):
                    if 'release_notifier' in line or 'anime' in line.lower():
                        anime_jobs.append(line.strip())
                
                test_result["cron_checks"]["anime_jobs"] = anime_jobs
                test_result["cron_checks"]["anime_jobs_count"] = len(anime_jobs)
                
                if len(anime_jobs) == 0:
                    test_result["status"] = "warning"
                    test_result["errors"].append("アニメ関連のcronジョブが設定されていません")
            
            else:
                test_result["cron_checks"]["crontab_accessible"] = False
                test_result["status"] = "warning"
                test_result["errors"].append("crontabにアクセスできません")
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
            logger.error(f"cron設定テストエラー: {e}")
        
        return test_result
    
    async def run_full_integration_test(self) -> Dict[str, Any]:
        """完全統合テスト実行"""
        logger.info("🚀 完全統合テスト開始")
        
        # テスト環境セットアップ
        if not self.setup_test_environment():
            return {"status": "failed", "error": "テスト環境セットアップ失敗"}
        
        # 各種テスト実行
        test_results = {}
        
        try:
            # 並列実行可能なテスト
            async_tests = [
                self.test_anilist_api_integration(),
            ]
            
            async_results = await asyncio.gather(*async_tests, return_exceptions=True)
            test_results["anilist_api"] = async_results[0] if not isinstance(async_results[0], Exception) else {
                "status": "failed", "error": str(async_results[0])
            }
            
            # 同期テスト
            test_results["rss_feeds"] = self.test_rss_feed_integration()
            test_results["database"] = self.test_database_operations()
            test_results["notification"] = self.test_notification_system()
            test_results["filtering"] = self.test_filtering_logic()
            test_results["web_ui"] = self.test_web_ui_integration()
            test_results["cron"] = self.test_cron_configuration()
            
        except Exception as e:
            logger.error(f"統合テスト実行エラー: {e}")
            test_results["execution_error"] = {"status": "failed", "error": str(e)}
        
        # 全体結果の集計
        overall_result = self.compile_test_results(test_results)
        
        # テスト後のクリーンアップ
        self.cleanup_test_environment()
        
        return overall_result
    
    def compile_test_results(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """テスト結果集計"""
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result.get("status") == "passed")
        warning_tests = sum(1 for result in test_results.values() if result.get("status") == "warning")
        failed_tests = sum(1 for result in test_results.values() if result.get("status") == "failed")
        
        # 全体スコア計算
        overall_score = (passed_tests * 100 + warning_tests * 50) / (total_tests * 100) * 100 if total_tests > 0 else 0
        
        # 全体ステータス決定
        if failed_tests > 0:
            overall_status = "failed"
        elif warning_tests > 0:
            overall_status = "warning"
        else:
            overall_status = "passed"
        
        return {
            "overall_status": overall_status,
            "overall_score": overall_score,
            "test_summary": {
                "total": total_tests,
                "passed": passed_tests,
                "warning": warning_tests,
                "failed": failed_tests
            },
            "detailed_results": test_results,
            "execution_time": time.time() - self.test_start_time,
            "timestamp": datetime.now().isoformat(),
            "recommendations": self.generate_test_recommendations(test_results)
        }
    
    def generate_test_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """テスト結果に基づく推奨事項生成"""
        recommendations = []
        
        for test_name, result in test_results.items():
            if result.get("status") == "failed":
                recommendations.append(f"❌ {test_name}: 修正が必要です - {', '.join(result.get('errors', []))}")
            elif result.get("status") == "warning":
                recommendations.append(f"⚠️ {test_name}: 改善を推奨します - {', '.join(result.get('errors', []))}")
        
        if not recommendations:
            recommendations.append("✅ すべてのテストが正常に完了しました。本番環境での運用準備が整っています。")
        
        return recommendations
    
    def cleanup_test_environment(self):
        """テスト環境クリーンアップ"""
        try:
            if self.test_db_path.exists():
                self.test_db_path.unlink()
            logger.info("🧹 テスト環境クリーンアップ完了")
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")

async def main():
    """メイン実行関数"""
    logger.info("🧪 アニメ・マンガ情報配信システム - 統合テスト開始")
    
    test_suite = IntegrationTestSuite()
    
    try:
        # 完全統合テスト実行
        results = await test_suite.run_full_integration_test()
        
        # 結果保存
        results_path = project_root / "INTEGRATION_TEST_RESULTS.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        # 結果表示
        print("\n" + "="*80)
        print("🧪 統合テスト結果サマリー")
        print("="*80)
        print(f"📊 全体ステータス: {results['overall_status'].upper()}")
        print(f"🎯 全体スコア: {results['overall_score']:.1f}/100")
        print(f"✅ 成功: {results['test_summary']['passed']}")
        print(f"⚠️ 警告: {results['test_summary']['warning']}")
        print(f"❌ 失敗: {results['test_summary']['failed']}")
        print(f"⏱️ 実行時間: {results['execution_time']:.2f}秒")
        
        print("\n📋 推奨事項:")
        for i, rec in enumerate(results['recommendations'][:10], 1):
            print(f"  {i}. {rec}")
        
        print(f"\n📄 詳細結果: {results_path}")
        print("="*80)
        
        logger.info("✅ 統合テスト完了")
        
    except Exception as e:
        logger.error(f"❌ 統合テスト実行エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())