#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
設定管理モジュール（拡張版）

JSON設定ファイルと環境変数を統合した設定管理システム。
環境変数による設定のオーバーライドをサポート。

使用例:
    from modules.config_loader import ConfigLoader

    config = ConfigLoader()
    email = config.get('notification.email.recipients')
    if config.is_enabled('anime_sources.anilist'):
        # AniList APIを使用
        pass
"""

import json
import logging
import os

logger = logging.getLogger(__name__)
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv


class ConfigLoader:
    """
    設定管理クラス

    JSON設定ファイルと環境変数を統合し、
    階層的な設定へのアクセスを提供します。

    Attributes:
        config_path: 設定ファイルのパス
        _config: 読み込まれた設定データ
        _env_loaded: 環境変数の読み込み状態
    """

    def __init__(
        self,
        config_path: str = "config.json",
        env_file: Optional[str] = ".env",
        auto_load: bool = True,
    ):
        """
        Args:
            config_path: 設定ファイルのパス
            env_file: 環境変数ファイルのパス（None=読み込まない）
            auto_load: 初期化時に自動的に設定を読み込むか
        """
        self.config_path = Path(config_path)
        self.env_file = env_file
        self._config: Dict = {}
        self._env_loaded = False

        if auto_load:
            self.load()

    def load(self) -> Dict:
        """
        設定ファイルと環境変数を読み込む

        Returns:
            読み込まれた設定データ

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            json.JSONDecodeError: JSONのパースエラー
        """
        # 環境変数の読み込み
        if self.env_file and not self._env_loaded:
            env_path = Path(self.env_file)
            if env_path.exists():
                load_dotenv(env_path)
                self._env_loaded = True
                logger.info(f"Loaded environment variables from {self.env_file}")

        # JSONファイルの読み込み
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            self._config = self._get_default_config()
        else:
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                logger.info(f"Loaded config from {self.config_path}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse config file: {e}")
                raise

        # 環境変数による設定のオーバーライド
        self._apply_env_overrides()

        return self._config

    def _get_default_config(self) -> Dict:
        """
        デフォルト設定を返す

        Returns:
            デフォルト設定辞書
        """
        return {
            "anime_sources": {
                "anilist": {"enabled": True, "api_url": "https://graphql.anilist.co"},
                "syoboi": {"enabled": True, "api_url": "https://cal.syoboi.jp/db.php"},
            },
            "manga_sources": {"rss_feeds": []},
            "notification": {
                "email": {"enabled": True, "recipients": []},
                "calendar": {"enabled": True, "calendar_id": "primary"},
            },
            "filter": {"ng_keywords": []},
            "schedule": {"run_time": "08:00", "timezone": "Asia/Tokyo"},
        }

    def _apply_env_overrides(self):
        """環境変数による設定のオーバーライド"""
        # 通知メールアドレス
        if email := os.getenv("NOTIFICATION_EMAIL"):
            recipients = [e.strip() for e in email.split(",")]
            self._set_nested("notification.email.recipients", recipients)

        # データベースパス
        if db_path := os.getenv("DATABASE_PATH"):
            self._config["database_path"] = db_path

        # ログレベル
        if log_level := os.getenv("LOG_LEVEL"):
            self._config["log_level"] = log_level

        # NGキーワード
        if ng_keywords := os.getenv("NG_KEYWORDS"):
            keywords = [k.strip() for k in ng_keywords.split(",")]
            self._set_nested("filter.ng_keywords", keywords)

        # API URL
        if anilist_url := os.getenv("ANILIST_API_URL"):
            self._set_nested("anime_sources.anilist.api_url", anilist_url)

        if syoboi_url := os.getenv("SYOBOI_API_URL"):
            self._set_nested("anime_sources.syoboi.api_url", syoboi_url)

        # タイムゾーン
        if timezone := os.getenv("TIMEZONE"):
            self._set_nested("schedule.timezone", timezone)

        # テストモード
        if test_mode := os.getenv("TEST_MODE"):
            self._config["test_mode"] = test_mode.lower() == "true"

        logger.debug("Applied environment variable overrides")

    def get(self, key: str, default: Any = None) -> Any:
        """
        ドット記法で設定値を取得

        Args:
            key: ドット区切りの設定キー（例: 'notification.email.enabled'）
            default: キーが存在しない場合のデフォルト値

        Returns:
            設定値、存在しない場合はdefault

        Examples:
            >>> config = ConfigLoader()
            >>> config.get('notification.email.enabled')
            True
            >>> config.get('non.existent.key', 'default')
            'default'
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

        return value

    def _set_nested(self, key: str, value: Any):
        """
        ドット記法で設定値をセット

        Args:
            key: ドット区切りの設定キー
            value: 設定する値
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def is_enabled(self, source_path: str) -> bool:
        """
        ソースの有効/無効をチェック

        Args:
            source_path: ソースのパス（例: 'anime_sources.anilist'）

        Returns:
            有効な場合True

        Examples:
            >>> config = ConfigLoader()
            >>> config.is_enabled('anime_sources.anilist')
            True
        """
        return self.get(f"{source_path}.enabled", False)

    def get_api_url(self, source_path: str) -> Optional[str]:
        """
        APIのURLを取得

        Args:
            source_path: ソースのパス

        Returns:
            API URL、存在しない場合None
        """
        return self.get(f"{source_path}.api_url")

    def get_ng_keywords(self) -> List[str]:
        """
        NGキーワードのリストを取得

        Returns:
            NGキーワードのリスト
        """
        return self.get("filter.ng_keywords", [])

    def get_notification_emails(self) -> List[str]:
        """
        通知先メールアドレスのリストを取得

        Returns:
            メールアドレスのリスト
        """
        return self.get("notification.email.recipients", [])

    def get_database_path(self) -> str:
        """
        データベースファイルのパスを取得

        Returns:
            データベースパス
        """
        return self.get("database_path", "db.sqlite3")

    def get_log_level(self) -> str:
        """
        ログレベルを取得

        Returns:
            ログレベル文字列（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        """
        return self.get("log_level", "INFO")

    def is_test_mode(self) -> bool:
        """
        テストモードかどうかを確認

        Returns:
            テストモードの場合True
        """
        return self.get("test_mode", False)

    def save(self, path: Optional[str] = None):
        """
        現在の設定をJSONファイルに保存

        Args:
            path: 保存先パス（省略時は読み込み元と同じ）
        """
        save_path = Path(path) if path else self.config_path

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved config to {save_path}")

    def validate(self) -> List[str]:
        """
        設定の妥当性を検証

        Returns:
            検証エラーのリスト（空の場合はエラーなし）
        """
        errors = []

        # メールアドレスの検証
        import re

        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        for email in self.get_notification_emails():
            if not re.match(email_regex, email):
                errors.append(f"Invalid email address: {email}")

        # データベースパスの検証
        db_path = Path(self.get_database_path())
        if db_path.exists() and not db_path.is_file():
            errors.append(f"Database path is not a file: {db_path}")

        # タイムゾーンの検証
        try:
            import pytz

            timezone = self.get("schedule.timezone", "Asia/Tokyo")
            pytz.timezone(timezone)
        except Exception as e:
            errors.append(f"Invalid timezone: {e}")

        return errors

    def __repr__(self) -> str:
        """設定の文字列表現"""
        return f"ConfigLoader(config_path={self.config_path}, loaded={bool(self._config)})"


# グローバルインスタンス（シングルトンパターン）
_global_config: Optional[ConfigLoader] = None


def get_config(
    config_path: str = "config.json",
    env_file: Optional[str] = ".env",
    reload: bool = False,
) -> ConfigLoader:
    """
    グローバル設定インスタンスを取得

    Args:
        config_path: 設定ファイルのパス
        env_file: 環境変数ファイルのパス
        reload: 既存のインスタンスを再読み込みするか

    Returns:
        ConfigLoaderインスタンス

    Examples:
        >>> config = get_config()
        >>> email = config.get('notification.email.recipients')
    """
    global _global_config

    if _global_config is None or reload:
        _global_config = ConfigLoader(config_path, env_file)

    return _global_config


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Testing ConfigLoader...")

    # 設定の読み込み
    config = ConfigLoader()

    # 各種設定の取得
    logger.info("\n--- Configuration ---")
    logger.info(f"AniList enabled: {config.is_enabled('anime_sources.anilist')}")
    logger.info(f"AniList URL: {config.get_api_url('anime_sources.anilist')}")
    logger.info(f"NG Keywords: {config.get_ng_keywords()}")
    logger.info(f"Notification emails: {config.get_notification_emails()}")
    logger.info(f"Database path: {config.get_database_path()}")
    logger.info(f"Log level: {config.get_log_level()}")
    logger.info(f"Test mode: {config.is_test_mode()}")

    # 設定の検証
    logger.info("\n--- Validation ---")
    errors = config.validate()
    if errors:
        logger.info("Validation errors:")
        for error in errors:
            logger.info(f"  - {error}")
    else:
        logger.info("All validations passed!")

    # ネストされた設定の取得
    logger.info("\n--- Nested Config ---")
    logger.info(f"Schedule timezone: {config.get('schedule.timezone')}")
    logger.info(f"Calendar ID: {config.get('notification.calendar.calendar_id')}")
