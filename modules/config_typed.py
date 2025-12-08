"""
設定管理モジュール（型ヒント付き）
"""

import json
import os
from typing import Any, Dict, List, Optional


class Config:
    """設定クラス"""

    def __init__(self, config_path: str = "config/config.json") -> None:
        """
        初期化

        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        設定ファイルを読み込み

        Returns:
            Dict[str, Any]: 設定内容
        """
        if not os.path.exists(self.config_path):
            return self._get_default_config()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config: Dict[str, Any] = json.load(f)
                return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"設定ファイル読み込みエラー: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        デフォルト設定を取得

        Returns:
            Dict[str, Any]: デフォルト設定
        """
        return {
            "database": {"path": "data/db.sqlite3"},
            "gmail": {
                "credentials_path": "config/credentials.json",
                "token_path": "config/token.json",
                "recipient": "your-email@example.com",
            },
            "calendar": {
                "credentials_path": "config/credentials.json",
                "token_path": "config/calendar_token.json",
                "calendar_id": "primary",
            },
            "anilist": {"api_url": "https://graphql.anilist.co", "rate_limit": 90},
            "ng_keywords": ["エロ", "R18", "成人向け", "BL", "百合", "ボーイズラブ"],
            "rss_feeds": {
                "bookwalker": "https://bookwalker.jp/series/rss/",
                "magapoke": "https://pocket.shonenmagazine.com/rss",
                "danime": "https://anime.dmkt-sp.jp/animestore/CF/rss/",
            },
            "schedule": {"daily_run_time": "08:00", "timezone": "Asia/Tokyo"},
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/app.log",
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得

        Args:
            key: 設定キー（ドット区切りで階層指定可能）
            default: デフォルト値

        Returns:
            Any: 設定値
        """
        keys = key.split(".")
        value: Any = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        設定値を設定

        Args:
            key: 設定キー（ドット区切りで階層指定可能）
            value: 設定値
        """
        keys = key.split(".")
        config: Dict[str, Any] = self.config

        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self) -> None:
        """設定ファイルを保存"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get_ng_keywords(self) -> List[str]:
        """
        NGキーワードリストを取得

        Returns:
            List[str]: NGキーワードのリスト
        """
        keywords = self.get("ng_keywords", [])
        if isinstance(keywords, list):
            return keywords
        return []

    def get_database_path(self) -> str:
        """
        データベースパスを取得

        Returns:
            str: データベースパス
        """
        path = self.get("database.path", "data/db.sqlite3")
        return str(path) if path else "data/db.sqlite3"

    def get_gmail_config(self) -> Dict[str, str]:
        """
        Gmail設定を取得

        Returns:
            Dict[str, str]: Gmail設定
        """
        gmail_config = self.get("gmail", {})
        if not isinstance(gmail_config, dict):
            gmail_config = {}

        return {
            "credentials_path": str(
                gmail_config.get("credentials_path", "config/credentials.json")
            ),
            "token_path": str(gmail_config.get("token_path", "config/token.json")),
            "recipient": str(gmail_config.get("recipient", "your-email@example.com")),
        }

    def get_calendar_config(self) -> Dict[str, str]:
        """
        カレンダー設定を取得

        Returns:
            Dict[str, str]: カレンダー設定
        """
        calendar_config = self.get("calendar", {})
        if not isinstance(calendar_config, dict):
            calendar_config = {}

        return {
            "credentials_path": str(
                calendar_config.get("credentials_path", "config/credentials.json")
            ),
            "token_path": str(calendar_config.get("token_path", "config/calendar_token.json")),
            "calendar_id": str(calendar_config.get("calendar_id", "primary")),
        }

    def get_rss_feeds(self) -> Dict[str, str]:
        """
        RSSフィード設定を取得

        Returns:
            Dict[str, str]: RSSフィードのURL辞書
        """
        feeds = self.get("rss_feeds", {})
        if isinstance(feeds, dict):
            return {k: str(v) for k, v in feeds.items()}
        return {}


# グローバル設定インスタンス
_config_instance: Optional[Config] = None


def get_config(config_path: str = "config/config.json") -> Config:
    """
    設定インスタンスを取得（シングルトン）

    Args:
        config_path: 設定ファイルのパス

    Returns:
        Config: 設定インスタンス
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = Config(config_path)

    return _config_instance


def reload_config(config_path: str = "config/config.json") -> Config:
    """
    設定を再読み込み

    Args:
        config_path: 設定ファイルのパス

    Returns:
        Config: 新しい設定インスタンス
    """
    global _config_instance
    _config_instance = Config(config_path)
    return _config_instance
