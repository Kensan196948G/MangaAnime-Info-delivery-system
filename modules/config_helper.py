"""
config.json アクセス用ヘルパー関数

新しいconfig.json構造に対応したヘルパークラス
従来の分散した設定を統一的にアクセスできるようにする
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
from typing import Any, Dict, List, Optional


class ConfigHelper:
    """設定ファイル読み込みヘルパー"""

    def __init__(self, config_path: str = "config.json"):
        """
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self):
        """設定ファイルを読み込み"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")

    def reload(self):
        """設定ファイルを再読み込み"""
        logger.info("Reloading configuration...")
        self.load()

    def save(self, backup: bool = True):
        """
        設定ファイルを保存

        Args:
            backup: バックアップを作成するか
        """
        if backup:
            backup_path = self.config_path.with_suffix(".json.bak")
            if self.config_path.exists():
                import shutil

                shutil.copy2(self.config_path, backup_path)
                logger.info(f"Backup created: {backup_path}")

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)
        logger.info(f"Configuration saved to {self.config_path}")

    @property
    def config(self) -> Dict[str, Any]:
        """設定全体を取得"""
        return self._config

    # ========================================
    # Email設定
    # ========================================

    @property
    def email_enabled(self) -> bool:
        """メール通知が有効か"""
        return self._config.get("notifications", {}).get("email", {}).get("enabled", False)

    @email_enabled.setter
    def email_enabled(self, value: bool):
        """メール通知の有効/無効を設定"""
        if "notifications" not in self._config:
            self._config["notifications"] = {}
        if "email" not in self._config["notifications"]:
            self._config["notifications"]["email"] = {}
        self._config["notifications"]["email"]["enabled"] = value

    @property
    def email_to(self) -> str:
        """送信先メールアドレス"""
        return self._config.get("notifications", {}).get("email", {}).get("to", "")

    @email_to.setter
    def email_to(self, value: str):
        """送信先メールアドレスを設定"""
        if "notifications" not in self._config:
            self._config["notifications"] = {}
        if "email" not in self._config["notifications"]:
            self._config["notifications"]["email"] = {}
        self._config["notifications"]["email"]["to"] = value

    @property
    def email_subject_prefix(self) -> str:
        """メール件名のプレフィックス"""
        return (
            self._config.get("notifications", {})
            .get("email", {})
            .get("subject_prefix", "[アニメ・マンガ情報]")
        )

    @property
    def email_send_time(self) -> str:
        """メール送信時刻"""
        return self._config.get("notifications", {}).get("email", {}).get("send_time", "08:00")

    @property
    def email_html_template(self) -> Optional[str]:
        """HTMLメールテンプレートファイル"""
        return self._config.get("notifications", {}).get("email", {}).get("html_template")

    # ========================================
    # Calendar設定
    # ========================================

    @property
    def calendar_enabled(self) -> bool:
        """カレンダー連携が有効か"""
        return self._config.get("notifications", {}).get("calendar", {}).get("enabled", False)

    @calendar_enabled.setter
    def calendar_enabled(self, value: bool):
        """カレンダー連携の有効/無効を設定"""
        if "notifications" not in self._config:
            self._config["notifications"] = {}
        if "calendar" not in self._config["notifications"]:
            self._config["notifications"]["calendar"] = {}
        self._config["notifications"]["calendar"]["enabled"] = value

    @property
    def calendar_id(self) -> str:
        """GoogleカレンダーID"""
        return (
            self._config.get("notifications", {}).get("calendar", {}).get("calendar_id", "primary")
        )

    @property
    def calendar_title_format(self) -> str:
        """カレンダーイベントのタイトルフォーマット"""
        return (
            self._config.get("notifications", {})
            .get("calendar", {})
            .get("event_title_format", "{title} {type} {number}")
        )

    @property
    def calendar_color_by_genre(self) -> bool:
        """ジャンル別の色分けが有効か"""
        return self._config.get("notifications", {}).get("calendar", {}).get("color_by_genre", True)

    @property
    def calendar_reminders(self) -> List[int]:
        """カレンダーリマインダー（分前）"""
        return (
            self._config.get("notifications", {})
            .get("calendar", {})
            .get("reminder_minutes", [1440, 60])
        )

    @property
    def calendar_default_duration(self) -> int:
        """デフォルトイベント時間（分）"""
        return (
            self._config.get("notifications", {})
            .get("calendar", {})
            .get("default_duration_minutes", 30)
        )

    # ========================================
    # Filters設定
    # ========================================

    @property
    def ng_keywords(self) -> List[str]:
        """NGキーワードリスト"""
        return self._config.get("filters", {}).get("ng_keywords", [])

    @property
    def min_rating(self) -> Optional[float]:
        """最低評価（AniListスコア）"""
        return self._config.get("filters", {}).get("min_rating")

    @property
    def excluded_genres(self) -> List[str]:
        """除外ジャンルリスト"""
        return self._config.get("filters", {}).get("excluded_genres", [])

    @property
    def filter_apply_to_description(self) -> bool:
        """説明文にもフィルタを適用するか"""
        return self._config.get("filters", {}).get("apply_to_description", True)

    @property
    def filter_case_sensitive(self) -> bool:
        """フィルタで大文字小文字を区別するか"""
        return self._config.get("filters", {}).get("case_sensitive", False)

    # ========================================
    # Sources設定
    # ========================================

    @property
    def anime_sources(self) -> List[str]:
        """アニメ情報ソースリスト"""
        return self._config.get("sources", {}).get("anime", [])

    @property
    def manga_sources(self) -> List[str]:
        """マンガ情報ソースリスト"""
        return self._config.get("sources", {}).get("manga", [])

    @property
    def streaming_sources(self) -> List[str]:
        """配信情報ソースリスト"""
        return self._config.get("sources", {}).get("streaming", [])

    @property
    def source_retry_on_failure(self) -> bool:
        """失敗時のリトライが有効か"""
        return self._config.get("sources", {}).get("retry_on_failure", True)

    @property
    def source_max_retries(self) -> int:
        """最大リトライ回数"""
        return self._config.get("sources", {}).get("max_retries", 3)

    @property
    def source_timeout_seconds(self) -> int:
        """ソース取得のタイムアウト（秒）"""
        return self._config.get("sources", {}).get("timeout_seconds", 30)

    # ========================================
    # Database設定
    # ========================================

    @property
    def db_path(self) -> str:
        """データベースファイルのパス"""
        return self._config.get("database", {}).get("path", "db.sqlite3")

    @property
    def db_backup_enabled(self) -> bool:
        """データベース自動バックアップが有効か"""
        return self._config.get("database", {}).get("backup_enabled", True)

    @property
    def db_backup_interval_days(self) -> int:
        """データベースバックアップ間隔（日）"""
        return self._config.get("database", {}).get("backup_interval_days", 7)

    @property
    def db_backup_path(self) -> Optional[str]:
        """データベースバックアップ保存先"""
        return self._config.get("database", {}).get("backup_path")

    @property
    def db_max_backups(self) -> int:
        """最大バックアップ数"""
        return self._config.get("database", {}).get("max_backups", 30)

    @property
    def db_vacuum_on_startup(self) -> bool:
        """起動時にVACUUMを実行するか"""
        return self._config.get("database", {}).get("vacuum_on_startup", False)

    # ========================================
    # Logging設定
    # ========================================

    @property
    def log_level(self) -> str:
        """ログレベル"""
        return self._config.get("logging", {}).get("level", "INFO")

    @property
    def log_file(self) -> str:
        """ログファイルのパス"""
        return self._config.get("logging", {}).get("file", "logs/system.log")

    @property
    def log_max_bytes(self) -> int:
        """ログファイルの最大サイズ（バイト）"""
        return self._config.get("logging", {}).get("max_bytes", 10485760)

    @property
    def log_backup_count(self) -> int:
        """ログファイルのバックアップ数"""
        return self._config.get("logging", {}).get("backup_count", 5)

    @property
    def log_format(self) -> str:
        """ログフォーマット"""
        return self._config.get("logging", {}).get(
            "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    @property
    def log_error_notification(self) -> bool:
        """エラー時のメール通知が有効か"""
        return self._config.get("logging", {}).get("error_notification", False)

    # ========================================
    # Scheduling設定
    # ========================================

    @property
    def cron_expression(self) -> str:
        """cron式"""
        return self._config.get("scheduling", {}).get("cron_expression", "0 8 * * *")

    @property
    def timezone(self) -> str:
        """タイムゾーン"""
        return self._config.get("scheduling", {}).get("timezone", "Asia/Tokyo")

    @property
    def max_execution_time_minutes(self) -> int:
        """最大実行時間（分）"""
        return self._config.get("scheduling", {}).get("max_execution_time_minutes", 30)

    @property
    def concurrent_workers(self) -> int:
        """並列ワーカー数"""
        return self._config.get("scheduling", {}).get("concurrent_workers", 4)

    # ========================================
    # API設定（オプション）
    # ========================================

    @property
    def api_anilist_rate_limit(self) -> int:
        """AniList APIのレート制限（回/分）"""
        return (
            self._config.get("api", {})
            .get("rate_limiting", {})
            .get("anilist_requests_per_minute", 85)
        )

    @property
    def api_rss_rate_limit(self) -> int:
        """RSS取得のレート制限（回/分）"""
        return (
            self._config.get("api", {}).get("rate_limiting", {}).get("rss_requests_per_minute", 30)
        )

    @property
    def api_cache_enabled(self) -> bool:
        """APIキャッシュが有効か"""
        return self._config.get("api", {}).get("cache", {}).get("enabled", True)

    @property
    def api_cache_ttl_seconds(self) -> int:
        """APIキャッシュのTTL（秒）"""
        return self._config.get("api", {}).get("cache", {}).get("ttl_seconds", 3600)

    # ========================================
    # ユーティリティメソッド
    # ========================================

    def get(self, key: str, default: Any = None) -> Any:
        """
        ドット記法でネストした設定値を取得

        Args:
            key: 'notifications.email.enabled' のようなドット記法のキー
            default: デフォルト値

        Returns:
            設定値

        Example:
            >>> config = ConfigHelper()
            >>> config.get('notifications.email.enabled')
            True
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any):
        """
        ドット記法でネストした設定値を設定

        Args:
            key: 'notifications.email.enabled' のようなドット記法のキー
            value: 設定する値

        Example:
            >>> config = ConfigHelper()
            >>> config.set('notifications.email.enabled', False)
        """
        keys = key.split(".")
        current = self._config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def validate(self) -> bool:
        """
        設定の妥当性を検証

        Returns:
            検証結果
        """
        # 必須セクションの確認
        required_sections = ["notifications", "filters", "sources"]
        for section in required_sections:
            if section not in self._config:
                logger.error(f"Missing required section: {section}")
                return False

        # メール設定の確認
        if self.email_enabled:
            if not self.email_to:
                logger.error("Email notification is enabled but 'to' is not set")
                return False
            if "@" not in self.email_to:
                logger.error(f"Invalid email address: {self.email_to}")
                return False

        # ソース設定の確認
        if not self.anime_sources and not self.manga_sources:
            logger.error("No data sources configured")
            return False

        logger.info("Configuration validation passed")
        return True


# ========================================
# グローバルインスタンス（シングルトン）
# ========================================

_config_helper: Optional[ConfigHelper] = None


def get_config(config_path: str = "config.json") -> ConfigHelper:
    """
    設定ヘルパーのシングルトンインスタンスを取得

    Args:
        config_path: 設定ファイルのパス（初回のみ有効）

    Returns:
        ConfigHelperインスタンス

    Example:
        >>> from config_helper import get_config
        >>> config = get_config()
        >>> if config.email_enabled:
        ...     send_email(config.email_to, "Test")
    """
    global _config_helper
    if _config_helper is None:
        _config_helper = ConfigHelper(config_path)
    return _config_helper


def reset_config():
    """シングルトンインスタンスをリセット（主にテスト用）"""
    global _config_helper
    _config_helper = None


# ========================================
# 使用例
# ========================================

if __name__ == "__main__":
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 設定を読み込み
    config = get_config()

    # 設定値の表示
    logger.info("=" * 60)
    logger.info("Configuration Summary")
    logger.info("=" * 60)
    logger.info(f"Email Enabled: {config.email_enabled}")
    logger.info(f"Email To: {config.email_to}")
    logger.info(f"Calendar Enabled: {config.calendar_enabled}")
    logger.info(f"NG Keywords: {', '.join(config.ng_keywords)}")
    logger.info(f"Anime Sources: {', '.join(config.anime_sources)}")
    logger.info(f"Manga Sources: {', '.join(config.manga_sources)}")
    logger.info(f"DB Path: {config.db_path}")
    logger.info(f"Log Level: {config.log_level}")
    logger.info("=" * 60)

    # 検証
    if config.validate():
        logger.info("✓ Configuration is valid")
    else:
        logger.info("✗ Configuration validation failed")
