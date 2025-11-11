"""
MangaAnime Information Delivery System - Test Suite

This package contains comprehensive tests for the anime/manga information
delivery system, including unit tests, integration tests, and end-to-end tests.

Test Structure:
- Unit tests: Test individual modules and functions in isolation
- Integration tests: Test interactions between components
- E2E tests: Test complete workflows from data collection to notification
- Performance tests: Test system performance under load
- Security tests: Test security compliance and vulnerability checks

Test Categories:
- test_database.py: Database operations and models
- test_config.py: Configuration management
- test_anilist_api.py: AniList GraphQL API integration
- test_rss_processing.py: RSS feed processing
- test_filtering.py: Content filtering logic
- test_google_apis.py: Gmail and Calendar API integration
- test_mailer_integration.py: Email notification system
- test_calendar_integration.py: Calendar integration
- test_monitoring.py: System monitoring and logging
- test_security_comprehensive.py: Security validation
- test_performance_*.py: Performance testing suite
- test_e2e_workflow.py: End-to-end workflow testing

Usage:
    # Run all tests
    pytest

    # Run specific test category
    pytest tests/test_database.py

    # Run with coverage
    pytest --cov=modules --cov-report=html

    # Run performance tests
    pytest tests/test_performance_*.py

Test Configuration:
- Uses pytest as the testing framework
- Includes fixtures for database and API mocking
- Supports parallel test execution
- Generates coverage reports in HTML and XML formats
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test configuration
TEST_DB_PATH = ":memory:"  # Use in-memory database for tests
TEST_CONFIG_PATH = project_root / "config.json.template"
TEST_DATA_DIR = Path(__file__).parent / "fixtures" / "data"
MOCK_API_DIR = Path(__file__).parent / "fixtures" / "mock_api_data"

# Logging configuration for tests
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise during testing
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Disable logging for external libraries during tests
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.getLogger("google").setLevel(logging.CRITICAL)


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (medium speed)"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests (slow, full system)"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests (benchmarking)"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests (vulnerability checks)"
    )
    config.addinivalue_line(
        "markers", "api: marks tests that require external API access"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running (> 5 seconds)"
    )


def get_test_database_path():
    """Get the test database path."""
    return TEST_DB_PATH


def get_test_config_path():
    """Get the test configuration file path."""
    return TEST_CONFIG_PATH


def get_test_data_dir():
    """Get the test data directory path."""
    return TEST_DATA_DIR


def get_mock_api_dir():
    """Get the mock API data directory path."""
    return MOCK_API_DIR


# Test utility functions
def setup_test_environment():
    """Set up the test environment with necessary fixtures."""
    # Ensure test directories exist
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    MOCK_API_DIR.mkdir(parents=True, exist_ok=True)

    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_PATH"] = TEST_DB_PATH


def cleanup_test_environment():
    """Clean up the test environment after tests."""
    # Remove test environment variables
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
    if "DATABASE_PATH" in os.environ:
        del os.environ["DATABASE_PATH"]


# Export commonly used test utilities
__all__ = [
    "TEST_DB_PATH",
    "TEST_CONFIG_PATH",
    "TEST_DATA_DIR",
    "MOCK_API_DIR",
    "get_test_database_path",
    "get_test_config_path",
    "get_test_data_dir",
    "get_mock_api_dir",
    "setup_test_environment",
    "cleanup_test_environment",
    "pytest_configure",
]
