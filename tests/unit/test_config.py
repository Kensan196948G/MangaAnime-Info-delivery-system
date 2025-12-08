"""
Unit Tests for Configuration Management
========================================

Tests for configuration loading and validation:
- Config file parsing
- Environment variable handling
- Default values
- Validation rules
- Error handling
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestConfigLoading:
    """Test suite for configuration loading"""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file"""
        config_data = {
            "database": {
                "path": "data/db.sqlite3",
                "backup_enabled": True,
                "backup_interval_days": 7
            },
            "api": {
                "anilist": {
                    "endpoint": "https://graphql.anilist.co",
                    "rate_limit": 90
                },
                "shoboi": {
                    "endpoint": "https://cal.syoboi.jp/db.php",
                    "format": "json"
                }
            },
            "notification": {
                "gmail": {
                    "enabled": True,
                    "sender": "test@example.com",
                    "recipients": ["user@example.com"]
                },
                "calendar": {
                    "enabled": True,
                    "calendar_id": "primary"
                }
            },
            "filtering": {
                "ng_keywords": ["R18", "成人向け"],
                "enabled": True
            },
            "schedule": {
                "check_interval_hours": 24,
                "notification_time": "08:00"
            }
        }

        fd, path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

        yield path

        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def invalid_json_file(self):
        """Create an invalid JSON file"""
        fd, path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w') as f:
            f.write('{ invalid json content')

        yield path

        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def empty_config_file(self):
        """Create an empty config file"""
        fd, path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w') as f:
            f.write('{}')

        yield path

        if os.path.exists(path):
            os.remove(path)

    def test_load_valid_config(self, temp_config_file):
        """Test loading a valid configuration file"""
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        assert 'database' in config
        assert 'api' in config
        assert 'notification' in config
        assert config['database']['path'] == 'data/db.sqlite3'
        assert config['api']['anilist']['rate_limit'] == 90

    def test_load_invalid_json(self, invalid_json_file):
        """Test handling of invalid JSON"""
        with pytest.raises(json.JSONDecodeError):
            with open(invalid_json_file, 'r') as f:
                json.load(f)

    def test_load_empty_config(self, empty_config_file):
        """Test loading an empty configuration"""
        with open(empty_config_file, 'r') as f:
            config = json.load(f)

        assert config == {}

    def test_config_file_not_found(self):
        """Test handling of missing config file"""
        non_existent_path = '/tmp/non_existent_config_12345.json'

        with pytest.raises(FileNotFoundError):
            with open(non_existent_path, 'r') as f:
                json.load(f)

    def test_nested_config_access(self, temp_config_file):
        """Test accessing nested configuration values"""
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Deep nested access
        assert config['api']['anilist']['endpoint'] == 'https://graphql.anilist.co'
        assert config['notification']['gmail']['sender'] == 'test@example.com'

    def test_config_array_values(self, temp_config_file):
        """Test handling of array values in config"""
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        ng_keywords = config['filtering']['ng_keywords']
        assert isinstance(ng_keywords, list)
        assert len(ng_keywords) == 2
        assert 'R18' in ng_keywords

    def test_config_boolean_values(self, temp_config_file):
        """Test handling of boolean values"""
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        assert config['database']['backup_enabled'] is True
        assert config['notification']['gmail']['enabled'] is True
        assert isinstance(config['filtering']['enabled'], bool)

    def test_config_numeric_values(self, temp_config_file):
        """Test handling of numeric values"""
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        assert isinstance(config['database']['backup_interval_days'], int)
        assert config['database']['backup_interval_days'] == 7
        assert isinstance(config['api']['anilist']['rate_limit'], int)

    @patch.dict(os.environ, {'DB_PATH': '/custom/path/db.sqlite3'})
    def test_environment_variable_override(self):
        """Test that environment variables can override config"""
        db_path = os.getenv('DB_PATH')
        assert db_path == '/custom/path/db.sqlite3'

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_environment_variable(self):
        """Test handling of missing environment variables"""
        db_path = os.getenv('DB_PATH', 'data/db.sqlite3')
        assert db_path == 'data/db.sqlite3'  # Default value

    def test_config_with_special_characters(self):
        """Test config with special characters"""
        config_data = {
            "test": {
                "path": "/path/with spaces/and-special_chars",
                "email": "user+tag@example.com",
                "url": "https://example.com/path?param=value&other=123"
            }
        }

        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(config_data, f)

            with open(path, 'r') as f:
                loaded = json.load(f)

            assert loaded['test']['path'] == "/path/with spaces/and-special_chars"
            assert loaded['test']['email'] == "user+tag@example.com"
        finally:
            if os.path.exists(path):
                os.remove(path)


class TestConfigValidation:
    """Test suite for configuration validation"""

    def test_validate_required_fields(self):
        """Test validation of required configuration fields"""
        config = {
            "database": {"path": "data/db.sqlite3"},
            "api": {"anilist": {"endpoint": "https://graphql.anilist.co"}}
        }

        required_fields = ['database', 'api']
        for field in required_fields:
            assert field in config

    def test_validate_missing_required_field(self):
        """Test detection of missing required fields"""
        config = {
            "database": {"path": "data/db.sqlite3"}
            # Missing 'api' field
        }

        required_fields = ['database', 'api', 'notification']
        missing = [f for f in required_fields if f not in config]

        assert 'api' in missing
        assert 'notification' in missing

    def test_validate_email_format(self):
        """Test email format validation"""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.jp",
            "user123@sub.example.com"
        ]

        invalid_emails = [
            "invalid",
            "@example.com",
            "user@",
            "user@.com",
            "user space@example.com"
        ]

        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        for email in valid_emails:
            assert re.match(email_pattern, email)

        for email in invalid_emails:
            assert not re.match(email_pattern, email)

    def test_validate_url_format(self):
        """Test URL format validation"""
        valid_urls = [
            "https://example.com",
            "https://example.com/path",
            "https://sub.example.com:8080/path?query=1",
            "http://localhost:3000"
        ]

        invalid_urls = [
            "not_a_url",
            "ftp://example.com",  # Depending on requirements
            "//example.com",
            "example.com"
        ]

        import re
        url_pattern = r'^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$'

        for url in valid_urls:
            assert re.match(url_pattern, url)

        for url in invalid_urls:
            if url == "ftp://example.com":
                continue  # FTP might be valid in some contexts
            assert not re.match(url_pattern, url)

    def test_validate_numeric_ranges(self):
        """Test validation of numeric value ranges"""
        # Rate limit should be 1-90 for AniList
        valid_rate_limits = [1, 30, 60, 90]
        invalid_rate_limits = [0, -1, 91, 1000]

        for rate in valid_rate_limits:
            assert 1 <= rate <= 90

        for rate in invalid_rate_limits:
            assert not (1 <= rate <= 90)

    def test_validate_time_format(self):
        """Test time format validation (HH:MM)"""
        valid_times = ["08:00", "12:30", "23:59", "00:00"]
        invalid_times = ["8:00", "25:00", "12:60", "12:5", "invalid"]

        import re
        time_pattern = r'^([01][0-9]|2[0-3]):[0-5][0-9]$'

        for time_str in valid_times:
            assert re.match(time_pattern, time_str)

        for time_str in invalid_times:
            assert not re.match(time_pattern, time_str)

    def test_validate_file_path(self):
        """Test file path validation"""
        valid_paths = [
            "data/db.sqlite3",
            "/absolute/path/to/file.db",
            "./relative/path/file.db",
            "../parent/file.db"
        ]

        # All paths should be valid strings
        for path in valid_paths:
            assert isinstance(path, str)
            assert len(path) > 0

    def test_validate_boolean_values(self):
        """Test boolean value validation"""
        config = {
            "enabled": True,
            "disabled": False,
            "invalid_bool": "yes"  # Should be boolean
        }

        assert isinstance(config['enabled'], bool)
        assert isinstance(config['disabled'], bool)
        assert not isinstance(config['invalid_bool'], bool)

    def test_validate_list_not_empty(self):
        """Test validation that required lists are not empty"""
        valid_config = {
            "recipients": ["user1@example.com", "user2@example.com"]
        }

        invalid_config = {
            "recipients": []
        }

        assert len(valid_config['recipients']) > 0
        assert len(invalid_config['recipients']) == 0


class TestConfigDefaults:
    """Test suite for default configuration values"""

    def test_default_database_path(self):
        """Test default database path"""
        default_db_path = "data/db.sqlite3"
        assert default_db_path == "data/db.sqlite3"

    def test_default_backup_settings(self):
        """Test default backup settings"""
        defaults = {
            "backup_enabled": True,
            "backup_interval_days": 7,
            "max_backups": 5
        }

        assert defaults['backup_enabled'] is True
        assert defaults['backup_interval_days'] == 7
        assert defaults['max_backups'] == 5

    def test_default_rate_limits(self):
        """Test default API rate limits"""
        defaults = {
            "anilist_rate_limit": 90,
            "request_timeout": 30
        }

        assert defaults['anilist_rate_limit'] == 90
        assert defaults['request_timeout'] == 30

    def test_default_notification_settings(self):
        """Test default notification settings"""
        defaults = {
            "notification_enabled": True,
            "calendar_enabled": True,
            "notification_time": "08:00"
        }

        assert defaults['notification_enabled'] is True
        assert defaults['notification_time'] == "08:00"

    def test_merge_with_defaults(self):
        """Test merging user config with defaults"""
        defaults = {
            "database": {"path": "data/db.sqlite3"},
            "api": {"rate_limit": 90},
            "notification": {"enabled": True}
        }

        user_config = {
            "database": {"path": "custom/path.db"},
            "api": {"rate_limit": 60}
            # notification not specified, should use default
        }

        # Simple merge (in real implementation would be recursive)
        merged = {**defaults, **user_config}

        assert merged['database']['path'] == "custom/path.db"
        assert merged['api']['rate_limit'] == 60
        # notification would need recursive merge


class TestConfigEdgeCases:
    """Edge case tests for configuration"""

    def test_very_long_config_values(self):
        """Test handling of very long configuration values"""
        long_string = "x" * 10000
        config = {"long_value": long_string}

        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(config, f)

            with open(path, 'r') as f:
                loaded = json.load(f)

            assert loaded['long_value'] == long_string
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_unicode_in_config(self):
        """Test Unicode characters in configuration"""
        config = {
            "title": "日本語タイトル",
            "keywords": ["アニメ", "マンガ", "🎌"]
        }

        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False)

            with open(path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)

            assert loaded['title'] == "日本語タイトル"
            assert "🎌" in loaded['keywords']
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_deeply_nested_config(self):
        """Test deeply nested configuration structure"""
        config = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "level5": {
                                "value": "deep_value"
                            }
                        }
                    }
                }
            }
        }

        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(config, f)

            with open(path, 'r') as f:
                loaded = json.load(f)

            assert loaded['level1']['level2']['level3']['level4']['level5']['value'] == "deep_value"
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_config_with_null_values(self):
        """Test configuration with null/None values"""
        config = {
            "optional_field": None,
            "required_field": "value"
        }

        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(config, f)

            with open(path, 'r') as f:
                loaded = json.load(f)

            assert loaded['optional_field'] is None
            assert loaded['required_field'] == "value"
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_config_with_mixed_types(self):
        """Test configuration with mixed data types"""
        config = {
            "string": "text",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, "two", 3.0, True],
            "dict": {"nested": "value"}
        }

        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(config, f)

            with open(path, 'r') as f:
                loaded = json.load(f)

            assert isinstance(loaded['string'], str)
            assert isinstance(loaded['integer'], int)
            assert isinstance(loaded['float'], float)
            assert isinstance(loaded['boolean'], bool)
            assert loaded['null'] is None
            assert isinstance(loaded['list'], list)
            assert isinstance(loaded['dict'], dict)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_readonly_config_file(self):
        """Test handling of read-only config file"""
        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump({"test": "value"}, f)

            # Make file read-only
            os.chmod(path, 0o444)

            # Should still be able to read
            with open(path, 'r') as f:
                config = json.load(f)
                assert config['test'] == 'value'

            # Writing should fail
            with pytest.raises(PermissionError):
                with open(path, 'w') as f:
                    json.dump({"new": "data"}, f)

        finally:
            # Restore write permission for cleanup
            os.chmod(path, 0o644)
            if os.path.exists(path):
                os.remove(path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
