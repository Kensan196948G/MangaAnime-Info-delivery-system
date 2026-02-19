#!/usr/bin/env python3
"""
アニメ・マンガ情報配信システム - メインエントリポイント

このスクリプトは以下の処理を順次実行します：
1. 情報収集（AniList API、RSS、しょぼいカレンダー）
2. データ正規化とフィルタリング
3. データベース保存
4. 未通知リリースの通知処理（Gmail + Googleカレンダー）

Usage:
    python3 release_notifier.py [--config CONFIG_PATH] [--dry-run] [--verbose] [--force-send]

Environment Variables:
    DATABASE_PATH: データベースファイルのパス
    LOG_LEVEL: ログレベル (DEBUG, INFO, WARNING, ERROR)
    GMAIL_FROM_EMAIL: Gmail送信者アドレス
    GMAIL_TO_EMAIL: Gmail受信者アドレス
"""

import argparse
import logging
import signal
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# 環境変数を.envファイルから読み込み
from dotenv import load_dotenv

load_dotenv()

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent  # app/の親ディレクトリ（プロジェクトルート）
sys.path.insert(0, str(project_root))

from modules import get_config
from modules.db import DatabaseManager
from modules.email_scheduler import EmailScheduler
from modules.logger import setup_logging

logger = logging.getLogger(__name__)


class ReleaseNotifierSystem:
    """アニメ・マンガ情報配信システムメインクラス"""

    def __init__(
        self,
        config_path: Optional[str] = None,
        dry_run: bool = False,
        force_send: bool = False,
    ):
        """
        システムの初期化

        Args:
            config_path (Optional[str]): 設定ファイルパス
            dry_run (bool): ドライランモード（実際の通知は送信しない）
            force_send (bool): 強制送信モード（時刻に関係なく送信）
        """
        self.dry_run = dry_run
        self.force_send = force_send
        self.config = get_config(config_path)

        # ログの設定
        setup_logging(self.config)
        self.logger = logging.getLogger(__name__)

        self.logger.info("=" * 60)
        self.logger.info(
            f"🚀 {self.config.get_system_name()} v{self.config.get_system_version()} 開始"
        )
        self.logger.info(f"環境: {self.config.get_environment()}")
        self.logger.info(f"ドライランモード: {'有効' if dry_run else '無効'}")
        self.logger.info("=" * 60)

        # 設定の検証
        config_errors = self.config.validate_config()
        if config_errors:
            for error in config_errors:
                self.logger.error(f"設定エラー: {error}")
            raise ValueError("設定に問題があります。ログを確認してください。")

        # データベースの初期化
        self.db = DatabaseManager(self.config.get_db_path())

        # メール配信スケジューラーの初期化
        self.email_scheduler = EmailScheduler(self.config)

        # モジュール初期化（遅延インポートで循環参照を回避）
        self._collectors = None
        self._mailer = None
        self._calendar = None
        self._filter = None
        self._email_generator = None

        self.start_time = datetime.now()
        self.statistics = {
            "processed_sources": 0,
            "new_works": 0,
            "new_releases": 0,
            "notifications_sent": 0,
            "calendar_events_created": 0,
            "filtered_items": 0,
            "errors": 0,
            # Phase 2: Enhanced statistics
            "duplicate_items_removed": 0,
            "total_processing_time": 0.0,
            "average_response_time": 0.0,
            "performance_grade": "N/A",
        }

    def _import_modules(self):
        """必要なモジュールを遅延インポート"""
        if self._collectors is None:
            from modules.anime_anilist import AniListCollector
            from modules.calendar_integration import GoogleCalendarManager
            from modules.filter_logic import ContentFilter
            from modules.mailer import EmailTemplateGenerator, GmailNotifier
            from modules.manga_rss import MangaRSSCollector

            # 設定を辞書形式で渡す
            config_dict = self.config._config_data if hasattr(self.config, "_config_data") else {}

            self._collectors = {
                "anilist": AniListCollector(config_dict),
                "manga_rss": MangaRSSCollector(self.config),
                # 'syoboi': syoboi_calendar.SyoboiCollector(self.config)  # 将来実装
            }
            self._filter = ContentFilter(self.config)
            self._mailer = GmailNotifier(self.config)
            self._calendar = GoogleCalendarManager(self.config)
            self._email_generator = EmailTemplateGenerator(self.config)

            self.logger.info("すべてのモジュールを初期化しました")

    def collect_information(self) -> List[Dict[str, Any]]:
        """
        各種ソースから情報収集 - Phase 2 Performance Optimized

        Returns:
            List[Dict[str, Any]]: 収集した作品・リリース情報のリスト
        """
        self.logger.info("📡 情報収集を開始します... (Phase 2 最適化版)")
        self._import_modules()

        # Phase 2: Performance monitoring integration
        from modules.monitoring import add_monitoring_alert, record_api_performance

        all_items = []
        collection_start_time = time.time()

        for source_name, collector in self._collectors.items():
            source_start_time = time.time()
            try:
                self.logger.info(f"  {source_name} から情報収集中...")

                if source_name == "anilist":
                    items = collector.collect()
                else:
                    items = collector.collect()

                source_duration = time.time() - source_start_time

                if items:
                    self.logger.info(
                        f"  {source_name}: {len(items)} 件の情報を取得 (時間: {source_duration:.2f}秒)"
                    )
                    all_items.extend(items)
                    self.statistics["processed_sources"] += 1

                    # Performance monitoring
                    record_api_performance(source_name.replace("_", ""), source_duration, True)
                else:
                    self.logger.warning(
                        f"  {source_name}: データが取得できませんでした (時間: {source_duration:.2f}秒)"
                    )
                    record_api_performance(source_name.replace("_", ""), source_duration, False)

                # Adaptive rate limiting based on performance
                if source_duration > 5.0:
                    self.logger.info(
                        f"  {source_name} のレスポンスが遅いため、長めの待機時間を設定"
                    )
                    time.sleep(3)  # Longer wait for slow services
                else:
                    time.sleep(1)  # Normal rate limiting

            except Exception as e:
                source_duration = time.time() - source_start_time
                self.logger.error(
                    f"  {source_name} でエラーが発生: {e} (時間: {source_duration:.2f}秒)"
                )
                self.statistics["errors"] += 1

                # Performance monitoring for errors
                record_api_performance(source_name.replace("_", ""), source_duration, False)
                add_monitoring_alert(f"データ収集エラー: {source_name} - {e}", "ERROR")

                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug(traceback.format_exc())

        total_collection_time = time.time() - collection_start_time
        self.logger.info(
            f"📡 情報収集完了: 総計 {len(all_items)} 件 (総時間: {total_collection_time:.2f}秒)"
        )

        # Performance analysis and alerting
        if total_collection_time > 60:  # More than 1 minute
            add_monitoring_alert(f"情報収集が遅い: {total_collection_time:.1f}秒", "WARNING")

        if len(all_items) == 0:
            add_monitoring_alert("情報収集でデータが0件", "WARNING")

        return all_items

    def process_and_filter_data(self, raw_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        データの正規化とフィルタリング

        Args:
            raw_items (List[Dict[str, Any]]): 収集した生データ

        Returns:
            List[Dict[str, Any]]: 処理済みデータ
        """
        self.logger.info("🔍 データ処理とフィルタリングを開始します...")
        self._import_modules()

        processed_items = []

        for item in raw_items:
            try:
                # NGキーワードフィルタリング
                if self._filter.should_filter(item):
                    self.logger.debug(f"フィルタリング除外: {item.get('title', '不明')}")
                    self.statistics["filtered_items"] += 1
                    continue

                processed_items.append(item)

            except Exception as e:
                self.logger.error(f"データ処理エラー: {e}")
                self.statistics["errors"] += 1

        self.logger.info(
            f"🔍 フィルタリング完了: {len(processed_items)} 件が残存 ({len(raw_items) - len(processed_items)} 件除外)"
        )
        return processed_items

    def save_to_database(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        データベースに保存し、新しいリリース情報を返す

        Args:
            items (List[Dict[str, Any]]): 処理済みデータ

        Returns:
            List[Dict[str, Any]]: 新しいリリース情報
        """
        self.logger.info("💾 データベース保存を開始します...")

        new_releases = []

        for item in items:
            try:
                # 作品の取得または作成
                work_id = self.db.get_or_create_work(
                    title=item.get("title", ""),
                    title_kana=item.get("title_kana"),
                    title_en=item.get("title_en"),
                    work_type=item.get("type", "unknown"),
                    official_url=item.get("official_url"),
                )

                if work_id:
                    # リリース情報の保存
                    release_id = self.db.create_release(
                        work_id=work_id,
                        release_type=item.get(
                            "release_type",
                            "episode" if item.get("type") == "anime" else "volume",
                        ),
                        number=item.get("number"),
                        platform=item.get("platform"),
                        release_date=item.get("release_date"),
                        source=item.get("source"),
                        source_url=item.get("source_url"),
                    )

                    if release_id:
                        # 新しいリリースとして追加
                        release_info = item.copy()
                        release_info["release_id"] = release_id
                        release_info["work_id"] = work_id
                        new_releases.append(release_info)
                        self.statistics["new_releases"] += 1

                if item.get("is_new_work", False):
                    self.statistics["new_works"] += 1

            except Exception as e:
                self.logger.error(f"データベース保存エラー: {e}")
                self.statistics["errors"] += 1

        self.logger.info(f"💾 データベース保存完了: {len(new_releases)} 件の新しいリリース")
        return new_releases

    def send_notifications(
        self, new_releases: List[Dict[str, Any]], force_send: bool = False
    ) -> bool:
        """
        メール通知とカレンダーイベントの作成（分散配信対応）

        Args:
            new_releases (List[Dict[str, Any]]): 新しいリリース情報
            force_send (bool): 強制送信フラグ（時刻に関係なく送信）

        Returns:
            bool: 通知処理が成功した場合True
        """
        if not new_releases:
            self.logger.info("📧 新しいリリースがないため、通知をスキップします")
            return True

        self.logger.info(f"📧 分散配信対応通知処理を開始: {len(new_releases)} 件")
        self._import_modules()

        # 配信計画の作成
        batches = self.email_scheduler.plan_delivery(new_releases)

        if not batches:
            self.logger.warning("📧 配信バッチが作成されませんでした")
            return False

        success = True
        sent_batches = 0

        try:
            # Gmail認証
            if not self._mailer.authenticate():
                self.logger.error("Gmail認証に失敗しました")
                return False

            # Calendar認証
            if not self._calendar.authenticate():
                self.logger.error("Google Calendar認証に失敗しました")
                return False

            # 各バッチの処理
            for batch in batches:
                should_send = force_send or self.email_scheduler.should_send_now(batch.schedule)

                if not should_send:
                    next_time = self.email_scheduler.get_next_delivery_time(batch.schedule)
                    self.logger.info(
                        f"📧 バッチ {batch.current_batch}/{batch.total_batches} は "
                        f"{batch.schedule.to_time_str()} 配信予定 (次回: {next_time.strftime('%m/%d %H:%M')})"
                    )
                    continue

                # バッチ配信実行
                batch_success = self._send_batch(batch)

                if batch_success:
                    sent_batches += 1
                    self.email_scheduler.mark_batch_sent(batch.batch_id)
                    self.logger.info(
                        f"✅ バッチ {batch.current_batch}/{batch.total_batches} "
                        f"配信完了 ({len(batch.releases)} 件)"
                    )
                else:
                    self.logger.error(
                        f"❌ バッチ {batch.current_batch}/{batch.total_batches} " "配信失敗"
                    )
                    success = False

            # 統計更新
            self.statistics["notifications_sent"] += sent_batches

            if sent_batches > 0:
                self.logger.info(f"📧 分散配信完了: {sent_batches}/{len(batches)} バッチ送信")
            else:
                self.logger.info("📧 配信時刻ではないため、バッチ送信をスキップ")

        except Exception as e:
            self.logger.error(f"分散配信処理エラー: {e}")
            success = False

        return success

    def _send_batch(self, batch) -> bool:
        """
        単一バッチの送信処理

        Args:
            batch: EmailBatch オブジェクト

        Returns:
            bool: 送信成功の場合True
        """
        try:
            if not self.dry_run:
                # メール通知の作成と送信
                notification = self._email_generator.generate_release_notification(
                    batch.releases, subject_prefix=batch.get_subject_prefix()
                )

                if not self._mailer.send_notification(notification):
                    self.logger.error(f"バッチ {batch.batch_id} のメール送信に失敗")
                    return False

                # カレンダーイベントの作成
                calendar_results = self._calendar.bulk_create_release_events(batch.releases)
                created_events = len([v for v in calendar_results.values() if v])

                if created_events > 0:
                    self.logger.info(f"✅ カレンダーイベントを {created_events} 件作成")
                    self.statistics["calendar_events_created"] += created_events

                # データベースの通知済みフラグ更新
                for release in batch.releases:
                    if "release_id" in release:
                        self.db.mark_release_notified(release["release_id"])

            else:
                self.logger.info(f"🔒 [DRY-RUN] バッチ {batch.batch_id} ({len(batch.releases)} 件)")

                # ドライラン用の詳細表示
                for release in batch.releases:
                    title = release.get("title", "不明なタイトル")
                    number = release.get("number", "")
                    platform = release.get("platform", "")
                    self.logger.info(f"  📧 [DRY-RUN] {title} {number} ({platform})")

            return True

        except Exception as e:
            self.logger.error(f"バッチ送信エラー: {e}")
            return False

    def cleanup_old_data(self):
        """古いデータのクリーンアップ"""
        try:
            # 設定から保持期間を取得（デフォルト: 30日）
            retention_days = self.config.get_value("database.backup_retention_days", 30)
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            cleaned_count = self.db.cleanup_old_releases(cutoff_date)
            if cleaned_count > 0:
                self.logger.info(f"🧹 {cleaned_count} 件の古いリリース情報を削除しました")

        except Exception as e:
            self.logger.error(f"データクリーンアップエラー: {e}")

    def _format_delivery_stats(self) -> str:
        """分散配信統計のフォーマット"""
        try:
            stats = self.email_scheduler.get_delivery_stats()
            return """総バッチ数: {stats['total_batches']}
  送信済みバッチ数: {stats['sent_batches']}
  未送信バッチ数: {stats['pending_batches']}
  完了率: {stats['completion_rate']:.1f}%
  最終更新: {stats['last_update']}"""
        except Exception:
            return "統計取得エラー"

    def generate_report(self) -> str:
        """実行結果レポートの生成 - Phase 2 Enhanced"""
        execution_time = datetime.now() - self.start_time

        # Phase 2: Enhanced monitoring integration
        from modules.monitoring import get_collection_health_status

        health_status = get_collection_health_status()

        # Calculate performance metrics
        items_per_second = (
            self.statistics["new_releases"] / execution_time.total_seconds()
            if execution_time.total_seconds() > 0
            else 0
        )
        error_rate = (
            self.statistics["errors"] / max(self.statistics["processed_sources"], 1)
        ) * 100

        report = """
{'=' * 60}
📊 Phase 2 実行結果レポート
{'=' * 60}
実行時間: {execution_time.total_seconds():.1f}秒
開始時刻: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎆 システムヘルスグレード: {health_status.get('system_health_grade', 'N/A')}

📈 処理統計:
  処理ソース数: {self.statistics['processed_sources']}
  新作品数: {self.statistics['new_works']}
  新リリース数: {self.statistics['new_releases']}
  フィルタリング除外数: {self.statistics['filtered_items']}
  🚀 処理速度: {items_per_second:.2f} リリース/秒

📧 通知統計:
  メール通知送信数: {self.statistics['notifications_sent']}
  カレンダーイベント作成数: {self.statistics['calendar_events_created']}

❌ エラー統計:
  エラー発生回数: {self.statistics['errors']}
  📉 エラー率: {error_rate:.1f}%

💾 データベース統計:
  総作品数: {self.db.get_work_stats().get('total', 0)}
  総リリース数: {self.db.get_work_stats().get('total_releases', 0)}
  未通知数: {len(self.db.get_unnotified_releases(100))}

📅 分散配信統計:
  {self._format_delivery_stats()}

📀 Phase 2 パフォーマンス指標:
  モニタリングアクティブ: {health_status.get('monitoring_active', False)}
  アクティブアラート: {health_status.get('active_alerts_count', 0)} 件
  パフォーマンストレンド: {health_status.get('performance_trend', 'N/A')}
"""

        # Add critical issues if any
        critical_issues = health_status.get("critical_issues", [])
        if critical_issues:
            report += """
⚠️ 重要な問題:
"""
            for issue in critical_issues[:5]:  # Show max 5 issues
                report += f"  • {issue}\n"

        # Add collection performance details
        collection_perf = health_status.get("collection_performance", {})
        if collection_perf:
            report += """
🔍 収集システムパフォーマンス:
"""
            for service, metrics in collection_perf.items():
                if any(v > 0 for v in metrics.values() if isinstance(v, (int, float))):
                    report += f"  {service}:\n"
                    if "requests" in metrics and metrics["requests"] > 0:
                        report += f"    リクエスト数: {metrics['requests']}\n"
                    if "feeds_processed" in metrics and metrics["feeds_processed"] > 0:
                        report += f"    処理フィード数: {metrics['feeds_processed']}\n"
                    if "queries" in metrics and metrics["queries"] > 0:
                        report += f"    クエリ数: {metrics['queries']}\n"
                    if "errors" in metrics:
                        report += f"    エラー数: {metrics['errors']}\n"

        report += f"\n{'=' * 60}\n"
        return report.strip()

    def run(self) -> bool:
        """
        メインの実行処理

        Returns:
            bool: 正常に完了した場合True
        """
        try:
            # ステップ1: 情報収集
            raw_items = self.collect_information()

            # ステップ2: データ処理とフィルタリング
            processed_items = self.process_and_filter_data(raw_items)

            # ステップ3: データベース保存
            new_releases = self.save_to_database(processed_items)

            # ステップ4: 通知処理
            force_send = getattr(self, "force_send", False)
            notification_success = self.send_notifications(new_releases, force_send=force_send)

            # ステップ5: クリーンアップ
            self.cleanup_old_data()

            # ステップ6: スケジューラーの古いデータクリーンアップ
            self.email_scheduler.cleanup_old_state()

            # レポート生成
            report = self.generate_report()
            self.logger.info(report)

            if self.statistics["errors"] > 0:
                self.logger.warning(f"⚠️ {self.statistics['errors']} 件のエラーが発生しました")

            success = notification_success and self.statistics["errors"] == 0

            if success:
                self.logger.info("✅ すべての処理が正常に完了しました")
            else:
                self.logger.error("❌ 処理中にエラーが発生しました")

            return success

        except KeyboardInterrupt:
            self.logger.info("🛑 ユーザーによって処理が中断されました")
            return False
        except Exception as e:
            self.logger.error(f"💥 予期しないエラーが発生しました: {e}")
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(traceback.format_exc())
            return False
        finally:
            # リソースのクリーンアップ
            try:
                if hasattr(self, "db") and self.db:
                    self.db.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # リソースのクリーンアップ
        try:
            if hasattr(self, "db") and self.db:
                self.db.close()
        except Exception:
            pass


def signal_handler(signum, frame):
    """シグナルハンドラー"""
    logger.info("\n🛑 終了シグナルを受信しました。処理を停止しています...")
    sys.exit(0)


def main():
    """メイン関数"""
    # シグナルハンドラーの設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 引数解析
    parser = argparse.ArgumentParser(
        description="アニメ・マンガ情報配信システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""使用例:
  python3 release_notifier.py                    # 通常実行
  python3 release_notifier.py --dry-run          # ドライラン（通知なし）
  python3 release_notifier.py --verbose          # 詳細ログ
  python3 release_notifier.py --force-send       # 強制送信（時刻無視）
  python3 release_notifier.py --config custom.json --dry-run --verbose

分散配信について:
  ・100件以上のリリース: 2回分散（朝8時、夜20時）
  ・200件以上のリリース: 3回分散（朝8時、昼12時、夜20時）
  ・日本時間（Asia/Tokyo）で配信""",
    )

    parser.add_argument("--config", type=str, help="設定ファイルのパス (デフォルト: config.json)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ドライランモード（実際の通知は送信しない）",
    )
    parser.add_argument("--verbose", action="store_true", help="詳細ログを出力")
    parser.add_argument(
        "--force-send", action="store_true", help="時刻に関係なく強制的に通知を送信"
    )

    args = parser.parse_args()

    # 環境変数からログレベルを設定
    if args.verbose:
        import os

        os.environ["LOG_LEVEL"] = "DEBUG"

    exit_code = 0

    try:
        # システムの実行
        with ReleaseNotifierSystem(
            config_path=args.config, dry_run=args.dry_run, force_send=args.force_send
        ) as system:
            success = system.run()
            exit_code = 0 if success else 1

    except Exception as e:
        logger.error(f"システム初期化エラー: {e}")
        exit_code = 2

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
