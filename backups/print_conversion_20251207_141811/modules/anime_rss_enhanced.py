#!/usr/bin/env python3
"""
Enhanced Anime RSS collection module.

This module provides RSS feed collection for anime information from multiple sources:
- MyAnimeList News
- Crunchyroll News
- Tokyo Otaku Mode News
- Anime UK News
- Otaku News
- Other international anime news sources

Features:
- Multiple RSS source support
- Asynchronous fetching with error handling
- Retry logic and timeout management
- Feed-specific parsing rules
- Duplicate detection
"""

import logging
import feedparser
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import re

from .models import RSSFeedItem, Work, Release, WorkType, ReleaseType, DataSource


@dataclass
class AnimeRSSFeedConfig:
    """Anime RSS feed configuration."""

    name: str
    url: str
    category: str = "anime"
    enabled: bool = True
    priority: str = "medium"
    timeout: int = 20
    retry_count: int = 3
    retry_delay: int = 2
    parser_type: str = "standard"  # standard, json, html
    custom_selectors: Optional[Dict[str, str]] = None
    language: str = "en"  # en, ja
    region: str = "global"  # global, jp, na, eu


class EnhancedAnimeRSSCollector:
    """
    Enhanced anime RSS collector with support for multiple sources.

    Supported sources:
    - MyAnimeList (anime news)
    - Crunchyroll (anime news)
    - Tokyo Otaku Mode (anime news)
    - Anime UK News
    - Otaku News
    - Other anime RSS feeds
    """

    # Pre-configured anime sources
    ANIME_SOURCES = {
        "myanimelist": AnimeRSSFeedConfig(
            name="MyAnimeList News",
            url="https://myanimelist.net/rss/news.xml",
            category="anime",
            enabled=True,
            priority="high",
            timeout=20,
            parser_type="standard",
            language="en",
            region="global",
        ),
        "crunchyroll": AnimeRSSFeedConfig(
            name="Crunchyroll Anime News",
            url="https://feeds.feedburner.com/crunchyroll/animenews",
            category="anime",
            enabled=True,
            priority="high",
            timeout=20,
            parser_type="standard",
            language="en",
            region="global",
        ),
        "tokyo_otaku_mode": AnimeRSSFeedConfig(
            name="Tokyo Otaku Mode News",
            url="https://otakumode.com/news/feed",
            category="anime",
            enabled=True,
            priority="medium",
            timeout=20,
            parser_type="standard",
            language="en",
            region="global",
        ),
        "anime_uk_news": AnimeRSSFeedConfig(
            name="Anime UK News",
            url="https://animeuknews.net/feed",
            category="anime",
            enabled=True,
            priority="medium",
            timeout=20,
            parser_type="standard",
            language="en",
            region="eu",
        ),
        "otaku_news": AnimeRSSFeedConfig(
            name="Otaku News",
            url="https://otakunews.com/rss/rss.xml",
            category="anime",
            enabled=True,
            priority="medium",
            timeout=20,
            parser_type="standard",
            language="en",
            region="na",
        ),
    }

    def __init__(self, config_manager=None, timeout: int = 20, max_retries: int = 3):
        """
        Initialize enhanced anime RSS collector.

        Args:
            config_manager: Configuration manager instance
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.config = config_manager
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)

        # User agent for requests
        self.user_agent = "MangaAnimeNotifier/2.0 (Enhanced Anime RSS Collector)"

        # Request statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_items": 0,
            "duplicates_filtered": 0,
        }

        # Cache for deduplication
        self.seen_items = set()

        self.logger.info(
            "Enhanced Anime RSS Collector initialized with "
            f"{len(self.ANIME_SOURCES)} sources"
        )

    def get_all_sources(self) -> List[AnimeRSSFeedConfig]:
        """Get all available anime RSS sources."""
        return [source for source in self.ANIME_SOURCES.values() if source.enabled]

    def get_sources_by_region(self, region: str) -> List[AnimeRSSFeedConfig]:
        """Get anime RSS sources by region."""
        return [
            source
            for source in self.ANIME_SOURCES.values()
            if source.enabled and source.region == region
        ]

    def get_source_by_name(self, name: str) -> Optional[AnimeRSSFeedConfig]:
        """Get anime RSS source by name."""
        return self.ANIME_SOURCES.get(name)

    async def fetch_feed_async(
        self, feed_config: AnimeRSSFeedConfig
    ) -> List[RSSFeedItem]:
        """
        Asynchronously fetch and parse RSS feed.

        Args:
            feed_config: Feed configuration

        Returns:
            List of RSS feed items
        """
        self.logger.info(f"Fetching feed: {feed_config.name}")

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/rss+xml, application/xml, text/xml, text/html",
        }

        retry_count = 0
        while retry_count <= self.max_retries:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        feed_config.url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=feed_config.timeout),
                    ) as response:
                        self.stats["total_requests"] += 1

                        if response.status == 200:
                            content = await response.text()

                            # Parse RSS feed
                            items = self._parse_standard_rss(content, feed_config)

                            # Filter duplicates
                            unique_items = []
                            for item in items:
                                item_hash = hash(f"{item.title}:{item.link}")
                                if item_hash not in self.seen_items:
                                    self.seen_items.add(item_hash)
                                    unique_items.append(item)
                                else:
                                    self.stats["duplicates_filtered"] += 1

                            self.stats["successful_requests"] += 1
                            self.stats["total_items"] += len(unique_items)

                            self.logger.info(
                                f"Successfully fetched {len(unique_items)} unique items "
                                f"from {feed_config.name}"
                            )

                            return unique_items

                        elif response.status == 404:
                            self.logger.warning(
                                f"Feed not found (404): {feed_config.name}"
                            )
                            self.stats["failed_requests"] += 1
                            return []

                        elif response.status >= 500:
                            self.logger.warning(
                                f"Server error ({response.status}): {feed_config.name}"
                            )
                            # Retry on server error
                            retry_count += 1
                            if retry_count <= self.max_retries:
                                await asyncio.sleep(feed_config.retry_delay)
                                continue
                            else:
                                self.stats["failed_requests"] += 1
                                return []
                        else:
                            self.logger.warning(
                                f"HTTP error ({response.status}): {feed_config.name}"
                            )
                            self.stats["failed_requests"] += 1
                            return []

            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout fetching {feed_config.name}")
                retry_count += 1
                if retry_count <= self.max_retries:
                    await asyncio.sleep(feed_config.retry_delay)
                    continue
                else:
                    self.stats["failed_requests"] += 1
                    return []

            except Exception as e:
                self.logger.error(f"Error fetching {feed_config.name}: {e}")
                retry_count += 1
                if retry_count <= self.max_retries:
                    await asyncio.sleep(feed_config.retry_delay)
                    continue
                else:
                    self.stats["failed_requests"] += 1
                    return []

        return []

    def _parse_standard_rss(
        self, content: str, feed_config: AnimeRSSFeedConfig
    ) -> List[RSSFeedItem]:
        """Parse standard RSS/Atom feed."""
        items = []

        try:
            feed = feedparser.parse(content)

            # Check if feed is valid
            if not feed.entries:
                self.logger.warning(f"No entries found in {feed_config.name}")
                return items

            for entry in feed.entries:
                # Extract basic information
                title = entry.get("title", "")
                link = entry.get("link", "")
                description = entry.get("summary", entry.get("description", ""))
                pub_date = self._parse_date(
                    entry.get("published", entry.get("updated", ""))
                )

                # Skip if no title or link
                if not title or not link:
                    continue

                # Extract metadata
                metadata = {
                    "source": feed_config.name,
                    "feed_url": feed_config.url,
                    "category": feed_config.category,
                    "region": feed_config.region,
                    "language": feed_config.language,
                }

                # Add author if available
                if "author_detail" in entry:
                    metadata["author"] = entry["author_detail"].get("name", "")
                elif "author" in entry:
                    metadata["author"] = entry["author"]

                # Add tags/categories
                if "tags" in entry:
                    metadata["tags"] = [tag.get("term", "") for tag in entry["tags"]]

                # Create feed item
                item = RSSFeedItem(
                    title=title,
                    link=link,
                    description=description,
                    pub_date=pub_date,
                    source=feed_config.name,
                    metadata=metadata,
                )

                items.append(item)

        except Exception as e:
            self.logger.error(f"Error parsing RSS from {feed_config.name}: {e}")

        return items

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats."""
        if not date_str:
            return None

        # Common date patterns
        patterns = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S GMT",
            "%Y-%m-%d",
            "%d/%m/%Y",
        ]

        for pattern in patterns:
            try:
                return datetime.strptime(date_str, pattern)
            except (ValueError, TypeError):
                continue

        # Try feedparser's date parser as fallback
        try:
            parsed = feedparser._parse_date(date_str)
            if parsed:
                return datetime(*parsed[:6])
        except:
            pass

        return None

    async def fetch_all_feeds(self) -> List[RSSFeedItem]:
        """
        Fetch all enabled anime RSS feeds asynchronously.

        Returns:
            Combined list of all RSS feed items
        """
        all_items = []

        # Get enabled sources
        sources = self.get_all_sources()

        # Create tasks for parallel fetching
        tasks = [self.fetch_feed_async(source) for source in sources]

        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Task failed with exception: {result}")

        self.logger.info(
            f"Fetched total of {len(all_items)} items from {len(sources)} sources"
        )

        return all_items

    def convert_to_works_and_releases(
        self, feed_items: List[RSSFeedItem]
    ) -> Tuple[List[Work], List[Release]]:
        """
        Convert RSS feed items to Work and Release models.

        Args:
            feed_items: List of RSS feed items

        Returns:
            Tuple of (works, releases)
        """
        works = []
        releases = []

        work_map: Dict[str, int] = {}  # title -> work index

        for item in feed_items:
            # Extract episode number from title
            number, release_type = self._extract_episode_number(item.title)

            # Clean title (remove episode numbers)
            clean_title = self._clean_title(item.title)

            # Check if work already exists
            if clean_title not in work_map:
                # Create new work
                work = Work(
                    title=clean_title,
                    work_type=WorkType.ANIME,
                    official_url=item.link,
                    metadata={
                        "source": item.source,
                        "description": item.description,
                        "original_title": item.title,
                    },
                )
                works.append(work)
                work_map[clean_title] = len(works) - 1

            # Create release
            release = Release(
                work_id=0,  # Will be set after DB insert
                release_type=release_type or ReleaseType.EPISODE,
                number=number,
                platform="News",
                release_date=(
                    item.pub_date.date() if item.pub_date else datetime.now().date()
                ),
                source=DataSource.RSS_GENERAL,
                source_url=item.link,
                metadata={"source": item.source, "description": item.description},
            )
            releases.append(release)

        self.logger.info(
            f"Converted {len(feed_items)} items to "
            f"{len(works)} works and {len(releases)} releases"
        )

        return works, releases

    def _extract_episode_number(
        self, title: str
    ) -> Tuple[Optional[str], Optional[ReleaseType]]:
        """Extract episode number from title."""
        # Episode patterns
        episode_patterns = [
            r"第(\d+)話",
            r"episode\s+(\d+)",
            r"ep\.?\s*(\d+)",
            r"#(\d+)",
            r"\s(\d+)話",
        ]

        for pattern in episode_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1), ReleaseType.EPISODE

        return None, None

    def _clean_title(self, title: str) -> str:
        """Clean title by removing episode numbers and metadata."""
        # Remove episode numbers and common prefixes
        patterns = [
            r"\s*第\d+話",
            r"\s*episode\s+\d+",
            r"\s*ep\.?\s*\d+",
            r"\s*#\d+",
            r"\s*\d+話",
            r"\s*[「『].*[」』]$",  # Remove quoted text at end
        ]

        clean = title
        for pattern in patterns:
            clean = re.sub(pattern, "", clean, flags=re.IGNORECASE)

        # Remove extra whitespace
        clean = re.sub(r"\s+", " ", clean).strip()

        return clean

    def get_statistics(self) -> Dict[str, Any]:
        """Get collector statistics."""
        success_rate = 0.0
        if self.stats["total_requests"] > 0:
            success_rate = (
                self.stats["successful_requests"] / self.stats["total_requests"]
            )

        return {
            "total_requests": self.stats["total_requests"],
            "successful_requests": self.stats["successful_requests"],
            "failed_requests": self.stats["failed_requests"],
            "success_rate": f"{success_rate:.2%}",
            "total_items_collected": self.stats["total_items"],
            "duplicates_filtered": self.stats["duplicates_filtered"],
            "available_sources": len(self.ANIME_SOURCES),
            "enabled_sources": len(self.get_all_sources()),
        }


# Async wrapper functions


async def fetch_enhanced_anime_feeds() -> List[RSSFeedItem]:
    """Fetch all enhanced anime RSS feeds."""
    collector = EnhancedAnimeRSSCollector()
    return await collector.fetch_all_feeds()


async def fetch_anime_works_and_releases() -> Tuple[List[Work], List[Release]]:
    """Fetch anime data as Work/Release models."""
    collector = EnhancedAnimeRSSCollector()
    items = await collector.fetch_all_feeds()
    return collector.convert_to_works_and_releases(items)


# Synchronous wrappers


def fetch_enhanced_anime_feeds_sync() -> List[RSSFeedItem]:
    """Synchronous wrapper for fetch_enhanced_anime_feeds."""
    return asyncio.run(fetch_enhanced_anime_feeds())


def fetch_anime_works_and_releases_sync() -> Tuple[List[Work], List[Release]]:
    """Synchronous wrapper for fetch_anime_works_and_releases."""
    return asyncio.run(fetch_anime_works_and_releases())
