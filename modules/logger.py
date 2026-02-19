#!/usr/bin/env python3
"""
ログ管理モジュール
アニメ・マンガ情報配信システムのログ設定と管理
"""

import json
import logging
import logging.handlers
import sys

logger = logging.getLogger(__name__)
from datetime import datetime
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """JSON形式でログを出力するフォーマッター"""

    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをJSON形式でフォーマット"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 例外情報がある場合は追加
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # 追加属性があれば追加
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
            ]:
                log_entry[key] = str(value)

        return json.dumps(log_entry, ensure_ascii=False)


class ColorFormatter(logging.Formatter):
    """色付きログフォーマッター（コンソール出力用）"""

    # ANSIカラーコード
    COLORS = {
        "DEBUG": "\033[36m",  # シアン
        "INFO": "\033[32m",  # 緑
        "WARNING": "\033[33m",  # 黄
        "ERROR": "\033[31m",  # 赤
        "CRITICAL": "\033[35m",  # マゼンタ
        "RESET": "\033[0m",  # リセット
    }

    def format(self, record: logging.LogRecord) -> str:
        """色付きでログをフォーマット"""
        # 標準のフォーマット
        formatted = super().format(record)

        # ターミナルが色をサポートしている場合のみ色付け
        if hasattr(sys.stderr, "isatty") and sys.stderr.isatty():
            color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
            reset = self.COLORS["RESET"]
            return f"{color}{formatted}{reset}"

        return formatted


def setup_logging(config_manager, force_reload: bool = False) -> logging.Logger:
    """
    ログシステムの設定

    Args:
        config_manager: 設定管理インスタンス
        force_reload (bool): 強制的に再設定するかどうか

    Returns:
        logging.Logger: ルートロガー
    """
    root_logger = logging.getLogger()

    # すでに設定されている場合はスキップ（force_reloadが無効の場合）
    if not force_reload and root_logger.handlers:
        return root_logger

    # 既存のハンドラーをクリア
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    # ログレベル設定
    log_level = getattr(logging, config_manager.get_log_level().upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # ログファイル設定
    log_file_path = Path(config_manager.get_log_file_path())
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # ファイルハンドラー（ローテーション付き）
    max_bytes = config_manager.get_log_max_file_size_mb() * 1024 * 1024
    backup_count = config_manager.get_log_backup_count()

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )

    # ファイル用フォーマッター（通常の形式）
    file_format = config_manager.get_log_format()
    date_format = config_manager.get_log_date_format()
    file_formatter = logging.Formatter(file_format, date_format)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)  # ファイルには全レベルを記録

    root_logger.addHandler(file_handler)

    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)

    # コンソール用フォーマッター（色付き）
    console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_formatter = ColorFormatter(console_format, date_format)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)

    root_logger.addHandler(console_handler)

    # JSON出力ファイル（オプション）
    environment = config_manager.get_environment()
    if environment == "production":
        json_log_path = log_file_path.with_suffix(".json")
        json_handler = logging.handlers.RotatingFileHandler(
            filename=json_log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        json_formatter = JSONFormatter()
        json_handler.setFormatter(json_formatter)
        json_handler.setLevel(logging.INFO)  # JSONログはINFO以上

        root_logger.addHandler(json_handler)

    # 特定のモジュールのログレベル調整
    _configure_module_loggers()

    # 初期ログメッセージ
    logger.info(f"ログシステムが初期化されました (レベル: {config_manager.get_log_level()})")
    logger.info(f"ログファイル: {log_file_path}")

    return root_logger


def _configure_module_loggers():
    """特定のモジュールのログレベルを調整"""

    # 外部ライブラリのログレベルを調整（ノイズ削減）
    noisy_loggers = [
        "urllib3.connectionpool",
        "requests.packages.urllib3.connectionpool",
        "googleapiclient.discovery",
        "googleapiclient.discovery_cache",
        "google.auth.transport.requests",
        "google_auth_httplib2",
    ]

    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # HTTPライブラリの詳細ログ（DEBUGの場合のみ）
    if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
        logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)
        logging.getLogger("urllib3").setLevel(logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    """
    名前付きロガーを取得

    Args:
        name (str): ロガー名

    Returns:
        logging.Logger: ロガーインスタンス
    """
    return logging.getLogger(name)


def log_execution_time(logger: logging.Logger):
    """実行時間をログ出力するデコレータ"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger.debug(f"🚀 {func.__name__} 開始")

            try:
                result = func(*args, **kwargs)
                execution_time = datetime.now() - start_time
                logger.debug(f"✅ {func.__name__} 完了 (実行時間: {execution_time})")
                return result
            except Exception as e:
                execution_time = datetime.now() - start_time
                logger.error(f"❌ {func.__name__} エラー (実行時間: {execution_time}): {e}")
                raise

        return wrapper

    return decorator


def log_rate_limit(logger: logging.Logger, max_calls: int, time_window: int):
    """レート制限付きログ出力"""
    call_times = []

    def rate_limited_log(level: int, message: str, *args, **kwargs):
        now = datetime.now()

        # 時間枠内の呼び出しをフィルター
        call_times[:] = [t for t in call_times if (now - t).total_seconds() < time_window]

        if len(call_times) < max_calls:
            call_times.append(now)
            logger.log(level, message, *args, **kwargs)
        else:
            # レート制限に達した場合は、最初の制限メッセージのみログ出力
            if len(call_times) == max_calls:
                logger.warning(f"ログレート制限に達しました (最大 {max_calls} 回/{time_window}秒)")

    return rate_limited_log


class LogContext:
    """ログコンテキスト管理クラス"""

    def __init__(self, logger: logging.Logger, **context):
        """
        Args:
            logger (logging.Logger): ロガー
            **context: コンテキスト情報
        """
        self.logger = logger
        self.context = context

    def __enter__(self):
        # コンテキスト情報をロガーに追加
        for key, value in self.context.items():
            setattr(self.logger, key, value)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        # コンテキスト情報を削除
        for key in self.context.keys():
            if hasattr(self.logger, key):
                delattr(self.logger, key)


def with_log_context(logger: logging.Logger, **context):
    """
    ログコンテキストを設定するコンテキストマネージャー

    Usage:
        with with_log_context(logger, work_id=123, source="anilist"):
            logger.info("作品を処理中")  # コンテキスト情報が自動的に含まれる
    """
    return LogContext(logger, **context)


class PerformanceLogger:
    """パフォーマンス測定用ロガー"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timers = {}

    def start_timer(self, name: str):
        """タイマー開始"""
        self.timers[name] = datetime.now()
        self.logger.debug(f"⏱️ タイマー開始: {name}")

    def stop_timer(self, name: str) -> float:
        """タイマー終了"""
        if name not in self.timers:
            self.logger.warning(f"タイマー '{name}' が見つかりません")
            return 0.0

        elapsed = (datetime.now() - self.timers[name]).total_seconds()
        del self.timers[name]

        self.logger.info(f"⏱️ {name}: {elapsed:.3f}秒")
        return elapsed

    def log_memory_usage(self):
        """メモリ使用量をログ出力"""
        try:
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.logger.debug(f"🧠 メモリ使用量: {memory_mb:.1f}MB")
        except ImportError:
            self.logger.debug("psutilが利用できません。メモリ使用量は測定できません。")


# モジュールレベルでのデフォルトロガー
_module_logger = logging.getLogger(__name__)


def setup_test_logging():
    """テスト用の簡易ログ設定"""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


class StructuredLogger:
    """
    構造化ログ出力のためのラッパークラス

    システム全体で一貫した形式のログ出力を提供し、
    後からの解析・監視を容易にする。
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_api_call(
        self,
        source: str,
        url: str,
        status_code: int = None,
        response_time: float = None,
        error: str = None,
    ):
        """API呼び出しログ"""
        log_data = {
            "event_type": "api_call",
            "source": source,
            "url": url,
            "status_code": status_code,
            "response_time_ms": round(response_time * 1000) if response_time else None,
            "error": error,
        }

        if error:
            self.logger.error(f"API呼び出し失敗: {source} - {error}", extra=log_data)
        else:
            self.logger.info(f"API呼び出し成功: {source} ({status_code})", extra=log_data)

    def log_data_processing(
        self,
        stage: str,
        input_count: int,
        output_count: int,
        filtered_count: int = 0,
        duration: float = None,
    ):
        """データ処理ログ"""
        log_data = {
            "event_type": "data_processing",
            "stage": stage,
            "input_count": input_count,
            "output_count": output_count,
            "filtered_count": filtered_count,
            "duration_ms": round(duration * 1000) if duration else None,
        }

        self.logger.info(
            f"データ処理完了: {stage} ({input_count}→{output_count}, {filtered_count}件除外)",
            extra=log_data,
        )

    def log_notification_sent(
        self,
        notification_type: str,
        recipient: str,
        item_count: int,
        success: bool,
        error: str = None,
    ):
        """通知送信ログ"""
        log_data = {
            "event_type": "notification",
            "type": notification_type,
            "recipient": recipient,
            "item_count": item_count,
            "success": success,
            "error": error,
        }

        if success:
            self.logger.info(f"通知送信成功: {notification_type} ({item_count}件)", extra=log_data)
        else:
            self.logger.error(f"通知送信失敗: {notification_type} - {error}", extra=log_data)

    def log_system_event(self, event_type: str, message: str, **metadata):
        """システムイベントログ"""
        log_data = {
            "event_type": "system_event",
            "system_event_type": event_type,
            **metadata,
        }

        self.logger.info(f"システムイベント: {message}", extra=log_data)


def create_structured_logger(name: str) -> StructuredLogger:
    """構造化ロガーの作成"""
    return StructuredLogger(logging.getLogger(name))
