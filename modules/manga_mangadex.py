#!/usr/bin/env python3
"""
MangaDex API integration module for manga data collection.

This module provides:
- MangaDex REST API client with rate limiting
- Manga data retrieval and normalization
- Chapter updates tracking
- Error handling and retry logic
- Data validation and filtering

MangaDex API Documentation: https://api.mangadex.org/docs/
Rate Limits: 40 requests per minute (5 bursts allowed)
"""

import asyncio
import json
import logging
import time

logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

from .models import DataSource, WorkType


class MangaDexAPIError(Exception):
    """Custom exception for MangaDex API errors."""


class RateLimiter:
    """Rate limiter for MangaDex API (40 requests per minute)."""

    def __init__(self, requests_per_minute: int = 40):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = 0

    async def wait(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()


class MangaDexAPIClient:
    """MangaDex API client with rate limiting and error handling."""

    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "https://api.mangadex.org")
        self.timeout = config.get("timeout_seconds", 30)
        self.rate_limit_config = config.get("rate_limit", {})
        self.rate_limiter = RateLimiter(self.rate_limit_config.get("requests_per_minute", 40))
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def get_recent_manga(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recently updated manga from MangaDex.

        Args:
            limit: Maximum number of results (max 100)

        Returns:
            List of manga data dictionaries
        """
        await self.rate_limiter.wait()

        params = {
            "limit": min(limit, 100),
            "order[updatedAt]": "desc",
            "includes[]": ["cover_art", "author", "artist"],
            "contentRating[]": [
                "safe",
                "suggestive",
            ],  # Exclude erotica and pornographic
        }

        try:
            async with self.session.get(f"{self.base_url}/manga", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_manga_list(data.get("data", []))
                elif response.status == 429:
                    self.logger.warning("Rate limit exceeded, waiting...")
                    await asyncio.sleep(10)
                    return await self.get_recent_manga(limit)
                else:
                    self.logger.error(
                        f"MangaDex API error: {response.status} - {await response.text()}"
                    )
                    raise MangaDexAPIError(f"API request failed with status {response.status}")

        except asyncio.TimeoutError:
            self.logger.error("MangaDex API request timeout")
            raise MangaDexAPIError("Request timeout")
        except Exception as e:
            self.logger.error(f"MangaDex API request error: {str(e)}")
            raise MangaDexAPIError(f"Request failed: {str(e)}")

    async def get_latest_chapters(self, limit: int = 100, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get latest chapter updates from MangaDex.

        Args:
            limit: Maximum number of results (max 500)
            hours: Get chapters from last N hours

        Returns:
            List of chapter data dictionaries
        """
        await self.rate_limiter.wait()

        # Calculate time range
        now = datetime.utcnow()
        since = now - timedelta(hours=hours)
        created_at_since = since.isoformat(timespec="seconds")

        params = {
            "limit": min(limit, 500),
            "order[createdAt]": "desc",
            "translatedLanguage[]": ["ja", "en"],
            "contentRating[]": ["safe", "suggestive"],
            "includes[]": ["manga", "scanlation_group"],
            "createdAtSince": created_at_since,
        }

        try:
            async with self.session.get(f"{self.base_url}/chapter", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_chapter_list(data.get("data", []))
                else:
                    self.logger.error(f"MangaDex API error: {response.status}")
                    raise MangaDexAPIError(f"API request failed with status {response.status}")

        except Exception as e:
            self.logger.error(f"MangaDex API request error: {str(e)}")
            raise MangaDexAPIError(f"Request failed: {str(e)}")

    async def search_manga(self, title: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search manga by title.

        Args:
            title: Search query
            limit: Maximum number of results

        Returns:
            List of manga data dictionaries
        """
        await self.rate_limiter.wait()

        params = {
            "title": title,
            "limit": min(limit, 100),
            "includes[]": ["cover_art", "author", "artist"],
            "contentRating[]": ["safe", "suggestive"],
        }

        try:
            async with self.session.get(f"{self.base_url}/manga", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_manga_list(data.get("data", []))
                else:
                    self.logger.error(f"MangaDex API error: {response.status}")
                    raise MangaDexAPIError(f"API request failed with status {response.status}")

        except Exception as e:
            self.logger.error(f"MangaDex API request error: {str(e)}")
            raise MangaDexAPIError(f"Request failed: {str(e)}")

    def _normalize_manga_list(self, manga_list: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize manga data from MangaDex API format."""
        normalized = []

        for manga in manga_list:
            try:
                attrs = manga.get("attributes", {})
                manga_id = manga.get("id", "")

                # Get titles
                titles = attrs.get("title", {})
                alt_titles = attrs.get("altTitles", [])

                title_ja = titles.get("ja", "")
                title_en = titles.get("en", "")

                # Use first available title as canonical
                canonical_title = title_en or title_ja or list(titles.values())[0] if titles else ""

                # Get cover image
                cover_url = ""
                relationships = manga.get("relationships", [])
                for rel in relationships:
                    if rel.get("type") == "cover_art":
                        cover_filename = rel.get("attributes", {}).get("fileName", "")
                        if cover_filename:
                            cover_url = (
                                f"https://uploads.mangadex.org/covers/{manga_id}/{cover_filename}"
                            )
                        break

                normalized_item = {
                    "id": manga_id,
                    "title": canonical_title,
                    "title_ja": title_ja,
                    "title_en": title_en,
                    "alt_titles": alt_titles,
                    "type": WorkType.MANGA.value,
                    "status": attrs.get("status", ""),
                    "description": attrs.get("description", {}).get("en", ""),
                    "year": attrs.get("year", ""),
                    "content_rating": attrs.get("contentRating", ""),
                    "tags": [
                        tag.get("attributes", {}).get("name", {}).get("en", "")
                        for tag in attrs.get("tags", [])
                    ],
                    "cover_image": cover_url,
                    "source": DataSource.MANGADEX.value,
                    "source_url": f"https://mangadex.org/title/{manga_id}",
                    "last_updated": attrs.get("updatedAt", ""),
                }
                normalized.append(normalized_item)
            except Exception as e:
                self.logger.warning(f"Failed to normalize manga data: {str(e)}")
                continue

        return normalized

    def _normalize_chapter_list(self, chapter_list: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize chapter data from MangaDex API format."""
        normalized = []

        for chapter in chapter_list:
            try:
                attrs = chapter.get("attributes", {})
                chapter_id = chapter.get("id", "")

                # Get manga ID from relationships
                manga_id = ""
                manga_title = ""
                relationships = chapter.get("relationships", [])
                for rel in relationships:
                    if rel.get("type") == "manga":
                        manga_id = rel.get("id", "")
                        manga_title = (
                            rel.get("attributes", {}).get("title", {}).get("en", "Unknown")
                        )
                        break

                normalized_item = {
                    "id": chapter_id,
                    "manga_id": manga_id,
                    "manga_title": manga_title,
                    "chapter": attrs.get("chapter", ""),
                    "volume": attrs.get("volume", ""),
                    "title": attrs.get("title", ""),
                    "language": attrs.get("translatedLanguage", ""),
                    "pages": attrs.get("pages", 0),
                    "publish_date": attrs.get("publishAt", ""),
                    "created_at": attrs.get("createdAt", ""),
                    "updated_at": attrs.get("updatedAt", ""),
                    "source": DataSource.MANGADEX.value,
                    "source_url": f"https://mangadex.org/chapter/{chapter_id}",
                    "manga_url": f"https://mangadex.org/title/{manga_id}",
                }
                normalized.append(normalized_item)
            except Exception as e:
                self.logger.warning(f"Failed to normalize chapter data: {str(e)}")
                continue

        return normalized


async def collect_mangadex_manga(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Collect manga data from MangaDex API.

    Args:
        config: API configuration dictionary

    Returns:
        List of normalized manga data
    """
    logger.info("Starting MangaDex manga collection...")

    all_manga = []

    async with MangaDexAPIClient(config) as client:
        try:
            # Get recently updated manga
            recent_manga = await client.get_recent_manga(limit=50)
            all_manga.extend(recent_manga)
            logger.info(f"Collected {len(recent_manga)} recent manga")

        except MangaDexAPIError as e:
            logger.error(f"MangaDex API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in MangaDex manga collection: {str(e)}")

    logger.info(f"MangaDex manga collection complete: {len(all_manga)} total items")
    return all_manga


async def collect_mangadex_chapters(
    config: Dict[str, Any], hours: int = 24
) -> List[Dict[str, Any]]:
    """
    Collect chapter updates from MangaDex API.

    Args:
        config: API configuration dictionary
        hours: Get chapters from last N hours

    Returns:
        List of normalized chapter data
    """
    logger.info(f"Starting MangaDex chapter collection (last {hours} hours)...")

    all_chapters = []

    async with MangaDexAPIClient(config) as client:
        try:
            # Get latest chapter updates
            latest_chapters = await client.get_latest_chapters(limit=100, hours=hours)
            all_chapters.extend(latest_chapters)
            logger.info(f"Collected {len(latest_chapters)} chapter updates")

        except MangaDexAPIError as e:
            logger.error(f"MangaDex API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in MangaDex chapter collection: {str(e)}")

    logger.info(f"MangaDex chapter collection complete: {len(all_chapters)} total items")
    return all_chapters


if __name__ == "__main__":
    # Test code
    logging.basicConfig(level=logging.INFO)

    import json

    config = {
        "base_url": "https://api.mangadex.org",
        "timeout_seconds": 30,
        "rate_limit": {"requests_per_minute": 40, "retry_delay_seconds": 5},
    }

    async def test():
        manga_data = await collect_mangadex_manga(config)
        chapter_data = await collect_mangadex_chapters(config, hours=24)
        logger.info(f"Collected {len(manga_data)} manga and {len(chapter_data)} chapter updates")
        if manga_data:
            logger.info("\nSample manga:")
            logger.info(json.dumps(manga_data[0], indent=2, ensure_ascii=False))

    asyncio.run(test())
