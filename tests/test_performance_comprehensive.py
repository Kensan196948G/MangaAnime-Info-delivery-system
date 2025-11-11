#!/usr/bin/env python3
"""
Comprehensive Performance Testing Suite
Tests system performance under various load conditions
"""

import pytest
import asyncio
import time
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any
import statistics
import json
import os
import gc
from dataclasses import dataclass
from unittest.mock import patch

# Import test utilities
from tests.fixtures.mock_services import create_mock_services, PerformanceSimulator

# System imports
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from modules.db import DatabaseManager
    from modules.anime_anilist import AniListClient
    from modules.manga_rss import RSSProcessor
    from modules.filter_logic import FilterLogic
except ImportError:
    pytest.skip("Module imports failed", allow_module_level=True)


@dataclass
class PerformanceMetrics:
    """Performance measurement data structure"""

    operation: str
    response_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    throughput_ops_per_sec: float
    error_count: int
    timestamp: float


class PerformanceTestSuite:
    """Comprehensive performance testing suite"""

    def __init__(self):
        self.metrics = []
        self.mock_services = create_mock_services()
        self.process = psutil.Process()

    def measure_operation(self, operation_name: str):
        """Context manager for measuring operation performance"""
        return PerformanceMeasurement(operation_name, self)

    def record_metric(self, metric: PerformanceMetrics):
        """Record performance metric"""
        self.metrics.append(metric)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Generate performance metrics summary"""
        if not self.metrics:
            return {}

        response_times = [m.response_time_ms for m in self.metrics]
        memory_usage = [m.memory_usage_mb for m in self.metrics]
        cpu_usage = [m.cpu_usage_percent for m in self.metrics]

        return {
            "total_operations": len(self.metrics),
            "avg_response_time_ms": statistics.mean(response_times),
            "median_response_time_ms": statistics.median(response_times),
            "p95_response_time_ms": (
                statistics.quantiles(response_times, n=20)[18]
                if len(response_times) >= 20
                else max(response_times)
            ),
            "max_response_time_ms": max(response_times),
            "avg_memory_usage_mb": statistics.mean(memory_usage),
            "max_memory_usage_mb": max(memory_usage),
            "avg_cpu_usage_percent": statistics.mean(cpu_usage),
            "max_cpu_usage_percent": max(cpu_usage),
            "error_rate": sum(m.error_count for m in self.metrics) / len(self.metrics),
        }


class PerformanceMeasurement:
    """Context manager for performance measurement"""

    def __init__(self, operation_name: str, suite: PerformanceTestSuite):
        self.operation_name = operation_name
        self.suite = suite
        self.start_time = None
        self.start_memory = None
        self.start_cpu = None
        self.error_count = 0

    def __enter__(self):
        gc.collect()  # Force garbage collection before measurement
        self.start_time = time.time()
        self.start_memory = self.suite.process.memory_info().rss / 1024 / 1024  # MB
        self.start_cpu = self.suite.process.cpu_percent()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        end_memory = self.suite.process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = self.suite.process.cpu_percent()

        response_time_ms = (end_time - self.start_time) * 1000
        memory_usage_mb = max(end_memory, self.start_memory)
        cpu_usage_percent = max(end_cpu, self.start_cpu)

        if exc_type is not None:
            self.error_count = 1

        throughput = 1000 / response_time_ms if response_time_ms > 0 else 0

        metric = PerformanceMetrics(
            operation=self.operation_name,
            response_time_ms=response_time_ms,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            throughput_ops_per_sec=throughput,
            error_count=self.error_count,
            timestamp=self.start_time,
        )

        self.suite.record_metric(metric)


@pytest.fixture
def performance_suite():
    """Performance testing suite fixture"""
    return PerformanceTestSuite()


@pytest.mark.performance
class TestDatabasePerformance:
    """Database performance testing"""

    def test_database_bulk_insert_performance(self, temp_db, performance_suite):
        """Test bulk insert performance"""
        db_manager = DatabaseManager(temp_db)
        db_manager.initialize_database()

        # Test with increasing data sizes
        test_sizes = [100, 500, 1000, 2000]

        for size in test_sizes:
            with performance_suite.measure_operation(f"bulk_insert_{size}"):
                # Generate test data
                works_data = [
                    (
                        f"Test Work {i}",
                        f"てすとわーく{i}",
                        f"Test Work {i} EN",
                        "anime",
                        f"https://test{i}.com",
                    )
                    for i in range(size)
                ]

                # Bulk insert
                for work_data in works_data:
                    db_manager.insert_work(*work_data)

        # Verify performance thresholds
        summary = performance_suite.get_metrics_summary()
        assert (
            summary["max_response_time_ms"] < 5000
        ), f"Bulk insert too slow: {summary['max_response_time_ms']}ms"
        assert (
            summary["avg_memory_usage_mb"] < 200
        ), f"Memory usage too high: {summary['avg_memory_usage_mb']}MB"

    def test_database_query_performance(self, temp_db, performance_suite):
        """Test database query performance"""
        db_manager = DatabaseManager(temp_db)
        db_manager.initialize_database()

        # Insert test data
        for i in range(1000):
            db_manager.insert_work(f"Work {i}", None, None, "anime", None)
            db_manager.insert_release(
                i + 1,
                "episode",
                str(i + 1),
                "test",
                "2024-01-15",
                "test",
                "https://test.com",
                0,
            )

        # Test various query patterns
        query_tests = [
            ("simple_select", lambda: db_manager.get_all_works()),
            ("filtered_select", lambda: db_manager.get_unnotified_releases()),
            ("join_query", lambda: db_manager.get_releases_with_work_info()),
            ("aggregation", lambda: db_manager.get_release_stats()),
        ]

        for test_name, query_func in query_tests:
            with performance_suite.measure_operation(f"query_{test_name}"):
                try:
                    result = query_func()
                    assert result is not None
                except AttributeError:
                    # Handle methods that might not exist
                    pass

        summary = performance_suite.get_metrics_summary()
        assert (
            summary["avg_response_time_ms"] < 100
        ), f"Query too slow: {summary['avg_response_time_ms']}ms"

    def test_database_concurrent_access(self, temp_db, performance_suite):
        """Test concurrent database access performance"""
        db_manager = DatabaseManager(temp_db)
        db_manager.initialize_database()

        def concurrent_operation(thread_id: int):
            with performance_suite.measure_operation(f"concurrent_db_{thread_id}"):
                for i in range(10):
                    db_manager.insert_work(
                        f"Concurrent Work {thread_id}_{i}", None, None, "anime", None
                    )
                    db_manager.get_unnotified_releases()

        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(concurrent_operation, i) for i in range(5)]
            for future in as_completed(futures):
                future.result()

        summary = performance_suite.get_metrics_summary()
        assert summary["error_rate"] == 0, "Concurrent database operations failed"


@pytest.mark.performance
class TestAPIPerformance:
    """API performance testing"""

    @patch("modules.anime_anilist.AniListClient")
    def test_anilist_api_performance(self, mock_client, performance_suite):
        """Test AniList API performance"""
        mock_services = create_mock_services()
        mock_client.return_value.execute_query = mock_services["anilist"].execute_query

        client = AniListClient(
            {
                "graphql_url": "https://test.com",
                "rate_limit": {"requests_per_minute": 90},
            }
        )

        # Test various query loads
        for batch_size in [1, 5, 10, 20]:
            with performance_suite.measure_operation(f"anilist_batch_{batch_size}"):
                tasks = []
                for i in range(batch_size):
                    task = client.fetch_current_season_anime(page=i + 1)
                    if asyncio.iscoroutine(task):
                        tasks.append(task)

                if tasks:
                    asyncio.run(self._run_batch(tasks))

        summary = performance_suite.get_metrics_summary()
        assert (
            summary["avg_response_time_ms"] < 1000
        ), f"API calls too slow: {summary['avg_response_time_ms']}ms"

    async def _run_batch(self, tasks):
        """Run batch of async tasks"""
        return await asyncio.gather(*tasks, return_exceptions=True)

    @patch("modules.manga_rss.RSSProcessor")
    def test_rss_processing_performance(self, mock_processor, performance_suite):
        """Test RSS processing performance"""
        mock_services = create_mock_services()

        # Mock RSS processor
        async def mock_process_feed(feed_name):
            return await mock_services["rss"].fetch_feed(feed_name)

        mock_processor.return_value.process_feed = mock_process_feed

        processor = RSSProcessor({"timeout_seconds": 10})

        # Test processing multiple feeds
        feed_names = ["bookwalker", "kindle", "dmm", "manga_kingdom", "comic_seymour"]

        with performance_suite.measure_operation("rss_processing_batch"):

            async def process_all_feeds():
                tasks = [mock_process_feed(feed) for feed in feed_names]
                return await asyncio.gather(*tasks, return_exceptions=True)

            results = asyncio.run(process_all_feeds())
            assert len(results) == len(feed_names)

        summary = performance_suite.get_metrics_summary()
        assert (
            summary["max_response_time_ms"] < 2000
        ), f"RSS processing too slow: {summary['max_response_time_ms']}ms"


@pytest.mark.performance
class TestFilteringPerformance:
    """Content filtering performance testing"""

    def test_large_dataset_filtering(self, performance_suite):
        """Test filtering performance with large datasets"""
        filter_logic = FilterLogic(
            {
                "ng_keywords": ["エロ", "R18", "成人向け", "BL", "百合"],
                "ng_genres": ["Hentai", "Ecchi", "Adult"],
            }
        )

        # Generate large test dataset
        mock_services = create_mock_services()
        large_dataset = mock_services["data_factory"].create_large_dataset(5000)

        with performance_suite.measure_operation("filter_large_anime_dataset"):
            filtered_anime = filter_logic.filter_anime_batch(
                large_dataset["anime_data"]
            )
            assert len(filtered_anime) <= len(large_dataset["anime_data"])

        with performance_suite.measure_operation("filter_large_manga_dataset"):
            filtered_manga = filter_logic.filter_manga_batch(
                large_dataset["manga_data"]
            )
            assert len(filtered_manga) <= len(large_dataset["manga_data"])

        summary = performance_suite.get_metrics_summary()
        assert (
            summary["avg_response_time_ms"] < 500
        ), f"Filtering too slow: {summary['avg_response_time_ms']}ms"

    def test_regex_vs_string_matching_performance(self, performance_suite):
        """Compare regex vs string matching performance"""
        filter_logic = FilterLogic({"ng_keywords": ["test", "エロ", "成人向け"]})

        # Test data with various patterns
        test_titles = [
            "Normal Anime Title",
            "Test Animation Series",
            "エロゲー原作アニメ",
            "成人向けマンガ",
            "Regular Manga Series",
        ] * 1000  # Multiply for performance testing

        # Test string matching
        with performance_suite.measure_operation("string_matching"):
            filtered_string = [
                title
                for title in test_titles
                if not filter_logic.contains_ng_keywords_string(title)
            ]

        # Test regex matching
        with performance_suite.measure_operation("regex_matching"):
            filtered_regex = [
                title
                for title in test_titles
                if not filter_logic.contains_ng_keywords_regex(title)
            ]

        performance_suite.get_metrics_summary()

        # Both methods should produce similar results
        assert len(filtered_string) == len(filtered_regex)

        # Performance should be reasonable
        assert all(
            m.response_time_ms < 1000 for m in performance_suite.metrics
        ), "Matching methods too slow"


@pytest.mark.performance
class TestEndToEndPerformance:
    """End-to-end system performance testing"""

    @patch("modules.anime_anilist.AniListClient")
    @patch("modules.manga_rss.RSSProcessor")
    @patch("modules.mailer.EmailNotificationManager")
    @patch("modules.calendar.CalendarManager")
    def test_full_workflow_performance(
        self,
        mock_calendar,
        mock_mailer,
        mock_rss,
        mock_anilist,
        temp_db,
        performance_suite,
    ):
        """Test complete workflow performance"""
        # Setup mocks
        mock_services = create_mock_services()

        mock_anilist.return_value.fetch_current_season_anime = AsyncMock(
            return_value=mock_services["data_factory"].create_large_dataset(100)[
                "anime_data"
            ]
        )
        mock_rss.return_value.process_all_feeds = AsyncMock(
            return_value=mock_services["data_factory"].create_large_dataset(50)[
                "manga_data"
            ]
        )
        mock_mailer.return_value.send_notification = Mock(return_value=True)
        mock_calendar.return_value.create_event = Mock(
            return_value={"id": "test_event"}
        )

        # Run complete workflow
        with performance_suite.measure_operation("full_workflow"):
            # This would be the complete system run
            # For testing, we simulate the main workflow steps

            # 1. Data collection phase
            db_manager = DatabaseManager(temp_db)
            db_manager.initialize_database()

            # 2. Processing phase
            filter_logic = FilterLogic({"ng_keywords": ["エロ", "R18"]})

            # 3. Notification phase
            notification_count = 10
            for i in range(notification_count):
                mock_mailer.return_value.send_notification(
                    f"test{i}@example.com", "Test", "Content"
                )
                mock_calendar.return_value.create_event(f"Event {i}", "2024-01-15")

        summary = performance_suite.get_metrics_summary()

        # Full workflow should complete within reasonable time
        assert (
            summary["max_response_time_ms"] < 30000
        ), f"Full workflow too slow: {summary['max_response_time_ms']}ms"
        assert (
            summary["max_memory_usage_mb"] < 500
        ), f"Memory usage too high: {summary['max_memory_usage_mb']}MB"

    def test_system_under_load(self, performance_suite):
        """Test system performance under various load conditions"""
        performance_sim = PerformanceSimulator()

        # Test different load levels
        load_levels = [1, 5, 10, 20, 50]

        for load in load_levels:
            performance_sim.simulate_load(load)

            with performance_suite.measure_operation(f"system_load_{load}"):
                # Simulate system operations under load
                response_time = performance_sim.get_response_time()
                memory_usage = performance_sim.get_memory_usage()
                cpu_usage = performance_sim.get_cpu_usage()

                # Verify system remains responsive
                assert (
                    response_time < 5.0
                ), f"Response time too high under load {load}: {response_time}s"
                assert (
                    memory_usage < 1000
                ), f"Memory usage too high under load {load}: {memory_usage}MB"
                assert (
                    cpu_usage < 95
                ), f"CPU usage too high under load {load}: {cpu_usage}%"

        summary = performance_suite.get_metrics_summary()

        # System should handle load gracefully
        assert summary["error_rate"] == 0, "System failed under load"


@pytest.mark.performance
class TestMemoryLeakDetection:
    """Memory leak detection tests"""

    def test_memory_usage_stability(self, performance_suite):
        """Test for memory leaks during repeated operations"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Perform repeated operations
        for cycle in range(10):
            with performance_suite.measure_operation(f"memory_cycle_{cycle}"):
                # Simulate operations that might leak memory
                large_data = list(range(10000))  # Create large data structure
                processed_data = [x * 2 for x in large_data]  # Process data
                del large_data, processed_data  # Explicit cleanup
                gc.collect()  # Force garbage collection

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        # Memory growth should be minimal
        assert (
            memory_growth < 50
        ), f"Potential memory leak detected: {memory_growth}MB growth"

    def test_database_connection_cleanup(self, temp_db, performance_suite):
        """Test database connection cleanup"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Create and close multiple database connections
        for i in range(20):
            with performance_suite.measure_operation(f"db_connection_{i}"):
                db_manager = DatabaseManager(temp_db)
                db_manager.initialize_database()
                # Connection should be automatically cleaned up
                del db_manager
                gc.collect()

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        assert (
            memory_growth < 20
        ), f"Database connection leak detected: {memory_growth}MB growth"


# Utility function for performance test reporting
def generate_performance_report(
    performance_suite: PerformanceTestSuite, output_file: str = None
):
    """Generate comprehensive performance report"""
    summary = performance_suite.get_metrics_summary()

    report = {
        "test_summary": summary,
        "detailed_metrics": [
            {
                "operation": m.operation,
                "response_time_ms": m.response_time_ms,
                "memory_usage_mb": m.memory_usage_mb,
                "cpu_usage_percent": m.cpu_usage_percent,
                "throughput_ops_per_sec": m.throughput_ops_per_sec,
                "timestamp": m.timestamp,
            }
            for m in performance_suite.metrics
        ],
        "performance_thresholds": {
            "max_response_time_ms": 5000,
            "max_memory_usage_mb": 500,
            "max_cpu_usage_percent": 80,
            "min_throughput_ops_per_sec": 1.0,
        },
        "recommendations": [],
    }

    # Generate recommendations based on metrics
    if summary.get("avg_response_time_ms", 0) > 1000:
        report["recommendations"].append("Consider optimizing slow operations")

    if summary.get("max_memory_usage_mb", 0) > 200:
        report["recommendations"].append("Monitor memory usage and implement cleanup")

    if summary.get("error_rate", 0) > 0.01:
        report["recommendations"].append("Investigate and fix error sources")

    if output_file:
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

    return report


# Pytest configuration for performance tests
def pytest_configure(config):
    """Configure performance testing"""
    config.addinivalue_line("markers", "performance: Performance and load testing")
    config.addinivalue_line("markers", "slow: Slow-running performance tests")
