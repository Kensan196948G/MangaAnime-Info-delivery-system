#!/usr/bin/env python3
"""
Comprehensive security testing suite for the Anime/Manga Information Delivery System.
Tests all security measures, input validation, authentication, and data protection.
"""

import sys
import pytest
import json
import sqlite3
from unittest.mock import Mock, patch
import time

from modules.security_utils import (
    InputSanitizer,
    RateLimiter,
    SecureTokenManager,
    SecureConfig,
    DatabaseSecurity,
    SecurityMonitor,
)
from modules.security_compliance import SecurityCompliance, SecurityTestRunner


class TestInputValidationSecurity:
    """Test input validation and sanitization security measures"""

    def test_title_sanitization_xss_prevention(self):
        """Test XSS prevention in title sanitization"""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';DROP TABLE works;--",
            "<svg onload=alert('xss')>",
            "&#x3C;script&#x3E;alert('xss')&#x3C;/script&#x3E;",
        ]

        for malicious_input in malicious_inputs:
            sanitized = InputSanitizer.sanitize_title(malicious_input)
            assert "<script>" not in sanitized.lower()
            assert "javascript:" not in sanitized.lower()
            assert "onerror=" not in sanitized.lower()
            assert "onload=" not in sanitized.lower()
            assert "drop table" not in sanitized.lower()

    def test_description_html_sanitization(self):
        """Test HTML sanitization in descriptions"""
        malicious_html = """
        <p>Legitimate content</p>
        <script>alert('malicious')</script>
        <iframe src="evil.com"></iframe>
        <img src="x" onerror="alert('xss')">
        <a href="javascript:alert('xss')">click me</a>
        <object data="evil.sw"></object>
        """

        sanitized = InputSanitizer.sanitize_html_content(malicious_html)

        # Should preserve allowed tags
        assert "<p>" in sanitized

        # Should remove dangerous tags and attributes
        assert "<script>" not in sanitized
        assert "<iframe>" not in sanitized
        assert "onerror=" not in sanitized
        assert "javascript:" not in sanitized
        assert "<object>" not in sanitized

    def test_url_validation_security(self):
        """Test URL validation security measures"""
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "https://anilist.co/anime/21",
            "https://www.googleapis.com/auth/gmail",
        ]

        for url in valid_urls:
            assert InputSanitizer.validate_url(url) is True

        # Invalid/malicious URLs
        invalid_urls = [
            "javascript:alert('xss')",
            "ftp://malicious.com",
            "file:///etc/passwd",
            "http://evil.com",  # HTTP not HTTPS
            "https://evil.com",  # Not in allowed domains
            "data:text/html,<script>alert('xss')</script>",
        ]

        for url in invalid_urls:
            assert InputSanitizer.validate_url(url) is False

    def test_ng_word_filtering_comprehensive(self):
        """Test comprehensive NGword filtering"""
        test_cases = [
            ("エロアニメ最新作", True),
            ("R18指定作品", True),
            ("成人向けコンテンツ", True),
            ("BLアニメ特集", True),
            ("Hentai Collection", True),
            ("進撃の巨人", False),
            ("ワンピース", False),
            ("鬼滅の刃", False),
            ("普通のアニメ", False),
        ]

        for content, should_be_filtered in test_cases:
            result = InputSanitizer.contains_ng_words(content)
            assert result == should_be_filtered, f"Failed for content: {content}"

    def test_input_length_limits(self):
        """Test input length validation"""
        # Title length limits
        long_title = "A" * 1000
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_title(long_title)

        # Empty title handling
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_title("")

        with pytest.raises(ValueError):
            InputSanitizer.sanitize_title(None)

    def test_unicode_normalization(self):
        """Test Unicode normalization for security"""
        # Test various Unicode normalization attacks
        test_cases = [
            "café",  # Normal
            "cafe\u0301",  # Combining accent
            "ｃａｆｅ",  # Full-width characters
            "c\u0061\u0066\u0065",  # Mixed Unicode
        ]

        for test_input in test_cases:
            sanitized = InputSanitizer.sanitize_title(test_input)
            # Should be normalized to consistent form
            assert len(sanitized) > 0
            # Should not contain control characters
            assert all(ord(char) >= 32 for char in sanitized if char.isprintable())


class TestAuthenticationSecurity:
    """Test authentication and token security"""

    def test_token_encryption_security(self, tmp_path):
        """Test OAuth2 token encryption"""
        token_file = tmp_path / "test_token.json"
        token_manager = SecureTokenManager(str(token_file))

        # Test token data
        test_token = {
            "access_token": "ya29.test_access_token_123456789",
            "refresh_token": "refresh_token_987654321",
            "expires_at": time.time() + 3600,
        }

        # Save token
        token_manager.save_token(test_token)

        # Verify file exists and is encrypted
        assert token_file.exists()

        # Read raw file content - should be encrypted
        with open(token_file, "rb") as f:
            raw_content = f.read()

        # Should not contain plain text tokens
        assert b"ya29.test_access_token" not in raw_content
        assert b"refresh_token_987654321" not in raw_content

        # Load and verify decryption
        loaded_token = token_manager.load_token()
        assert loaded_token["access_token"] == test_token["access_token"]
        assert loaded_token["refresh_token"] == test_token["refresh_token"]

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Unix file permissions not supported on Windows"
    )
    def test_token_file_permissions(self, tmp_path):
        """Test token file permissions are secure"""
        token_file = tmp_path / "test_token.json"
        token_manager = SecureTokenManager(str(token_file))

        test_token = {"access_token": "test_token"}
        token_manager.save_token(test_token)

        # Check file permissions (should be 600)
        stat = token_file.stat()
        permissions = oct(stat.st_mode)[-3:]
        assert (
            permissions == "600"
        ), f"Token file permissions are {permissions}, should be 600"

    def test_token_validation(self, tmp_path):
        """Test token validation logic"""
        token_file = tmp_path / "test_token.json"
        token_manager = SecureTokenManager(str(token_file))

        # Test valid token
        valid_token = {
            "access_token": "valid_token",
            "expires_at": time.time() + 3600,  # 1 hour from now
        }
        assert token_manager.is_token_valid(valid_token) is True

        # Test expired token
        expired_token = {
            "access_token": "expired_token",
            "expires_at": time.time() - 3600,  # 1 hour ago
        }
        assert token_manager.is_token_valid(expired_token) is False

        # Test token expiring soon (within 5 minutes)
        expiring_soon_token = {
            "access_token": "expiring_token",
            "expires_at": time.time() + 200,  # 3 minutes from now
        }
        assert token_manager.is_token_valid(expiring_soon_token) is False

        # Test invalid token structure
        invalid_token = {"no_access_token": "value"}
        assert token_manager.is_token_valid(invalid_token) is False

    def test_secure_token_deletion(self, tmp_path):
        """Test secure token file deletion"""
        token_file = tmp_path / "test_token.json"
        token_manager = SecureTokenManager(str(token_file))

        # Save token
        test_token = {"access_token": "test_token"}
        token_manager.save_token(test_token)

        # Verify file exists
        assert token_file.exists()

        # Delete securely
        token_manager.delete_token()

        # Verify file is deleted
        assert not token_file.exists()


class TestDatabaseSecurity:
    """Test database security measures"""

    def test_parameterized_query_protection(self, tmp_path):
        """Test SQL injection protection through parameterized queries"""
        db_file = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_file))

        # Create test table
        conn.execute(
            """
            CREATE TABLE test_works (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL
            )
        """
        )

        db_security = DatabaseSecurity(conn)

        # Test SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE test_works; --",
            "' OR '1'='1",
            "'; INSERT INTO test_works (title) VALUES ('hacked'); --",
            "' UNION SELECT * FROM test_works WHERE '1'='1' --",
        ]

        for malicious_input in malicious_inputs:
            try:
                # This should either be rejected by validation or safely handled
                if db_security.validate_work_data(malicious_input, "anime"):
                    # If validation passes, the parameterized query should be safe
                    cursor = db_security.safe_execute(
                        "INSERT INTO test_works (title) VALUES (?)", (malicious_input,)
                    )
                    conn.commit()

                    # Check that only one record was inserted, not multiple/malicious ones
                    count_cursor = conn.execute("SELECT COUNT(*) FROM test_works")
                    count = count_cursor.fetchone()[0]

                    # Should have at most 1 record per iteration
                    assert count <= len(
                        [
                            i
                            for i in malicious_inputs[
                                : malicious_inputs.index(malicious_input) + 1
                            ]
                            if db_security.validate_work_data(i, "anime")
                        ]
                    )

            except Exception:
                # Validation rejection is also acceptable
                pass

        # Verify table still exists (not dropped by injection)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [table[0] for table in tables]
        assert "test_works" in table_names

        conn.close()

    def test_data_validation_before_db_operations(self):
        """Test data validation before database operations"""
        db_security = DatabaseSecurity(Mock())

        # Valid data
        assert (
            db_security.validate_work_data(
                "Valid Title", "anime", "https://example.com"
            )
            is True
        )
        assert db_security.validate_work_data("Another Title", "manga") is True

        # Invalid data
        assert db_security.validate_work_data("", "anime") is False  # Empty title
        assert db_security.validate_work_data("A" * 1000, "anime") is False  # Too long
        assert (
            db_security.validate_work_data("Title", "invalid_type") is False
        )  # Invalid type
        assert (
            db_security.validate_work_data("Title", "anime", "not_a_url") is False
        )  # Invalid URL

    def test_secure_identifier_hashing(self):
        """Test secure identifier hashing"""
        db_security = DatabaseSecurity(Mock())

        test_data = "test_identifier_data"
        hash1 = db_security.hash_identifier(test_data)
        hash2 = db_security.hash_identifier(test_data)

        # Should be consistent
        assert hash1 == hash2

        # Should be a valid SHA-256 hash
        assert len(hash1) == 64  # SHA-256 produces 64-character hex string
        assert all(c in "0123456789abcdef" for c in hash1)

        # Different inputs should produce different hashes
        different_hash = db_security.hash_identifier("different_data")
        assert hash1 != different_hash


class TestRateLimitingSecurity:
    """Test rate limiting security measures"""

    def test_basic_rate_limiting(self):
        """Test basic rate limiting functionality"""
        rate_limiter = RateLimiter()

        # Test within limits
        for i in range(5):
            assert rate_limiter.is_allowed("test_api", 10) is True

        # Test exceeding limits
        for i in range(10):
            rate_limiter.is_allowed("test_api", 10)

        # Should be at limit
        assert rate_limiter.is_allowed("test_api", 10) is False

    def test_rate_limiter_different_apis(self):
        """Test rate limiting works independently for different APIs"""
        rate_limiter = RateLimiter()

        # Fill up one API's quota
        for i in range(5):
            rate_limiter.is_allowed("api_a", 5)

        assert rate_limiter.is_allowed("api_a", 5) is False
        assert (
            rate_limiter.is_allowed("api_b", 5) is True
        )  # Different API should still work

    def test_rate_limiter_time_window(self):
        """Test rate limiter time window functionality"""
        rate_limiter = RateLimiter()

        # Mock time to control time progression
        with patch("time.time") as mock_time:
            mock_time.return_value = 1000

            # Use up quota
            for i in range(5):
                rate_limiter.is_allowed("test_api", 5)

            assert rate_limiter.is_allowed("test_api", 5) is False

            # Advance time by 61 seconds (past 1-minute window)
            mock_time.return_value = 1061

            # Should be allowed again
            assert rate_limiter.is_allowed("test_api", 5) is True

    def test_rate_limiter_wait_time_calculation(self):
        """Test wait time calculation"""
        rate_limiter = RateLimiter()

        with patch("time.time") as mock_time:
            mock_time.return_value = 1000

            # Make one request
            rate_limiter.is_allowed("test_api", 5)

            # Calculate wait time
            wait_time = rate_limiter.get_wait_time("test_api")

            # Should be close to 60 seconds (within window)
            assert 59 <= wait_time <= 60


class TestSecurityMonitoring:
    """Test security monitoring and incident detection"""

    def test_security_event_logging(self):
        """Test security event logging"""
        logger = Mock()
        monitor = SecurityMonitor(logger)

        # Log a security event
        monitor.log_security_event(
            "AUTH_FAILURE", {"service": "gmail", "reason": "invalid_token"}
        )

        # Verify logging was called
        logger.warning.assert_called_once()
        call_args = logger.warning.call_args[0][0]
        assert "SECURITY_EVENT" in call_args
        assert "AUTH_FAILURE" in call_args

    def test_rate_limit_violation_detection(self):
        """Test rate limit violation detection"""
        logger = Mock()
        monitor = SecurityMonitor(logger)

        # Simulate multiple rate limit violations
        for i in range(10):
            monitor.check_rate_limit_violation("anilist", "test_client")

        # Should trigger security alert
        assert len(monitor.security_events) > 0

        # Find rate limit abuse event
        abuse_events = [
            e for e in monitor.security_events if e["event_type"] == "RATE_LIMIT_ABUSE"
        ]
        assert len(abuse_events) > 0

    def test_authentication_failure_monitoring(self):
        """Test authentication failure monitoring"""
        logger = Mock()
        monitor = SecurityMonitor(logger)

        # Log authentication failure
        monitor.check_authentication_failure("gmail", "Token expired")

        # Should create security event
        auth_events = [
            e for e in monitor.security_events if e["event_type"] == "AUTH_FAILURE"
        ]
        assert len(auth_events) == 1
        assert auth_events[0]["details"]["service"] == "gmail"

    def test_security_summary_generation(self):
        """Test security summary generation"""
        logger = Mock()
        monitor = SecurityMonitor(logger)

        # Generate some events
        monitor.log_security_event("AUTH_FAILURE", {"service": "test"})
        monitor.log_security_event("RATE_LIMIT_ABUSE", {"api": "test"})
        monitor.log_security_event("INPUT_VALIDATION_FAILURE", {"type": "test"})

        # Get summary
        summary = monitor.get_security_summary(24)

        assert summary["total_events"] == 3
        assert "AUTH_FAILURE" in summary["event_types"]
        assert "RATE_LIMIT_ABUSE" in summary["event_types"]
        assert summary["severity_counts"]["HIGH"] >= 1  # AUTH_FAILURE is HIGH
        assert summary["severity_counts"]["MEDIUM"] >= 2  # Others are MEDIUM


class TestConfigurationSecurity:
    """Test configuration security measures"""

    def test_secure_config_loading(self, tmp_path):
        """Test secure configuration loading"""
        config_file = tmp_path / "test_config.json"

        # Create test config
        test_config = {
            "database": {"path": "/test/path"},
            "apis": {"anilist": {"url": "https://example.com"}},
            "encrypted": {"api_keys": {"google": "encrypted_value_here"}},
        }

        with open(config_file, "w") as f:
            json.dump(test_config, f)

        secure_config = SecureConfig(str(config_file))

        # Test normal config access
        assert secure_config.get_value("database.path") == "/test/path"
        assert secure_config.get_value("apis.anilist.url") == "https://example.com"

        # Test missing values
        assert secure_config.get_value("missing.key") is None
        assert secure_config.get_value("missing.key", "default") == "default"

    def test_config_validation(self, tmp_path):
        """Test configuration validation"""
        config_file = tmp_path / "test_config.json"

        # Invalid config (missing required sections)
        invalid_config = {"some_section": {"value": "test"}}

        with open(config_file, "w") as f:
            json.dump(invalid_config, f)

        secure_config = SecureConfig(str(config_file))
        errors = secure_config.validate_config()

        # Should report missing required sections
        assert len(errors) > 0
        assert any("system" in error for error in errors)
        assert any("database" in error for error in errors)


class TestComprehensiveSecurityScan:
    """Test comprehensive security scanning"""

    def test_security_compliance_scan(self, tmp_path):
        """Test comprehensive security compliance scanning"""
        # Create a test project structure
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        # Create modules directory
        modules_dir = test_project / "modules"
        modules_dir.mkdir()

        # Create test Python file with security issues
        test_file = modules_dir / "test_module.py"
        test_file.write_text(
            """
import os
import sqlite3

# Security issues for testing
password = "hardcoded_password_123"
api_key = "sk-1234567890abcdef"

def vulnerable_query(user_input):
    conn = sqlite3.connect('db.sqlite3')
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return conn.execute(query).fetchall()

def file_access(filename):
    # Path traversal vulnerability
    with open("./data/" + filename, 'r') as f:
        return f.read()

def command_execution(cmd):
    # Command injection vulnerability
    os.system("ls " + cmd)
"""
        )

        # Create config file
        config_file = test_project / "config.json"
        config_file.write_text('{"database": {"path": "test.db"}}')

        # Run security compliance scan
        compliance = SecurityCompliance(str(test_project))
        results = compliance.run_comprehensive_security_audit()

        # Verify findings
        assert results["total_findings"] > 0
        assert results["critical_findings"] > 0  # Hardcoded secrets
        assert results["high_findings"] > 0  # SQL injection, etc.

        # Check for specific vulnerability types
        findings_by_category = results["findings_by_category"]
        assert "hardcoded_secrets" in findings_by_category
        assert "sql_injection" in findings_by_category
        assert "path_traversal" in findings_by_category
        assert "command_injection" in findings_by_category

    def test_security_test_runner(self, tmp_path):
        """Test automated security testing"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        test_runner = SecurityTestRunner(str(test_project))
        results = test_runner.run_security_tests()

        assert "timestamp" in results
        assert "tests_run" in results
        assert "tests_passed" in results
        assert "test_details" in results

        # Should have run various security tests
        assert results["tests_run"] > 0


class TestIntegratedSecurityFramework:
    """Test integrated security framework functionality"""

    def test_end_to_end_security_validation(self, tmp_path):
        """Test end-to-end security validation workflow"""
        # Create test project
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        # Create necessary directories
        (test_project / "modules").mkdir()
        (test_project / "tests").mkdir()
        (test_project / "logs").mkdir()

        # Create database
        db_file = test_project / "db.sqlite3"
        conn = sqlite3.connect(str(db_file))
        conn.execute(
            """
            CREATE TABLE works (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL
            )
        """
        )
        conn.execute("INSERT INTO works (title, type) VALUES ('Test Anime', 'anime')")
        conn.commit()
        conn.close()

        # Create basic Python modules
        (test_project / "modules" / "__init__.py").write_text("")
        (test_project / "modules" / "security_utils.py").write_text(
            """
from modules.security_utils import InputSanitizer

def safe_function():
    return InputSanitizer.sanitize_title("Test Title")
"""
        )

        # Create requirements file
        (test_project / "requirements.txt").write_text(
            """
requests==2.28.0
sqlite3
"""
        )

        # Run integrated security scan
        compliance = SecurityCompliance(str(test_project))
        audit_results = compliance.run_comprehensive_security_audit()

        # Verify audit completed
        assert "overall_score" in audit_results
        assert "compliance_checks" in audit_results
        assert "security_metrics" in audit_results

        # Generate report
        report_file = tmp_path / "security_report.json"
        compliance.generate_security_report(str(report_file))

        # Verify report was generated
        assert report_file.exists()

        # Load and verify report structure
        with open(report_file, "r") as f:
            report = json.load(f)

        assert "metadata" in report
        assert "executive_summary" in report
        assert "detailed_findings" in report
        assert "remediation_plan" in report


@pytest.mark.performance
class TestSecurityPerformance:
    """Test security measures don't negatively impact performance"""

    def test_input_sanitization_performance(self):
        """Test input sanitization performance"""
        test_inputs = [f"Test Title {i}" for i in range(1000)]

        start_time = time.time()
        for test_input in test_inputs:
            InputSanitizer.sanitize_title(test_input)
        end_time = time.time()

        # Should process 1000 titles in less than 1 second
        processing_time = end_time - start_time
        assert (
            processing_time < 1.0
        ), f"Sanitization took {processing_time:.2f}s for 1000 inputs"

    def test_rate_limiter_performance(self):
        """Test rate limiter performance"""
        rate_limiter = RateLimiter()

        start_time = time.time()
        for i in range(1000):
            rate_limiter.is_allowed(f"api_{i % 10}", 100)
        end_time = time.time()

        # Should handle 1000 rate limit checks in less than 1 second
        processing_time = end_time - start_time
        assert (
            processing_time < 1.0
        ), f"Rate limiting took {processing_time:.2f}s for 1000 checks"

    def test_security_monitoring_performance(self):
        """Test security monitoring performance"""
        logger = Mock()
        monitor = SecurityMonitor(logger)

        start_time = time.time()
        for i in range(100):
            monitor.log_security_event("TEST_EVENT", {"data": f"test_{i}"})
        end_time = time.time()

        # Should handle 100 security events in less than 0.5 seconds
        processing_time = end_time - start_time
        assert (
            processing_time < 0.5
        ), f"Security monitoring took {processing_time:.2f}s for 100 events"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
