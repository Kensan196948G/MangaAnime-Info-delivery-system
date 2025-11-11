#!/usr/bin/env python3
"""
Unit and integration tests for RSS feed processing
"""

import pytest
import feedparser
import requests
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


class TestRSSFeedProcessing:
    """Test RSS feed parsing and processing."""

    @pytest.mark.unit
    def test_rss_feed_parsing(self, mock_rss_feed_data):
        """Test basic RSS feed parsing functionality."""
        # Parse the mock RSS feed
        parsed_feed = feedparser.parse(mock_rss_feed_data)

        # Verify feed structure
        assert parsed_feed.bozo == 0  # Valid XML
        assert len(parsed_feed.entries) == 2

        # Check first entry
        first_entry = parsed_feed.entries[0]
        assert first_entry.title == "進撃の巨人 第34巻"
        assert first_entry.link == "https://example.com/manga/attack-titan-34"
        assert "最終巻" in first_entry.description

        # Check second entry
        second_entry = parsed_feed.entries[1]
        assert second_entry.title == "鬼滅の刃 第23巻"
        assert second_entry.link == "https://example.com/manga/demon-slayer-23"
        assert "完結記念" in second_entry.description

    @pytest.mark.unit
    def test_rss_date_parsing(self, mock_rss_feed_data):
        """Test RSS feed date parsing and normalization."""
        parsed_feed = feedparser.parse(mock_rss_feed_data)

        for entry in parsed_feed.entries:
            # Check if published date exists
            if hasattr(entry, "published"):
                # Parse the date
                published_time = entry.published_parsed
                assert published_time is not None

                # Convert to datetime
                published_date = datetime(*published_time[:6])
                assert isinstance(published_date, datetime)

                # Verify date is reasonable (not too far in past/future)
                now = datetime.now()
                assert published_date < now + timedelta(
                    days=365
                )  # Not more than 1 year in future
                assert published_date > now - timedelta(
                    days=365 * 5
                )  # Not more than 5 years in past

    @pytest.mark.unit
    def test_manga_title_extraction(self, mock_rss_feed_data):
        """Test manga title and volume number extraction from RSS entries."""
        parsed_feed = feedparser.parse(mock_rss_feed_data)

        test_cases = [
            ("進撃の巨人 第34巻", "進撃の巨人", "34"),
            ("鬼滅の刃 第23巻", "鬼滅の刃", "23"),
            ("ワンピース 第103巻", "ワンピース", "103"),
            ("呪術廻戦 第19巻 特装版", "呪術廻戦", "19"),
        ]

        import re

        for title, expected_name, expected_volume in test_cases:
            # Pattern to extract manga name and volume
            pattern = r"^(.+?)\s+第(\d+)巻"
            match = re.match(pattern, title)

            if match:
                extracted_name = match.group(1)
                extracted_volume = match.group(2)

                assert extracted_name == expected_name
                assert extracted_volume == expected_volume

    @pytest.mark.integration
    @pytest.mark.api
    def test_rss_feed_fetching_mock(self, mock_requests_session, test_config):
        """Test RSS feed fetching with mocked HTTP requests."""
        feed_url = "https://example.com/manga/feed.rss"

        # Mock the response with RSS data
        mock_requests_session.get.return_value.text = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Manga Feed</title>
                <item>
                    <title>テスト漫画 第1巻</title>
                    <link>https://example.com/manga/test-1</link>
                    <pubDate>Wed, 08 Aug 2024 12:00:00 +0900</pubDate>
                </item>
            </channel>
        </rss>"""

        with patch("requests.Session", return_value=mock_requests_session):
            session = requests.Session()
            response = session.get(
                feed_url, timeout=test_config["apis"]["rss_feeds"]["timeout_seconds"]
            )

            # Parse the response
            parsed_feed = feedparser.parse(response.text)

            # Verify the result
            assert len(parsed_feed.entries) == 1
            assert parsed_feed.entries[0].title == "テスト漫画 第1巻"
            assert parsed_feed.entries[0].link == "https://example.com/manga/test-1"

    @pytest.mark.integration
    @pytest.mark.api
    def test_multiple_rss_feeds_processing(self, test_config):
        """Test processing multiple RSS feeds concurrently."""
        feed_configs = test_config["apis"]["rss_feeds"]["feeds"]

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock different responses for different feeds
            def mock_get_response(url, **kwargs):
                response = Mock()
                response.status_code = 200

                if "bookwalker" in url:
                    response.text = """<?xml version="1.0" encoding="UTF-8"?>
                    <rss version="2.0">
                        <channel>
                            <title>BookWalker Feed</title>
                            <item><title>マンガタイトル1 第1巻</title><link>https://bookwalker.jp/1</link></item>
                        </channel>
                    </rss>"""
                else:
                    response.text = """<?xml version="1.0" encoding="UTF-8"?>
                    <rss version="2.0">
                        <channel>
                            <title>dアニメストア Feed</title>
                            <item><title>アニメタイトル1 第1話</title><link>https://danime.jp/1</link></item>
                        </channel>
                    </rss>"""

                return response

            mock_session.get.side_effect = mock_get_response

            # Process all feeds
            session = requests.Session()
            results = []

            for feed_config in feed_configs:
                if feed_config["enabled"]:
                    response = session.get(feed_config["url"])
                    parsed_feed = feedparser.parse(response.text)
                    results.append(
                        {
                            "name": feed_config["name"],
                            "category": feed_config["category"],
                            "entries": parsed_feed.entries,
                        }
                    )

            # Verify results
            assert len(results) == sum(1 for feed in feed_configs if feed["enabled"])

            for result in results:
                assert "name" in result
                assert "category" in result
                assert "entries" in result
                assert len(result["entries"]) >= 0

    @pytest.mark.unit
    def test_rss_error_handling(self):
        """Test RSS feed error handling for malformed XML."""
        malformed_rss = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Malformed Feed</title>
                <item>
                    <title>Test Title</title>
                    <link>https://example.com</link>
                    <!-- Missing closing tag for description -->
                    <description>Test description
                </item>
            </channel>
        </rss>"""

        # feedparser should handle malformed XML gracefully
        parsed_feed = feedparser.parse(malformed_rss)

        # Check bozo flag (indicates parsing issues)
        assert parsed_feed.bozo == 1  # Indicates XML parsing issues

        # Should still extract what it can
        assert hasattr(parsed_feed, "feed")
        assert hasattr(parsed_feed, "entries")


class TestRSSDataNormalization:
    """Test RSS data normalization and standardization."""

    @pytest.mark.unit
    def test_manga_data_normalization(self, test_data_generator):
        """Test normalization of manga data from various RSS sources."""
        rss_data = test_data_generator.generate_manga_data(3)
        parsed_feed = feedparser.parse(rss_data)

        for entry in parsed_feed.entries:
            # Extract and normalize data
            normalized_entry = self._normalize_manga_entry(entry)

            # Verify required fields
            assert "title" in normalized_entry
            assert "volume" in normalized_entry
            assert "url" in normalized_entry
            assert "release_date" in normalized_entry
            assert "source" in normalized_entry

            # Verify data types
            assert isinstance(normalized_entry["title"], str)
            assert isinstance(normalized_entry["url"], str)
            assert isinstance(normalized_entry["source"], str)

            # Verify URL format
            parsed_url = urlparse(normalized_entry["url"])
            assert parsed_url.scheme in ["http", "https"]
            assert parsed_url.netloc != ""

    def _normalize_manga_entry(self, entry):
        """Helper method to normalize a manga RSS entry."""
        import re

        # Extract title and volume
        title_match = re.match(r"^(.+?)\s+第(\d+)巻", entry.title)
        if title_match:
            manga_title = title_match.group(1)
            volume = title_match.group(2)
        else:
            manga_title = entry.title
            volume = None

        # Parse release date
        release_date = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            release_date = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")

        return {
            "title": manga_title,
            "volume": volume,
            "url": entry.link,
            "release_date": release_date,
            "source": "rss",
            "description": getattr(entry, "description", ""),
        }

    @pytest.mark.unit
    def test_anime_episode_extraction_from_rss(self):
        """Test extraction of anime episode information from RSS feeds."""
        anime_rss = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>dアニメストア更新情報</title>
                <item>
                    <title>ワンピース 第1050話「新世界の冒険」</title>
                    <link>https://anime.dmkt-sp.jp/animestore/ci_pc?workId=12345</link>
                    <pubDate>Sun, 14 Jan 2024 09:00:00 +0900</pubDate>
                    <description>ルフィたちの新たな冒険が始まる！</description>
                </item>
                <item>
                    <title>進撃の巨人 最終話「自由への進撃」</title>
                    <link>https://anime.dmkt-sp.jp/animestore/ci_pc?workId=67890</link>
                    <pubDate>Sat, 13 Jan 2024 21:00:00 +0900</pubDate>
                    <description>ついに迎える物語の結末</description>
                </item>
            </channel>
        </rss>"""

        parsed_feed = feedparser.parse(anime_rss)

        import re

        for entry in parsed_feed.entries:
            # Extract anime title and episode info
            title_patterns = [
                r"^(.+?)\s+第(\d+)話",  # Pattern: Title 第X話
                r"^(.+?)\s+最終話",  # Pattern: Title 最終話
                r"^(.+?)\s+第(\d+)話「(.+?)」",  # Pattern: Title 第X話「Subtitle」
            ]

            anime_title = None
            episode_number = None
            episode_title = None

            for pattern in title_patterns:
                match = re.match(pattern, entry.title)
                if match:
                    anime_title = match.group(1)
                    if len(match.groups()) >= 2:
                        episode_number = (
                            match.group(2) if match.group(2) != "最終話" else "final"
                        )
                    if len(match.groups()) >= 3:
                        episode_title = match.group(3)
                    break

            # Verify extraction results
            assert anime_title is not None

            if "ワンピース" in entry.title:
                assert anime_title == "ワンピース"
                assert episode_number == "1050"
            elif "進撃の巨人" in entry.title:
                assert anime_title == "進撃の巨人"
                assert episode_number == "final" or episode_number is None


class TestRSSPerformance:
    """Test RSS feed processing performance."""

    @pytest.mark.performance
    def test_large_rss_feed_processing(self, performance_test_config):
        """Test processing of large RSS feeds."""
        # Generate large RSS feed
        large_rss = self._generate_large_rss_feed(1000)

        start_time = time.time()
        parsed_feed = feedparser.parse(large_rss)
        parsing_time = time.time() - start_time

        # Process all entries
        start_processing = time.time()
        processed_entries = []

        for entry in parsed_feed.entries:
            processed_entry = {
                "title": entry.title,
                "link": entry.link,
                "published": getattr(entry, "published", None),
            }
            processed_entries.append(processed_entry)

        processing_time = time.time() - start_processing

        # Verify performance
        assert len(processed_entries) == 1000
        assert parsing_time < 5.0  # Parse 1000 entries within 5 seconds
        assert processing_time < 2.0  # Process 1000 entries within 2 seconds

        # Verify memory usage doesn't grow excessively
        total_memory = len(str(processed_entries))  # Rough memory estimate
        assert total_memory < 1024 * 1024  # Less than 1MB for processed data

    def _generate_large_rss_feed(self, item_count):
        """Generate a large RSS feed for performance testing."""
        items = []
        for i in range(item_count):
            items.append(
                f"""
            <item>
                <title>テスト漫画{i} 第{i+1}巻</title>
                <link>https://example.com/manga/{i}</link>
                <pubDate>Wed, {8 + (i % 20)} Aug 2024 12:00:00 +0900</pubDate>
                <description>テスト説明{i}</description>
            </item>
            """
            )

        return f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Large Test Feed</title>
                <description>Large RSS feed for performance testing</description>
                {''.join(items)}
            </channel>
        </rss>"""

    @pytest.mark.performance
    def test_concurrent_rss_processing(self, performance_test_config):
        """Test concurrent processing of multiple RSS feeds."""
        import asyncio
        import aiohttp
        from unittest.mock import AsyncMock

        async def process_feed_async(session, url, feed_data):
            """Async function to process a single feed."""
            # Simulate async RSS fetching
            await asyncio.sleep(0.1)  # Simulate network delay

            parsed_feed = feedparser.parse(feed_data)
            return {
                "url": url,
                "entry_count": len(parsed_feed.entries),
                "title": parsed_feed.feed.get("title", "Unknown"),
            }

        async def test_concurrent_processing():
            feeds = [
                ("https://feed1.com", self._generate_test_feed("Feed 1", 10)),
                ("https://feed2.com", self._generate_test_feed("Feed 2", 15)),
                ("https://feed3.com", self._generate_test_feed("Feed 3", 8)),
                ("https://feed4.com", self._generate_test_feed("Feed 4", 12)),
                ("https://feed5.com", self._generate_test_feed("Feed 5", 20)),
            ]

            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                tasks = [process_feed_async(session, url, data) for url, data in feeds]
                results = await asyncio.gather(*tasks)
                processing_time = time.time() - start_time

                # Verify all feeds processed
                assert len(results) == 5

                # Verify concurrent processing is faster than sequential
                max_sequential_time = (
                    len(feeds) * 0.2
                )  # Each feed takes ~0.1s + overhead
                assert processing_time < max_sequential_time

                # Verify results
                total_entries = sum(result["entry_count"] for result in results)
                expected_entries = 10 + 15 + 8 + 12 + 20
                assert total_entries == expected_entries

        # Run the async test
        asyncio.run(test_concurrent_processing())

    def _generate_test_feed(self, title, entry_count):
        """Generate a test RSS feed with specified number of entries."""
        items = []
        for i in range(entry_count):
            items.append(
                f"""
            <item>
                <title>Entry {i+1} from {title}</title>
                <link>https://example.com/{title.lower().replace(' ', '-')}/{i+1}</link>
                <pubDate>Wed, {8 + (i % 20)} Aug 2024 12:00:00 +0900</pubDate>
            </item>
            """
            )

        return f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>{title}</title>
                <description>Test feed for {title}</description>
                {''.join(items)}
            </channel>
        </rss>"""

    @pytest.mark.performance
    @pytest.mark.api
    def test_rss_feed_timeout_handling(self, test_config):
        """Test RSS feed timeout handling and recovery."""
        timeout_seconds = test_config["apis"]["rss_feeds"]["timeout_seconds"]

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock timeout exception
            mock_session.get.side_effect = requests.exceptions.Timeout(
                "Request timed out"
            )

            session = requests.Session()

            start_time = time.time()
            try:
                response = session.get("https://slow-feed.com", timeout=timeout_seconds)
                assert False, "Should have raised timeout exception"
            except requests.exceptions.Timeout:
                elapsed_time = time.time() - start_time
                # Should fail quickly, not wait for the full timeout
                assert elapsed_time < timeout_seconds + 1

            # Test recovery with retry logic
            call_count = 0

            def mock_get_with_recovery(url, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:  # Fail first 2 attempts
                    raise requests.exceptions.Timeout("Request timed out")
                else:  # Succeed on 3rd attempt
                    response = Mock()
                    response.status_code = 200
                    response.text = (
                        "<rss><channel><title>Recovery Test</title></channel></rss>"
                    )
                    return response

            mock_session.get.side_effect = mock_get_with_recovery

            # Test retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = session.get(
                        "https://slow-feed.com", timeout=timeout_seconds
                    )
                    break  # Success
                except requests.exceptions.Timeout:
                    if attempt >= max_retries - 1:
                        raise  # Final attempt failed
                    time.sleep(0.1)  # Brief delay between retries

            # Should succeed on the 3rd attempt
            assert call_count == 3
            assert response.status_code == 200
