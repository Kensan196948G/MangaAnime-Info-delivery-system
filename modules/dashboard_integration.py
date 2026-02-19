"""
Dashboard Integration Module
監視・統計ダッシュボード統合機能
"""

import logging
import sqlite3
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from .monitoring import MetricsCollector


# Note: dashboard_service循環参照を避けるため、遅延インポート
def get_dashboard_service():
    """Get dashboard service instance (lazy import to avoid circular dependency)"""
    from .dashboard import dashboard_service

    return dashboard_service


class DashboardIntegration:
    """ダッシュボード統合クラス - 既存のモジュールにメトリクス収集機能を追加"""

    def __init__(self, db_path: str = "db.sqlite3", config: Optional[Dict] = None):
        self.db_path = db_path
        self.config = config or {}
        # SystemMonitorは必要時に初期化
        self.performance_monitor = None
        self.metrics_collector = MetricsCollector() if MetricsCollector else None

    @contextmanager
    def track_operation(self, operation_name: str, component: str = "system"):
        """操作の実行時間を追跡し、ダッシュボードに記録"""
        start_time = time.time()
        success = False
        error_message = None

        try:
            yield
            success = True
        except Exception as e:
            error_message = str(e)
            logger.error(f"Operation {operation_name} failed: {e}")
            raise
        finally:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            # パフォーマンスメトリクスを記録
            try:
                service = get_dashboard_service()
                service.record_metric(
                    f"{operation_name}_duration",
                    duration_ms,
                    "timer",
                    source=component,
                    metadata={
                        "success": success,
                        "error_message": error_message,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                # システムヘルス状態を更新
                status = "healthy" if success else "error"
                service.update_system_health(
                    component,
                    status,
                    error_message,
                    performance_score=1.0 if success else 0.0,
                )
            except Exception as e:
                logger.warning(f"Failed to record dashboard metrics: {e}")

    def track_api_request(self, api_name: str, response_time_ms: float, success: bool):
        """API リクエストを追跡"""
        service = get_dashboard_service()
        service.record_metric(
            f"{api_name}_response_time",
            response_time_ms,
            "timer",
            source=f"{api_name}_api",
            metadata={"success": success, "timestamp": datetime.now().isoformat()},
        )

        # 成功/失敗カウンターも更新
        metric_name = f"{api_name}_{'success' if success else 'error'}"
        service.record_metric(metric_name, 1, "counter", source=f"{api_name}_api")

    def track_rss_collection(self, source: str, success: bool, items_count: int = 0):
        """RSS収集結果を追跡"""
        # 成功/失敗を記録
        metric_name = f"rss_{'success' if success else 'error'}"
        service = get_dashboard_service()
        service.record_metric(
            metric_name,
            1,
            "counter",
            source=source,
            metadata={
                "items_collected": items_count,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # アイテム数も記録
        if success and items_count > 0:
            service = get_dashboard_service()
            service.record_metric("rss_items_collected", items_count, "counter", source=source)

    def track_database_operation(self, operation: str, duration_ms: float, rows_affected: int = 0):
        """データベース操作を追跡"""
        service = get_dashboard_service()
        service.record_metric(
            "db_query_time",
            duration_ms,
            "timer",
            source="database",
            metadata={
                "operation": operation,
                "rows_affected": rows_affected,
                "timestamp": datetime.now().isoformat(),
            },
        )

        service.record_metric(f"db_{operation}_count", 1, "counter", source="database")

    def track_notification_sent(
        self, notification_type: str, success: bool, recipient_count: int = 1
    ):
        """通知送信結果を追跡"""
        metric_name = f"notification_{'success' if success else 'error'}"
        service = get_dashboard_service()
        service.record_metric(
            metric_name,
            recipient_count,
            "counter",
            source=notification_type,
            metadata={
                "type": notification_type,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """パフォーマンス要約を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                since = datetime.now() - timedelta(hours=hours)

                # API パフォーマンス
                cursor = conn.execute(
                    """
                    SELECT
                        source,
                        AVG(metric_value) as avg_response_time,
                        MAX(metric_value) as max_response_time,
                        COUNT(*) as request_count
                    FROM dashboard_stats
                    WHERE metric_name LIKE '%_response_time'
                    AND timestamp > ?
                    GROUP BY source
                """,
                    (since,),
                )
                api_performance = [dict(row) for row in cursor.fetchall()]

                # RSS収集統計
                cursor = conn.execute(
                    """
                    SELECT
                        SUM(CASE WHEN metric_name = 'rss_success' THEN metric_value ELSE 0 END) as successes,
                        SUM(CASE WHEN metric_name = 'rss_error' THEN metric_value ELSE 0 END) as errors
                    FROM dashboard_stats
                    WHERE metric_name IN ('rss_success', 'rss_error')
                    AND timestamp > ?
                """,
                    (since,),
                )
                rss_stats = dict(cursor.fetchone() or {})

                # データベース統計
                cursor = conn.execute(
                    """
                    SELECT
                        AVG(metric_value) as avg_query_time,
                        COUNT(*) as total_queries
                    FROM dashboard_stats
                    WHERE metric_name = 'db_query_time'
                    AND timestamp > ?
                """,
                    (since,),
                )
                db_stats = dict(cursor.fetchone() or {})

                # 通知統計
                cursor = conn.execute(
                    """
                    SELECT
                        SUM(CASE WHEN metric_name = 'notification_success' THEN metric_value ELSE 0 END) as successful_notifications,
                        SUM(CASE WHEN metric_name = 'notification_error' THEN metric_value ELSE 0 END) as failed_notifications
                    FROM dashboard_stats
                    WHERE metric_name IN ('notification_success', 'notification_error')
                    AND timestamp > ?
                """,
                    (since,),
                )
                notification_stats = dict(cursor.fetchone() or {})

                return {
                    "api_performance": api_performance,
                    "rss_stats": rss_stats,
                    "database_stats": db_stats,
                    "notification_stats": notification_stats,
                    "period_hours": hours,
                    "generated_at": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {}

    def cleanup_old_metrics(self, days: int = 30):
        """古いメトリクスデータをクリーンアップ"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM dashboard_stats
                    WHERE timestamp < ?
                """,
                    (cutoff_date,),
                )

                deleted_count = cursor.rowcount
                logger.info(f"Cleaned up {deleted_count} old metric records")

                # システムヘルスの古いレコードもクリーンアップ
                cursor = conn.execute(
                    """
                    DELETE FROM system_health
                    WHERE last_check < ?
                """,
                    (cutoff_date,),
                )

                deleted_health_count = cursor.rowcount
                logger.info(f"Cleaned up {deleted_health_count} old health records")

                return {
                    "metrics_deleted": deleted_count,
                    "health_deleted": deleted_health_count,
                }

        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")
            return {}


# グローバルインスタンス
dashboard_integration = DashboardIntegration()


# デコレータ関数
def track_performance(operation_name: str, component: str = "system"):
    """パフォーマンス追跡デコレータ"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            with dashboard_integration.track_operation(operation_name, component):
                return func(*args, **kwargs)

        return wrapper

    return decorator
