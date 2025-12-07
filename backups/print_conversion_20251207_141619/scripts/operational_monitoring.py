from datetime import datetime
from typing import Any, Dict
#!/usr/bin/env python3
"""
運用監視・24時間365日システム対応監視スクリプト
Operational Monitoring and 24/7 System Health Check
"""

import time
import json
import logging
import sqlite3
import requests
import psutil
import subprocess
from pathlib import Path
import schedule
import sys

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs/operational_monitoring.log"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class OperationalMonitor:
    """運用監視クラス - 24時間365日システム監視"""

    def __init__(self):
        self.project_root = Path(__file__).parent.resolve()
        self.config_path = self.project_root / "config" / "config.json"
        self.db_path = self.project_root / "db.sqlite3"
        self.monitoring_active = True
        self.alert_thresholds = {
            "cpu_usage_max": 80.0,
            "memory_usage_max": 85.0,
            "disk_usage_max": 90.0,
            "api_response_time_max": 5000,  # ms
            "db_response_time_max": 1000,  # ms
        }
        self.last_health_check = datetime.now()
        self.health_status = {}

    def load_config(self) -> Dict:
        """設定ファイル読み込み"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"設定ファイル読み込みエラー: {e}")
            return {}

    def check_system_health(self) -> Dict[str, Any]:
        """システムヘルスチェック"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {},
            "alerts": [],
            "metrics": {},
        }

        try:
            # CPU使用率チェック
            cpu_usage = psutil.cpu_percent(interval=1)
            health_status["metrics"]["cpu_usage"] = cpu_usage
            health_status["components"]["cpu"] = (
                "healthy"
                if cpu_usage < self.alert_thresholds["cpu_usage_max"]
                else "warning"
            )

            if cpu_usage >= self.alert_thresholds["cpu_usage_max"]:
                health_status["alerts"].append(f"CPU使用率が高い: {cpu_usage:.1f}%")

            # メモリ使用率チェック
            memory = psutil.virtual_memory()
            health_status["metrics"]["memory_usage"] = memory.percent
            health_status["components"]["memory"] = (
                "healthy"
                if memory.percent < self.alert_thresholds["memory_usage_max"]
                else "warning"
            )

            if memory.percent >= self.alert_thresholds["memory_usage_max"]:
                health_status["alerts"].append(f"メモリ使用率が高い: {memory.percent:.1f}%")

            # ディスク使用率チェック
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            health_status["metrics"]["disk_usage"] = disk_percent
            health_status["components"]["disk"] = (
                "healthy"
                if disk_percent < self.alert_thresholds["disk_usage_max"]
                else "critical"
            )

            if disk_percent >= self.alert_thresholds["disk_usage_max"]:
                health_status["alerts"].append(f"ディスク使用率が高い: {disk_percent:.1f}%")

            # データベース接続チェック
            db_status = self.check_database_health()
            health_status["components"]["database"] = db_status["status"]
            health_status["metrics"]["db_response_time"] = db_status["response_time"]

            if (
                db_status["response_time"]
                >= self.alert_thresholds["db_response_time_max"]
            ):
                health_status["alerts"].append(
                    f"データベース応答が遅い: {db_status['response_time']:.1f}ms"
                )

            # 外部API接続チェック
            api_status = self.check_external_apis()
            health_status["components"]["external_apis"] = api_status["overall_status"]
            health_status["metrics"]["api_checks"] = api_status["individual_results"]

            # プロセス監視
            process_status = self.check_critical_processes()
            health_status["components"]["processes"] = process_status["status"]
            health_status["metrics"]["process_count"] = process_status["count"]

            # ログファイル監視
            log_status = self.check_log_files()
            health_status["components"]["logs"] = log_status["status"]
            health_status["metrics"]["log_size"] = log_status["total_size"]

            # 全体ステータス決定
            component_statuses = list(health_status["components"].values())
            if "critical" in component_statuses:
                health_status["overall_status"] = "critical"
            elif "warning" in component_statuses:
                health_status["overall_status"] = "warning"
            elif "error" in component_statuses:
                health_status["overall_status"] = "error"

        except Exception as e:
            logger.error(f"システムヘルスチェックエラー: {e}")
            health_status["overall_status"] = "error"
            health_status["alerts"].append(f"ヘルスチェック実行エラー: {str(e)}")

        self.health_status = health_status
        self.last_health_check = datetime.now()
        return health_status

    def check_database_health(self) -> Dict[str, Any]:
        """データベースヘルスチェック"""
        try:
            start_time = time.time()
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()

            # 基本的な接続テスト
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            # パフォーマンステスト
            cursor.execute("SELECT COUNT(*) FROM works")
            work_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM releases")
            release_count = cursor.fetchone()[0]

            conn.close()
            response_time = (time.time() - start_time) * 1000

            return {
                "status": (
                    "healthy"
                    if response_time < self.alert_thresholds["db_response_time_max"]
                    else "warning"
                ),
                "response_time": response_time,
                "table_count": table_count,
                "work_count": work_count,
                "release_count": release_count,
            }

        except Exception as e:
            logger.error(f"データベースヘルスチェックエラー: {e}")
            return {"status": "error", "response_time": 9999, "error": str(e)}

    def check_external_apis(self) -> Dict[str, Any]:
        """外部API接続チェック"""
        apis_to_check = [
            ("AniList GraphQL", "https://graphql.anilist.co", "POST"),
            ("dアニメストアRSS", "https://anime.dmkt-sp.jp/animestore/CF/rss/", "GET"),
            ("BookWalker RSS", "https://bookwalker.jp/rss/", "GET"),
        ]

        results = {}
        healthy_count = 0

        for api_name, url, method in apis_to_check:
            try:
                start_time = time.time()
                if method == "POST":
                    # AniList用の軽量クエリ
                    query = "query { Viewer { id } }"
                    response = requests.post(url, json={"query": query}, timeout=10)
                else:
                    response = requests.get(url, timeout=10)

                response_time = (time.time() - start_time) * 1000

                if response.status_code < 400:
                    results[api_name] = {
                        "status": "healthy",
                        "response_time": response_time,
                        "status_code": response.status_code,
                    }
                    healthy_count += 1
                else:
                    results[api_name] = {
                        "status": "warning",
                        "response_time": response_time,
                        "status_code": response.status_code,
                    }

            except Exception as e:
                results[api_name] = {"status": "error", "error": str(e)}

        overall_status = (
            "healthy"
            if healthy_count == len(apis_to_check)
            else "warning"
            if healthy_count > 0
            else "error"
        )

        return {
            "overall_status": overall_status,
            "individual_results": results,
            "healthy_apis": healthy_count,
            "total_apis": len(apis_to_check),
        }

    def check_critical_processes(self) -> Dict[str, Any]:
        """重要プロセス監視"""
        try:
            processes = []
            for proc in psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_percent"]
            ):
                try:
                    proc_info = proc.info
                    if "python" in proc_info["name"].lower():
                        processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return {
                "status": "healthy" if len(processes) > 0 else "warning",
                "count": len(processes),
                "python_processes": len(processes),
            }

        except Exception as e:
            logger.error(f"プロセスチェックエラー: {e}")
            return {"status": "error", "error": str(e), "count": 0}

    def check_log_files(self) -> Dict[str, Any]:
        """ログファイル監視"""
        try:
            log_dir = self.project_root / "logs"
            if not log_dir.exists():
                return {
                    "status": "warning",
                    "total_size": 0,
                    "message": "ログディレクトリが存在しません",
                }

            log_files = list(log_dir.glob("*.log"))
            total_size = sum(f.stat().st_size for f in log_files)

            # ログファイルサイズが100MBを超えた場合は警告
            status = "healthy" if total_size < 100 * 1024 * 1024 else "warning"

            return {
                "status": status,
                "total_size": total_size,
                "file_count": len(log_files),
                "largest_file": max((f.stat().st_size for f in log_files), default=0),
            }

        except Exception as e:
            logger.error(f"ログファイルチェックエラー: {e}")
            return {"status": "error", "error": str(e), "total_size": 0}

    def check_scheduled_tasks(self) -> Dict[str, Any]:
        """スケジュールタスク確認"""
        try:
            # crontab確認
            cron_result = subprocess.run(
                ["crontab", "-l"], capture_output=True, text=True
            )

            if cron_result.returncode == 0:
                cron_lines = [
                    line.strip()
                    for line in cron_result.stdout.split("\n")
                    if line.strip()
                ]
                anime_tasks = [
                    line
                    for line in cron_lines
                    if "release_notifier" in line or "anime" in line.lower()
                ]

                return {
                    "status": "healthy" if len(anime_tasks) > 0 else "warning",
                    "total_cron_jobs": len(cron_lines),
                    "anime_related_jobs": len(anime_tasks),
                    "jobs": anime_tasks,
                }
            else:
                return {
                    "status": "warning",
                    "message": "crontabの読み取りに失敗",
                    "error": cron_result.stderr,
                }

        except Exception as e:
            logger.error(f"スケジュールタスク確認エラー: {e}")
            return {"status": "error", "error": str(e)}

    def send_alert_notification(self, health_status: Dict[str, Any]) -> bool:
        """アラート通知送信"""
        try:
            if health_status["overall_status"] in ["critical", "error"]:
                # 重要なアラートの場合のみ通知
                alert_message = self.format_alert_message(health_status)
                logger.critical(f"システムアラート: {alert_message}")

                # ここでメール通知やSlack通知などを実装可能
                # 現在はログ出力のみ
                return True

        except Exception as e:
            logger.error(f"アラート通知エラー: {e}")
            return False

    def format_alert_message(self, health_status: Dict[str, Any]) -> str:
        """アラートメッセージフォーマット"""
        message_parts = [
            f"🚨 システムアラート - {health_status['overall_status'].upper()}",
            f"⏰ 時刻: {health_status['timestamp']}",
            "",
        ]

        if health_status.get("alerts"):
            message_parts.append("📋 アラート内容:")
            for alert in health_status["alerts"]:
                message_parts.append(f"  • {alert}")
            message_parts.append("")

        if health_status.get("components"):
            message_parts.append("🔍 コンポーネント状況:")
            for component, status in health_status["components"].items():
                status_emoji = (
                    "✅" if status == "healthy" else "⚠️" if status == "warning" else "❌"
                )
                message_parts.append(f"  {status_emoji} {component}: {status}")

        return "\n".join(message_parts)

    def generate_daily_report(self) -> Dict[str, Any]:
        """日次レポート生成"""
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "system_uptime": self.get_system_uptime(),
            "daily_summary": {},
            "performance_metrics": {},
            "recommendations": [],
        }

        # 最新のヘルスチェック結果を取得
        latest_health = self.check_system_health()

        report["daily_summary"] = {
            "overall_status": latest_health["overall_status"],
            "total_alerts": len(latest_health.get("alerts", [])),
            "healthy_components": sum(
                1
                for status in latest_health["components"].values()
                if status == "healthy"
            ),
            "total_components": len(latest_health["components"]),
        }

        report["performance_metrics"] = latest_health.get("metrics", {})

        # 推奨事項生成
        if latest_health["overall_status"] != "healthy":
            report["recommendations"].append("システムの詳細確認と対処が必要です")

        if latest_health["metrics"].get("cpu_usage", 0) > 70:
            report["recommendations"].append("CPU使用率が高いです。プロセスの最適化を検討してください")

        if latest_health["metrics"].get("memory_usage", 0) > 80:
            report["recommendations"].append("メモリ使用率が高いです。メモリ不足の対処が必要です")

        return report

    def get_system_uptime(self) -> str:
        """システム稼働時間取得"""
        try:
            uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{days}日 {hours}時間 {minutes}分"
        except Exception:
            return "取得できませんでした"

    def start_monitoring(self):
        """継続監視開始"""
        logger.info("🔄 継続監視を開始します")

        # スケジュール設定
        schedule.every(5).minutes.do(self.check_system_health)
        schedule.every().hour.do(self.check_scheduled_tasks)
        schedule.every().day.at("09:00").do(self.generate_daily_report)

        while self.monitoring_active:
            schedule.run_pending()
            time.sleep(60)  # 1分間隔でチェック

    def stop_monitoring(self):
        """監視停止"""
        self.monitoring_active = False
        logger.info("⏹️ 継続監視を停止しました")


def run_immediate_health_check():
    """即座にヘルスチェック実行"""
    monitor = OperationalMonitor()

    print("🔍 システムヘルスチェック実行中...")
    health_status = monitor.check_system_health()

    # 結果表示
    print("\n" + "=" * 60)
    print("🏥 システムヘルスチェック結果")
    print("=" * 60)
    print(f"📊 総合ステータス: {health_status['overall_status'].upper()}")
    print(f"⏰ チェック時刻: {health_status['timestamp']}")

    print("\n🔍 コンポーネント状況:")
    for component, status in health_status["components"].items():
        status_emoji = (
            "✅" if status == "healthy" else "⚠️" if status == "warning" else "❌"
        )
        print(f"  {status_emoji} {component}: {status}")

    if health_status.get("alerts"):
        print("\n🚨 アラート:")
        for alert in health_status["alerts"]:
            print(f"  • {alert}")

    print("\n📈 主要メトリクス:")
    metrics = health_status.get("metrics", {})
    if "cpu_usage" in metrics:
        print(f"  💻 CPU使用率: {metrics['cpu_usage']:.1f}%")
    if "memory_usage" in metrics:
        print(f"  🧠 メモリ使用率: {metrics['memory_usage']:.1f}%")
    if "disk_usage" in metrics:
        print(f"  💾 ディスク使用率: {metrics['disk_usage']:.1f}%")

    print("=" * 60)

    # 日次レポート生成
    daily_report = monitor.generate_daily_report()

    print("\n📋 日次サマリー:")
    print(
        f"  健全なコンポーネント: {daily_report['daily_summary']['healthy_components']}/{daily_report['daily_summary']['total_components']}"
    )
    print(f"  システム稼働時間: {daily_report['system_uptime']}")

    if daily_report.get("recommendations"):
        print("\n💡 推奨事項:")
        for rec in daily_report["recommendations"]:
            print(f"  • {rec}")

    # レポート保存
    report_path = (
        "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs/health_check_report.json"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(health_status, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n📄 詳細レポート: {report_path}")


def main():
    """メイン関数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        # デーモンモードで継続監視
        monitor = OperationalMonitor()
        try:
            monitor.start_monitoring()
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("\n👋 監視を停止しました")
    else:
        # 即座にヘルスチェック実行
        run_immediate_health_check()


if __name__ == "__main__":
    main()
