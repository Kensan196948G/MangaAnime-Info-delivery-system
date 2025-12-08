"""
Configuration utilities for MangaAnime Info Delivery System.

Provides unified configuration access that eliminates scattered os.getenv() calls.
"""

import os
from typing import Optional, Any, Dict, List
from pathlib import Path


class ConfigHelper:
    """
    Centralized configuration helper.

    Provides type-safe access to environment variables and configuration values.
    """

    # Environment variable mappings
    ENV_VARS = {
        # Database
        'DATABASE_PATH': './data/db.sqlite3',
        'DB_BACKUP_ENABLED': 'true',
        'DB_BACKUP_RETENTION_DAYS': '30',

        # Email
        'GMAIL_SENDER_EMAIL': '',
        'GMAIL_RECIPIENT_EMAIL': '',
        'GMAIL_ADDRESS': '',
        'GMAIL_APP_PASSWORD': '',
        'NOTIFICATION_EMAIL': '',

        # Google API
        'GOOGLE_CREDENTIALS_FILE': './credentials.json',
        'GOOGLE_TOKEN_FILE': './token.json',

        # Logging
        'LOG_LEVEL': 'INFO',
        'LOG_DIR': './logs',

        # API URLs
        'ANILIST_API_URL': 'https://graphql.anilist.co',
        'SYOBOI_API_URL': 'https://cal.syoboi.jp',

        # Filtering
        'NG_KEYWORDS': '',

        # System
        'TIMEZONE': 'Asia/Tokyo',
        'TEST_MODE': 'false',

        # Security
        'SECRET_KEY': '',
        'FLASK_SECRET_KEY': '',
        'SESSION_TYPE': 'filesystem',

        # Redis
        'REDIS_URL': 'redis://localhost:6379',

        # Rate Limiting
        'RATE_LIMIT_ENABLED': 'true',
        'RATE_LIMIT_REQUESTS': '90',

        # Monitoring
        'USE_DB_AUDIT_LOG': 'true',
        'MONITORING_ENABLED': 'true',
    }

    @staticmethod
    def get(key: str, default: Optional[str] = None) -> str:
        """
        Get configuration value from environment.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Configuration value
        """
        if default is None:
            default = ConfigHelper.ENV_VARS.get(key, '')

        return os.getenv(key, default)

    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """
        Get boolean configuration value.

        Args:
            key: Environment variable name
            default: Default boolean value

        Returns:
            Boolean configuration value
        """
        default_str = ConfigHelper.ENV_VARS.get(key, str(default).lower())
        value = os.getenv(key, default_str)
        return value.lower() in ('true', '1', 'yes', 'on')

    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        """
        Get integer configuration value.

        Args:
            key: Environment variable name
            default: Default integer value

        Returns:
            Integer configuration value
        """
        default_str = ConfigHelper.ENV_VARS.get(key, str(default))
        value = os.getenv(key, default_str)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def get_list(key: str, delimiter: str = ',', default: Optional[List[str]] = None) -> List[str]:
        """
        Get list configuration value.

        Args:
            key: Environment variable name
            delimiter: List delimiter
            default: Default list value

        Returns:
            List of configuration values
        """
        value = ConfigHelper.get(key, '')
        if not value:
            return default or []

        return [item.strip() for item in value.split(delimiter) if item.strip()]

    @staticmethod
    def get_path(key: str, default: Optional[str] = None, ensure_exists: bool = False) -> Path:
        """
        Get path configuration value.

        Args:
            key: Environment variable name
            default: Default path value
            ensure_exists: Whether to create directory if it doesn't exist

        Returns:
            Path object
        """
        path_str = ConfigHelper.get(key, default)
        path = Path(path_str)

        if ensure_exists and not path.exists():
            if '.' in path.name:  # It's a file
                path.parent.mkdir(parents=True, exist_ok=True)
            else:  # It's a directory
                path.mkdir(parents=True, exist_ok=True)

        return path

    @staticmethod
    def get_all() -> Dict[str, str]:
        """
        Get all configuration values.

        Returns:
            Dictionary of all environment variables
        """
        return {key: ConfigHelper.get(key) for key in ConfigHelper.ENV_VARS.keys()}


# Convenience functions for common configurations
def get_config(key: str, default: Optional[str] = None) -> str:
    """Get configuration value."""
    return ConfigHelper.get(key, default)


def get_db_path(custom_path: Optional[str] = None) -> str:
    """
    Get database path.

    Args:
        custom_path: Optional custom path

    Returns:
        Database path string
    """
    if custom_path:
        return custom_path
    return ConfigHelper.get('DATABASE_PATH', './data/db.sqlite3')


def get_log_level() -> str:
    """Get log level."""
    return ConfigHelper.get('LOG_LEVEL', 'INFO')


def get_timezone() -> str:
    """Get timezone."""
    return ConfigHelper.get('TIMEZONE', 'Asia/Tokyo')


def is_test_mode() -> bool:
    """Check if test mode is enabled."""
    return ConfigHelper.get_bool('TEST_MODE', False)


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return ConfigHelper.get_bool('DEBUG', False)


def get_ng_keywords() -> List[str]:
    """Get NG keywords list."""
    return ConfigHelper.get_list('NG_KEYWORDS', default=[])


def get_notification_emails() -> List[str]:
    """Get notification email addresses."""
    return ConfigHelper.get_list('NOTIFICATION_EMAIL', default=[])


def get_env_config() -> Dict[str, Any]:
    """
    Get comprehensive environment configuration.

    Returns:
        Dictionary with all configuration sections
    """
    return {
        'database': {
            'path': get_db_path(),
            'backup_enabled': ConfigHelper.get_bool('DB_BACKUP_ENABLED', True),
            'backup_retention_days': ConfigHelper.get_int('DB_BACKUP_RETENTION_DAYS', 30),
        },
        'email': {
            'sender': ConfigHelper.get('GMAIL_SENDER_EMAIL'),
            'recipient': ConfigHelper.get('GMAIL_RECIPIENT_EMAIL'),
            'app_password': ConfigHelper.get('GMAIL_APP_PASSWORD'),
        },
        'google': {
            'credentials_file': ConfigHelper.get('GOOGLE_CREDENTIALS_FILE', './credentials.json'),
            'token_file': ConfigHelper.get('GOOGLE_TOKEN_FILE', './token.json'),
        },
        'logging': {
            'level': get_log_level(),
            'dir': ConfigHelper.get('LOG_DIR', './logs'),
        },
        'apis': {
            'anilist_url': ConfigHelper.get('ANILIST_API_URL', 'https://graphql.anilist.co'),
            'syoboi_url': ConfigHelper.get('SYOBOI_API_URL', 'https://cal.syoboi.jp'),
        },
        'filtering': {
            'ng_keywords': get_ng_keywords(),
        },
        'system': {
            'timezone': get_timezone(),
            'test_mode': is_test_mode(),
            'debug_mode': is_debug_mode(),
        },
        'security': {
            'secret_key': ConfigHelper.get('SECRET_KEY'),
            'flask_secret_key': ConfigHelper.get('FLASK_SECRET_KEY'),
        },
        'monitoring': {
            'enabled': ConfigHelper.get_bool('MONITORING_ENABLED', True),
            'use_db_audit_log': ConfigHelper.get_bool('USE_DB_AUDIT_LOG', True),
        },
    }


def validate_required_config() -> List[str]:
    """
    Validate that required configuration is set.

    Returns:
        List of missing required configuration keys
    """
    required = [
        'DATABASE_PATH',
    ]

    missing = []
    for key in required:
        if not ConfigHelper.get(key):
            missing.append(key)

    return missing


def print_config_summary() -> None:
    """Print configuration summary for debugging."""
    config = get_env_config()

    print("=" * 60)
    print("Configuration Summary")
    print("=" * 60)

    for section, values in config.items():
        print(f"\n[{section.upper()}]")
        for key, value in values.items():
            # Mask sensitive values
            if any(s in key.lower() for s in ['password', 'secret', 'key']):
                display_value = '***MASKED***' if value else '(not set)'
            else:
                display_value = value or '(not set)'

            print(f"  {key}: {display_value}")

    print("\n" + "=" * 60)
