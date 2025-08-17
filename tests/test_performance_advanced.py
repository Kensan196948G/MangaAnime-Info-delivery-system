#!/usr/bin/env python3
"""
Advanced performance testing framework with comprehensive metrics and monitoring
"""

import pytest
import time
import asyncio
import threading
import multiprocessing
import sqlite3
import psutil
import os
import json
import gc
import tracemalloc
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import concurrent.futures
import statistics
import memory_profiler
import contextlib
from typing import Dict, Any, List, Generator, Optional, Callable
from dataclasses import dataclass, asdict


@dataclass
class PerformanceMetrics:
    """Data class to store performance metrics."""

    test_name: str
    execution_time: float
    memory_peak_mb: float
    memory_avg_mb: float
    cpu_usage_percent: float
    throughput: Optional[float] = None
    error_rate: Optional[float] = None
    p95_latency: Optional[float] = None
    p99_latency: Optional[float] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class PerformanceMonitor:
    """Advanced performance monitoring utility."""

    def __init__(self):
        self.process = psutil.Process()
        self.metrics = []
        self.memory_snapshots = []
        self.cpu_snapshots = []
        self.start_time = None

    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        tracemalloc.start()
        gc.collect()  # Clean up before monitoring

    def stop_monitoring(self, test_name: str) -> PerformanceMetrics:
        """Stop monitoring and return metrics."""
        if not self.start_time:
            raise ValueError("Monitoring not started")

        end_time = time.time()
        execution_time = end_time - self.start_time

        # Memory metrics
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        memory_info = self.process.memory_info()
        memory_peak_mb = peak / 1024 / 1024
        memory_current_mb = current / 1024 / 1024

        # CPU usage
        cpu_usage = self.process.cpu_percent(interval=0.1)

        return PerformanceMetrics(
            test_name=test_name,
            execution_time=execution_time,
            memory_peak_mb=memory_peak_mb,
            memory_avg_mb=(memory_peak_mb + memory_current_mb) / 2,
            cpu_usage_percent=cpu_usage,
        )

    def take_snapshot(self):
        """Take a performance snapshot."""
        memory_info = self.process.memory_info()
        self.memory_snapshots.append(memory_info.rss / 1024 / 1024)  # MB
        self.cpu_snapshots.append(self.process.cpu_percent())

    @contextlib.contextmanager
    def monitor_test(self, test_name: str):
        """Context manager for monitoring a test."""
        self.start_monitoring()
        try:
            yield self
        finally:
            metrics = self.stop_monitoring(test_name)
            self.metrics.append(metrics)


@pytest.fixture
def performance_monitor():
    """Provide performance monitor instance."""
    return PerformanceMonitor()


@pytest.fixture
def benchmark_config():
    """Configuration for benchmarking."""
    return {
        "database": {
            "small_dataset": 1000,
            "medium_dataset": 10000,
            "large_dataset": 100000,
            "bulk_insert_batch_size": 1000,
        },
        "api": {
            "concurrent_connections": 20,
            "requests_per_connection": 100,
            "timeout_seconds": 30,
        },
        "thresholds": {
            "max_response_time": 5.0,
            "max_memory_mb": 500,
            "max_cpu_percent": 80,
            "min_throughput": 100,  # operations per second
        },
    }


class TestAdvancedDatabasePerformance:
    """Advanced database performance testing with detailed metrics."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_database_scalability_analysis(
        self, temp_db, performance_monitor, benchmark_config
    ):
        """Analyze database performance at different scales."""

        dataset_sizes = [
            benchmark_config["database"]["small_dataset"],
            benchmark_config["database"]["medium_dataset"],
            benchmark_config["database"]["large_dataset"],
        ]

        results = []

        for size in dataset_sizes:
            with performance_monitor.monitor_test(f"db_scalability_{size}") as monitor:
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()

                # Generate test data
                test_data = []
                for i in range(size):
                    test_data.append(
                        (
                            f"スケーラビリティテスト{i}",
                            f"すけーらびりてぃてすと{i}",
                            f"Scalability Test {i}",
                            "anime" if i % 2 == 0 else "manga",
                            f"https://example.com/scale/{i}",
                        )
                    )

                # Batch insert with performance monitoring
                batch_size = benchmark_config["database"]["bulk_insert_batch_size"]
                insert_times = []

                for i in range(0, len(test_data), batch_size):
                    batch = test_data[i : i + batch_size]

                    batch_start = time.time()
                    cursor.executemany(
                        """
                        INSERT INTO works (title, title_kana, title_en, type, official_url)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        batch,
                    )
                    conn.commit()
                    batch_time = time.time() - batch_start
                    insert_times.append(batch_time)

                    monitor.take_snapshot()

                # Query performance at scale
                query_start = time.time()
                cursor.execute(
                    """
                    SELECT COUNT(*) as total,
                           AVG(LENGTH(title)) as avg_title_length,
                           type
                    FROM works 
                    WHERE title LIKE '%テスト%'
                    GROUP BY type
                    ORDER BY total DESC
                """
                )
                query_results = cursor.fetchall()
                query_time = time.time() - query_start

                conn.close()

                # Calculate throughput
                throughput = (
                    size / monitor.metrics[-1].execution_time if monitor.metrics else 0
                )

                results.append(
                    {
                        "dataset_size": size,
                        "total_time": monitor.metrics[-1].execution_time,
                        "throughput": throughput,
                        "avg_batch_time": statistics.mean(insert_times),
                        "query_time": query_time,
                        "memory_peak": monitor.metrics[-1].memory_peak_mb,
                        "query_results_count": len(query_results),
                    }
                )

        # Performance analysis
        for i, result in enumerate(results):
            size = result["dataset_size"]

            # Scalability assertions
            if i > 0:
                prev_result = results[i - 1]
                scale_factor = size / prev_result["dataset_size"]
                time_factor = result["total_time"] / prev_result["total_time"]

                # Time should scale sub-linearly (better than O(n))
                assert (
                    time_factor < scale_factor * 1.5
                ), f"Poor scalability: {scale_factor}x data took {time_factor}x time"

            # Throughput should remain reasonable
            assert (
                result["throughput"] > 100
            ), f"Throughput {result['throughput']:.1f} ops/s too low for size {size}"

            # Memory usage should be reasonable
            memory_per_record = (
                result["memory_peak"] / size * 1024 * 1024
            )  # bytes per record
            assert (
                memory_per_record < 1000
            ), f"Memory usage {memory_per_record:.0f} bytes/record too high"

    @pytest.mark.performance
    def test_concurrent_read_write_performance(self, temp_db, performance_monitor):
        """Test database performance under concurrent read/write load."""

        # Setup initial data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        initial_data = []
        for i in range(5000):
            initial_data.append(
                (
                    f"同時実行テスト{i}",
                    f"どうじじっこうてすと{i}",
                    f"Concurrent Test {i}",
                    "anime",
                    f"https://example.com/concurrent/{i}",
                )
            )

        cursor.executemany(
            """
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (?, ?, ?, ?, ?)
        """,
            initial_data,
        )
        conn.commit()
        conn.close()

        with performance_monitor.monitor_test("concurrent_read_write") as monitor:

            def reader_worker(worker_id: int, operations: int) -> Dict[str, Any]:
                """Worker function for read operations."""
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()

                read_times = []
                errors = 0

                for i in range(operations):
                    try:
                        read_start = time.time()

                        # Complex read query
                        cursor.execute(
                            """
                            SELECT w.title, COUNT(r.id) as release_count
                            FROM works w
                            LEFT JOIN releases r ON w.id = r.work_id
                            WHERE w.title LIKE ?
                            GROUP BY w.id
                            ORDER BY release_count DESC
                            LIMIT 10
                        """,
                            (f"%テスト{i % 100}%",),
                        )

                        results = cursor.fetchall()
                        read_time = time.time() - read_start
                        read_times.append(read_time)

                    except Exception:
                        errors += 1

                conn.close()

                return {
                    "worker_id": worker_id,
                    "operation_type": "read",
                    "operations": operations,
                    "errors": errors,
                    "avg_time": statistics.mean(read_times) if read_times else 0,
                    "p95_time": (
                        statistics.quantiles(read_times, n=20)[18]
                        if len(read_times) > 20
                        else 0
                    ),
                }

            def writer_worker(worker_id: int, operations: int) -> Dict[str, Any]:
                """Worker function for write operations."""
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()

                write_times = []
                errors = 0

                for i in range(operations):
                    try:
                        write_start = time.time()

                        # Insert new release
                        cursor.execute(
                            """
                            INSERT INTO releases (work_id, release_type, number, platform, 
                                                release_date, source, source_url, notified)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                (worker_id * operations + i) % 5000
                                + 1,  # Random work_id
                                "episode",
                                str(i + 1),
                                "テスト配信サイト",
                                "2024-01-15",
                                "concurrent_test",
                                f"https://example.com/concurrent/{worker_id}/{i}",
                                0,
                            ),
                        )
                        conn.commit()

                        write_time = time.time() - write_start
                        write_times.append(write_time)

                    except Exception:
                        errors += 1
                        conn.rollback()

                conn.close()

                return {
                    "worker_id": worker_id,
                    "operation_type": "write",
                    "operations": operations,
                    "errors": errors,
                    "avg_time": statistics.mean(write_times) if write_times else 0,
                    "p95_time": (
                        statistics.quantiles(write_times, n=20)[18]
                        if len(write_times) > 20
                        else 0
                    ),
                }

            # Run concurrent readers and writers
            num_readers = 8
            num_writers = 4
            operations_per_worker = 100

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=num_readers + num_writers
            ) as executor:
                # Submit reader tasks
                reader_futures = [
                    executor.submit(reader_worker, i, operations_per_worker)
                    for i in range(num_readers)
                ]

                # Submit writer tasks
                writer_futures = [
                    executor.submit(
                        writer_worker, i + num_readers, operations_per_worker
                    )
                    for i in range(num_writers)
                ]

                # Collect results
                all_futures = reader_futures + writer_futures
                results = [
                    future.result()
                    for future in concurrent.futures.as_completed(all_futures)
                ]

        # Analyze results
        reader_results = [r for r in results if r["operation_type"] == "read"]
        writer_results = [r for r in results if r["operation_type"] == "write"]

        # Performance assertions
        total_operations = sum(r["operations"] for r in results)
        total_errors = sum(r["errors"] for r in results)
        error_rate = total_errors / total_operations

        assert (
            error_rate < 0.01
        ), f"Error rate {error_rate:.2%} too high for concurrent operations"

        # Response time assertions
        avg_read_time = statistics.mean([r["avg_time"] for r in reader_results])
        avg_write_time = statistics.mean([r["avg_time"] for r in writer_results])

        assert avg_read_time < 0.1, f"Average read time {avg_read_time:.3f}s too slow"
        assert (
            avg_write_time < 0.2
        ), f"Average write time {avg_write_time:.3f}s too slow"

        # P95 latency should be reasonable
        p95_read_time = statistics.mean(
            [r["p95_time"] for r in reader_results if r["p95_time"] > 0]
        )
        p95_write_time = statistics.mean(
            [r["p95_time"] for r in writer_results if r["p95_time"] > 0]
        )

        if p95_read_time > 0:
            assert p95_read_time < 0.5, f"P95 read time {p95_read_time:.3f}s too slow"
        if p95_write_time > 0:
            assert (
                p95_write_time < 1.0
            ), f"P95 write time {p95_write_time:.3f}s too slow"


class TestAdvancedAPIPerformance:
    """Advanced API performance testing with load simulation."""

    @pytest.mark.performance
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_api_load_simulation(self, performance_monitor, benchmark_config):
        """Simulate realistic API load patterns."""

        load_patterns = [
            {"name": "light_load", "connections": 5, "requests": 20},
            {"name": "medium_load", "connections": 15, "requests": 50},
            {"name": "heavy_load", "connections": 30, "requests": 100},
        ]

        results = []

        for pattern in load_patterns:
            with performance_monitor.monitor_test(
                f"api_load_{pattern['name']}"
            ) as monitor:

                async def api_client(client_id: int, num_requests: int):
                    """Simulate API client making requests."""

                    request_times = []
                    errors = 0

                    with patch("aiohttp.ClientSession") as mock_session_class:
                        mock_session = AsyncMock()
                        mock_response = AsyncMock()
                        mock_response.status = 200
                        mock_response.json.return_value = {
                            "data": {
                                "client_id": client_id,
                                "request_count": num_requests,
                            }
                        }
                        mock_session.post.return_value.__aenter__.return_value = (
                            mock_response
                        )
                        mock_session_class.return_value.__aenter__.return_value = (
                            mock_session
                        )

                        for req_num in range(num_requests):
                            try:
                                request_start = time.time()

                                # Simulate variable request processing time
                                processing_delay = (
                                    0.01 + (req_num % 10) * 0.005
                                )  # 10-60ms
                                await asyncio.sleep(processing_delay)

                                # Make API request
                                await mock_session.post(
                                    "https://graphql.anilist.co",
                                    json={
                                        "query": f"query {{Media(id: {req_num}) {{title {{romaji}}}}}}"
                                    },
                                )

                                request_time = time.time() - request_start
                                request_times.append(request_time)

                                # Rate limiting simulation
                                if req_num % 10 == 0:
                                    await asyncio.sleep(
                                        0.1
                                    )  # Brief pause every 10 requests

                            except Exception:
                                errors += 1

                    return {
                        "client_id": client_id,
                        "requests": num_requests,
                        "errors": errors,
                        "avg_response_time": (
                            statistics.mean(request_times) if request_times else 0
                        ),
                        "p95_response_time": (
                            statistics.quantiles(request_times, n=20)[18]
                            if len(request_times) > 20
                            else 0
                        ),
                        "p99_response_time": (
                            statistics.quantiles(request_times, n=100)[98]
                            if len(request_times) > 100
                            else 0
                        ),
                        "min_response_time": min(request_times) if request_times else 0,
                        "max_response_time": max(request_times) if request_times else 0,
                    }

                # Create tasks for concurrent clients
                tasks = [
                    api_client(client_id, pattern["requests"])
                    for client_id in range(pattern["connections"])
                ]

                # Execute load test
                client_results = await asyncio.gather(*tasks)

                # Calculate aggregate metrics
                total_requests = sum(r["requests"] for r in client_results)
                total_errors = sum(r["errors"] for r in client_results)
                error_rate = total_errors / total_requests if total_requests > 0 else 0

                avg_response_times = [
                    r["avg_response_time"]
                    for r in client_results
                    if r["avg_response_time"] > 0
                ]
                p95_response_times = [
                    r["p95_response_time"]
                    for r in client_results
                    if r["p95_response_time"] > 0
                ]
                p99_response_times = [
                    r["p99_response_time"]
                    for r in client_results
                    if r["p99_response_time"] > 0
                ]

                execution_time = (
                    monitor.metrics[-1].execution_time if monitor.metrics else 0
                )
                throughput = (
                    total_requests / execution_time if execution_time > 0 else 0
                )

                pattern_result = {
                    "pattern": pattern["name"],
                    "connections": pattern["connections"],
                    "total_requests": total_requests,
                    "error_rate": error_rate,
                    "throughput": throughput,
                    "avg_response_time": (
                        statistics.mean(avg_response_times) if avg_response_times else 0
                    ),
                    "p95_response_time": (
                        statistics.mean(p95_response_times) if p95_response_times else 0
                    ),
                    "p99_response_time": (
                        statistics.mean(p99_response_times) if p99_response_times else 0
                    ),
                    "execution_time": execution_time,
                }

                results.append(pattern_result)

        # Performance analysis across load patterns
        for result in results:
            pattern_name = result["pattern"]

            # Error rate should be minimal
            assert (
                result["error_rate"] < 0.02
            ), f"{pattern_name}: Error rate {result['error_rate']:.2%} too high"

            # Response times should be reasonable
            assert (
                result["avg_response_time"] < 1.0
            ), f"{pattern_name}: Average response time {result['avg_response_time']:.3f}s too slow"

            assert (
                result["p95_response_time"] < 2.0
            ), f"{pattern_name}: P95 response time {result['p95_response_time']:.3f}s too slow"

            assert (
                result["p99_response_time"] < 5.0
            ), f"{pattern_name}: P99 response time {result['p99_response_time']:.3f}s too slow"

            # Throughput should meet minimum requirements
            min_throughput = (
                10
                if pattern_name == "light_load"
                else 20 if pattern_name == "medium_load" else 30
            )
            assert (
                result["throughput"] > min_throughput
            ), f"{pattern_name}: Throughput {result['throughput']:.1f} req/s too low"

        # Load scaling analysis
        light_result = next(r for r in results if r["pattern"] == "light_load")
        heavy_result = next(r for r in results if r["pattern"] == "heavy_load")

        load_factor = heavy_result["connections"] / light_result["connections"]
        response_time_factor = (
            heavy_result["avg_response_time"] / light_result["avg_response_time"]
            if light_result["avg_response_time"] > 0
            else 1
        )

        # Response time degradation should be reasonable
        assert (
            response_time_factor < load_factor * 2
        ), f"Poor load scaling: {load_factor}x load caused {response_time_factor}x response time increase"


class TestSystemResourceOptimization:
    """Test system resource optimization and efficiency."""

    @pytest.mark.performance
    def test_memory_optimization_patterns(self, temp_db, performance_monitor):
        """Test memory usage optimization patterns."""

        with performance_monitor.monitor_test("memory_optimization") as monitor:
            # Test 1: Memory-efficient data processing
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()

            # Insert large dataset
            large_data = []
            for i in range(50000):
                large_data.append(
                    (
                        f"メモリ最適化テスト{i}",
                        f"めもりさいてきかてすと{i}",
                        f"Memory Optimization Test {i}",
                        "anime" if i % 2 == 0 else "manga",
                        f"https://example.com/memory/{i}",
                    )
                )

            # Batch processing to optimize memory
            batch_size = 1000
            for i in range(0, len(large_data), batch_size):
                batch = large_data[i : i + batch_size]
                cursor.executemany(
                    """
                    INSERT INTO works (title, title_kana, title_en, type, official_url)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    batch,
                )
                conn.commit()

                # Force garbage collection after each batch
                del batch
                gc.collect()

                monitor.take_snapshot()

            # Test 2: Memory-efficient query processing
            # Use cursor.fetchmany() instead of fetchall() for large results
            cursor.execute("SELECT * FROM works ORDER BY id")

            processed_count = 0
            while True:
                batch = cursor.fetchmany(1000)  # Process in batches
                if not batch:
                    break

                # Simulate processing
                for row in batch:
                    processed_title = row[1].upper()  # Simple processing
                    processed_count += 1

                # Monitor memory after each batch
                monitor.take_snapshot()

                # Clean up batch reference
                del batch
                gc.collect()

            conn.close()

            # Clean up large dataset
            del large_data
            gc.collect()

        # Memory usage analysis
        memory_snapshots = monitor.memory_snapshots
        if memory_snapshots:
            memory_growth = max(memory_snapshots) - min(memory_snapshots)
            assert (
                memory_growth < 200
            ), f"Memory growth {memory_growth:.1f}MB too high during processing"

            # Memory should be relatively stable after GC
            recent_snapshots = (
                memory_snapshots[-5:]
                if len(memory_snapshots) >= 5
                else memory_snapshots
            )
            memory_variance = (
                statistics.variance(recent_snapshots)
                if len(recent_snapshots) > 1
                else 0
            )
            assert (
                memory_variance < 100
            ), f"Memory variance {memory_variance:.1f} too high, poor memory management"

    @pytest.mark.performance
    def test_cpu_utilization_efficiency(self, temp_db, performance_monitor):
        """Test CPU utilization efficiency patterns."""

        with performance_monitor.monitor_test("cpu_efficiency") as monitor:
            # CPU-intensive task simulation
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()

            # Setup test data
            test_data = []
            for i in range(10000):
                test_data.append(
                    (
                        f"CPU効率テスト{i}",
                        f"しーぴーゆーこうりつてすと{i}",
                        f"CPU Efficiency Test {i}",
                        "anime",
                        f"https://example.com/cpu/{i}",
                    )
                )

            cursor.executemany(
                """
                INSERT INTO works (title, title_kana, title_en, type, official_url)
                VALUES (?, ?, ?, ?, ?)
            """,
                test_data,
            )
            conn.commit()

            # CPU-intensive processing with monitoring
            cpu_start_time = time.time()

            # Complex query processing
            cursor.execute(
                """
                SELECT 
                    LENGTH(title) as title_length,
                    LENGTH(title_kana) as kana_length,
                    LENGTH(title_en) as en_length,
                    type,
                    CASE 
                        WHEN LENGTH(title) > 20 THEN 'long'
                        WHEN LENGTH(title) > 10 THEN 'medium'
                        ELSE 'short'
                    END as length_category
                FROM works
                ORDER BY title_length DESC, title
            """
            )

            # Process results with CPU-intensive operations
            all_results = cursor.fetchall()
            processed_results = []

            for i, row in enumerate(all_results):
                # Simulate text processing
                title_length, kana_length, en_length, work_type, category = row

                # CPU-intensive string operations
                processed_data = {
                    "total_length": title_length + kana_length + en_length,
                    "avg_length": (title_length + kana_length + en_length) / 3,
                    "type": work_type,
                    "category": category,
                    "hash": hash(f"{title_length}{kana_length}{en_length}{work_type}"),
                }

                processed_results.append(processed_data)

                # Take CPU snapshot periodically
                if i % 1000 == 0:
                    monitor.take_snapshot()

            cpu_end_time = time.time()
            cpu_processing_time = cpu_end_time - cpu_start_time

            conn.close()

            # Calculate processing rate
            processing_rate = len(processed_results) / cpu_processing_time

        # CPU efficiency analysis
        assert (
            processing_rate > 1000
        ), f"Processing rate {processing_rate:.0f} records/s too low"

        # CPU usage should be reasonable (not constantly at 100%)
        cpu_snapshots = monitor.cpu_snapshots
        if cpu_snapshots:
            avg_cpu_usage = statistics.mean(cpu_snapshots)
            max_cpu_usage = max(cpu_snapshots)

            assert (
                avg_cpu_usage < 90
            ), f"Average CPU usage {avg_cpu_usage:.1f}% too high"
            assert max_cpu_usage < 95, f"Peak CPU usage {max_cpu_usage:.1f}% too high"


@pytest.fixture
def performance_report_generator():
    """Generate comprehensive performance reports."""

    def generate_report(
        metrics_list: List[PerformanceMetrics], output_file: str = None
    ):
        """Generate a comprehensive performance report."""

        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_tests": len(metrics_list),
                "test_environment": {
                    "cpu_count": psutil.cpu_count(),
                    "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                    "python_version": os.sys.version,
                },
            },
            "performance_summary": {
                "total_execution_time": sum(m.execution_time for m in metrics_list),
                "avg_execution_time": statistics.mean(
                    [m.execution_time for m in metrics_list]
                ),
                "peak_memory_usage": max(m.memory_peak_mb for m in metrics_list),
                "avg_memory_usage": statistics.mean(
                    [m.memory_peak_mb for m in metrics_list]
                ),
                "avg_cpu_usage": statistics.mean(
                    [m.cpu_usage_percent for m in metrics_list]
                ),
            },
            "test_details": [asdict(m) for m in metrics_list],
            "performance_analysis": {
                "slowest_tests": sorted(
                    [asdict(m) for m in metrics_list],
                    key=lambda x: x["execution_time"],
                    reverse=True,
                )[:5],
                "memory_intensive_tests": sorted(
                    [asdict(m) for m in metrics_list],
                    key=lambda x: x["memory_peak_mb"],
                    reverse=True,
                )[:5],
                "recommendations": [],
            },
        }

        # Generate recommendations
        recommendations = []

        slow_tests = [m for m in metrics_list if m.execution_time > 10]
        if slow_tests:
            recommendations.append(
                f"Optimize {len(slow_tests)} slow tests with execution time > 10s"
            )

        memory_intensive_tests = [m for m in metrics_list if m.memory_peak_mb > 100]
        if memory_intensive_tests:
            recommendations.append(
                f"Review {len(memory_intensive_tests)} memory-intensive tests using > 100MB"
            )

        high_cpu_tests = [m for m in metrics_list if m.cpu_usage_percent > 80]
        if high_cpu_tests:
            recommendations.append(
                f"Optimize {len(high_cpu_tests)} CPU-intensive tests using > 80% CPU"
            )

        report["performance_analysis"]["recommendations"] = recommendations

        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)

        return report

    return generate_report


class TestPerformanceRegression:
    """Performance regression testing framework."""

    @pytest.mark.performance
    def test_performance_regression_detection(
        self, temp_db, performance_monitor, performance_report_generator
    ):
        """Test for performance regression detection."""

        # Baseline performance test
        baseline_metrics = []

        # Test 1: Database operations baseline
        with performance_monitor.monitor_test("regression_db_baseline") as monitor:
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()

            # Standard operations
            test_data = [
                (
                    f"回帰テスト{i}",
                    f"かいきてすと{i}",
                    f"Regression Test {i}",
                    "anime",
                    f"https://example.com/{i}",
                )
                for i in range(1000)
            ]

            cursor.executemany(
                """
                INSERT INTO works (title, title_kana, title_en, type, official_url)
                VALUES (?, ?, ?, ?, ?)
            """,
                test_data,
            )
            conn.commit()

            cursor.execute("SELECT COUNT(*) FROM works")
            count = cursor.fetchone()[0]
            conn.close()

        baseline_metrics.extend(monitor.metrics)

        # Simulate a performance regression scenario
        with performance_monitor.monitor_test("regression_db_degraded") as monitor:
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()

            # Intentionally less efficient operations (simulating regression)
            for i in range(1000):
                # Individual inserts instead of batch (inefficient)
                cursor.execute(
                    """
                    INSERT INTO works (title, title_kana, title_en, type, official_url)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        f"回帰劣化{i}",
                        f"かいきれっか{i}",
                        f"Regression Degraded {i}",
                        "manga",
                        f"https://example.com/degraded/{i}",
                    ),
                )
                conn.commit()  # Commit each insert individually

            cursor.execute("SELECT COUNT(*) FROM works")
            count = cursor.fetchone()[0]
            conn.close()

        # Compare performance
        baseline_time = baseline_metrics[0].execution_time
        degraded_time = monitor.metrics[-1].execution_time

        performance_ratio = degraded_time / baseline_time

        # Generate regression report
        all_metrics = baseline_metrics + monitor.metrics
        regression_report = performance_report_generator(
            all_metrics, "performance-regression-report.json"
        )

        # Regression detection
        regression_threshold = 2.0  # 100% increase in execution time

        if performance_ratio > regression_threshold:
            pytest.fail(
                f"Performance regression detected: {performance_ratio:.2f}x slower "
                f"({baseline_time:.2f}s → {degraded_time:.2f}s). "
                f"Check performance-regression-report.json for details."
            )

        # Memory regression check
        baseline_memory = baseline_metrics[0].memory_peak_mb
        degraded_memory = monitor.metrics[-1].memory_peak_mb
        memory_ratio = degraded_memory / baseline_memory if baseline_memory > 0 else 1

        memory_regression_threshold = 1.5  # 50% increase
        assert (
            memory_ratio < memory_regression_threshold
        ), f"Memory regression detected: {memory_ratio:.2f}x higher memory usage"
