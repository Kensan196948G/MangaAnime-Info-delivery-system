#!/usr/bin/env python3
"""
Enhanced Manga RSS collection module with additional sources.

This module extends the manga_rss module with:
- Magazine Pocket (マガポケ) RSS feed support
- Jump BOOK Store (ジャンプBOOKストア) integration
- Rakuten Kobo manga feed support
- Improved error handling and retry logic
- Feed-specific parsing rules
"""

import logging
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import time
from urllib.parse import urljoin, urlparse
import re
import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup

from .models import RSSFeedItem, Work, Release, WorkType, ReleaseType, DataSource


@dataclass
class MangaRSSFeedConfig:
    """Manga RSS feed configuration."""

    name: str
    url: str
    category: str = "manga"
    enabled: bool = True
    priority: str = "medium"
    timeout: int = 20
    retry_count: int = 3
    retry_delay: int = 2
    parser_type: str = "standard"  # standard, json, html
    custom_selectors: Optional[Dict[str, str]] = None


class EnhancedMangaRSSCollector:
    """
    Enhanced manga RSS collector with support for multiple sources.

    Supported sources:
    - Magazine Pocket (マガポケ)
    - Jump BOOK Store (ジャンプBOOKストア)
    - Rakuten Kobo
    - BookWalker
    - General manga RSS feeds
    """

    # Pre-configured manga sources
    MANGA_SOURCES = {
        "magapoke": MangaRSSFeedConfig(
            name="マガジンポケット (Magazine Pocket)",
            url="https://pocket.shonenmagazine.com/rss/series/",
            category="manga",
            enabled=True,
            priority="high",
            timeout=20,
            parser_type="html",
            custom_selectors={
                "title": ".series-title",
                "description": ".series-description",
                "link": "a.series-link"
            }
        ),
        "jump_book_store": MangaRSSFeedConfig(
            name="ジャンプBOOKストア (Jump BOOK Store)",
            url="https://jumpbookstore.com/rss/newrelease.xml",
            category="manga",
            enabled=True,
            priority="high",
            timeout=20,
            parser_type="standard"
        ),
        "rakuten_kobo": MangaRSSFeedConfig(
            name="楽天Kobo - コミック新刊",
            url="https://books.rakuten.co.jp/rss/comics/",
            category="manga",
            enabled=True,
            priority="medium",
            timeout=20,
            parser_type="standard"
        ),
        "bookwalker": MangaRSSFeedConfig(
            name="BOOK☆WALKER - マンガ新刊",
            url="https://bookwalker.jp/series/rss/",
            category="manga",
            enabled=True,
            priority="high",
            timeout=20,
            parser_type="standard"
        ),
        "manga_up": MangaRSSFeedConfig(
            name="マンガUP! - SQUARE ENIX",
            url="https://magazine.jp.square-enix.com/mangaup/rss/",
            category="manga",
            enabled=True,
            priority="medium",
            timeout=20,
            parser_type="html"
        ),
        "comic_walker": MangaRSSFeedConfig(
            name="ComicWalker - 無料マンガ",
            url="https://comic-walker.com/rss/",
            category="manga",
            enabled=True,
            priority="medium",
            timeout=20,
            parser_type="standard"
        )
    }

    def __init__(
        self,
        config_manager=None,
        timeout: int = 20,
        max_retries: int = 3
    ):
        """
        Initialize enhanced manga RSS collector.

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
        self.user_agent = "MangaAnimeNotifier/2.0 (Enhanced RSS Collector)"

        # Request statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_items": 0
        }

        self.logger.info(
            f"Enhanced Manga RSS Collector initialized with "
            f"{len(self.MANGA_SOURCES)} sources"
        )

    def get_all_sources(self) -> List[MangaRSSFeedConfig]:
        """Get all available manga RSS sources."""
        return [
            source for source in self.MANGA_SOURCES.values()
            if source.enabled
        ]

    def get_source_by_name(self, name: str) -> Optional[MangaRSSFeedConfig]:
        """Get manga RSS source by name."""
        return self.MANGA_SOURCES.get(name)

    async def fetch_feed_async(
        self,
        feed_config: MangaRSSFeedConfig
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
            "Accept": "application/rss+xml, application/xml, text/xml, text/html"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    feed_config.url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=feed_config.timeout)
                ) as response:
                    self.stats["total_requests"] += 1

                    if response.status == 200:
                        content = await response.text()

                        # Parse based on parser type
                        if feed_config.parser_type == "standard":
                            items = self._parse_standard_rss(content, feed_config)
                        elif feed_config.parser_type == "json":
                            items = self._parse_json_feed(content, feed_config)
                        elif feed_config.parser_type == "html":
                            items = self._parse_html_feed(content, feed_config)
                        else:
                            items = self._parse_standard_rss(content, feed_config)

                        self.stats["successful_requests"] += 1
                        self.stats["total_items"] += len(items)

                        self.logger.info(
                            f"Successfully fetched {len(items)} items from {feed_config.name}"
                        )

                        return items

                    else:
                        self.logger.warning(
                            f"Failed to fetch {feed_config.name}: HTTP {response.status}"
                        )
                        self.stats["failed_requests"] += 1
                        return []

        except Exception as e:
            self.logger.error(f"Error fetching {feed_config.name}: {e}")
            self.stats["failed_requests"] += 1
            return []

    def _parse_standard_rss(
        self,
        content: str,
        feed_config: MangaRSSFeedConfig
    ) -> List[RSSFeedItem]:
        """Parse standard RSS/Atom feed."""
        items = []

        try:
            feed = feedparser.parse(content)

            for entry in feed.entries:
                # Extract basic information
                title = entry.get("title", "")
                link = entry.get("link", "")
                description = entry.get("summary", entry.get("description", ""))
                pub_date = self._parse_date(entry.get("published", entry.get("updated", "")))

                # Extract metadata
                metadata = {
                    "source": feed_config.name,
                    "feed_url": feed_config.url,
                    "category": feed_config.category
                }

                # Add author if available
                if "author" in entry:
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
                    metadata=metadata
                )

                items.append(item)

        except Exception as e:
            self.logger.error(f"Error parsing standard RSS: {e}")

        return items

    def _parse_json_feed(
        self,
        content: str,
        feed_config: MangaRSSFeedConfig
    ) -> List[RSSFeedItem]:
        """Parse JSON feed format."""
        items = []

        try:
            data = json.loads(content)

            # Handle different JSON feed structures
            entries = data.get("items", data.get("entries", []))

            for entry in entries:
                title = entry.get("title", "")
                link = entry.get("url", entry.get("link", ""))
                description = entry.get("content_text", entry.get("summary", ""))
                pub_date = self._parse_date(
                    entry.get("date_published", entry.get("published", ""))
                )

                metadata = {
                    "source": feed_config.name,
                    "feed_url": feed_config.url,
                    "category": feed_config.category
                }

                # Add author
                if "author" in entry:
                    author_info = entry["author"]
                    if isinstance(author_info, dict):
                        metadata["author"] = author_info.get("name", "")
                    else:
                        metadata["author"] = str(author_info)

                # Add tags
                if "tags" in entry:
                    metadata["tags"] = entry["tags"]

                item = RSSFeedItem(
                    title=title,
                    link=link,
                    description=description,
                    pub_date=pub_date,
                    source=feed_config.name,
                    metadata=metadata
                )

                items.append(item)

        except Exception as e:
            self.logger.error(f"Error parsing JSON feed: {e}")

        return items

    def _parse_html_feed(
        self,
        content: str,
        feed_config: MangaRSSFeedConfig
    ) -> List[RSSFeedItem]:
        """Parse HTML page as feed using custom selectors."""
        items = []

        try:
            soup = BeautifulSoup(content, 'html.parser')

            # Use custom selectors if provided
            if feed_config.custom_selectors:
                title_selector = feed_config.custom_selectors.get("title", ".title")
                link_selector = feed_config.custom_selectors.get("link", "a")
                desc_selector = feed_config.custom_selectors.get("description", ".description")

                # Find all items (assume they're in a common container)
                containers = soup.find_all(class_=re.compile(r"(item|entry|article|series)"))

                for container in containers:
                    title_elem = container.select_one(title_selector)
                    link_elem = container.select_one(link_selector)
                    desc_elem = container.select_one(desc_selector)

                    title = title_elem.get_text(strip=True) if title_elem else ""
                    link = link_elem.get("href", "") if link_elem else ""
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    if title and link:
                        # Make link absolute if needed
                        if not link.startswith("http"):
                            base_url = urlparse(feed_config.url).scheme + "://" + urlparse(feed_config.url).netloc
                            link = urljoin(base_url, link)

                        item = RSSFeedItem(
                            title=title,
                            link=link,
                            description=description,
                            pub_date=datetime.now(),
                            source=feed_config.name,
                            metadata={
                                "source": feed_config.name,
                                "feed_url": feed_config.url,
                                "category": feed_config.category
                            }
                        )

                        items.append(item)

        except Exception as e:
            self.logger.error(f"Error parsing HTML feed: {e}")

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
            "%a, %d %b %Y %H:%M:%S %z",
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
            import feedparser
            parsed = feedparser._parse_date(date_str)
            if parsed:
                return datetime(*parsed[:6])
        except:
            pass

        return None

    async def fetch_all_feeds(self) -> List[RSSFeedItem]:
        """
        Fetch all enabled manga RSS feeds asynchronously.

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
        self,
        feed_items: List[RSSFeedItem]
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
            # Extract volume/episode number from title
            number, release_type = self._extract_number_and_type(item.title)

            # Clean title (remove volume/episode numbers)
            clean_title = self._clean_title(item.title)

            # Check if work already exists
            if clean_title not in work_map:
                # Create new work
                work = Work(
                    title=clean_title,
                    work_type=WorkType.MANGA,
                    official_url=item.link,
                    metadata={
                        "source": item.source,
                        "description": item.description,
                        "original_title": item.title
                    }
                )
                works.append(work)
                work_map[clean_title] = len(works) - 1

            # Create release
            release = Release(
                work_id=0,  # Will be set after DB insert
                release_type=release_type or ReleaseType.VOLUME,
                number=number,
                platform=item.source,
                release_date=item.pub_date.date() if item.pub_date else datetime.now().date(),
                source=DataSource.RSS_GENERAL,
                source_url=item.link,
                metadata={
                    "source": item.source,
                    "description": item.description
                }
            )
            releases.append(release)

        self.logger.info(
            f"Converted {len(feed_items)} items to "
            f"{len(works)} works and {len(releases)} releases"
        )

        return works, releases

    def _extract_number_and_type(self, title: str) -> Tuple[Optional[str], Optional[ReleaseType]]:
        """Extract volume/episode number and release type from title."""
        # Volume patterns
        volume_patterns = [
            r"第(\d+)巻",
            r"(\d+)巻",
            r"vol\.?\s*(\d+)",
            r"volume\s*(\d+)",
        ]

        # Episode patterns
        episode_patterns = [
            r"第(\d+)話",
            r"#(\d+)",
            r"ep\.?\s*(\d+)",
            r"episode\s*(\d+)",
        ]

        # Check volume patterns
        for pattern in volume_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1), ReleaseType.VOLUME

        # Check episode patterns
        for pattern in episode_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1), ReleaseType.EPISODE

        return None, None

    def _clean_title(self, title: str) -> str:
        """Clean title by removing volume/episode numbers."""
        # Remove volume/episode numbers
        patterns = [
            r"\s*第\d+[巻話]",
            r"\s*\d+巻",
            r"\s*vol\.?\s*\d+",
            r"\s*volume\s*\d+",
            r"\s*第\d+話",
            r"\s*#\d+",
            r"\s*ep\.?\s*\d+",
            r"\s*episode\s*\d+",
        ]

        clean = title
        for pattern in patterns:
            clean = re.sub(pattern, "", clean, flags=re.IGNORECASE)

        return clean.strip()

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
            "available_sources": len(self.MANGA_SOURCES),
            "enabled_sources": len(self.get_all_sources())
        }


# Async wrapper functions

async def fetch_enhanced_manga_feeds() -> List[RSSFeedItem]:
    """Fetch all enhanced manga RSS feeds."""
    collector = EnhancedMangaRSSCollector()
    return await collector.fetch_all_feeds()


async def fetch_manga_works_and_releases() -> Tuple[List[Work], List[Release]]:
    """Fetch manga data as Work/Release models."""
    collector = EnhancedMangaRSSCollector()
    items = await collector.fetch_all_feeds()
    return collector.convert_to_works_and_releases(items)


# Synchronous wrappers

def fetch_enhanced_manga_feeds_sync() -> List[RSSFeedItem]:
    """Synchronous wrapper for fetch_enhanced_manga_feeds."""
    return asyncio.run(fetch_enhanced_manga_feeds())


def fetch_manga_works_and_releases_sync() -> Tuple[List[Work], List[Release]]:
    """Synchronous wrapper for fetch_manga_works_and_releases."""
    return asyncio.run(fetch_manga_works_and_releases())
