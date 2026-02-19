"""
Configuration management module for the Anime/Manga information delivery system.

This module provides:
- JSON configuration file loading and validation
- Environment variable override support
- Default configuration values
- Configuration schema validation
- Runtime configuration updates
"""

import base64
import copy
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    path: str = "./db.sqlite3"
    backup_enabled: bool = True
    backup_retention_days: int = 30

    def __post_init__(self):
        # Ensure database directory exists
        db_path = Path(self.path)
        if not db_path.parent.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""

    requests_per_minute: int = 90
    retry_delay_seconds: int = 5


@dataclass
class AniListConfig:
    """AniList API configuration."""

    graphql_url: str = "https://graphql.anilist.co"
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    timeout_seconds: int = 30


@dataclass
class SyoboiConfig:
    """Syoboi Calendar API configuration."""

    base_url: str = "https://cal.syoboi.jp"
    endpoints: Dict[str, str] = field(
        default_factory=lambda: {"json": "/json.php", "db": "/db.php"}
    )
    timeout_seconds: int = 15


@dataclass
class FeedConfig:
    """Individual RSS feed configuration."""

    name: str
    url: str
    type: str = "anime"  # anime or manga
    category: str = ""
    enabled: bool = True
    description: str = ""
    verified: bool = False
    retry_count: int = 3
    retry_delay: int = 2
    timeout: int = 25


@dataclass
class RSSConfig:
    """RSS feeds configuration."""

    enabled: bool = True
    timeout_seconds: int = 20
    user_agent: str = "MangaAnimeNotifier/1.0 (https://github.com/user/manga-anime-notifier)"
    feeds: List[FeedConfig] = field(default_factory=list)
    max_parallel_workers: int = 5
    stats: dict = field(default_factory=dict)

    def __post_init__(self):
        # Convert dict feeds to FeedConfig objects
        if self.feeds and isinstance(self.feeds[0], dict):
            self.feeds = [FeedConfig(**feed) for feed in self.feeds]


@dataclass
class GoogleConfig:
    """Google APIs configuration."""

    credentials_file: str = "./credentials.json"
    token_file: str = "./token.json"
    scopes: List[str] = field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/calendar.events",
        ]
    )


@dataclass
class GmailConfig:
    """Gmail notification configuration."""

    from_email: str = ""
    to_email: str = ""
    subject_prefix: str = "[アニメ・マンガ情報]"
    html_template_enabled: bool = True


@dataclass
class CalendarConfig:
    """Google Calendar configuration."""

    calendar_id: str = "primary"
    event_duration_hours: int = 1
    reminder_minutes: List[int] = field(default_factory=lambda: [60, 10])


@dataclass
class FilteringConfig:
    """Content filtering configuration."""

    ng_keywords: List[str] = field(
        default_factory=lambda: [
            "エロ",
            "R18",
            "成人向け",
            "BL",
            "百合",
            "ボーイズラブ",
            "アダルト",
            "18禁",
            "官能",
            "ハーレクイン",
        ]
    )
    ng_genres: List[str] = field(default_factory=lambda: ["Hentai", "Ecchi"])
    exclude_tags: List[str] = field(default_factory=lambda: ["Adult Cast", "Erotica"])


@dataclass
class SchedulingConfig:
    """Scheduling configuration."""

    default_run_time: str = "08:00"
    timezone: str = "Asia/Tokyo"
    max_execution_time_minutes: int = 30
    retry_attempts: int = 3
    retry_delay_minutes: int = 5


@dataclass
class EmailNotificationConfig:
    """Email notification settings."""

    enabled: bool = True
    max_items_per_email: int = 20
    include_images: bool = True
    template_style: str = "modern"


@dataclass
class CalendarNotificationConfig:
    """Calendar notification settings."""

    enabled: bool = True
    create_all_day_events: bool = False
    color_by_type: Dict[str, str] = field(
        default_factory=lambda: {"anime": "blue", "manga": "green"}
    )


@dataclass
class NotificationConfig:
    """Notification configuration."""

    email: EmailNotificationConfig = field(default_factory=EmailNotificationConfig)
    calendar: CalendarNotificationConfig = field(default_factory=CalendarNotificationConfig)


@dataclass
class LoggingConfig:
    """Logging configuration."""

    file_path: str = "./logs/app.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"

    def __post_init__(self):
        # Ensure log directory exists
        log_path = Path(self.file_path)
        if not log_path.parent.exists():
            log_path.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class SystemConfig:
    """System-level configuration."""

    name: str = "MangaAnime情報配信システム"
    version: str = "1.0.0"
    environment: str = "production"
    timezone: str = "Asia/Tokyo"
    log_level: str = "INFO"


class SecureConfigManager:
    """Secure configuration manager with encryption support."""

    def __init__(self, password: Optional[str] = None):
        """
        Initialize secure configuration manager.

        Args:
            password: Password for encrypting sensitive data
        """
        self.logger = logging.getLogger(__name__)
        self._encryption_key = None

        if password:
            self._setup_encryption(password)

    def _setup_encryption(self, password: str) -> None:
        """Setup encryption key from password."""
        try:
            # Generate salt for key derivation
            salt = os.environ.get("MANGA_ANIME_SALT", "manga_anime_salt_2025").encode()

            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            self._encryption_key = Fernet(key)

            self.logger.debug("Encryption key setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup encryption: {e}")
            raise

    def encrypt_value(self, value: str) -> str:
        """Encrypt a sensitive value."""
        if not self._encryption_key:
            return value

        try:
            encrypted = self._encryption_key.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            self.logger.error(f"Failed to encrypt value: {e}")
            return value

    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a sensitive value."""
        if not self._encryption_key:
            return encrypted_value

        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = self._encryption_key.decrypt(encrypted_data)
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"Failed to decrypt value: {e}")
            return encrypted_value


class ConfigManager:
    """
    Configuration manager for the anime/manga information system.

    Loads configuration from JSON files with support for environment
    variable overrides and runtime configuration updates.
    """

    DEFAULT_CONFIG_PATHS = [
        "./config.json",
        "./config/config.json",
        "./config.local.json",
        os.path.expanduser("~/.manga-anime-notifier/config.json"),
    ]

    def __init__(self, config_path: Optional[str] = None, enable_encryption: bool = False):
        """
        Initialize configuration manager.

        Args:
            config_path: Custom configuration file path (optional)
            enable_encryption: Enable encryption for sensitive data
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self._config_data = {}
        self._loaded_from = None
        self._enable_encryption = enable_encryption
        self._secure_manager = None

        # Setup encryption if enabled
        if enable_encryption:
            password = os.environ.get("MANGA_ANIME_MASTER_PASSWORD")
            if password:
                self._secure_manager = SecureConfigManager(password)
                self.logger.info("Encryption enabled for sensitive configuration data")
            else:
                self.logger.warning("Encryption requested but MANGA_ANIME_MASTER_PASSWORD not set")

        # Load configuration
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file and environment variables."""
        config_paths = [self.config_path] if self.config_path else self.DEFAULT_CONFIG_PATHS

        for path in config_paths:
            if path and os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self._config_data = json.load(f)
                    self._loaded_from = path
                    self.logger.info(f"Loaded configuration from: {path}")
                    break
                except Exception as e:
                    self.logger.warning(f"Failed to load config from {path}: {e}")
                    continue
        else:
            # No config file found, use defaults
            self.logger.info("No configuration file found, using defaults")
            self._config_data = self._get_default_config()
            self._loaded_from = "defaults"

        # Apply environment variable overrides
        self._apply_env_overrides()

        # Validate configuration
        self._validate_config()

    def get_system_name(self) -> str:
        """Get system name."""
        return self._config_data.get("system", {}).get("name", "MangaAnime情報配信システム")

    def get_system_version(self) -> str:
        """Get system version."""
        return self._config_data.get("system", {}).get("version", "1.0.0")

    def get_environment(self) -> str:
        """Get environment."""
        return self._config_data.get("system", {}).get("environment", "development")

    def get_db_path(self) -> str:
        """Get database path."""
        return self._config_data.get("database", {}).get("path", "./db.sqlite3")

    def get_log_level(self) -> str:
        """Get log level."""
        return self._config_data.get("system", {}).get("log_level", "INFO")

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []

        # Check required Google API settings
        google_config = self._config_data.get("google", {})
        if not google_config.get("credentials_file"):
            errors.append("Google credentials file not specified")

        gmail_config = google_config.get("gmail", {})
        if not gmail_config.get("from_email"):
            errors.append("Gmail from_email not configured")
        if not gmail_config.get("to_email"):
            errors.append("Gmail to_email not configured")

        return errors

    def get_log_file_path(self) -> str:
        """Get log file path."""
        return self._config_data.get("logging", {}).get("file_path", "./logs/app.log")

    def get_log_max_file_size_mb(self) -> int:
        """Get log max file size in MB."""
        return self._config_data.get("logging", {}).get("max_file_size_mb", 10)

    def get_log_backup_count(self) -> int:
        """Get log backup count."""
        return self._config_data.get("logging", {}).get("backup_count", 5)

    def get_log_format(self) -> str:
        """Get log format."""
        return self._config_data.get("logging", {}).get(
            "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def get_log_date_format(self) -> str:
        """Get log date format."""
        return self._config_data.get("logging", {}).get("date_format", "%Y-%m-%d %H:%M:%S")

    def get_rss_config(self) -> Dict[str, Any]:
        """Get RSS configuration."""
        return self._config_data.get("apis", {}).get("rss_feeds", {})

    def get_enabled_rss_feeds(self) -> List[Dict[str, Any]]:
        """Get enabled RSS feeds."""
        rss_config = self.get_rss_config()
        feeds = rss_config.get("feeds", [])
        return [feed for feed in feeds if feed.get("enabled", True)]

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "system": {
                "name": "MangaAnime情報配信システム",
                "version": "1.0.0",
                "environment": "development",
                "timezone": "Asia/Tokyo",
                "log_level": "INFO",
            },
            "database": {
                "path": "./db.sqlite3",
                "backup_enabled": True,
                "backup_retention_days": 30,
            },
            "apis": {
                "anilist": {
                    "graphql_url": "https://graphql.anilist.co",
                    "rate_limit": {"requests_per_minute": 90, "retry_delay_seconds": 5},
                    "timeout_seconds": 30,
                },
                "rss_feeds": {
                    "timeout_seconds": 20,
                    "user_agent": "MangaAnimeNotifier/1.0",
                    "feeds": [],
                },
            },
            "google": {
                "credentials_file": "./credentials.json",
                "token_file": "./token.json",
                "scopes": [
                    "https://www.googleapis.com/auth/gmail.send",
                    "https://www.googleapis.com/auth/calendar.events",
                ],
                "gmail": {
                    "from_email": "",
                    "to_email": "",
                    "subject_prefix": "[アニメ・マンガ情報]",
                    "html_template_enabled": True,
                },
                "calendar": {
                    "calendar_id": "primary",
                    "event_duration_hours": 1,
                    "reminder_minutes": [60, 10],
                },
            },
            "filtering": {
                "ng_keywords": [
                    "エロ",
                    "R18",
                    "成人向け",
                    "BL",
                    "百合",
                    "ボーイズラブ",
                ],
                "ng_genres": ["Hentai", "Ecchi"],
                "exclude_tags": ["Adult Cast", "Erotica"],
            },
            "scheduling": {
                "default_run_time": "08:00",
                "timezone": "Asia/Tokyo",
                "max_execution_time_minutes": 30,
                "retry_attempts": 3,
                "retry_delay_minutes": 5,
            },
            "notification": {
                "email": {
                    "enabled": True,
                    "max_items_per_email": 20,
                    "include_images": True,
                    "template_style": "modern",
                },
                "calendar": {
                    "enabled": True,
                    "create_all_day_events": False,
                    "color_by_type": {"anime": "blue", "manga": "green"},
                },
            },
            "logging": {
                "file_path": "./logs/app.log",
                "max_file_size_mb": 10,
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "date_format": "%Y-%m-%d %H:%M:%S",
            },
        }

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # Define environment variable mappings with enhanced security support
        env_mappings = {
            # Database configuration
            "MANGA_ANIME_DB_PATH": ["database", "path"],
            # System configuration
            "MANGA_ANIME_LOG_LEVEL": ["system", "log_level"],
            "MANGA_ANIME_LOG_PATH": ["logging", "file_path"],
            "MANGA_ANIME_ENVIRONMENT": ["system", "environment"],
            # Gmail configuration with OAuth2 support
            "MANGA_ANIME_GMAIL_FROM": ["google", "gmail", "from_email"],
            "MANGA_ANIME_GMAIL_TO": ["google", "gmail", "to_email"],
            "GMAIL_APP_PASSWORD": ["google", "gmail", "app_password"],
            "GMAIL_CLIENT_ID": ["google", "gmail", "client_id"],
            "GMAIL_CLIENT_SECRET": ["google", "gmail", "client_secret"],
            # Google API credentials
            "MANGA_ANIME_CREDENTIALS_FILE": ["google", "credentials_file"],
            "MANGA_ANIME_TOKEN_FILE": ["google", "token_file"],
            "GOOGLE_APPLICATION_CREDENTIALS": ["google", "service_account_file"],
            # Calendar configuration
            "MANGA_ANIME_CALENDAR_ID": ["google", "calendar", "calendar_id"],
            "CALENDAR_CLIENT_ID": ["google", "calendar", "client_id"],
            "CALENDAR_CLIENT_SECRET": ["google", "calendar", "client_secret"],
            # API Keys with enhanced security
            "ANILIST_API_KEY": ["apis", "anilist", "api_key"],
            "SYOBOI_API_KEY": ["apis", "syoboi", "api_key"],
            # Security settings
            "MANGA_ANIME_SECRET_KEY": ["security", "secret_key"],
            "MANGA_ANIME_ENCRYPTION_KEY": ["security", "encryption_key"],
            # Rate limiting
            "MANGA_ANIME_RATE_LIMIT_RPM": ["apis", "rate_limit", "requests_per_minute"],
            "MANGA_ANIME_RETRY_DELAY": ["apis", "rate_limit", "retry_delay_seconds"],
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                # Special handling for sensitive values
                if any(
                    sensitive in env_var.lower()
                    for sensitive in ["password", "secret", "key", "token"]
                ):
                    # Don't log sensitive values
                    self.logger.debug(
                        f"Applied secure environment override: {env_var} -> {'.'.join(config_path)} [REDACTED]"
                    )
                else:
                    self.logger.debug(
                        f"Applied environment override: {env_var} -> {'.'.join(config_path)} = {value}"
                    )

                # Type conversion for numeric values
                if env_var.endswith("_RPM") or env_var.endswith("_DELAY"):
                    try:
                        value = int(value)
                    except ValueError:
                        self.logger.warning(f"Invalid numeric value for {env_var}: {value}")
                        continue

                self._set_nested_value(self._config_data, config_path, value)

    def _set_nested_value(self, data: Dict, path: List[str], value: Any) -> None:
        """Set nested dictionary value using path list."""
        for key in path[:-1]:
            data = data.setdefault(key, {})
        data[path[-1]] = value

    def _validate_config(self) -> None:
        """Validate configuration values."""
        required_sections = ["system", "database", "apis"]

        for section in required_sections:
            if section not in self._config_data:
                raise ValueError(f"Required configuration section missing: {section}")

        # Validate specific values
        db_path = self._config_data.get("database", {}).get("path")
        if db_path:
            db_dir = os.path.dirname(os.path.abspath(db_path))
            if not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except OSError as e:
                    self.logger.warning(f"Cannot create database directory {db_dir}: {e}")

        self.logger.debug("Configuration validation completed")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key.

        Args:
            key: Dot-separated key (e.g., 'database.path')
            default: Default value if key not found

        Returns:
            Configuration value (automatically decrypted if encrypted)
        """
        keys = key.split(".")
        value = self._config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        # Auto-decrypt encrypted values
        if isinstance(value, str) and self._secure_manager:
            # Check if this is a sensitive key that might be encrypted
            sensitive_keywords = ["password", "secret", "key", "token", "credentials"]
            if any(keyword in key.lower() for keyword in sensitive_keywords):
                return self._secure_manager.decrypt_value(value)

        return value

    def get_secure(self, key: str, default: Any = None) -> Any:
        """
        Get encrypted configuration value with explicit decryption.

        Args:
            key: Dot-separated key (e.g., 'google.gmail.app_password')
            default: Default value if key not found

        Returns:
            Decrypted configuration value
        """
        value = self.get(key, default)

        if isinstance(value, str) and self._secure_manager:
            return self._secure_manager.decrypt_value(value)

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by dot-separated key.

        Args:
            key: Dot-separated key (e.g., 'database.path')
            value: Value to set
        """
        keys = key.split(".")
        config_section = self._config_data

        # Navigate to the parent section
        for k in keys[:-1]:
            if k not in config_section:
                config_section[k] = {}
            config_section = config_section[k]

        # Set the final value
        config_section[keys[-1]] = value

    def set_secure(self, key: str, value: str) -> None:
        """
        Set encrypted configuration value.

        Args:
            key: Dot-separated key
            value: Value to encrypt and store
        """
        if self._secure_manager:
            encrypted_value = self._secure_manager.encrypt_value(value)
            self.set(key, encrypted_value)
        else:
            self.set(key, value)

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.

        Args:
            section: Section name

        Returns:
            Configuration section dictionary
        """
        return self._config_data.get(section, {})

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration object."""
        db_config = self.get_section("database")
        return DatabaseConfig(**db_config)

    def get_anilist_config(self) -> AniListConfig:
        """Get AniList API configuration object."""
        anilist_config = self.get_section("apis").get("anilist", {})
        rate_limit_data = anilist_config.get("rate_limit", {})

        return AniListConfig(
            graphql_url=anilist_config.get("graphql_url", "https://graphql.anilist.co"),
            rate_limit=RateLimitConfig(**rate_limit_data),
            timeout_seconds=anilist_config.get("timeout_seconds", 30),
        )

    def get_rss_config_object(self) -> RSSConfig:
        """Get RSS feeds configuration object."""
        rss_config = self.get_section("apis").get("rss_feeds", {})
        return RSSConfig(**rss_config)

    def get_google_config(self) -> GoogleConfig:
        """Get Google APIs configuration object."""
        google_config = self.get_section("google")
        return GoogleConfig(**google_config)

    def get_gmail_config(self) -> GmailConfig:
        """Get Gmail configuration object."""
        gmail_config = self.get_section("google").get("gmail", {})
        return GmailConfig(**gmail_config)

    def get_calendar_config(self) -> CalendarConfig:
        """Get Calendar configuration object."""
        calendar_config = self.get_section("google").get("calendar", {})
        return CalendarConfig(**calendar_config)

    def get_filtering_config(self) -> FilteringConfig:
        """Get filtering configuration object."""
        filtering_config = self.get_section("filtering")
        return FilteringConfig(**filtering_config)

    def get_scheduling_config(self) -> SchedulingConfig:
        """Get scheduling configuration object."""
        scheduling_config = self.get_section("scheduling")
        return SchedulingConfig(**scheduling_config)

    def get_notification_config(self) -> NotificationConfig:
        """Get notification configuration object."""
        notification_config = self.get_section("notification")

        email_config = EmailNotificationConfig(**notification_config.get("email", {}))
        calendar_config = CalendarNotificationConfig(**notification_config.get("calendar", {}))

        return NotificationConfig(email=email_config, calendar=calendar_config)

    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration object."""
        logging_config = self.get_section("logging")
        return LoggingConfig(**logging_config)

    def get_system_config(self) -> SystemConfig:
        """Get system configuration object."""
        system_config = self.get_section("system")
        return SystemConfig(**system_config)

    def get_ng_keywords(self) -> List[str]:
        """Get NG keywords list."""
        return self._config_data.get("filtering", {}).get("ng_keywords", [])

    def get_ng_genres(self) -> List[str]:
        """Get NG genres list."""
        return self._config_data.get("filtering", {}).get("ng_genres", [])

    def get_exclude_tags(self) -> List[str]:
        """Get exclude tags list."""
        return self._config_data.get("filtering", {}).get("exclude_tags", [])

    def get_value(self, key: str, default: Any = None) -> Any:
        """Alias for get method for backward compatibility."""
        return self.get(key, default)

    def update_config(self, key: str, value: Any) -> None:
        """
        Update configuration value at runtime.

        Args:
            key: Dot-separated key (e.g., 'database.path')
            value: New value
        """
        keys = key.split(".")
        config = self._config_data

        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value

        self.logger.info(f"Updated configuration: {key} = {value}")

    def save_config(self, path: Optional[str] = None) -> None:
        """
        Save current configuration to file.

        Args:
            path: Custom save path (optional, uses loaded path by default)
        """
        save_path = path or self._loaded_from

        if not save_path or save_path == "defaults":
            save_path = "./config.json"

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved configuration to: {save_path}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration to {save_path}: {e}")
            raise

    def get_all(self) -> Dict[str, Any]:
        """Get complete configuration dictionary."""
        return copy.deepcopy(self._config_data)

    def reload(self) -> None:
        """Reload configuration from file."""
        self.load_config()
        self.logger.info("Configuration reloaded")


# Global configuration manager instance
_config_manager = None


def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """
    Get global configuration manager instance.

    Args:
        config_path: Custom configuration file path (optional)

    Returns:
        ConfigManager instance
    """
    global _config_manager

    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    elif config_path and config_path != _config_manager.config_path:
        # Create new instance if different path is requested
        _config_manager = ConfigManager(config_path)

    return _config_manager


def load_config_file(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from file without creating global instance.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
