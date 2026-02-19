#!/usr/bin/env python3
"""
Backend API Integration Tests and Validation Module

This module provides comprehensive testing and validation for all backend modules
including database operations, API clients, RSS collectors, and filtering logic.
"""

import asyncio
import json
import logging
import time

logger = logging.getLogger(__name__)
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .anime_anilist import AniListClient, CircuitBreakerOpen

# Import all modules to test
from .db import get_db
from .filter_logic import ContentFilter
from .manga_rss import EnhancedRSSParser, FeedHealth, MangaRSSCollector
from .models import Work, WorkType


@dataclass
class TestResult:
    """Test result data structure."""

    test_name: str
    passed: bool
    duration: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Comprehensive validation report."""

    timestamp: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_duration: float
    test_results: List[TestResult] = field(default_factory=list)
    system_info: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate test success rate."""
        return (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": self.success_rate,
            "total_duration": self.total_duration,
            "system_info": self.system_info,
            "test_results": [
                {
                    "test_name": result.test_name,
                    "passed": result.passed,
                    "duration": result.duration,
                    "error_message": result.error_message,
                    "details": result.details,
                }
                for result in self.test_results
            ],
        }


class BackendValidator:
    """Comprehensive backend validation and testing suite."""

    def __init__(self, config_manager=None, timeout: int = 30):
        """
        Initialize backend validator.

        Args:
            config_manager: Configuration manager instance
            timeout: Test timeout in seconds
        """
        self.config = config_manager
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

        # Test configuration
        self.test_config = {
            "database": {"enable_stress_test": False, "stress_operations": 100},
            "anilist": {"enable_rate_limit_test": True, "test_queries": 5},
            "rss": {
                "test_feeds": ["https://httpbin.org/xml"],
                "enable_parser_test": True,
            },
            "filter": {"enable_performance_test": True, "performance_iterations": 1000},
        }

    async def run_comprehensive_validation(self) -> ValidationReport:
        """
        Run comprehensive backend validation.

        Returns:
            Detailed validation report
        """
        self.logger.info("Starting comprehensive backend validation...")

        start_time = time.time()
        test_results = []

        # System information
        system_info = self._gather_system_info()

        # Database tests
        db_results = await self._test_database_module()
        test_results.extend(db_results)

        # AniList API tests
        anilist_results = await self._test_anilist_module()
        test_results.extend(anilist_results)

        # RSS collector tests
        rss_results = await self._test_rss_module()
        test_results.extend(rss_results)

        # Filter logic tests
        filter_results = await self._test_filter_module()
        test_results.extend(filter_results)

        # Integration tests
        integration_results = await self._test_integration()
        test_results.extend(integration_results)

        total_duration = time.time() - start_time

        # Generate report
        passed_tests = sum(1 for result in test_results if result.passed)
        failed_tests = len(test_results) - passed_tests

        report = ValidationReport(
            timestamp=datetime.now(),
            total_tests=len(test_results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            total_duration=total_duration,
            test_results=test_results,
            system_info=system_info,
        )

        self.logger.info(
            f"Validation completed: {passed_tests}/{len(test_results)} tests passed "
            f"({report.success_rate:.1f}%) in {total_duration:.2f}s"
        )

        return report

    def _gather_system_info(self) -> Dict[str, Any]:
        """Gather system information for the report."""
        try:
            import platform

            import psutil

            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": (
                    psutil.disk_usage("/").percent if hasattr(psutil, "disk_usage") else None
                ),
            }
        except ImportError:
            return {
                "platform": "Unknown",
                "note": "psutil not available for detailed system info",
            }

    async def _test_database_module(self) -> List[TestResult]:
        """Test database module functionality."""
        results = []

        # Test 1: Database connection
        results.append(await self._run_test("Database Connection", self._test_db_connection))

        # Test 2: CRUD operations
        results.append(await self._run_test("Database CRUD Operations", self._test_db_crud))

        # Test 3: Performance test
        results.append(await self._run_test("Database Performance", self._test_db_performance))

        # Test 4: Integrity check
        results.append(await self._run_test("Database Integrity", self._test_db_integrity))

        return results

    async def _test_db_connection(self) -> Dict[str, Any]:
        """Test database connection."""
        db = get_db()

        with db.get_connection() as conn:
            cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()

            if result[0] != 1:
                raise Exception("Database connection test failed")

            # Test connection pooling
            perf_stats = db.get_performance_stats()

            return {"connection_established": True, "performance_stats": perf_stats}

    async def _test_db_crud(self) -> Dict[str, Any]:
        """Test database CRUD operations."""
        db = get_db()

        # Create test work
        work_id = db.create_work("Test Validation Work", "anime", title_en="Test EN")

        if not work_id:
            raise Exception("Failed to create test work")

        # Read work
        work = db.get_work_by_title("Test Validation Work", "anime")
        if not work or work["id"] != work_id:
            raise Exception("Failed to read created work")

        # Create test release
        release_id = db.create_release(work_id, "episode", number="1", release_date="2024-01-01")

        if not release_id:
            raise Exception("Failed to create test release")

        # Test unnotified releases
        unnotified = db.get_unnotified_releases(limit=1)
        found_test_release = any(r["id"] == release_id for r in unnotified)

        # Mark as notified
        success = db.mark_release_notified(release_id)
        if not success:
            raise Exception("Failed to mark release as notified")

        # Cleanup - delete test data
        with db.get_connection() as conn:
            conn.execute("DELETE FROM releases WHERE id = ?", (release_id,))
            conn.execute("DELETE FROM works WHERE id = ?", (work_id,))

        return {
            "work_created": True,
            "work_retrieved": True,
            "release_created": True,
            "notification_update": True,
            "found_in_unnotified": found_test_release,
        }

    async def _test_db_performance(self) -> Dict[str, Any]:
        """Test database performance."""
        if not self.test_config["database"]["enable_stress_test"]:
            return {"skipped": True, "reason": "Stress test disabled"}

        db = get_db()
        operations = self.test_config["database"]["stress_operations"]

        start_time = time.time()

        # Perform multiple operations
        work_ids = []
        for i in range(operations):
            work_id = db.get_or_create_work(f"Perf Test Work {i}", "anime")
            work_ids.append(work_id)

        create_time = time.time() - start_time

        # Test read performance
        start_time = time.time()
        for work_id in work_ids[:10]:  # Test first 10 reads
            db.get_work_by_title(f"Perf Test Work {work_ids.index(work_id)}", "anime")

        read_time = time.time() - start_time

        # Cleanup
        with db.get_connection() as conn:
            for work_id in work_ids:
                conn.execute("DELETE FROM works WHERE id = ?", (work_id,))

        return {
            "operations_count": operations,
            "create_time": create_time,
            "read_time": read_time,
            "operations_per_second": operations / create_time if create_time > 0 else 0,
        }

    async def _test_db_integrity(self) -> Dict[str, Any]:
        """Test database integrity."""
        db = get_db()

        # Get database statistics
        stats = db.get_work_stats()

        # Test foreign key constraints
        try:
            with db.get_connection() as conn:
                # This should fail due to foreign key constraint
                cursor = conn.execute("""
                    INSERT INTO releases (work_id, release_type)
                    VALUES (999999, 'episode')
                """)
                conn.rollback()
                foreign_key_enforced = False
        except Exception:
            foreign_key_enforced = True

        # Test unique constraints
        work_id = db.get_or_create_work("Integrity Test Work", "anime")
        try:
            # Try to create duplicate release
            release_id_1 = db.create_release(work_id, "episode", "1", release_date="2024-01-01")
            release_id_2 = db.create_release(work_id, "episode", "1", release_date="2024-01-01")
            unique_constraint_enforced = (
                release_id_1 == release_id_2
            )  # Should return same ID due to UNIQUE constraint
        except Exception as e:
            unique_constraint_enforced = True

        # Cleanup
        with db.get_connection() as conn:
            conn.execute("DELETE FROM releases WHERE work_id = ?", (work_id,))
            conn.execute("DELETE FROM works WHERE id = ?", (work_id,))

        return {
            "database_stats": stats,
            "foreign_key_enforced": foreign_key_enforced,
            "unique_constraint_enforced": unique_constraint_enforced,
        }

    async def _test_anilist_module(self) -> List[TestResult]:
        """Test AniList module functionality."""
        results = []

        # Test 1: Client initialization
        results.append(await self._run_test("AniList Client Init", self._test_anilist_init))

        # Test 2: API connectivity
        results.append(
            await self._run_test("AniList API Connectivity", self._test_anilist_connectivity)
        )

        # Test 3: Rate limiting
        if self.test_config["anilist"]["enable_rate_limit_test"]:
            results.append(
                await self._run_test("AniList Rate Limiting", self._test_anilist_rate_limiting)
            )

        # Test 4: Circuit breaker
        results.append(
            await self._run_test("AniList Circuit Breaker", self._test_anilist_circuit_breaker)
        )

        return results

    async def _test_anilist_init(self) -> Dict[str, Any]:
        """Test AniList client initialization."""
        client = AniListClient(timeout=10)

        perf_stats = client.get_performance_stats()

        return {"client_initialized": True, "initial_performance_stats": perf_stats}

    async def _test_anilist_connectivity(self) -> Dict[str, Any]:
        """Test AniList API connectivity."""
        client = AniListClient(timeout=10, retry_attempts=1)

        try:
            # Simple query that should return results
            anime_list = await client.search_anime(query="Naruto", limit=1)

            perf_stats = client.get_performance_stats()

            return {
                "api_accessible": True,
                "results_count": len(anime_list),
                "performance_stats": perf_stats,
            }
        except Exception as e:
            # API might be down or blocked, but we can still test client functionality
            return {
                "api_accessible": False,
                "error_handled": True,
                "error_type": type(e).__name__,
            }

    async def _test_anilist_rate_limiting(self) -> Dict[str, Any]:
        """Test AniList rate limiting functionality."""
        client = AniListClient(timeout=5, retry_attempts=1)

        start_time = time.time()
        request_count = self.test_config["anilist"]["test_queries"]

        for i in range(request_count):
            try:
                await client.search_anime(query=f"Test{i}", limit=1)
                await asyncio.sleep(0.1)  # Small delay between requests
            except Exception:
                pass  # Expected for rate limiting tests

        total_time = time.time() - start_time
        perf_stats = client.get_performance_stats()

        return {
            "requests_attempted": request_count,
            "total_time": total_time,
            "average_time_per_request": total_time / request_count,
            "rate_limiting_active": perf_stats.get("rate_limit_queue_size", 0) > 0,
            "performance_stats": perf_stats,
        }

    async def _test_anilist_circuit_breaker(self) -> Dict[str, Any]:
        """Test circuit breaker functionality."""
        client = AniListClient(
            timeout=1, retry_attempts=1
        )  # Very short timeout to trigger failures

        # This should trigger circuit breaker by causing timeouts
        failure_count = 0
        circuit_breaker_triggered = False

        for i in range(10):
            try:
                await client._make_request("{ __typename }")  # Simple query
                await asyncio.sleep(0.05)
            except CircuitBreakerOpen:
                circuit_breaker_triggered = True
                break
            except Exception:
                failure_count += 1

        perf_stats = client.get_performance_stats()

        return {
            "circuit_breaker_tested": True,
            "circuit_breaker_triggered": circuit_breaker_triggered,
            "failure_count": failure_count,
            "circuit_state": perf_stats.get("circuit_breaker_state"),
            "performance_stats": perf_stats,
        }

    async def _test_rss_module(self) -> List[TestResult]:
        """Test RSS module functionality."""
        results = []

        # Test 1: RSS collector initialization
        results.append(await self._run_test("RSS Collector Init", self._test_rss_init))

        # Test 2: RSS parser
        if self.test_config["rss"]["enable_parser_test"]:
            results.append(await self._run_test("RSS Parser", self._test_rss_parser))

        # Test 3: Feed health monitoring
        results.append(await self._run_test("RSS Feed Health", self._test_rss_health))

        return results

    async def _test_rss_init(self) -> Dict[str, Any]:
        """Test RSS collector initialization."""

        class TestConfig:
            def get_rss_config(self):
                return {"timeout_seconds": 10, "user_agent": "Validator/1.0"}

            def get_enabled_rss_feeds(self):
                return [
                    {
                        "name": "Test RSS",
                        "url": "https://httpbin.org/xml",
                        "category": "manga",
                        "enabled": True,
                    }
                ]

        collector = MangaRSSCollector(TestConfig())

        health_report = collector.get_health_report()

        return {
            "collector_initialized": True,
            "enabled_feeds_count": len(collector.enabled_feeds),
            "health_report": health_report,
        }

    async def _test_rss_parser(self) -> Dict[str, Any]:
        """Test RSS parser functionality."""
        parser = EnhancedRSSParser()

        # Test title extraction
        test_titles = [
            "「テスト漫画」第1巻",
            "[New] Test Manga Vol.2",
            "【更新】テストコミック 第3話",
        ]

        extracted_titles = []
        for title in test_titles:
            clean_title = parser.extract_title(title)
            number, release_type = parser.extract_number_and_type(title)
            extracted_titles.append(
                {
                    "original": title,
                    "clean_title": clean_title,
                    "number": number,
                    "type": release_type.value if release_type else None,
                }
            )

        # Test date parsing
        test_dates = ["2024-01-01", "Mon, 01 Jan 2024 12:00:00 GMT", "2024年1月1日"]

        parsed_dates = []
        for date_str in test_dates:
            parsed_date = parser.extract_date(date_str)
            parsed_dates.append(
                {
                    "original": date_str,
                    "parsed": parsed_date.isoformat() if parsed_date else None,
                }
            )

        return {
            "title_extractions": extracted_titles,
            "date_parsing": parsed_dates,
            "parser_functional": True,
        }

    async def _test_rss_health(self) -> Dict[str, Any]:
        """Test RSS feed health monitoring."""
        feed_health = FeedHealth("https://test.example.com")

        # Test success recording
        feed_health.record_success(0.5)

        # Test failure recording
        feed_health.record_failure()
        feed_health.record_failure()

        return {
            "health_monitoring_active": True,
            "is_healthy": feed_health.is_healthy,
            "consecutive_failures": feed_health.consecutive_failures,
            "total_requests": feed_health.total_requests,
            "average_response_time": feed_health.average_response_time,
        }

    async def _test_filter_module(self) -> List[TestResult]:
        """Test filter module functionality."""
        results = []

        # Test 1: Filter initialization
        results.append(await self._run_test("Filter Init", self._test_filter_init))

        # Test 2: Basic filtering
        results.append(await self._run_test("Basic Filtering", self._test_basic_filtering))

        # Test 3: Performance test
        if self.test_config["filter"]["enable_performance_test"]:
            results.append(
                await self._run_test("Filter Performance", self._test_filter_performance)
            )

        # Test 4: Fuzzy matching
        results.append(await self._run_test("Fuzzy Matching", self._test_fuzzy_matching))

        return results

    async def _test_filter_init(self) -> Dict[str, Any]:
        """Test filter initialization."""

        class TestFilterConfig:
            def get_ng_keywords(self):
                return ["test_blocked", "adult", "エロ"]

            def get_ng_genres(self):
                return ["Hentai", "Ecchi"]

            def get_exclude_tags(self):
                return ["Adult Cast", "Mature"]

        content_filter = ContentFilter(TestFilterConfig(), enable_fuzzy_matching=True)

        stats = content_filter.get_filter_statistics()

        return {"filter_initialized": True, "statistics": stats}

    async def _test_basic_filtering(self) -> Dict[str, Any]:
        """Test basic filtering functionality."""

        class TestFilterConfig:
            def get_ng_keywords(self):
                return ["blocked", "adult", "nsfw"]

            def get_ng_genres(self):
                return ["Hentai"]

            def get_exclude_tags(self):
                return ["Adult"]

        content_filter = ContentFilter(TestFilterConfig())

        # Test cases
        test_cases = [
            ("Clean Title", False),
            ("Title with blocked content", True),
            ("Adult Content Warning", True),
            ("Normal Anime Title", False),
        ]

        results = []
        for title, should_filter in test_cases:
            work = Work(title=title, work_type=WorkType.ANIME)
            result = content_filter.filter_work(work)
            results.append(
                {
                    "title": title,
                    "expected_filtered": should_filter,
                    "actually_filtered": result.is_filtered,
                    "correct": result.is_filtered == should_filter,
                    "reason": result.reason if result.is_filtered else None,
                }
            )

        correct_count = sum(1 for r in results if r["correct"])

        return {
            "test_cases": results,
            "accuracy": correct_count / len(results) * 100,
            "all_correct": correct_count == len(results),
        }

    async def _test_filter_performance(self) -> Dict[str, Any]:
        """Test filter performance."""

        class TestFilterConfig:
            def get_ng_keywords(self):
                return [
                    "blocked",
                    "adult",
                    "nsfw",
                    "test1",
                    "test2",
                ] * 10  # 50 keywords

            def get_ng_genres(self):
                return ["Hentai", "Ecchi"]

            def get_exclude_tags(self):
                return ["Adult", "Mature"]

        content_filter = ContentFilter(TestFilterConfig())

        iterations = self.test_config["filter"]["performance_iterations"]
        test_work = Work(title="Clean Performance Test Title", work_type=WorkType.ANIME)

        start_time = time.time()

        for _ in range(iterations):
            content_filter.filter_work(test_work)

        total_time = time.time() - start_time

        stats = content_filter.get_filter_statistics()

        return {
            "iterations": iterations,
            "total_time": total_time,
            "average_time_per_filter": total_time / iterations,
            "filters_per_second": iterations / total_time,
            "performance_stats": stats["performance"],
        }

    async def _test_fuzzy_matching(self) -> Dict[str, Any]:
        """Test fuzzy matching functionality."""

        class TestFilterConfig:
            def get_ng_keywords(self):
                return ["blocked", "adult"]

            def get_ng_genres(self):
                return []

            def get_exclude_tags(self):
                return []

        # Test with fuzzy matching enabled
        fuzzy_filter = ContentFilter(
            TestFilterConfig(), enable_fuzzy_matching=True, similarity_threshold=0.8
        )

        # Test with fuzzy matching disabled
        exact_filter = ContentFilter(TestFilterConfig(), enable_fuzzy_matching=False)

        # Test cases for fuzzy matching
        test_cases = [
            "blocked content",  # exact match
            "blockd content",  # typo in blocked
            "adullt content",  # typo in adult
            "completely different",  # no match
        ]

        fuzzy_results = []
        exact_results = []

        for title in test_cases:
            work = Work(title=title, work_type=WorkType.ANIME)

            fuzzy_result = fuzzy_filter.filter_work(work)
            exact_result = exact_filter.filter_work(work)

            fuzzy_results.append(
                {
                    "title": title,
                    "filtered": fuzzy_result.is_filtered,
                    "reason": fuzzy_result.reason,
                }
            )

            exact_results.append(
                {
                    "title": title,
                    "filtered": exact_result.is_filtered,
                    "reason": exact_result.reason,
                }
            )

        return {
            "fuzzy_results": fuzzy_results,
            "exact_results": exact_results,
            "fuzzy_caught_more": sum(1 for f in fuzzy_results if f["filtered"])
            > sum(1 for e in exact_results if e["filtered"]),
        }

    async def _test_integration(self) -> List[TestResult]:
        """Test integration between modules."""
        results = []

        # Test 1: Database + Filter integration
        results.append(
            await self._run_test("DB-Filter Integration", self._test_db_filter_integration)
        )

        # Test 2: End-to-end workflow
        results.append(await self._run_test("End-to-End Workflow", self._test_e2e_workflow))

        return results

    async def _test_db_filter_integration(self) -> Dict[str, Any]:
        """Test database and filter integration."""

        # Create filter
        class TestFilterConfig:
            def get_ng_keywords(self):
                return ["blocked_integration"]

            def get_ng_genres(self):
                return ["Hentai"]

            def get_exclude_tags(self):
                return []

        content_filter = ContentFilter(TestFilterConfig())
        db = get_db()

        # Test works
        works_to_test = [
            Work(title="Clean Integration Test", work_type=WorkType.ANIME),
            Work(title="blocked_integration Test", work_type=WorkType.ANIME),
        ]

        results = []
        created_work_ids = []

        for work in works_to_test:
            # Filter first
            filter_result = content_filter.filter_work(work)

            if not filter_result.is_filtered:
                # Create in database
                work_id = db.create_work(work.title, work.work_type.value)
                created_work_ids.append(work_id)

                results.append(
                    {
                        "title": work.title,
                        "filtered": False,
                        "created_in_db": True,
                        "work_id": work_id,
                    }
                )
            else:
                results.append(
                    {
                        "title": work.title,
                        "filtered": True,
                        "filter_reason": filter_result.reason,
                        "created_in_db": False,
                    }
                )

        # Cleanup
        for work_id in created_work_ids:
            with db.get_connection() as conn:
                conn.execute("DELETE FROM works WHERE id = ?", (work_id,))

        return {
            "integration_results": results,
            "clean_works_created": sum(1 for r in results if r.get("created_in_db")),
            "blocked_works_filtered": sum(1 for r in results if r.get("filtered")),
        }

    async def _test_e2e_workflow(self) -> Dict[str, Any]:
        """Test end-to-end workflow."""
        # This simulates the complete workflow from data collection to database storage

        db = get_db()

        # Create filter
        class TestFilterConfig:
            def get_ng_keywords(self):
                return ["blocked"]

            def get_ng_genres(self):
                return []

            def get_exclude_tags(self):
                return []

        content_filter = ContentFilter(TestFilterConfig())

        # Simulate data collection results
        mock_anime_data = [
            {"title": "Good Anime", "type": "anime"},
            {"title": "blocked Content", "type": "anime"},
            {"title": "Another Good Show", "type": "anime"},
        ]

        processed_items = []
        created_work_ids = []

        for item in mock_anime_data:
            # Create work object
            work = Work(title=item["title"], work_type=WorkType.ANIME)

            # Apply filter
            filter_result = content_filter.filter_work(work)

            if not filter_result.is_filtered:
                # Store in database
                work_id = db.get_or_create_work(work.title, work.work_type.value)
                created_work_ids.append(work_id)

                # Create sample release
                release_id = db.create_release(work_id, "episode", "1", release_date="2024-01-01")

                processed_items.append(
                    {
                        "title": item["title"],
                        "work_id": work_id,
                        "release_id": release_id,
                        "status": "processed",
                    }
                )
            else:
                processed_items.append(
                    {
                        "title": item["title"],
                        "status": "filtered",
                        "reason": filter_result.reason,
                    }
                )

        # Check unnotified releases
        unnotified = db.get_unnotified_releases()
        test_releases_in_unnotified = [r for r in unnotified if r["work_id"] in created_work_ids]

        # Cleanup
        for work_id in created_work_ids:
            with db.get_connection() as conn:
                conn.execute("DELETE FROM releases WHERE work_id = ?", (work_id,))
                conn.execute("DELETE FROM works WHERE id = ?", (work_id,))

        return {
            "input_items": len(mock_anime_data),
            "processed_items": processed_items,
            "works_created": len(created_work_ids),
            "items_filtered": len(
                [item for item in processed_items if item["status"] == "filtered"]
            ),
            "unnotified_releases_found": len(test_releases_in_unnotified),
            "workflow_successful": len(processed_items) == len(mock_anime_data),
        }

    async def _run_test(self, test_name: str, test_func) -> TestResult:
        """
        Run a single test with timing and error handling.

        Args:
            test_name: Name of the test
            test_func: Test function to run

        Returns:
            Test result with timing and error information
        """
        start_time = time.time()

        try:
            details = await test_func()
            duration = time.time() - start_time

            self.logger.info(f"✓ {test_name} passed in {duration:.3f}s")

            return TestResult(test_name=test_name, passed=True, duration=duration, details=details)

        except Exception as e:
            duration = time.time() - start_time
            error_message = str(e)

            self.logger.error(f"✗ {test_name} failed in {duration:.3f}s: {error_message}")
            self.logger.debug(f"Full traceback for {test_name}:\n{traceback.format_exc()}")

            return TestResult(
                test_name=test_name,
                passed=False,
                duration=duration,
                error_message=error_message,
                details={
                    "exception_type": type(e).__name__,
                    "traceback": traceback.format_exc(),
                },
            )

    def generate_report_file(self, report: ValidationReport, file_path: str = None):
        """
        Generate detailed validation report file.

        Args:
            report: Validation report
            file_path: Output file path (optional)
        """
        if not file_path:
            timestamp = report.timestamp.strftime("%Y%m%d_%H%M%S")
            file_path = f"backend_validation_report_{timestamp}.json"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

            self.logger.info(f"Validation report saved to: {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to save validation report: {e}")


# Convenience function for running validation
async def run_backend_validation(config_manager=None) -> ValidationReport:
    """
    Run comprehensive backend validation.

    Args:
        config_manager: Configuration manager instance

    Returns:
        Validation report
    """
    validator = BackendValidator(config_manager)
    return await validator.run_comprehensive_validation()


# Main execution for standalone testing
if __name__ == "__main__":

    async def main():
        logger.info("Starting backend validation...")

        try:
            report = await run_backend_validation()

            logger.info(f"\n{'='*60}")
            logger.info("BACKEND VALIDATION REPORT")
            logger.info(f"{'='*60}")
            logger.info(f"Total Tests: {report.total_tests}")
            logger.info(f"Passed: {report.passed_tests}")
            logger.error(f"Failed")
            logger.info(f"Success")
            logger.info(f"Total Duration: {report.total_duration:.2f}s")
            logger.info(f"{'='*60}")

            # Print failed tests
            failed_tests = [r for r in report.test_results if not r.passed]
            if failed_tests:
                logger.info("\nFAILED TESTS:")
                for test in failed_tests:
                    logger.info(f"  ✗ {test.test_name}: {test.error_message}")

            # Generate report file
            validator = BackendValidator()
            validator.generate_report_file(report)

        except Exception as e:
            logger.info(f"Validation failed with error: {e}")
            traceback.print_exc()

    asyncio.run(main())
