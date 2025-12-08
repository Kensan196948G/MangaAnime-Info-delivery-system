"""
Prometheus Metrics Module
カスタムメトリクス定義とFlask統合
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, REGISTRY
from prometheus_client import CollectorRegistry, multiprocess, CONTENT_TYPE_LATEST
from flask import Response
import time
import functools
import logging
import psutil
import os

logger = logging.getLogger(__name__)

# カスタムメトリクス定義

# リクエスト数カウンター
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# レイテンシヒストグラム
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

# エラー率カウンター
http_request_errors_total = Counter(
    'http_request_errors_total',
    'Total HTTP request errors',
    ['method', 'endpoint', 'error_type']
)

# データベース操作メトリクス
db_operations_total = Counter(
    'db_operations_total',
    'Total database operations',
    ['operation', 'table', 'status']
)

db_operation_duration_seconds = Histogram(
    'db_operation_duration_seconds',
    'Database operation duration',
    ['operation', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# API取得メトリクス
api_fetch_total = Counter(
    'api_fetch_total',
    'Total API fetch operations',
    ['source', 'status']
)

api_fetch_duration_seconds = Histogram(
    'api_fetch_duration_seconds',
    'API fetch duration',
    ['source'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)

# 通知メトリクス
notifications_sent_total = Counter(
    'notifications_sent_total',
    'Total notifications sent',
    ['type', 'status']
)

# カレンダー同期メトリクス
calendar_sync_total = Counter(
    'calendar_sync_total',
    'Total calendar sync operations',
    ['status']
)

calendar_events_created = Counter(
    'calendar_events_created',
    'Total calendar events created'
)

# アニメ・マンガ作品メトリクス
anime_works_total = Gauge(
    'anime_works_total',
    'Total anime works in database'
)

manga_works_total = Gauge(
    'manga_works_total',
    'Total manga works in database'
)

releases_pending = Gauge(
    'releases_pending',
    'Pending releases not notified',
    ['type']
)

# システムリソースメトリクス
system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes'
)

system_disk_usage = Gauge(
    'system_disk_usage_percent',
    'System disk usage percentage',
    ['path']
)

# アプリケーション情報
app_info = Info(
    'app',
    'Application information'
)

# アプリケーション情報の設定
app_info.info({
    'version': '1.0.0',
    'name': 'MangaAnime-Info-delivery-system',
    'python_version': '3.9+'
})


class MetricsCollector:
    """メトリクス収集クラス"""

    @staticmethod
    def collect_system_metrics():
        """システムメトリクスを収集"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_usage.set(cpu_percent)

            # メモリ使用量
            memory = psutil.virtual_memory()
            system_memory_usage.set(memory.used)

            # ディスク使用率
            disk = psutil.disk_usage('/')
            system_disk_usage.labels(path='/').set(disk.percent)

            logger.debug(f"System metrics collected: CPU={cpu_percent}%, Memory={memory.percent}%, Disk={disk.percent}%")
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    @staticmethod
    def update_work_counts(anime_count, manga_count):
        """作品数を更新"""
        anime_works_total.set(anime_count)
        manga_works_total.set(manga_count)

    @staticmethod
    def update_pending_releases(anime_pending, manga_pending):
        """未通知リリース数を更新"""
        releases_pending.labels(type='anime').set(anime_pending)
        releases_pending.labels(type='manga').set(manga_pending)


def track_request(func):
    """Flaskルートのメトリクス追跡デコレーター"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        method = 'GET'  # デフォルト
        endpoint = func.__name__

        start_time = time.time()
        status = '200'

        try:
            result = func(*args, **kwargs)
            if isinstance(result, tuple):
                status = str(result[1])
            return result
        except Exception as e:
            status = '500'
            http_request_errors_total.labels(
                method=method,
                endpoint=endpoint,
                error_type=type(e).__name__
            ).inc()
            raise
        finally:
            duration = time.time() - start_time
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

    return wrapper


def track_db_operation(operation, table):
    """データベース操作追跡デコレーター"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                logger.error(f"DB operation error: {operation} on {table} - {e}")
                raise
            finally:
                duration = time.time() - start_time
                db_operations_total.labels(
                    operation=operation,
                    table=table,
                    status=status
                ).inc()
                db_operation_duration_seconds.labels(
                    operation=operation,
                    table=table
                ).observe(duration)

        return wrapper
    return decorator


def track_api_fetch(source):
    """API取得追跡デコレーター"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                logger.error(f"API fetch error: {source} - {e}")
                raise
            finally:
                duration = time.time() - start_time
                api_fetch_total.labels(
                    source=source,
                    status=status
                ).inc()
                api_fetch_duration_seconds.labels(
                    source=source
                ).observe(duration)

        return wrapper
    return decorator


def record_notification(notification_type, status='success'):
    """通知送信を記録"""
    notifications_sent_total.labels(
        type=notification_type,
        status=status
    ).inc()


def record_calendar_sync(status='success'):
    """カレンダー同期を記録"""
    calendar_sync_total.labels(status=status).inc()


def record_calendar_event_created():
    """カレンダーイベント作成を記録"""
    calendar_events_created.inc()


def get_metrics():
    """メトリクスエンドポイント用のレスポンス生成"""
    try:
        # システムメトリクスを収集
        MetricsCollector.collect_system_metrics()

        # メトリクスを生成
        metrics_output = generate_latest(REGISTRY)
        return Response(metrics_output, mimetype=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response(f"Error generating metrics: {e}", status=500)


def init_metrics(app=None):
    """Flaskアプリケーションにメトリクスエンドポイントを追加"""
    if app:
        @app.route('/metrics')
        def metrics():
            return get_metrics()

        logger.info("Metrics endpoint initialized at /metrics")

    # 初期システムメトリクス収集
    MetricsCollector.collect_system_metrics()


# エクスポート
__all__ = [
    'MetricsCollector',
    'track_request',
    'track_db_operation',
    'track_api_fetch',
    'record_notification',
    'record_calendar_sync',
    'record_calendar_event_created',
    'get_metrics',
    'init_metrics',
    'http_requests_total',
    'http_request_duration_seconds',
    'http_request_errors_total',
    'db_operations_total',
    'db_operation_duration_seconds',
    'api_fetch_total',
    'api_fetch_duration_seconds',
    'notifications_sent_total',
    'calendar_sync_total',
    'calendar_events_created',
    'anime_works_total',
    'manga_works_total',
    'releases_pending',
    'system_cpu_usage',
    'system_memory_usage',
    'system_disk_usage',
]
