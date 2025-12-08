"""
Dashboard module for monitoring and statistics visualization
統計・監視ダッシュボード機能
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, render_template, request

from .monitoring import MetricsCollector

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


class DashboardService:
    """ダッシュボードデータ提供サービス"""

    def __init__(self, db_path: str = "db.sqlite3", config: Optional[Dict] = None):
        self.db_path = db_path
        self.config = config or {}
        # SystemMonitorは必要時に初期化（configが必要）
        self.monitor = None
        self.metrics_collector = MetricsCollector() if MetricsCollector else None
        self._init_dashboard_tables()

    def _init_dashboard_tables(self):
        """ダッシュボード用テーブルの初期化"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS dashboard_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        metric_type TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        source TEXT,
                        metadata TEXT
                    )
                """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS system_health (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        component TEXT NOT NULL,
                        status TEXT CHECK(status IN ('healthy','warning','error')),
                        last_check DATETIME DEFAULT CURRENT_TIMESTAMP,
                        error_message TEXT,
                        performance_score REAL
                    )
                """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_dashboard_stats_timestamp
                    ON dashboard_stats(timestamp)
                """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_dashboard_stats_metric
                    ON dashboard_stats(metric_name, timestamp)
                """
                )
        except Exception as e:
            logger.error(f"Failed to initialize dashboard tables: {e}")

    def get_real_time_stats(self, hours: int = 24) -> Dict[str, Any]:
        """リアルタイム統計データを取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # 指定時間内のメトリクス取得
                since = datetime.now() - timedelta(hours=hours)
                cursor = conn.execute(
                    """
                    SELECT metric_name, metric_value, metric_type, timestamp, source
                    FROM dashboard_stats
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                """,
                    (since,),
                )

                metrics = [dict(row) for row in cursor.fetchall()]

                # システムヘルス状態を取得
                cursor = conn.execute(
                    """
                    SELECT component, status, last_check, error_message, performance_score
                    FROM system_health
                    ORDER BY last_check DESC
                """
                )

                health = [dict(row) for row in cursor.fetchall()]

                return {
                    "metrics": metrics,
                    "system_health": health,
                    "timestamp": datetime.now().isoformat(),
                    "period_hours": hours,
                }

        except Exception as e:
            logger.error(f"Failed to get real-time stats: {e}")
            return {"metrics": [], "system_health": [], "error": str(e)}

    def get_performance_overview(self) -> Dict[str, Any]:
        """パフォーマンス概要データを取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # AniList API統計
                cursor = conn.execute(
                    """
                    SELECT AVG(metric_value) as avg_response_time,
                           COUNT(*) as total_requests,
                           MAX(metric_value) as max_response_time
                    FROM dashboard_stats
                    WHERE metric_name = 'anilist_response_time'
                    AND timestamp > datetime('now', '-24 hours')
                """
                )
                anilist_stats = dict(cursor.fetchone() or {})

                # RSS収集統計
                cursor = conn.execute(
                    """
                    SELECT
                        SUM(CASE WHEN metric_name = 'rss_success' THEN metric_value ELSE 0 END) as successes,
                        SUM(CASE WHEN metric_name = 'rss_error' THEN metric_value ELSE 0 END) as errors,
                        COUNT(DISTINCT source) as sources_checked
                    FROM dashboard_stats
                    WHERE metric_name IN ('rss_success', 'rss_error')
                    AND timestamp > datetime('now', '-24 hours')
                """
                )
                rss_stats = dict(cursor.fetchone() or {})

                # データベースパフォーマンス
                cursor = conn.execute(
                    """
                    SELECT AVG(metric_value) as avg_query_time,
                           COUNT(*) as total_queries
                    FROM dashboard_stats
                    WHERE metric_name = 'db_query_time'
                    AND timestamp > datetime('now', '-24 hours')
                """
                )
                db_stats = dict(cursor.fetchone() or {})

                # 通知統計
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) as total_notifications
                    FROM releases
                    WHERE notified = 1
                    AND created_at > datetime('now', '-24 hours')
                """
                )
                notification_stats = dict(cursor.fetchone() or {})

                return {
                    "anilist": anilist_stats,
                    "rss": rss_stats,
                    "database": db_stats,
                    "notifications": notification_stats,
                }

        except Exception as e:
            logger.error(f"Failed to get performance overview: {e}")
            return {}

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: str,
        source: str = None,
        metadata: Dict = None,
    ):
        """メトリクスを記録"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO dashboard_stats
                    (metric_name, metric_value, metric_type, source, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        name,
                        value,
                        metric_type,
                        source,
                        json.dumps(metadata) if metadata else None,
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to record metric {name}: {e}")

    def update_system_health(
        self,
        component: str,
        status: str,
        error_message: str = None,
        performance_score: float = None,
    ):
        """システムヘルス状態を更新"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO system_health
                    (component, status, error_message, performance_score)
                    VALUES (?, ?, ?, ?)
                """,
                    (component, status, error_message, performance_score),
                )
        except Exception as e:
            logger.error(f"Failed to update system health for {component}: {e}")

    def get_chart_data(self, metric_name: str, hours: int = 24) -> Dict[str, Any]:
        """Chart.js用データを生成"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                since = datetime.now() - timedelta(hours=hours)
                cursor = conn.execute(
                    """
                    SELECT metric_value, timestamp
                    FROM dashboard_stats
                    WHERE metric_name = ? AND timestamp > ?
                    ORDER BY timestamp ASC
                """,
                    (metric_name, since),
                )

                data = [dict(row) for row in cursor.fetchall()]

                labels = [row["timestamp"] for row in data]
                values = [row["metric_value"] for row in data]

                return {
                    "labels": labels,
                    "datasets": [
                        {
                            "label": metric_name,
                            "data": values,
                            "borderColor": "rgb(75, 192, 192)",
                            "backgroundColor": "rgba(75, 192, 192, 0.2)",
                            "tension": 0.1,
                        }
                    ],
                }

        except Exception as e:
            logger.error(f"Failed to get chart data for {metric_name}: {e}")
            return {"labels": [], "datasets": []}


# グローバルサービスインスタンス
dashboard_service = DashboardService()


@dashboard_bp.route("/")
def index():
    """ダッシュボードメインページ"""
    return render_template("dashboard/index.html")


@dashboard_bp.route("/api/stats")
def api_stats():
    """リアルタイム統計API"""
    hours = request.args.get("hours", 24, type=int)
    return jsonify(dashboard_service.get_real_time_stats(hours))


@dashboard_bp.route("/api/overview")
def api_overview():
    """パフォーマンス概要API"""
    return jsonify(dashboard_service.get_performance_overview())


@dashboard_bp.route("/api/chart/<metric_name>")
def api_chart_data(metric_name):
    """チャートデータAPI"""
    hours = request.args.get("hours", 24, type=int)
    return jsonify(dashboard_service.get_chart_data(metric_name, hours))


@dashboard_bp.route("/api/health")
def api_health():
    """システムヘルスAPI"""
    stats = dashboard_service.get_real_time_stats(1)  # 直近1時間
    return jsonify(
        {
            "status": "healthy",
            "components": stats.get("system_health", []),
            "timestamp": datetime.now().isoformat(),
        }
    )
