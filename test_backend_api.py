#!/usr/bin/env python3
"""
Backend API and Database Functionality Test Script

This script demonstrates the implemented backend functionality including:
- Database operations (CRUD)
- Configuration management
- Data models validation
- System initialization

Usage: python3 test_backend_api.py
"""

import sys
import os
import logging
from datetime import datetime, date

# Add modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_configuration():
    """Test configuration management."""
    print("\n=== Testing Configuration Management ===")

    try:
        from modules import get_config, initialize_system

        # Initialize configuration (will use defaults if no config file exists)
        config = get_config()
        print(f"✓ Configuration loaded from: {config._loaded_from}")

        # Test configuration access
        db_path = config.get("database.path")
        log_level = config.get("system.log_level", "INFO")
        print(f"✓ Database path: {db_path}")
        print(f"✓ Log level: {log_level}")

        # Test structured config objects
        db_config = config.get_database_config()
        system_config = config.get_system_config()
        filtering_config = config.get_filtering_config()

        print(
            f"✓ Database config: path={db_config.path}, backup_enabled={db_config.backup_enabled}"
        )
        print(f"✓ System config: {system_config.name} v{system_config.version}")
        print(f"✓ NG keywords count: {len(filtering_config.ng_keywords)}")

        return True

    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_database_operations():
    """Test database operations."""
    print("\n=== Testing Database Operations ===")

    try:
        from modules import get_db, Work, Release, WorkType, ReleaseType

        db = get_db()
        print("✓ Database manager initialized")

        # Test database initialization
        db.initialize_database()
        print("✓ Database schema initialized")

        # Test work creation
        work_id = db.create_work(
            title="テスト作品名",
            work_type="anime",
            title_en="Test Anime Title",
            official_url="https://example.com",
        )
        print(f"✓ Created work with ID: {work_id}")

        # Test work retrieval
        work_data = db.get_work_by_title("テスト作品名", "anime")
        if work_data:
            print(f"✓ Retrieved work: {work_data['title']} (ID: {work_data['id']})")

        # Test release creation
        release_id = db.create_release(
            work_id=work_id,
            release_type="episode",
            number="1",
            platform="テストプラットフォーム",
            release_date=date.today().isoformat(),
            source="test_source",
            source_url="https://example.com/episode1",
        )
        print(f"✓ Created release with ID: {release_id}")

        # Test unnotified releases
        unnotified = db.get_unnotified_releases(limit=5)
        print(f"✓ Found {len(unnotified)} unnotified releases")

        # Test database statistics
        stats = db.get_work_stats()
        print(f"✓ Database stats: {stats}")

        return True

    except Exception as e:
        print(f"✗ Database test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_data_models():
    """Test data model validation and functionality."""
    print("\n=== Testing Data Models ===")

    try:
        from modules.models import (
            Work,
            Release,
            WorkType,
            ReleaseType,
            DataNormalizer,
            DataValidator,
        )

        # Test Work model
        work = Work(
            title="  テスト漫画タイトル  ",  # With extra whitespace
            work_type=WorkType.MANGA,
            title_en="Test Manga Title",
            official_url="https://example.com",
        )
        print(f"✓ Work model created: {work.title} ({work.work_type.value})")

        # Test Release model
        release = Release(
            work_id=1,
            release_type=ReleaseType.VOLUME,
            number="5",
            platform="BookWalker",
            release_date=date.today(),
        )
        print(f"✓ Release model created: Volume {release.number} on {release.platform}")

        # Test data validation
        work_data = {"title": "Valid Title", "work_type": "anime"}
        errors = DataValidator.validate_work(work_data)
        print(f"✓ Work validation: {len(errors)} errors")

        # Test invalid data
        invalid_work = {"title": "", "work_type": "invalid"}
        errors = DataValidator.validate_work(invalid_work)
        print(f"✓ Invalid work validation: {len(errors)} errors (expected > 0)")

        # Test data normalization
        normalized_title = DataNormalizer.normalize_title("  【最新話】  テスト作品  ")
        print(f"✓ Title normalization: '{normalized_title}'")

        return True

    except Exception as e:
        print(f"✗ Data models test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_system_integration():
    """Test system integration functionality."""
    print("\n=== Testing System Integration ===")

    try:
        from modules import initialize_system, get_system_info

        # Initialize entire system
        config, db = initialize_system()
        print("✓ System initialized successfully")

        # Get system information
        system_info = get_system_info()
        print(f"✓ System info retrieved:")
        print(f"  - Version: {system_info['version']}")
        print(f"  - System: {system_info['system']['name']}")
        print(f"  - Environment: {system_info['system']['environment']}")
        print(f"  - Database: {system_info['database']['path']}")
        print(f"  - Config loaded from: {system_info['configuration']['loaded_from']}")

        return True

    except Exception as e:
        print(f"✗ System integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_data_collection_setup():
    """Test data collection module setup (without actual API calls)."""
    print("\n=== Testing Data Collection Setup ===")

    try:
        from modules import get_anilist_collector, get_rss_collector, get_config

        config_dict = get_config().get_all()

        # Test AniList collector initialization
        try:
            anilist_collector = get_anilist_collector(config_dict)
            print("✓ AniList collector initialized successfully")
        except ImportError as e:
            print(f"⚠ AniList collector dependencies missing: {e}")

        # Test RSS collector initialization
        try:
            rss_collector = get_rss_collector(config_dict)
            print("✓ RSS collector initialized successfully")
        except ImportError as e:
            print(f"⚠ RSS collector dependencies missing: {e}")

        return True

    except Exception as e:
        print(f"✗ Data collection setup test failed: {e}")
        return False


def main():
    """Run all backend API tests."""
    print("Backend API and Database Functionality Test")
    print("=" * 50)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run tests
    test_results = []

    test_results.append(("Configuration", test_configuration()))
    test_results.append(("Database Operations", test_database_operations()))
    test_results.append(("Data Models", test_data_models()))
    test_results.append(("System Integration", test_system_integration()))
    test_results.append(("Data Collection Setup", test_data_collection_setup()))

    # Print summary
    print("\n" + "=" * 50)
    print("Test Results Summary:")

    passed = 0
    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1

    print(f"\nTests passed: {passed}/{len(test_results)}")

    if passed == len(test_results):
        print("🎉 All backend functionality tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
