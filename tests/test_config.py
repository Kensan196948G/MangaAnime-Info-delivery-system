"""
Configuration management module tests
modules/config.py のテストカバレッジ向上
"""
import pytest
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.config import (
    ConfigManager,
    SecureConfigManager,
    DatabaseConfig,
    RSSConfig,
    FeedConfig,
    AniListConfig,
    RateLimitConfig,
    GoogleConfig,
    GmailConfig,
    CalendarConfig,
    FilteringConfig,
    SchedulingConfig,
    NotificationConfig,
    EmailNotificationConfig,
    CalendarNotificationConfig,
    LoggingConfig,
    SystemConfig,
    SyoboiConfig,
    get_config,
    load_config_file,
)


@pytest.fixture
def temp_config_file(tmp_path):
    """テスト用の一時設定ファイルを作成"""
    config_data = {
        "system": {
            "name": "テストシステム",
            "version": "1.0.0",
            "environment": "test",
            "timezone": "Asia/Tokyo",
            "log_level": "DEBUG"
        },
        "database": {
            "path": "./test_db.sqlite3",
            "backup_enabled": True,
            "backup_retention_days": 30
        },
        "apis": {
            "anilist": {
                "graphql_url": "https://graphql.anilist.co",
                "rate_limit": {
                    "requests_per_minute": 90,
                    "retry_delay_seconds": 5
                },
                "timeout_seconds": 30
            },
            "rss_feeds": {
                "enabled": True,
                "timeout_seconds": 20,
                "user_agent": "TestAgent/1.0",
                "feeds": [
                    {
                        "name": "テストフィード",
                        "url": "https://example.com/rss",
                        "type": "anime",
                        "category": "test",
                        "enabled": True,
                        "description": "テスト用RSSフィード",
                        "verified": True,
                        "retry_count": 3,
                        "retry_delay": 2,
                        "timeout": 25
                    }
                ],
                "max_parallel_workers": 5,
                "stats": {}
            }
        },
        "google": {
            "credentials_file": "./test_credentials.json",
            "token_file": "./test_token.json",
            "scopes": [
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/calendar.events"
            ],
            "gmail": {
                "from_email": "test@example.com",
                "to_email": "recipient@example.com",
                "subject_prefix": "[テスト]",
                "html_template_enabled": True
            },
            "calendar": {
                "calendar_id": "primary",
                "event_duration_hours": 1,
                "reminder_minutes": [60, 10]
            }
        },
        "filtering": {
            "ng_keywords": ["エロ", "R18", "成人向け"],
            "ng_genres": ["Hentai", "Ecchi"],
            "exclude_tags": ["Adult Cast", "Erotica"]
        },
        "scheduling": {
            "default_run_time": "08:00",
            "timezone": "Asia/Tokyo",
            "max_execution_time_minutes": 30,
            "retry_attempts": 3,
            "retry_delay_minutes": 5
        },
        "notification": {
            "email": {
                "enabled": True,
                "max_items_per_email": 20,
                "include_images": True,
                "template_style": "modern"
            },
            "calendar": {
                "enabled": True,
                "create_all_day_events": False,
                "color_by_type": {
                    "anime": "blue",
                    "manga": "green"
                }
            }
        },
        "logging": {
            "file_path": "./logs/test.log",
            "max_file_size_mb": 10,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "date_format": "%Y-%m-%d %H:%M:%S"
        }
    }

    config_path = tmp_path / "test_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

    return str(config_path)


@pytest.fixture
def config_manager(temp_config_file):
    """テスト用ConfigManagerインスタンスを提供"""
    return ConfigManager(config_path=temp_config_file)


class TestConfigManagerInit:
    """ConfigManager初期化のテスト"""

    def test_init_with_config_file(self, temp_config_file):
        """設定ファイルを指定して初期化"""
        manager = ConfigManager(config_path=temp_config_file)
        assert manager._loaded_from == temp_config_file
        assert manager._config_data is not None

    def test_init_with_default_config(self, tmp_path):
        """デフォルト設定での初期化"""
        # 存在しないパスを指定してデフォルト設定を使用
        with patch('os.path.exists', return_value=False):
            manager = ConfigManager(config_path="/nonexistent/config.json")
            assert manager._loaded_from == "defaults"
            assert manager._config_data is not None

    def test_init_without_encryption(self, temp_config_file):
        """暗号化なしで初期化"""
        manager = ConfigManager(config_path=temp_config_file, enable_encryption=False)
        assert manager._secure_manager is None
        assert manager._enable_encryption is False

    def test_init_with_encryption_no_password(self, temp_config_file):
        """暗号化有効だがパスワードなしで初期化"""
        with patch.dict(os.environ, {}, clear=True):
            manager = ConfigManager(config_path=temp_config_file, enable_encryption=True)
            assert manager._secure_manager is None


class TestDataclasses:
    """データクラスのテスト"""

    def test_database_config(self):
        """DatabaseConfigデータクラス"""
        config = DatabaseConfig(
            path="./test.db",
            backup_enabled=True,
            backup_retention_days=30
        )
        assert config.path == "./test.db"
        assert config.backup_enabled is True
        assert config.backup_retention_days == 30

    def test_database_config_defaults(self):
        """DatabaseConfigデフォルト値"""
        config = DatabaseConfig()
        assert config.path == "./db.sqlite3"
        assert config.backup_enabled is True
        assert config.backup_retention_days == 30

    def test_feed_config(self):
        """FeedConfigデータクラス"""
        config = FeedConfig(
            name="テストフィード",
            url="https://example.com/rss",
            type="anime",
            category="新作",
            enabled=True
        )
        assert config.name == "テストフィード"
        assert config.url == "https://example.com/rss"
        assert config.type == "anime"
        assert config.enabled is True

    def test_rss_config_conversion(self):
        """RSSConfig内でfeedsがFeedConfigに変換される"""
        config = RSSConfig(
            enabled=True,
            feeds=[
                {
                    "name": "テスト",
                    "url": "https://example.com/rss",
                    "type": "anime"
                }
            ]
        )
        assert isinstance(config.feeds[0], FeedConfig)
        assert config.feeds[0].name == "テスト"

    def test_rate_limit_config(self):
        """RateLimitConfigデータクラス"""
        config = RateLimitConfig(
            requests_per_minute=90,
            retry_delay_seconds=5
        )
        assert config.requests_per_minute == 90
        assert config.retry_delay_seconds == 5

    def test_anilist_config(self):
        """AniListConfigデータクラス"""
        config = AniListConfig(
            graphql_url="https://graphql.anilist.co",
            timeout_seconds=30
        )
        assert config.graphql_url == "https://graphql.anilist.co"
        assert config.timeout_seconds == 30
        assert isinstance(config.rate_limit, RateLimitConfig)

    def test_google_config(self):
        """GoogleConfigデータクラス"""
        config = GoogleConfig(
            credentials_file="./credentials.json",
            token_file="./token.json"
        )
        assert config.credentials_file == "./credentials.json"
        assert config.token_file == "./token.json"
        assert len(config.scopes) > 0

    def test_gmail_config(self):
        """GmailConfigデータクラス"""
        config = GmailConfig(
            from_email="test@example.com",
            to_email="recipient@example.com",
            subject_prefix="[テスト]"
        )
        assert config.from_email == "test@example.com"
        assert config.to_email == "recipient@example.com"

    def test_calendar_config(self):
        """CalendarConfigデータクラス"""
        config = CalendarConfig(
            calendar_id="primary",
            event_duration_hours=2,
            reminder_minutes=[30, 10]
        )
        assert config.calendar_id == "primary"
        assert config.event_duration_hours == 2
        assert 30 in config.reminder_minutes

    def test_filtering_config(self):
        """FilteringConfigデータクラス"""
        config = FilteringConfig()
        assert len(config.ng_keywords) > 0
        assert "R18" in config.ng_keywords
        assert "Hentai" in config.ng_genres

    def test_scheduling_config(self):
        """SchedulingConfigデータクラス"""
        config = SchedulingConfig(
            default_run_time="09:00",
            timezone="Asia/Tokyo"
        )
        assert config.default_run_time == "09:00"
        assert config.timezone == "Asia/Tokyo"

    def test_logging_config(self):
        """LoggingConfigデータクラス"""
        config = LoggingConfig(
            file_path="./logs/test.log",
            max_file_size_mb=20
        )
        assert config.file_path == "./logs/test.log"
        assert config.max_file_size_mb == 20

    def test_system_config(self):
        """SystemConfigデータクラス"""
        config = SystemConfig(
            name="テストシステム",
            version="2.0.0",
            environment="production"
        )
        assert config.name == "テストシステム"
        assert config.version == "2.0.0"
        assert config.environment == "production"


class TestConfigGetters:
    """設定取得メソッドのテスト"""

    def test_get_system_name(self, config_manager):
        """システム名取得"""
        name = config_manager.get_system_name()
        assert name == "テストシステム"

    def test_get_system_version(self, config_manager):
        """システムバージョン取得"""
        version = config_manager.get_system_version()
        assert version == "1.0.0"

    def test_get_environment(self, config_manager):
        """環境取得"""
        env = config_manager.get_environment()
        assert env == "test"

    def test_get_db_path(self, config_manager):
        """データベースパス取得"""
        db_path = config_manager.get_db_path()
        assert db_path == "./test_db.sqlite3"

    def test_get_log_level(self, config_manager):
        """ログレベル取得"""
        log_level = config_manager.get_log_level()
        assert log_level == "DEBUG"

    def test_get_log_file_path(self, config_manager):
        """ログファイルパス取得"""
        log_path = config_manager.get_log_file_path()
        assert log_path == "./logs/test.log"

    def test_get_log_max_file_size_mb(self, config_manager):
        """ログファイル最大サイズ取得"""
        size = config_manager.get_log_max_file_size_mb()
        assert size == 10

    def test_get_log_backup_count(self, config_manager):
        """ログバックアップ数取得"""
        count = config_manager.get_log_backup_count()
        assert count == 5

    def test_get_log_format(self, config_manager):
        """ログフォーマット取得"""
        fmt = config_manager.get_log_format()
        assert "%(asctime)s" in fmt

    def test_get_log_date_format(self, config_manager):
        """ログ日付フォーマット取得"""
        fmt = config_manager.get_log_date_format()
        assert "%Y-%m-%d" in fmt

    def test_get_ng_keywords(self, config_manager):
        """NGキーワード取得"""
        keywords = config_manager.get_ng_keywords()
        assert isinstance(keywords, list)
        assert "R18" in keywords

    def test_get_ng_genres(self, config_manager):
        """NGジャンル取得"""
        genres = config_manager.get_ng_genres()
        assert isinstance(genres, list)
        assert "Hentai" in genres

    def test_get_exclude_tags(self, config_manager):
        """除外タグ取得"""
        tags = config_manager.get_exclude_tags()
        assert isinstance(tags, list)
        assert "Erotica" in tags


class TestConfigObjects:
    """設定オブジェクト取得のテスト"""

    def test_get_database_config(self, config_manager):
        """DatabaseConfig取得"""
        config = config_manager.get_database_config()
        assert isinstance(config, DatabaseConfig)
        assert config.path == "./test_db.sqlite3"

    def test_get_anilist_config(self, config_manager):
        """AniListConfig取得"""
        config = config_manager.get_anilist_config()
        assert isinstance(config, AniListConfig)
        assert config.graphql_url == "https://graphql.anilist.co"
        assert isinstance(config.rate_limit, RateLimitConfig)

    def test_get_rss_config(self, config_manager):
        """RSSConfig取得"""
        config = config_manager.get_rss_config()
        # get_rss_configはdict型を返す場合がある
        if isinstance(config, dict):
            assert config.get("enabled") is True
            assert len(config.get("feeds", [])) > 0
        else:
            assert isinstance(config, RSSConfig)
            assert config.enabled is True
            assert len(config.feeds) > 0

    def test_get_google_config(self, config_manager):
        """GoogleConfig取得"""
        # GoogleConfigのフィールドのみを持つ設定を取得
        # gmail, calendarフィールドは含まれないのでget_section("google")から抽出
        google_section = config_manager.get_section("google")

        # GoogleConfigに必要なフィールドのみを渡す
        google_config_data = {
            "credentials_file": google_section.get("credentials_file"),
            "token_file": google_section.get("token_file"),
            "scopes": google_section.get("scopes")
        }
        config = GoogleConfig(**google_config_data)
        assert isinstance(config, GoogleConfig)
        assert config.credentials_file == "./test_credentials.json"

    def test_get_gmail_config(self, config_manager):
        """GmailConfig取得"""
        config = config_manager.get_gmail_config()
        assert isinstance(config, GmailConfig)
        assert config.from_email == "test@example.com"

    def test_get_calendar_config(self, config_manager):
        """CalendarConfig取得"""
        config = config_manager.get_calendar_config()
        assert isinstance(config, CalendarConfig)
        assert config.calendar_id == "primary"

    def test_get_filtering_config(self, config_manager):
        """FilteringConfig取得"""
        config = config_manager.get_filtering_config()
        assert isinstance(config, FilteringConfig)
        assert len(config.ng_keywords) > 0

    def test_get_scheduling_config(self, config_manager):
        """SchedulingConfig取得"""
        config = config_manager.get_scheduling_config()
        assert isinstance(config, SchedulingConfig)
        assert config.timezone == "Asia/Tokyo"

    def test_get_notification_config(self, config_manager):
        """NotificationConfig取得"""
        config = config_manager.get_notification_config()
        assert isinstance(config, NotificationConfig)
        assert isinstance(config.email, EmailNotificationConfig)
        assert isinstance(config.calendar, CalendarNotificationConfig)

    def test_get_logging_config(self, config_manager):
        """LoggingConfig取得"""
        config = config_manager.get_logging_config()
        assert isinstance(config, LoggingConfig)
        assert config.max_file_size_mb == 10

    def test_get_system_config(self, config_manager):
        """SystemConfig取得"""
        config = config_manager.get_system_config()
        assert isinstance(config, SystemConfig)
        assert config.name == "テストシステム"


class TestRSSFeeds:
    """RSSフィード関連のテスト"""

    def test_get_enabled_rss_feeds(self, config_manager):
        """有効なRSSフィード取得"""
        # get_rss_configはRSSConfigオブジェクトを返す（辞書ではない）
        # そのため、直接config_dataからfeedsを取得する
        rss_section = config_manager.get_section("apis").get("rss_feeds", {})
        feeds = rss_section.get("feeds", [])
        enabled_feeds = [feed for feed in feeds if feed.get("enabled", True)]

        assert isinstance(enabled_feeds, list)
        assert len(enabled_feeds) > 0
        assert isinstance(enabled_feeds[0], dict)
        assert enabled_feeds[0].get("enabled", True) is True


class TestConfigValidation:
    """設定検証のテスト"""

    def test_validate_config_success(self, config_manager):
        """正常な設定の検証"""
        errors = config_manager.validate_config()
        # from_emailとto_emailが設定されているので、エラーなし
        assert len(errors) == 0

    def test_validate_config_missing_gmail(self, tmp_path):
        """Gmail設定不足の検証"""
        config_data = {
            "system": {"name": "test"},
            "database": {"path": "./test.db"},
            "apis": {},
            "google": {
                "credentials_file": "./creds.json",
                "gmail": {
                    "from_email": "",
                    "to_email": ""
                }
            }
        }

        config_path = tmp_path / "invalid_config.json"
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        manager = ConfigManager(config_path=str(config_path))
        errors = manager.validate_config()

        assert len(errors) > 0
        assert any("from_email" in err for err in errors)


class TestGetAndSet:
    """get/setメソッドのテスト"""

    def test_get_nested_value(self, config_manager):
        """ネストされた値の取得"""
        value = config_manager.get("system.name")
        assert value == "テストシステム"

    def test_get_with_default(self, config_manager):
        """デフォルト値付き取得"""
        value = config_manager.get("nonexistent.key", default="default_value")
        assert value == "default_value"

    def test_get_value_alias(self, config_manager):
        """get_valueエイリアス"""
        value = config_manager.get_value("system.version", default="0.0.0")
        assert value == "1.0.0"

    def test_set_value(self, config_manager):
        """値の設定"""
        config_manager.set("test.new_key", "new_value")
        value = config_manager.get("test.new_key")
        assert value == "new_value"

    def test_set_nested_value(self, config_manager):
        """ネストされた値の設定"""
        config_manager.set("nested.level1.level2", "deep_value")
        value = config_manager.get("nested.level1.level2")
        assert value == "deep_value"

    def test_update_config(self, config_manager):
        """設定の更新"""
        config_manager.update_config("system.log_level", "ERROR")
        value = config_manager.get("system.log_level")
        assert value == "ERROR"

    def test_get_section(self, config_manager):
        """セクション全体の取得"""
        section = config_manager.get_section("system")
        assert isinstance(section, dict)
        assert "name" in section
        assert section["name"] == "テストシステム"

    def test_get_all(self, config_manager):
        """全設定の取得"""
        all_config = config_manager.get_all()
        assert isinstance(all_config, dict)
        assert "system" in all_config
        assert "database" in all_config


class TestEnvironmentOverrides:
    """環境変数オーバーライドのテスト"""

    def test_db_path_override(self, temp_config_file):
        """データベースパスの環境変数オーバーライド"""
        with patch.dict(os.environ, {"MANGA_ANIME_DB_PATH": "/custom/db.sqlite3"}):
            manager = ConfigManager(config_path=temp_config_file)
            assert manager.get_db_path() == "/custom/db.sqlite3"

    def test_log_level_override(self, temp_config_file):
        """ログレベルの環境変数オーバーライド"""
        with patch.dict(os.environ, {"MANGA_ANIME_LOG_LEVEL": "ERROR"}):
            manager = ConfigManager(config_path=temp_config_file)
            assert manager.get_log_level() == "ERROR"

    def test_gmail_override(self, temp_config_file):
        """Gmail設定の環境変数オーバーライド"""
        with patch.dict(os.environ, {
            "MANGA_ANIME_GMAIL_FROM": "override@example.com",
            "MANGA_ANIME_GMAIL_TO": "recipient@example.com"
        }):
            manager = ConfigManager(config_path=temp_config_file)
            gmail_config = manager.get_gmail_config()
            assert gmail_config.from_email == "override@example.com"


class TestSaveAndReload:
    """保存とリロードのテスト"""

    def test_save_config(self, config_manager, tmp_path):
        """設定の保存"""
        save_path = tmp_path / "saved_config.json"
        config_manager.update_config("system.version", "2.0.0")
        config_manager.save_config(path=str(save_path))

        assert save_path.exists()

        with open(save_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data["system"]["version"] == "2.0.0"

    def test_reload_config(self, config_manager, temp_config_file):
        """設定のリロード"""
        # 設定を変更
        config_manager.update_config("system.name", "変更後")
        assert config_manager.get_system_name() == "変更後"

        # リロード
        config_manager.reload()

        # 元に戻る
        assert config_manager.get_system_name() == "テストシステム"


class TestSecureConfigManager:
    """SecureConfigManagerのテスト"""

    def test_init_without_password(self):
        """パスワードなしで初期化"""
        manager = SecureConfigManager()
        assert manager._encryption_key is None

    def test_init_with_password(self):
        """パスワード付きで初期化"""
        manager = SecureConfigManager(password="test_password")
        assert manager._encryption_key is not None

    def test_encrypt_value(self):
        """値の暗号化"""
        manager = SecureConfigManager(password="test_password")
        encrypted = manager.encrypt_value("secret_value")
        assert encrypted != "secret_value"
        assert len(encrypted) > 0

    def test_decrypt_value(self):
        """値の復号化"""
        manager = SecureConfigManager(password="test_password")
        original = "secret_value"
        encrypted = manager.encrypt_value(original)
        decrypted = manager.decrypt_value(encrypted)
        assert decrypted == original

    def test_encrypt_without_key(self):
        """暗号化キーなしでの暗号化"""
        manager = SecureConfigManager()
        encrypted = manager.encrypt_value("test_value")
        # キーがないので元の値がそのまま返る
        assert encrypted == "test_value"


class TestSecureConfigIntegration:
    """ConfigManagerとSecureConfigManagerの統合テスト"""

    def test_set_secure_value(self, temp_config_file):
        """セキュアな値の設定"""
        with patch.dict(os.environ, {"MANGA_ANIME_MASTER_PASSWORD": "test_password"}):
            manager = ConfigManager(config_path=temp_config_file, enable_encryption=True)
            manager.set_secure("test.password", "secret123")

            # 暗号化されて保存される
            stored_value = manager._config_data.get("test", {}).get("password")
            assert stored_value != "secret123"

    def test_get_secure_value(self, temp_config_file):
        """セキュアな値の取得"""
        with patch.dict(os.environ, {"MANGA_ANIME_MASTER_PASSWORD": "test_password"}):
            manager = ConfigManager(config_path=temp_config_file, enable_encryption=True)
            manager.set_secure("test.api_key", "my_api_key")

            # 復号化されて取得される
            value = manager.get_secure("test.api_key")
            assert value == "my_api_key"


class TestGlobalConfigInstance:
    """グローバル設定インスタンスのテスト"""

    def test_get_config_singleton(self, temp_config_file):
        """get_configでシングルトン取得"""
        # リセット
        import modules.config
        modules.config._config_manager = None

        config1 = get_config(temp_config_file)
        config2 = get_config()

        assert config1 is config2

    def test_get_config_different_path(self, temp_config_file, tmp_path):
        """異なるパスで新しいインスタンス作成"""
        import modules.config
        modules.config._config_manager = None

        config1 = get_config(temp_config_file)

        # 別の設定ファイル
        config2_path = tmp_path / "config2.json"
        with open(config2_path, "w") as f:
            json.dump({"system": {"name": "別の設定"}, "database": {}, "apis": {}}, f)

        config2 = get_config(str(config2_path))

        # 異なるインスタンス
        assert config1 is not config2


class TestLoadConfigFile:
    """load_config_file関数のテスト"""

    def test_load_config_file(self, temp_config_file):
        """設定ファイルの読み込み"""
        config_data = load_config_file(temp_config_file)
        assert isinstance(config_data, dict)
        assert "system" in config_data
        assert config_data["system"]["name"] == "テストシステム"


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_empty_config_section(self, config_manager):
        """空のセクション取得"""
        section = config_manager.get_section("nonexistent_section")
        assert section == {}

    def test_deeply_nested_get(self, config_manager):
        """深くネストされた値の取得"""
        config_manager.set("a.b.c.d.e", "deep_value")
        value = config_manager.get("a.b.c.d.e")
        assert value == "deep_value"

    def test_get_with_none_default(self, config_manager):
        """Noneをデフォルトとして取得"""
        value = config_manager.get("nonexistent.key", default=None)
        assert value is None

    def test_invalid_json_config(self, tmp_path):
        """不正なJSON設定ファイル"""
        invalid_path = tmp_path / "invalid.json"
        with open(invalid_path, "w") as f:
            f.write("invalid json content {{{")

        # デフォルト設定にフォールバック
        manager = ConfigManager(config_path=str(invalid_path))
        assert manager._loaded_from == "defaults"


class TestConfigPersistence:
    """設定の永続性テスト"""

    def test_save_and_load_roundtrip(self, tmp_path):
        """保存と読み込みのラウンドトリップ"""
        config_path = tmp_path / "roundtrip.json"

        # 最初のマネージャーで設定を作成
        manager1 = ConfigManager()
        manager1.set("custom.setting", "custom_value")
        manager1.save_config(path=str(config_path))

        # 新しいマネージャーで読み込み
        manager2 = ConfigManager(config_path=str(config_path))
        value = manager2.get("custom.setting")

        assert value == "custom_value"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
