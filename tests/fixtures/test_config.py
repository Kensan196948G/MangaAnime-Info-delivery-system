#!/usr/bin/env python3
"""
Test Configuration Module
Provides complete configuration for all test suites
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
import json


class TestConfig:
    """Centralized test configuration"""

    def __init__(self):
        self.test_root = Path(__file__).parent.parent
        self.project_root = self.test_root.parent
        self.load_config()

    def load_config(self):
        """Load configuration from environment or defaults"""
        self.config = {
            # Database Configuration
            "database": {
                "test_db_path": ":memory:",  # In-memory database for tests
                "connection_timeout": 5,
                "enable_wal": False,  # WAL mode for SQLite
                "isolation_level": "DEFERRED",
            },
            # API Configuration
            "anilist": {
                "base_url": "https://graphql.anilist.co",
                "rate_limit": 90,
                "rate_limit_window": 60,  # seconds
                "timeout": 10,
                "retry_count": 3,
                "mock_enabled": True,  # Use mock service in tests
            },
            # RSS Feed Configuration
            "rss": {
                "feeds": {
                    "bookwalker": "https://bookwalker.jp/rss/new",
                    "kindle": "https://amazon.co.jp/kindle/rss",
                    "dmm": "https://book.dmm.com/rss",
                    "manga_kingdom": "https://comic.k-manga.jp/rss",
                    "comic_seymour": "https://cmoa.jp/rss",
                },
                "timeout": 15,
                "mock_enabled": True,
            },
            # Google API Configuration
            "google": {
                "gmail": {
                    "api_version": "v1",
                    "scopes": [
                        "https://www.googleapis.com/auth/gmail.send",
                        "https://www.googleapis.com/auth/gmail.readonly",
                    ],
                    "credentials_file": "test_credentials.json",
                    "token_file": "test_token.json",
                    "mock_enabled": True,
                },
                "calendar": {
                    "api_version": "v3",
                    "scopes": [
                        "https://www.googleapis.com/auth/calendar.events",
                        "https://www.googleapis.com/auth/calendar.readonly",
                    ],
                    "calendar_id": "primary",
                    "mock_enabled": True,
                },
                "oauth2": {
                    "client_id": "test_client_id",
                    "client_secret": "test_client_secret",
                    "redirect_uri": "http://localhost:8080/oauth2callback",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                },
            },
            # Filter Configuration
            "filter": {
                "ng_keywords": ["test_ng_word_1", "test_ng_word_2"],
                "min_quality_score": 0.5,
                "enable_adult_filter": True,
                "enable_genre_filter": True,
                "allowed_genres": ["Action", "Comedy", "Drama"],
            },
            # Notification Configuration
            "notification": {
                "email": {
                    "enabled": True,
                    "from_address": "test@example.com",
                    "to_address": "recipient@example.com",
                    "subject_template": "【新作情報】{title}",
                    "body_template": "<h1>{title}</h1><p>{description}</p>",
                    "max_items_per_email": 10,
                },
                "calendar": {
                    "enabled": True,
                    "reminder_minutes": 30,
                    "color_scheme": {
                        "anime": "blue",
                        "manga": "green",
                        "movie": "red",
                    },
                },
            },
            # Performance Configuration
            "performance": {
                "max_concurrent_requests": 10,
                "request_delay_ms": 100,
                "batch_size": 50,
                "cache_ttl_seconds": 3600,
                "enable_profiling": False,
                "enable_metrics": True,
            },
            # Test-specific Configuration
            "test": {
                "use_mocks": True,
                "verbose_logging": False,
                "save_test_artifacts": False,
                "test_data_dir": str(self.test_root / "data"),
                "fixture_timeout": 30,
                "async_timeout": 10,
                "reset_mocks_between_tests": True,
            },
            # Logging Configuration
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": None,  # No file logging in tests
                "console": True,
            },
        }

        # Override with environment variables if present
        self._load_env_overrides()

    def _load_env_overrides(self):
        """Load configuration overrides from environment variables"""
        env_mappings = {
            "TEST_DB_PATH": ["database", "test_db_path"],
            "TEST_USE_MOCKS": ["test", "use_mocks"],
            "TEST_VERBOSE": ["test", "verbose_logging"],
            "TEST_ASYNC_TIMEOUT": ["test", "async_timeout"],
            "ANILIST_MOCK": ["anilist", "mock_enabled"],
            "RSS_MOCK": ["rss", "mock_enabled"],
            "GMAIL_MOCK": ["google", "gmail", "mock_enabled"],
            "CALENDAR_MOCK": ["google", "calendar", "mock_enabled"],
        }

        for env_key, config_path in env_mappings.items():
            env_value = os.environ.get(env_key)
            if env_value is not None:
                self._set_nested_config(config_path, self._parse_env_value(env_value))

    def _set_nested_config(self, path: list, value: Any):
        """Set nested configuration value"""
        config = self.config
        for key in path[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[path[-1]] = value

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value"""
        if value.lower() in ("true", "1", "yes", "on"):
            return True
        elif value.lower() in ("false", "0", "no", "off"):
            return False
        elif value.isdigit():
            return int(value)
        else:
            try:
                return float(value)
            except ValueError:
                return value

    def get(self, *keys: str, default: Any = None) -> Any:
        """Get configuration value by nested keys"""
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.config.get(section, {})

    def update(self, updates: Dict[str, Any]):
        """Update configuration with dictionary"""
        self._deep_update(self.config, updates)

    def _deep_update(self, target: dict, source: dict):
        """Deep update dictionary"""
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_update(target[key], value)
            else:
                target[key] = value

    def reset(self):
        """Reset configuration to defaults"""
        self.load_config()

    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary"""
        return self.config.copy()

    def to_json(self, indent: int = 2) -> str:
        """Get configuration as JSON string"""
        return json.dumps(self.config, indent=indent, default=str)


# Global test configuration instance
test_config = TestConfig()


def get_test_config() -> TestConfig:
    """Get global test configuration instance"""
    return test_config


def reset_test_config():
    """Reset test configuration to defaults"""
    test_config.reset()
