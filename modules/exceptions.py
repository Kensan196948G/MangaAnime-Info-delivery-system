"""
アニメ・マンガ情報配信システム - 統一例外階層

すべてのカスタム例外をこのモジュールで定義し、
エラーハンドリングの一貫性と保守性を向上させる。
"""

from typing import Optional, Any, Dict


class MangaAnimeSystemError(Exception):
    """
    システム全体のベース例外クラス

    すべてのカスタム例外はこのクラスを継承する。
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            message: エラーメッセージ
            error_code: エラーコード（オプション）
            details: 追加の詳細情報（オプション）
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """
        例外情報を辞書形式で返す

        Returns:
            Dict[str, Any]: 例外情報
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


# =============================================================================
# データ収集関連の例外
# =============================================================================


class DataCollectionError(MangaAnimeSystemError):
    """データ収集に関するエラー"""


class APIError(DataCollectionError):
    """API呼び出しの失敗"""


class AniListAPIError(APIError):
    """AniList API固有のエラー"""


class RateLimitExceeded(APIError):
    """APIレート制限超過"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        """
        Args:
            message: エラーメッセージ
            retry_after: リトライまでの秒数
        """
        super().__init__(message, error_code="RATE_LIMIT_EXCEEDED", **kwargs)
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after"] = retry_after


class CircuitBreakerOpen(APIError):
    """サーキットブレーカーがOPEN状態"""

    def __init__(
        self,
        message: str = "Circuit breaker is open",
        failure_count: Optional[int] = None,
        **kwargs,
    ):
        """
        Args:
            message: エラーメッセージ
            failure_count: 連続失敗回数
        """
        super().__init__(message, error_code="CIRCUIT_BREAKER_OPEN", **kwargs)
        if failure_count:
            self.details["failure_count"] = failure_count


class RSSCollectionError(DataCollectionError):
    """RSSフィード収集のエラー"""


class RSSParsingError(RSSCollectionError):
    """RSSフィードの解析エラー"""

    def __init__(self, message: str, feed_url: Optional[str] = None, **kwargs):
        """
        Args:
            message: エラーメッセージ
            feed_url: 問題が発生したフィードURL
        """
        super().__init__(message, error_code="RSS_PARSING_ERROR", **kwargs)
        if feed_url:
            self.details["feed_url"] = feed_url


class FeedUnavailableError(RSSCollectionError):
    """RSSフィードが利用不可"""

    def __init__(
        self,
        message: str,
        feed_url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs,
    ):
        """
        Args:
            message: エラーメッセージ
            feed_url: フィードURL
            status_code: HTTPステータスコード
        """
        super().__init__(message, error_code="FEED_UNAVAILABLE", **kwargs)
        if feed_url:
            self.details["feed_url"] = feed_url
        if status_code:
            self.details["status_code"] = status_code


# =============================================================================
# データベース関連の例外
# =============================================================================


class DatabaseError(MangaAnimeSystemError):
    """データベース操作に関するエラー"""


class DatabaseConnectionError(DatabaseError):
    """データベース接続エラー"""

    def __init__(
        self,
        message: str = "Failed to connect to database",
        db_path: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, error_code="DB_CONNECTION_ERROR", **kwargs)
        if db_path:
            self.details["db_path"] = db_path


class DatabaseIntegrityError(DatabaseError):
    """データベース整合性エラー"""

    def __init__(self, message: str, constraint: Optional[str] = None, **kwargs):
        """
        Args:
            message: エラーメッセージ
            constraint: 違反した制約名
        """
        super().__init__(message, error_code="DB_INTEGRITY_ERROR", **kwargs)
        if constraint:
            self.details["constraint"] = constraint


class RecordNotFoundError(DatabaseError):
    """レコードが見つからない"""

    def __init__(
        self,
        message: str,
        record_type: Optional[str] = None,
        record_id: Optional[Any] = None,
        **kwargs,
    ):
        """
        Args:
            message: エラーメッセージ
            record_type: レコードの種類（work, releaseなど）
            record_id: レコードID
        """
        super().__init__(message, error_code="RECORD_NOT_FOUND", **kwargs)
        if record_type:
            self.details["record_type"] = record_type
        if record_id:
            self.details["record_id"] = record_id


# =============================================================================
# 通知関連の例外
# =============================================================================


class NotificationError(MangaAnimeSystemError):
    """通知送信に関するエラー"""


class EmailNotificationError(NotificationError):
    """メール通知のエラー"""


class EmailAuthenticationError(EmailNotificationError):
    """Gmail認証エラー"""

    def __init__(self, message: str = "Gmail authentication failed", **kwargs):
        super().__init__(message, error_code="EMAIL_AUTH_ERROR", **kwargs)


class EmailSendError(EmailNotificationError):
    """メール送信エラー"""

    def __init__(self, message: str, recipient: Optional[str] = None, **kwargs):
        """
        Args:
            message: エラーメッセージ
            recipient: 送信先アドレス
        """
        super().__init__(message, error_code="EMAIL_SEND_ERROR", **kwargs)
        if recipient:
            self.details["recipient"] = recipient


class CalendarNotificationError(NotificationError):
    """カレンダー通知のエラー"""


class CalendarAuthenticationError(CalendarNotificationError):
    """Google Calendar認証エラー"""

    def __init__(
        self, message: str = "Google Calendar authentication failed", **kwargs
    ):
        super().__init__(message, error_code="CALENDAR_AUTH_ERROR", **kwargs)


class CalendarEventCreationError(CalendarNotificationError):
    """カレンダーイベント作成エラー"""

    def __init__(self, message: str, event_title: Optional[str] = None, **kwargs):
        """
        Args:
            message: エラーメッセージ
            event_title: イベントタイトル
        """
        super().__init__(message, error_code="CALENDAR_EVENT_ERROR", **kwargs)
        if event_title:
            self.details["event_title"] = event_title


# =============================================================================
# データ処理関連の例外
# =============================================================================


class DataProcessingError(MangaAnimeSystemError):
    """データ処理に関するエラー"""


class DataValidationError(DataProcessingError):
    """データバリデーションエラー"""

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        invalid_value: Optional[Any] = None,
        **kwargs,
    ):
        """
        Args:
            message: エラーメッセージ
            field_name: 問題のあるフィールド名
            invalid_value: 無効な値
        """
        super().__init__(message, error_code="DATA_VALIDATION_ERROR", **kwargs)
        if field_name:
            self.details["field_name"] = field_name
        if invalid_value is not None:
            self.details["invalid_value"] = str(invalid_value)


class FilteringError(DataProcessingError):
    """フィルタリング処理のエラー"""


class NormalizationError(DataProcessingError):
    """データ正規化のエラー"""

    def __init__(
        self, message: str, source_data: Optional[Dict[str, Any]] = None, **kwargs
    ):
        """
        Args:
            message: エラーメッセージ
            source_data: 問題のあるソースデータ
        """
        super().__init__(message, error_code="NORMALIZATION_ERROR", **kwargs)
        if source_data:
            self.details["source_data_type"] = type(source_data).__name__


# =============================================================================
# 設定関連の例外
# =============================================================================


class ConfigurationError(MangaAnimeSystemError):
    """設定に関するエラー"""


class ConfigFileNotFoundError(ConfigurationError):
    """設定ファイルが見つからない"""

    def __init__(self, message: str, config_path: Optional[str] = None, **kwargs):
        """
        Args:
            message: エラーメッセージ
            config_path: 設定ファイルパス
        """
        super().__init__(message, error_code="CONFIG_FILE_NOT_FOUND", **kwargs)
        if config_path:
            self.details["config_path"] = config_path


class InvalidConfigurationError(ConfigurationError):
    """設定内容が無効"""

    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        """
        Args:
            message: エラーメッセージ
            config_key: 問題のある設定キー
        """
        super().__init__(message, error_code="INVALID_CONFIGURATION", **kwargs)
        if config_key:
            self.details["config_key"] = config_key


# =============================================================================
# セキュリティ関連の例外
# =============================================================================


class SecurityError(MangaAnimeSystemError):
    """セキュリティに関するエラー"""


class AuthenticationError(SecurityError):
    """認証エラー"""

    def __init__(
        self,
        message: str = "Authentication failed",
        service: Optional[str] = None,
        **kwargs,
    ):
        """
        Args:
            message: エラーメッセージ
            service: 認証対象サービス
        """
        super().__init__(message, error_code="AUTHENTICATION_ERROR", **kwargs)
        if service:
            self.details["service"] = service


class AuthorizationError(SecurityError):
    """認可エラー"""

    def __init__(
        self,
        message: str = "Authorization failed",
        required_permission: Optional[str] = None,
        **kwargs,
    ):
        """
        Args:
            message: エラーメッセージ
            required_permission: 必要な権限
        """
        super().__init__(message, error_code="AUTHORIZATION_ERROR", **kwargs)
        if required_permission:
            self.details["required_permission"] = required_permission


class InputValidationError(SecurityError):
    """入力バリデーションエラー"""

    def __init__(self, message: str, input_type: Optional[str] = None, **kwargs):
        """
        Args:
            message: エラーメッセージ
            input_type: 入力の種類
        """
        super().__init__(message, error_code="INPUT_VALIDATION_ERROR", **kwargs)
        if input_type:
            self.details["input_type"] = input_type


# =============================================================================
# ユーティリティ関数
# =============================================================================


def handle_exception(
    exception: Exception,
    logger,
    reraise: bool = True,
    additional_context: Optional[Dict[str, Any]] = None,
) -> Optional[MangaAnimeSystemError]:
    """
    例外を適切に処理し、ログ出力する

    Args:
        exception: 発生した例外
        logger: ロガーインスタンス
        reraise: 例外を再発生させるか
        additional_context: 追加のコンテキスト情報

    Returns:
        MangaAnimeSystemError: 変換された例外（reraiseがFalseの場合）

    Raises:
        MangaAnimeSystemError: reraiseがTrueの場合、変換された例外を再発生
    """
    # すでにカスタム例外の場合
    if isinstance(exception, MangaAnimeSystemError):
        logger.error(f"System error: {exception}")
        if reraise:
            raise
        return exception

    # 既知の例外を変換
    error_mapping = {
        "sqlite3.IntegrityError": DatabaseIntegrityError,
        "sqlite3.OperationalError": DatabaseError,
        "requests.HTTPError": APIError,
        "requests.Timeout": APIError,
        "requests.ConnectionError": APIError,
    }

    exception_type = f"{exception.__class__.__module__}.{exception.__class__.__name__}"
    converted_error_class = error_mapping.get(exception_type, MangaAnimeSystemError)

    # 例外を変換
    converted_error = converted_error_class(
        message=str(exception), details=additional_context or {}
    )

    logger.error(f"Exception converted: {exception_type} -> {converted_error}")

    if reraise:
        raise converted_error from exception

    return converted_error
