#!/usr/bin/env python3
"""
Performance and load testing for the anime/manga notification system
"""

import pytest
import time
import asyncio
import threading
import multiprocessing
import sqlite3
import psutil
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import concurrent.futures
import json
import memory_profiler


class TestDatabasePerformance:
    """Test database performance under various load conditions."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_bulk_data_insertion_performance(self, temp_db):
        """Test performance of bulk data insertion operations."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Test parameters
        work_count = 1000
        releases_per_work = 10

        # Generate test data
        works_data = []
        for i in range(work_count):
            works_data.append(
                (
                    f"テストアニメ{i}",
                    f"てすとあにめ{i}",
                    f"Test Anime {i}",
                    "anime" if i % 2 == 0 else "manga",
                    f"https://example.com/anime/{i}",
                )
            )

        # Measure bulk insertion performance
        start_time = time.time()

        cursor.executemany(
            """
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (?, ?, ?, ?, ?)
        """,
            works_data,
        )

        work_insertion_time = time.time() - start_time

        # Generate release data
        releases_data = []
        for work_id in range(1, work_count + 1):
            for release_num in range(1, releases_per_work + 1):
                releases_data.append(
                    (
                        work_id,
                        "episode" if work_id % 2 == 1 else "volume",
                        str(release_num),
                        "テスト配信サイト",
                        "2024-01-15",
                        "test_source",
                        f"https://example.com/release/{work_id}/{release_num}",
                        0,
                    )
                )

        start_time = time.time()

        cursor.executemany(
            """
            INSERT INTO releases (work_id, release_type, number, platform, release_date, source, source_url, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            releases_data,
        )

        release_insertion_time = time.time() - start_time

        conn.commit()

        # Performance assertions
        assert (
            work_insertion_time < 5.0
        ), f"Work insertion took {work_insertion_time:.2f}s, should be under 5s"
        assert (
            release_insertion_time < 10.0
        ), f"Release insertion took {release_insertion_time:.2f}s, should be under 10s"

        # Verify data integrity
        cursor.execute("SELECT COUNT(*) FROM works")
        assert cursor.fetchone()[0] == work_count

        cursor.execute("SELECT COUNT(*) FROM releases")
        assert cursor.fetchone()[0] == work_count * releases_per_work

        conn.close()

    @pytest.mark.performance
    def test_complex_query_performance(self, temp_db):
        """Test performance of complex JOIN queries."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Setup test data (moderate size)
        self._setup_performance_test_data(cursor, work_count=500, releases_per_work=5)

        # Test complex query performance
        complex_queries = [
            # Query 1: Unnotified releases with work info
            """
            SELECT r.*, w.title, w.title_kana, w.type
            FROM releases r
            JOIN works w ON r.work_id = w.id
            WHERE r.notified = 0
            ORDER BY r.release_date DESC, w.title ASC
            """,
            # Query 2: Releases by platform with counts
            """
            SELECT r.platform, COUNT(*) as release_count, w.type
            FROM releases r
            JOIN works w ON r.work_id = w.id
            GROUP BY r.platform, w.type
            ORDER BY release_count DESC
            """,
            # Query 3: Recent releases with date filtering
            """
            SELECT w.title, r.number, r.platform, r.release_date
            FROM works w
            JOIN releases r ON w.id = r.work_id
            WHERE r.release_date >= '2024-01-01'
            AND w.type = 'anime'
            ORDER BY r.release_date DESC
            LIMIT 100
            """,
        ]

        query_times = []
        for i, query in enumerate(complex_queries):
            start_time = time.time()
            cursor.execute(query)
            results = cursor.fetchall()
            query_time = time.time() - start_time

            query_times.append(query_time)

            # Verify queries return results
            assert len(results) > 0, f"Query {i+1} returned no results"

            # Performance assertion
            assert (
                query_time < 1.0
            ), f"Query {i+1} took {query_time:.3f}s, should be under 1s"

        # Overall query performance
        avg_query_time = sum(query_times) / len(query_times)
        assert (
            avg_query_time < 0.5
        ), f"Average query time {avg_query_time:.3f}s should be under 0.5s"

        conn.close()

    @pytest.mark.performance
    def test_concurrent_database_access(self, temp_db):
        """Test database performance under concurrent access."""

        # Setup test data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        self._setup_performance_test_data(cursor, work_count=100, releases_per_work=3)
        conn.close()

        def database_worker(worker_id: int, operation_count: int):
            """Worker function for concurrent database operations."""
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()

            results = []
            start_time = time.time()

            for i in range(operation_count):
                # Mix of read and write operations
                if i % 3 == 0:
                    # Read operation
                    cursor.execute(
                        """
                        SELECT w.title, COUNT(r.id) as release_count
                        FROM works w
                        LEFT JOIN releases r ON w.id = r.work_id
                        GROUP BY w.id
                        LIMIT 10
                    """
                    )
                    cursor.fetchall()
                else:
                    # Write operation (update)
                    cursor.execute(
                        """
                        UPDATE releases 
                        SET notified = CASE WHEN notified = 0 THEN 1 ELSE 0 END 
                        WHERE id = ?
                    """,
                        (((worker_id * operation_count + i) % 100) + 1,),
                    )
                    conn.commit()

            end_time = time.time()
            conn.close()

            return {
                "worker_id": worker_id,
                "operations": operation_count,
                "time_taken": end_time - start_time,
                "ops_per_second": operation_count / (end_time - start_time),
            }

        # Run concurrent workers
        num_workers = 5
        operations_per_worker = 50

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(database_worker, worker_id, operations_per_worker)
                for worker_id in range(num_workers)
            ]

            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        total_time = time.time() - start_time

        # Performance assertions
        assert (
            total_time < 10.0
        ), f"Concurrent operations took {total_time:.2f}s, should be under 10s"

        # Verify all workers completed successfully
        assert len(results) == num_workers

        # Check operations per second
        total_ops = sum(result["operations"] for result in results)
        overall_ops_per_second = total_ops / total_time

        assert (
            overall_ops_per_second > 10
        ), f"Overall throughput {overall_ops_per_second:.1f} ops/s should be > 10"

    @pytest.mark.performance
    def test_database_memory_usage(self, temp_db):
        """Test database memory usage patterns."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Large data operation
        large_data_count = 10000

        # Monitor memory during large insertion
        memory_measurements = []

        for batch in range(10):  # 10 batches of 1000 records each
            batch_data = []
            for i in range(1000):
                record_id = batch * 1000 + i
                batch_data.append(
                    (
                        f"大量データテスト{record_id}",
                        f"たいりょうでーたてすと{record_id}",
                        f"Large Data Test {record_id}",
                        "anime",
                        f"https://example.com/large/{record_id}",
                    )
                )

            cursor.executemany(
                """
                INSERT INTO works (title, title_kana, title_en, type, official_url)
                VALUES (?, ?, ?, ?, ?)
            """,
                batch_data,
            )
            conn.commit()

            # Measure memory after each batch
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_measurements.append(current_memory - initial_memory)

        # Memory usage assertions
        max_memory_increase = max(memory_measurements)
        final_memory_increase = memory_measurements[-1]

        assert (
            max_memory_increase < 100
        ), f"Peak memory increase {max_memory_increase:.1f}MB should be under 100MB"
        assert (
            final_memory_increase < 50
        ), f"Final memory increase {final_memory_increase:.1f}MB should be under 50MB"

        # Test memory cleanup after large query
        cursor.execute("SELECT COUNT(*) FROM works")
        total_count = cursor.fetchone()[0]
        assert total_count == large_data_count

        # Large query to test memory handling
        cursor.execute(
            """
            SELECT title, title_kana, title_en, type, official_url
            FROM works
            ORDER BY title
        """
        )

        all_records = cursor.fetchall()
        assert len(all_records) == large_data_count

        # Memory should not have grown significantly more
        post_query_memory = process.memory_info().rss / 1024 / 1024  # MB
        post_query_increase = post_query_memory - initial_memory

        assert (
            post_query_increase < max_memory_increase + 20
        ), "Query should not significantly increase memory"

        conn.close()

    def _setup_performance_test_data(
        self, cursor, work_count: int, releases_per_work: int
    ):
        """Helper to setup test data for performance tests."""
        # Insert works
        works_data = []
        for i in range(work_count):
            works_data.append(
                (
                    f"パフォーマンステスト{i}",
                    f"ぱふぉーまんすてすと{i}",
                    f"Performance Test {i}",
                    "anime" if i % 3 == 0 else "manga",
                    f"https://example.com/perf/{i}",
                )
            )

        cursor.executemany(
            """
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (?, ?, ?, ?, ?)
        """,
            works_data,
        )

        # Insert releases
        releases_data = []
        platforms = [
            "dアニメストア",
            "Netflix",
            "Crunchyroll",
            "BookWalker",
            "Amazon Prime",
        ]

        for work_id in range(1, work_count + 1):
            for release_num in range(1, releases_per_work + 1):
                platform = platforms[work_id % len(platforms)]
                release_date = (
                    (datetime.now() - timedelta(days=work_id)).date().isoformat()
                )

                releases_data.append(
                    (
                        work_id,
                        "episode" if work_id % 3 == 1 else "volume",
                        str(release_num),
                        platform,
                        release_date,
                        "performance_test",
                        f"https://example.com/perf/{work_id}/{release_num}",
                        work_id % 4,  # Mix of notified/unnotified
                    )
                )

        cursor.executemany(
            """
            INSERT INTO releases (work_id, release_type, number, platform, release_date, source, source_url, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            releases_data,
        )

        cursor.connection.commit()


class TestAPIPerformance:
    """Test API performance and rate limiting."""

    @pytest.mark.performance
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_anilist_api_rate_limiting_compliance(self):
        """Test AniList API rate limiting compliance under load."""

        # AniList allows 90 requests per minute
        max_requests_per_minute = 90
        test_requests = 20  # Test with subset to keep test time reasonable

        request_times = []

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"data": {"Page": {"media": []}}}
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Simulate rate-limited requests
            start_time = time.time()

            for i in range(test_requests):
                request_start = time.time()

                # Simulate API call with rate limiting
                if i > 0:
                    # Enforce minimum interval between requests
                    min_interval = 60.0 / max_requests_per_minute  # ~0.67 seconds
                    time_since_last = request_start - request_times[-1]

                    if time_since_last < min_interval:
                        sleep_time = min_interval - time_since_last
                        await asyncio.sleep(sleep_time)

                # Make request
                await mock_session.post(
                    "https://graphql.anilist.co", json={"query": "test"}
                )

                request_times.append(time.time())

            total_time = time.time() - start_time

            # Verify rate limiting compliance
            requests_per_second = test_requests / total_time
            requests_per_minute = requests_per_second * 60

            assert (
                requests_per_minute <= max_requests_per_minute
            ), f"Rate limit exceeded: {requests_per_minute:.1f} req/min > {max_requests_per_minute} req/min"

            # Verify reasonable performance
            assert (
                total_time < test_requests * 2
            ), f"Total time {total_time:.1f}s too slow for {test_requests} requests"

    @pytest.mark.performance
    @pytest.mark.api
    def test_rss_feed_collection_performance(self, mock_rss_feed_data):
        """Test RSS feed collection performance with multiple feeds."""

        # Simulate multiple RSS feeds
        feed_urls = [
            "https://bookwalker.jp/rss/manga",
            "https://manga-kingdom.com/rss",
            "https://ebookjapan.com/rss",
            "https://kobo.rakuten.co.jp/rss",
            "https://dmmbooks.com/rss",
        ]

        collection_results = []

        with patch("requests.get") as mock_get:
            # Mock RSS response for each feed
            mock_response = Mock()
            mock_response.content = mock_rss_feed_data.encode("utf-8")
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            start_time = time.time()

            # Collect from all feeds
            for feed_url in feed_urls:
                feed_start = time.time()

                # Simulate RSS collection
                response = mock_get(
                    feed_url, headers={"User-Agent": "Test/1.0"}, timeout=20
                )

                # Parse RSS (simplified)
                import feedparser

                feed = feedparser.parse(response.content)

                feed_time = time.time() - feed_start

                collection_results.append(
                    {"url": feed_url, "time": feed_time, "entries": len(feed.entries)}
                )

            total_collection_time = time.time() - start_time

            # Performance assertions
            assert (
                total_collection_time < 10.0
            ), f"RSS collection took {total_collection_time:.2f}s, should be under 10s"

            # Individual feed performance
            for result in collection_results:
                assert (
                    result["time"] < 3.0
                ), f"Feed {result['url']} took {result['time']:.2f}s, should be under 3s"
                assert (
                    result["entries"] > 0
                ), f"Feed {result['url']} returned no entries"

            # Average performance
            avg_time_per_feed = total_collection_time / len(feed_urls)
            assert (
                avg_time_per_feed < 2.0
            ), f"Average time per feed {avg_time_per_feed:.2f}s should be under 2s"

    @pytest.mark.performance
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_concurrent_api_requests_performance(self):
        """Test performance of concurrent API requests."""

        # Test parameters
        concurrent_requests = 10
        requests_per_connection = 5

        async def api_worker(worker_id: int):
            """Simulate API worker making multiple requests."""
            results = []

            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "data": {"test": f"worker_{worker_id}"}
                }
                mock_session.post.return_value.__aenter__.return_value = mock_response
                mock_session_class.return_value.__aenter__.return_value = mock_session

                start_time = time.time()

                for request_num in range(requests_per_connection):
                    request_start = time.time()

                    # Simulate API request with minimal delay
                    await asyncio.sleep(0.01)  # Simulate network delay
                    result = await mock_session.post(
                        "https://api.example.com", json={"query": f"test_{request_num}"}
                    )

                    request_time = time.time() - request_start
                    results.append(
                        {
                            "worker_id": worker_id,
                            "request_num": request_num,
                            "time": request_time,
                        }
                    )

                worker_time = time.time() - start_time
                return {
                    "worker_id": worker_id,
                    "total_time": worker_time,
                    "requests": results,
                }

        # Run concurrent workers
        start_time = time.time()

        tasks = [api_worker(i) for i in range(concurrent_requests)]
        worker_results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Performance analysis
        total_requests = concurrent_requests * requests_per_connection
        overall_throughput = total_requests / total_time

        # Assertions
        assert (
            total_time < 5.0
        ), f"Concurrent API requests took {total_time:.2f}s, should be under 5s"
        assert (
            overall_throughput > 10
        ), f"Throughput {overall_throughput:.1f} req/s should be > 10"

        # Verify all workers completed
        assert len(worker_results) == concurrent_requests

        # Check individual worker performance
        for worker_result in worker_results:
            assert (
                worker_result["total_time"] < 2.0
            ), f"Worker {worker_result['worker_id']} took too long"
            assert len(worker_result["requests"]) == requests_per_connection


class TestNotificationPerformance:
    """Test notification system performance."""

    @pytest.mark.performance
    def test_bulk_email_generation_performance(self, sample_release_data):
        """Test performance of bulk email generation."""

        # Scale up test data
        bulk_releases = []
        for i in range(100):
            release = sample_release_data[0].copy()
            release["work_id"] = i + 1
            release["title"] = f"テストアニメ{i}"
            release["number"] = str((i % 50) + 1)
            bulk_releases.append(release)

        start_time = time.time()

        generated_emails = []
        for release in bulk_releases:
            # Simulate email generation
            email_content = {
                "subject": f"新エピソード配信: {release['title']}",
                "body": f"""
                作品: {release['title']}
                エピソード: 第{release['number']}話
                配信日: {release['release_date']}
                プラットフォーム: {release['platform']}
                """,
                "html_body": f"""
                <html>
                <body>
                <h2>{release['title']} - 第{release['number']}話</h2>
                <p>配信日: {release['release_date']}</p>
                <p>プラットフォーム: {release['platform']}</p>
                </body>
                </html>
                """,
            }

            generated_emails.append(email_content)

        generation_time = time.time() - start_time

        # Performance assertions
        assert (
            generation_time < 2.0
        ), f"Email generation took {generation_time:.2f}s, should be under 2s"
        assert len(generated_emails) == 100

        # Verify content quality
        for email in generated_emails[:5]:  # Check first 5 emails
            assert "テストアニメ" in email["subject"]
            assert "配信日" in email["body"]
            assert "<html>" in email["html_body"]

    @pytest.mark.performance
    def test_calendar_event_creation_performance(
        self, mock_calendar_service, sample_release_data
    ):
        """Test performance of bulk calendar event creation."""

        # Scale up test data
        bulk_releases = []
        for i in range(50):
            release = sample_release_data[0].copy()
            release["work_id"] = i + 1
            release["title"] = f"カレンダーテスト{i}"
            bulk_releases.append(release)

        # Mock calendar service responses
        mock_calendar_service.events().insert.return_value.execute.return_value = {
            "id": "test_event",
            "htmlLink": "https://calendar.google.com/event?eid=test",
            "status": "confirmed",
        }

        start_time = time.time()

        created_events = []
        for release in bulk_releases:
            # Simulate calendar event creation
            event_data = {
                "summary": f"{release['title']} - 第{release['number']}話",
                "description": f"プラットフォーム: {release['platform']}",
                "start": {"date": release["release_date"], "timeZone": "Asia/Tokyo"},
                "end": {"date": release["release_date"], "timeZone": "Asia/Tokyo"},
                "colorId": "3",
            }

            result = (
                mock_calendar_service.events()
                .insert(calendarId="primary", body=event_data)
                .execute()
            )

            created_events.append(result)

        creation_time = time.time() - start_time

        # Performance assertions
        assert (
            creation_time < 5.0
        ), f"Calendar creation took {creation_time:.2f}s, should be under 5s"
        assert len(created_events) == 50

        # Verify API call efficiency
        events_per_second = len(created_events) / creation_time
        assert (
            events_per_second > 5
        ), f"Event creation rate {events_per_second:.1f}/s should be > 5/s"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_full_notification_pipeline_performance(
        self, temp_db, mock_gmail_service, mock_calendar_service
    ):
        """Test performance of complete notification pipeline."""

        # Setup large dataset
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Insert test works and releases
        work_count = 200
        works_data = []
        for i in range(work_count):
            works_data.append(
                (
                    f"パフォーマンステスト{i}",
                    f"ぱふぉーまんすてすと{i}",
                    f"Performance Test {i}",
                    "anime",
                    f"https://example.com/perf/{i}",
                )
            )

        cursor.executemany(
            """
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (?, ?, ?, ?, ?)
        """,
            works_data,
        )

        # Insert releases
        releases_data = []
        for work_id in range(1, work_count + 1):
            releases_data.append(
                (
                    work_id,
                    "episode",
                    "1",
                    "テスト配信",
                    "2024-01-15",
                    "test",
                    f"https://example.com/{work_id}",
                    0,  # Unnotified
                )
            )

        cursor.executemany(
            """
            INSERT INTO releases (work_id, release_type, number, platform, release_date, source, source_url, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            releases_data,
        )

        conn.commit()

        # Mock service responses
        mock_gmail_service.users().messages().send.return_value.execute.return_value = {
            "id": "bulk_test_email",
            "threadId": "bulk_thread",
        }
        mock_calendar_service.events().insert.return_value.execute.return_value = {
            "id": "bulk_test_event",
            "status": "confirmed",
        }

        # Run full notification pipeline
        pipeline_start = time.time()

        # Step 1: Query unnotified releases
        query_start = time.time()
        cursor.execute(
            """
            SELECT r.*, w.title, w.title_kana, w.title_en, w.type
            FROM releases r
            JOIN works w ON r.work_id = w.id
            WHERE r.notified = 0
            ORDER BY r.release_date ASC
        """
        )
        unnotified_releases = cursor.fetchall()
        query_time = time.time() - query_start

        # Step 2: Generate and send notifications
        notification_start = time.time()
        sent_notifications = []

        for release in unnotified_releases:
            # Email generation and sending
            mock_gmail_service.users().messages().send().execute()

            # Calendar event creation
            mock_calendar_service.events().insert(
                calendarId="primary", body={}
            ).execute()

            sent_notifications.append(release[0])  # release ID

        notification_time = time.time() - notification_start

        # Step 3: Mark as notified
        update_start = time.time()

        if sent_notifications:
            placeholders = ",".join("?" * len(sent_notifications))
            cursor.execute(
                f"""
                UPDATE releases SET notified = 1 
                WHERE id IN ({placeholders})
            """,
                sent_notifications,
            )
            conn.commit()

        update_time = time.time() - update_start
        total_pipeline_time = time.time() - pipeline_start

        # Performance assertions
        assert query_time < 1.0, f"Query time {query_time:.2f}s should be under 1s"
        assert (
            notification_time < 20.0
        ), f"Notification time {notification_time:.2f}s should be under 20s"
        assert update_time < 1.0, f"Update time {update_time:.2f}s should be under 1s"
        assert (
            total_pipeline_time < 25.0
        ), f"Total pipeline time {total_pipeline_time:.2f}s should be under 25s"

        # Verify throughput
        notifications_per_second = len(sent_notifications) / notification_time
        assert (
            notifications_per_second > 5
        ), f"Notification rate {notifications_per_second:.1f}/s should be > 5/s"

        # Verify completion
        assert len(sent_notifications) == work_count

        cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 0")
        remaining_unnotified = cursor.fetchone()[0]
        assert remaining_unnotified == 0

        conn.close()


class TestSystemResourceUsage:
    """Test system resource usage patterns."""

    @pytest.mark.performance
    def test_memory_usage_patterns(self, temp_db):
        """Test memory usage patterns during various operations."""

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_snapshots = {"initial": initial_memory}

        # Memory usage during database operations
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Large data insertion
        large_dataset = []
        for i in range(5000):
            large_dataset.append(
                (
                    f"メモリテスト{i}",
                    f"めもりてすと{i}",
                    f"Memory Test {i}",
                    "anime" if i % 2 == 0 else "manga",
                    f"https://example.com/memory/{i}",
                )
            )

        cursor.executemany(
            """
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (?, ?, ?, ?, ?)
        """,
            large_dataset,
        )
        conn.commit()

        memory_snapshots["after_insertion"] = process.memory_info().rss / 1024 / 1024

        # Memory usage during large query
        cursor.execute("SELECT * FROM works ORDER BY title")
        all_results = cursor.fetchall()

        memory_snapshots["after_query"] = process.memory_info().rss / 1024 / 1024

        # Memory usage during data processing
        processed_data = []
        for row in all_results:
            processed_item = {
                "id": row[0],
                "title": row[1],
                "title_processed": row[1].upper(),
                "type": row[4],
            }
            processed_data.append(processed_item)

        memory_snapshots["after_processing"] = process.memory_info().rss / 1024 / 1024

        # Cleanup
        del all_results
        del processed_data
        del large_dataset
        conn.close()

        memory_snapshots["after_cleanup"] = process.memory_info().rss / 1024 / 1024

        # Memory usage analysis
        max_memory_increase = max(
            memory_snapshots[key] - initial_memory
            for key in memory_snapshots
            if key != "initial"
        )

        final_memory_increase = memory_snapshots["after_cleanup"] - initial_memory

        # Assertions
        assert (
            max_memory_increase < 200
        ), f"Peak memory increase {max_memory_increase:.1f}MB should be under 200MB"
        assert (
            final_memory_increase < max_memory_increase * 0.5
        ), "Memory should be freed after cleanup"

        # Memory growth pattern should be reasonable
        insertion_growth = memory_snapshots["after_insertion"] - initial_memory
        query_growth = (
            memory_snapshots["after_query"] - memory_snapshots["after_insertion"]
        )

        assert insertion_growth > 0, "Memory should increase during data insertion"
        assert query_growth >= 0, "Memory may increase during large queries"

    @pytest.mark.performance
    def test_cpu_usage_patterns(self, temp_db):
        """Test CPU usage patterns during intensive operations."""

        process = psutil.Process()

        # CPU intensive operation: data processing
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Insert test data
        test_data = []
        for i in range(1000):
            test_data.append(
                (
                    f"CPUテスト{i}",
                    f"しーぴーゆーてすと{i}",
                    f"CPU Test {i}",
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

        # CPU intensive processing
        cpu_start = time.time()
        cpu_start_percent = process.cpu_percent()

        # Simulate data processing workload
        cursor.execute("SELECT * FROM works")
        all_works = cursor.fetchall()

        # Processing simulation
        processed_works = []
        for work in all_works:
            # Simulate text processing
            processed_title = work[1].upper().replace("テスト", "TEST")
            processed_kana = work[2].replace("てすと", "test")

            # Simulate filtering logic
            is_filtered = any(
                keyword in processed_title.lower() for keyword in ["test", "cpu"]
            )

            processed_works.append(
                {
                    "original": work,
                    "processed_title": processed_title,
                    "processed_kana": processed_kana,
                    "filtered": is_filtered,
                }
            )

        cpu_time = time.time() - cpu_start
        cpu_end_percent = process.cpu_percent()

        # CPU usage analysis
        cpu_usage_increase = cpu_end_percent - cpu_start_percent
        processing_rate = len(processed_works) / cpu_time

        # Assertions
        assert (
            cpu_time < 5.0
        ), f"CPU intensive processing took {cpu_time:.2f}s, should be under 5s"
        assert (
            processing_rate > 100
        ), f"Processing rate {processing_rate:.1f} items/s should be > 100/s"

        # CPU usage should be reasonable (not pinning CPU)
        # Note: CPU percentage can be unreliable in tests, so we mainly check processing speed

        conn.close()

    @pytest.mark.performance
    def test_disk_io_patterns(self, temp_db):
        """Test disk I/O patterns and database file growth."""

        initial_db_size = os.path.getsize(temp_db) / 1024  # KB

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Measure I/O during bulk operations
        io_measurements = []

        for batch in range(10):
            batch_start_size = os.path.getsize(temp_db) / 1024  # KB
            batch_start_time = time.time()

            # Insert batch of data
            batch_data = []
            for i in range(500):  # 500 records per batch
                record_id = batch * 500 + i
                batch_data.append(
                    (
                        f"IOテスト{record_id}",
                        f"あいおーてすと{record_id}",
                        f"IO Test {record_id}",
                        "anime" if record_id % 2 == 0 else "manga",
                        f"https://example.com/io/{record_id}",
                    )
                )

            cursor.executemany(
                """
                INSERT INTO works (title, title_kana, title_en, type, official_url)
                VALUES (?, ?, ?, ?, ?)
            """,
                batch_data,
            )
            conn.commit()

            batch_end_time = time.time()
            batch_end_size = os.path.getsize(temp_db) / 1024  # KB

            io_measurements.append(
                {
                    "batch": batch,
                    "time": batch_end_time - batch_start_time,
                    "size_growth": batch_end_size - batch_start_size,
                    "records": len(batch_data),
                }
            )

        final_db_size = os.path.getsize(temp_db) / 1024  # KB
        total_growth = final_db_size - initial_db_size

        # I/O performance analysis
        avg_batch_time = sum(m["time"] for m in io_measurements) / len(io_measurements)
        avg_size_growth = sum(m["size_growth"] for m in io_measurements) / len(
            io_measurements
        )
        total_records = sum(m["records"] for m in io_measurements)

        # Assertions
        assert (
            avg_batch_time < 1.0
        ), f"Average batch time {avg_batch_time:.2f}s should be under 1s"
        assert total_growth > 0, "Database should grow with data insertion"
        assert (
            total_growth < 10000
        ), f"Database growth {total_growth:.1f}KB should be reasonable"

        # Growth should be relatively consistent
        size_growth_values = [m["size_growth"] for m in io_measurements]
        size_growth_variance = max(size_growth_values) - min(size_growth_values)

        assert (
            size_growth_variance < avg_size_growth * 2
        ), "Database growth should be relatively consistent"

        conn.close()
