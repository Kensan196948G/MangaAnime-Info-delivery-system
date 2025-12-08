#!/usr/bin/env python3
"""
Dashboard Enhanced Release Notifier
ダッシュボード機能統合版リリース通知システム
"""

import json
import logging
import sys
import time
from datetime import datetime

from modules.anime_anilist import AniListCollector
from modules.calendar_integration import GoogleCalendarManager
from modules.dashboard_integration import dashboard_integration, track_performance
from modules.db import DatabaseManager
from modules.filter_logic import ContentFilter
from modules.mailer import GmailNotifier
from modules.manga_rss import MangaRSSCollector

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/dashboard_system.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class DashboardEnabledReleaseNotifier:
    """ダッシュボード機能統合版リリース通知システム"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path

        # 設定を読み込み
        self._load_config()

        # 各モジュールを初期化
        self.db_manager = DatabaseManager()
        self.anilist_api = AniListCollector()
        self.manga_collector = MangaRSSCollector()
        self.content_filter = ContentFilter()
        self.mail_sender = GmailNotifier()
        self.calendar_manager = GoogleCalendarManager()

        logger.info("Dashboard-enabled Release Notifier initialized")

    def _load_config(self):
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = {}

    @track_performance("anime_collection", "anilist")
    def collect_anime_data(self):
        """アニメデータを収集（ダッシュボード統合版）"""
        logger.info("Starting anime data collection...")
        collected_count = 0

        try:
            # AniList APIからデータを取得
            start_time = time.time()

            # 今期アニメを取得
            current_season_anime = self.anilist_api.get_current_season_anime()

            # API応答時間を記録
            response_time = (time.time() - start_time) * 1000
            dashboard_integration.track_api_request(
                "anilist", response_time, success=len(current_season_anime) > 0
            )

            for anime in current_season_anime:
                try:
                    # フィルタリング
                    if not self.content_filter.should_process_work(anime):
                        continue

                    # データベースに保存
                    start_db_time = time.time()
                    work_id = self.db_manager.save_work(anime)

                    # エピソード情報を保存
                    if anime.get("episodes_data"):
                        for episode in anime["episodes_data"]:
                            self.db_manager.save_release(work_id, episode)

                    # データベース操作時間を記録
                    db_duration = (time.time() - start_db_time) * 1000
                    dashboard_integration.track_database_operation("anime_insert", db_duration, 1)

                    collected_count += 1

                except Exception as e:
                    logger.error(f"Error processing anime {anime.get('title', 'Unknown')}: {e}")
                    dashboard_integration.track_api_request("anilist", 0, False)

            logger.info(f"Collected {collected_count} anime entries")

            # システムヘルス状態を更新
            dashboard_integration.dashboard_service.update_system_health(
                "anime_collection",
                "healthy",
                performance_score=min(1.0, collected_count / 10.0),  # 10件で満点
            )

            return collected_count

        except Exception as e:
            logger.error(f"Failed to collect anime data: {e}")
            dashboard_integration.dashboard_service.update_system_health(
                "anime_collection", "error", str(e)
            )
            raise

    @track_performance("manga_collection", "rss")
    def collect_manga_data(self):
        """マンガデータを収集（ダッシュボード統合版）"""
        logger.info("Starting manga data collection...")
        total_collected = 0

        # RSS ソース一覧
        rss_sources = self.config.get("manga_rss_sources", [])

        for source in rss_sources:
            try:
                source_name = source.get("name", "unknown")
                source_url = source.get("url", "")

                logger.info(f"Processing RSS source: {source_name}")

                # RSS データを収集
                start_time = time.time()
                manga_data = self.manga_collector.fetch_from_source(source_url)

                success = len(manga_data) > 0
                items_count = len(manga_data)

                # RSS収集結果を追跡
                dashboard_integration.track_rss_collection(source_name, success, items_count)

                # データを処理
                source_collected = 0
                for manga in manga_data:
                    try:
                        # フィルタリング
                        if not self.content_filter.should_process_work(manga):
                            continue

                        # データベースに保存
                        start_db_time = time.time()
                        work_id = self.db_manager.save_work(manga)

                        # リリース情報を保存
                        if manga.get("releases"):
                            for release in manga["releases"]:
                                self.db_manager.save_release(work_id, release)

                        # データベース操作時間を記録
                        db_duration = (time.time() - start_db_time) * 1000
                        dashboard_integration.track_database_operation(
                            "manga_insert", db_duration, 1
                        )

                        source_collected += 1

                    except Exception as e:
                        logger.error(f"Error processing manga from {source_name}: {e}")

                total_collected += source_collected
                logger.info(f"Collected {source_collected} manga entries from {source_name}")

            except Exception as e:
                logger.error(f"Error processing RSS source {source.get('name', 'unknown')}: {e}")
                dashboard_integration.track_rss_collection(source.get("name", "unknown"), False, 0)

        logger.info(f"Total manga collected: {total_collected}")

        # システムヘルス状態を更新
        dashboard_integration.dashboard_service.update_system_health(
            "manga_collection",
            "healthy" if total_collected > 0 else "warning",
            performance_score=min(1.0, total_collected / 20.0),  # 20件で満点
        )

        return total_collected

    @track_performance("notification_processing", "notification")
    def process_notifications(self):
        """通知処理（ダッシュボード統合版）"""
        logger.info("Processing notifications...")

        try:
            # 未通知のリリースを取得
            pending_releases = self.db_manager.get_pending_notifications()

            if not pending_releases:
                logger.info("No pending notifications")
                return 0

            sent_count = 0

            for release in pending_releases:
                try:
                    # メール通知
                    start_time = time.time()
                    email_success = self.mail_sender.send_release_notification(release)

                    # 通知送信結果を追跡
                    dashboard_integration.track_notification_sent("email", email_success)

                    # カレンダー登録
                    calendar_success = self.calendar_manager.add_release_event(release)
                    dashboard_integration.track_notification_sent("calendar", calendar_success)

                    if email_success:
                        # 通知済みフラグを更新
                        self.db_manager.mark_as_notified(release["id"])
                        sent_count += 1
                        logger.info(f"Notification sent for: {release['title']}")

                    # 短時間の間隔を空ける（API制限対応）
                    time.sleep(1)

                except Exception as e:
                    logger.error(f"Error sending notification for release {release['id']}: {e}")
                    dashboard_integration.track_notification_sent("email", False)

            logger.info(f"Sent {sent_count} notifications")

            # システムヘルス状態を更新
            dashboard_integration.dashboard_service.update_system_health(
                "notification_system",
                "healthy",
                performance_score=1.0 if sent_count > 0 else 0.8,
            )

            return sent_count

        except Exception as e:
            logger.error(f"Failed to process notifications: {e}")
            dashboard_integration.dashboard_service.update_system_health(
                "notification_system", "error", str(e)
            )
            raise

    @track_performance("full_system_run", "system")
    def run_full_cycle(self):
        """完全なデータ収集・通知サイクルを実行"""
        logger.info("=== Starting full system cycle ===")

        try:
            # データベース初期化
            self.db_manager.initialize_database()

            # データ収集
            anime_count = self.collect_anime_data()
            manga_count = self.collect_manga_data()

            # 通知処理
            notification_count = self.process_notifications()

            # 統計情報をログ出力
            logger.info("=== Cycle completed successfully ===")
            logger.info(f"Anime collected: {anime_count}")
            logger.info(f"Manga collected: {manga_count}")
            logger.info(f"Notifications sent: {notification_count}")

            # 全体的なシステムヘルス状態を更新
            dashboard_integration.dashboard_service.update_system_health(
                "overall_system", "healthy", performance_score=1.0
            )

            return {
                "anime_collected": anime_count,
                "manga_collected": manga_count,
                "notifications_sent": notification_count,
                "success": True,
            }

        except Exception as e:
            logger.error(f"System cycle failed: {e}")
            dashboard_integration.dashboard_service.update_system_health(
                "overall_system", "error", str(e)
            )
            raise

    def cleanup_old_data(self):
        """古いデータのクリーンアップ"""
        logger.info("Starting data cleanup...")

        try:
            # 古いメトリクスデータをクリーンアップ
            cleanup_result = dashboard_integration.cleanup_old_metrics(days=30)

            # 古いリリースデータもクリーンアップ（90日以上前）
            # TODO: 実装

            logger.info(f"Cleanup completed: {cleanup_result}")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


def main():
    """メイン関数"""
    try:
        # システム開始時刻を記録
        start_time = datetime.now()
        logger.info(f"System startup at {start_time}")

        # システム初期化
        notifier = DashboardEnabledReleaseNotifier()

        # 完全サイクルを実行
        result = notifier.run_full_cycle()

        # 完了時刻を記録
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"System cycle completed in {duration:.2f} seconds")
        logger.info(f"Results: {result}")

        # 週に1回のクリーンアップ（曜日で判定）
        if datetime.now().weekday() == 6:  # 日曜日
            notifier.cleanup_old_data()

    except Exception as e:
        logger.error(f"System failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
