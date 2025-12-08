"""
Distributed Tracing Module
OpenTelemetry統合とJaegerエクスポーター設定
"""

import logging
import functools
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor
    from opentelemetry.trace import Status, StatusCode
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

logger = logging.getLogger(__name__)

# グローバルトレーサー
_tracer: Optional[trace.Tracer] = None
_initialized = False


def init_tracing(
    service_name: str = "mangaanime-info-delivery",
    jaeger_host: str = "localhost",
    jaeger_port: int = 6831,
    enable_flask: bool = True,
    enable_requests: bool = True,
    enable_sqlite: bool = True
) -> bool:
    """
    分散トレーシングを初期化

    Args:
        service_name: サービス名
        jaeger_host: Jaegerホスト
        jaeger_port: Jaegerポート
        enable_flask: Flask自動計装を有効化
        enable_requests: Requests自動計装を有効化
        enable_sqlite: SQLite自動計装を有効化

    Returns:
        初期化成功フラグ
    """
    global _tracer, _initialized

    if not TRACING_AVAILABLE:
        logger.warning("OpenTelemetry not available. Tracing disabled.")
        return False

    if _initialized:
        logger.info("Tracing already initialized.")
        return True

    try:
        # リソース定義
        resource = Resource(attributes={
            SERVICE_NAME: service_name
        })

        # トレーサープロバイダー設定
        provider = TracerProvider(resource=resource)

        # Jaegerエクスポーター設定
        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_host,
            agent_port=jaeger_port,
        )

        # スパンプロセッサー追加
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

        # グローバルトレーサープロバイダー設定
        trace.set_tracer_provider(provider)

        # トレーサー取得
        _tracer = trace.get_tracer(__name__)

        # 自動計装
        if enable_requests:
            RequestsInstrumentor().instrument()
            logger.info("Requests instrumentation enabled")

        if enable_sqlite:
            SQLite3Instrumentor().instrument()
            logger.info("SQLite3 instrumentation enabled")

        _initialized = True
        logger.info(f"Tracing initialized: service={service_name}, jaeger={jaeger_host}:{jaeger_port}")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")
        return False


def init_flask_tracing(app):
    """Flask自動計装を初期化"""
    if not TRACING_AVAILABLE:
        logger.warning("OpenTelemetry not available. Flask tracing disabled.")
        return False

    try:
        FlaskInstrumentor().instrument_app(app)
        logger.info("Flask instrumentation enabled")
        return True
    except Exception as e:
        logger.error(f"Failed to instrument Flask: {e}")
        return False


def get_tracer() -> Optional[trace.Tracer]:
    """現在のトレーサーを取得"""
    return _tracer


@contextmanager
def trace_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL
):
    """
    トレーシングスパンコンテキストマネージャー

    Args:
        name: スパン名
        attributes: スパン属性
        kind: スパン種別

    Yields:
        スパンオブジェクト
    """
    if not _tracer or not _initialized:
        # トレーシング無効時はダミーコンテキスト
        yield None
        return

    with _tracer.start_as_current_span(name, kind=kind) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))

        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def trace_function(span_name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    関数トレーシングデコレーター

    Args:
        span_name: スパン名（指定しない場合は関数名）
        attributes: スパン属性
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = span_name or f"{func.__module__}.{func.__name__}"

            with trace_span(name, attributes) as span:
                start_time = time.time()

                try:
                    result = func(*args, **kwargs)

                    if span:
                        span.set_attribute("function.duration_ms", (time.time() - start_time) * 1000)
                        span.set_status(Status(StatusCode.OK))

                    return result
                except Exception as e:
                    if span:
                        span.set_attribute("error", True)
                        span.set_attribute("error.type", type(e).__name__)
                        span.set_attribute("error.message", str(e))
                    raise

        return wrapper
    return decorator


class TracedOperation:
    """トレース可能な操作クラス"""

    def __init__(self, operation_name: str, operation_type: str = "operation"):
        self.operation_name = operation_name
        self.operation_type = operation_type
        self.span = None
        self.start_time = None

    def __enter__(self):
        if not _tracer or not _initialized:
            return self

        self.start_time = time.time()
        self.span = _tracer.start_span(self.operation_name)
        self.span.set_attribute("operation.type", self.operation_type)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.span:
            return

        duration_ms = (time.time() - self.start_time) * 1000
        self.span.set_attribute("operation.duration_ms", duration_ms)

        if exc_type:
            self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
            self.span.record_exception(exc_val)
        else:
            self.span.set_status(Status(StatusCode.OK))

        self.span.end()

    def add_attribute(self, key: str, value: Any):
        """スパンに属性を追加"""
        if self.span:
            self.span.set_attribute(key, str(value))

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """スパンにイベントを追加"""
        if self.span:
            self.span.add_event(name, attributes or {})


# ドメイン固有のトレーシングヘルパー

@trace_function(attributes={"component": "anime_fetcher"})
def trace_anime_fetch(source: str):
    """アニメ情報取得トレーシング"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with trace_span(f"fetch_anime_{source}", {"source": source, "type": "anime"}):
                return func(*args, **kwargs)
        return wrapper
    return decorator


@trace_function(attributes={"component": "manga_fetcher"})
def trace_manga_fetch(source: str):
    """マンガ情報取得トレーシング"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with trace_span(f"fetch_manga_{source}", {"source": source, "type": "manga"}):
                return func(*args, **kwargs)
        return wrapper
    return decorator


@trace_function(attributes={"component": "notifier"})
def trace_notification(notification_type: str):
    """通知送信トレーシング"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with trace_span(f"send_{notification_type}", {"notification_type": notification_type}):
                return func(*args, **kwargs)
        return wrapper
    return decorator


@trace_function(attributes={"component": "calendar"})
def trace_calendar_operation(operation: str):
    """カレンダー操作トレーシング"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with trace_span(f"calendar_{operation}", {"operation": operation}):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def trace_db_query(table: str, operation: str):
    """データベースクエリトレーシング"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with trace_span(
                f"db_{operation}_{table}",
                {"db.table": table, "db.operation": operation, "component": "database"}
            ):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# エクスポート
__all__ = [
    'init_tracing',
    'init_flask_tracing',
    'get_tracer',
    'trace_span',
    'trace_function',
    'TracedOperation',
    'trace_anime_fetch',
    'trace_manga_fetch',
    'trace_notification',
    'trace_calendar_operation',
    'trace_db_query',
    'TRACING_AVAILABLE',
]
