#!/usr/bin/env python3
"""
MangaUpdates API integration module for manga release information.

This module provides:
- MangaUpdates REST API client with rate limiting
- Manga release data retrieval and normalization
- Series information tracking
- Error handling and retry logic
- Data validation and filtering

MangaUpdates API Documentation: https://api.mangaupdates.com/v1/docs
Rate Limits: 30 requests per minute
"""

import asyncio
import json
import logging
import time

logger = logging.getLogger(__name__)
from typing import Any, Dict, List, Optional

import aiohttp

from .models import DataSource, WorkType


class MangaUpdatesAPIError(Exception):
    """Custom exception for MangaUpdates API errors."""


class RateLimiter:
    """Rate limiter for MangaUpdates API (30 requests per minute)."""

    def __init__(self, requests_per_minute: int = 30):
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


class MangaUpdatesAPIClient:
    """MangaUpdates API client with rate limiting and error handling."""

    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "https://api.mangaupdates.com/v1")
        self.timeout = config.get("timeout_seconds", 30)
        self.rate_limit_config = config.get("rate_limit", {})
        self.rate_limiter = RateLimiter(self.rate_limit_config.get("requests_per_minute", 30))
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MangaAnime-Info-Delivery-System/1.0",
        }
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout), headers=headers
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def get_latest_releases(self, page: int = 1, per_page: int = 50) -> List[Dict[str, Any]]:
        """
        Get latest manga releases from MangaUpdates.

        Args:
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of release data dictionaries
        """
        await self.rate_limiter.wait()

        params = {"page": page, "perpage": min(per_page, 100)}

        try:
            async with self.session.get(f"{self.base_url}/releases", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_releases(data.get("results", []))
                elif response.status == 429:
                    self.logger.warning("Rate limit exceeded, waiting...")
                    await asyncio.sleep(10)
                    return await self.get_latest_releases(page, per_page)
                else:
                    self.logger.error(
                        f"MangaUpdates API error: {response.status} - {await response.text()}"
                    )
                    raise MangaUpdatesAPIError(f"API request failed with status {response.status}")

        except asyncio.TimeoutError:
            self.logger.error("MangaUpdates API request timeout")
            raise MangaUpdatesAPIError("Request timeout")
        except Exception as e:
            self.logger.error(f"MangaUpdates API request error: {str(e)}")
            raise MangaUpdatesAPIError(f"Request failed: {str(e)}")

    async def search_series(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """
        Search manga series by title.

        Args:
            query: Search query
            page: Page number

        Returns:
            List of series data dictionaries
        """
        await self.rate_limiter.wait()

        search_data = {"search": query, "page": page, "perpage": 25}

        try:
            async with self.session.post(
                f"{self.base_url}/series/search", json=search_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_series(data.get("results", []))
                else:
                    self.logger.error(f"MangaUpdates API error: {response.status}")
                    raise MangaUpdatesAPIError(f"API request failed with status {response.status}")

        except Exception as e:
            self.logger.error(f"MangaUpdates API request error: {str(e)}")
            raise MangaUpdatesAPIError(f"Request failed: {str(e)}")

    async def get_series_info(self, series_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a manga series.

        Args:
            series_id: Series ID

        Returns:
            Series data dictionary or None
        """
        await self.rate_limiter.wait()

        try:
            async with self.session.get(f"{self.base_url}/series/{series_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_series_detail(data)
                else:
                    self.logger.error(f"MangaUpdates API error: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"MangaUpdates API request error: {str(e)}")
            return None

    def _normalize_releases(self, releases: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize release data from MangaUpdates API format."""
        normalized = []

        for release in releases:
            try:
                record = release.get("record", {})
                series = record.get("series", {})

                normalized_item = {
                    "id": record.get("id", ""),
                    "series_id": series.get("id", ""),
                    "series_title": series.get("title", ""),
                    "chapter": record.get("chapter", ""),
                    "volume": record.get("volume", ""),
                    "release_date": record.get("release_date", ""),
                    "groups": [group.get("name", "") for group in record.get("groups", [])],
                    "type": WorkType.MANGA.value,
                    "source": DataSource.MANGAUPDATES.value,
                    "source_url": f"https://www.mangaupdates.com/series/{series.get('id', '')}",
                }
                normalized.append(normalized_item)
            except Exception as e:
                self.logger.warning(f"Failed to normalize release data: {str(e)}")
                continue

        return normalized

    def _normalize_series(self, series_list: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize series search results from MangaUpdates API format."""
        normalized = []

        for series in series_list:
            try:
                record = series.get("record", {})
                image = record.get("image", {})

                normalized_item = {
                    "id": record.get("id", ""),
                    "title": record.get("title", ""),
                    "type": record.get("type", ""),
                    "year": record.get("year", ""),
                    "description": record.get("description", ""),
                    "genres": [genre.get("genre", "") for genre in record.get("genres", [])],
                    "categories": [cat.get("category", "") for cat in record.get("categories", [])],
                    "latest_chapter": record.get("latest_chapter", ""),
                    "cover_image": image.get("url", {}).get("original", ""),
                    "work_type": WorkType.MANGA.value,
                    "source": DataSource.MANGAUPDATES.value,
                    "source_url": f"https://www.mangaupdates.com/series/{record.get('id', '')}",
                }
                normalized.append(normalized_item)
            except Exception as e:
                self.logger.warning(f"Failed to normalize series data: {str(e)}")
                continue

        return normalized

    def _normalize_series_detail(self, series: Dict) -> Dict[str, Any]:
        """Normalize detailed series information from MangaUpdates API format."""
        try:
            image = series.get("image", {})
            associated = series.get("associated", [])

            return {
                "id": series.get("series_id", ""),
                "title": series.get("title", ""),
                "alt_titles": [assoc.get("title", "") for assoc in associated],
                "description": series.get("description", ""),
                "type": series.get("type", ""),
                "year": series.get("year", ""),
                "status": series.get("status", ""),
                "licensed": series.get("licensed", False),
                "genres": [genre.get("genre", "") for genre in series.get("genres", [])],
                "categories": [cat.get("category", "") for cat in series.get("categories", [])],
                "latest_chapter": series.get("latest_chapter", ""),
                "cover_image": image.get("url", {}).get("original", ""),
                "rating": series.get("bayesian_rating", 0),
                "work_type": WorkType.MANGA.value,
                "source": DataSource.MANGAUPDATES.value,
                "source_url": f"https://www.mangaupdates.com/series/{series.get('series_id', '')}",
            }
        except Exception as e:
            self.logger.warning(f"Failed to normalize series detail: {str(e)}")
            return {}


async def collect_mangaupdates_releases(
    config: Dict[str, Any], pages: int = 2
) -> List[Dict[str, Any]]:
    """
    Collect latest manga releases from MangaUpdates API.

    Args:
        config: API configuration dictionary
        pages: Number of pages to fetch

    Returns:
        List of normalized release data
    """
    logger.info("Starting MangaUpdates releases collection...")

    all_releases = []

    async with MangaUpdatesAPIClient(config) as client:
        try:
            for page in range(1, pages + 1):
                releases = await client.get_latest_releases(page=page, per_page=50)
                all_releases.extend(releases)
                logger.info(f"Collected {len(releases)} releases from page {page}")

                # Add small delay between pages
                if page < pages:
                    await asyncio.sleep(1)

        except MangaUpdatesAPIError as e:
            logger.error(f"MangaUpdates API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in MangaUpdates releases collection: {str(e)}")

    logger.info(f"MangaUpdates releases collection complete: {len(all_releases)} total items")
    return all_releases


async def search_mangaupdates_series(config: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    """
    Search manga series on MangaUpdates.

    Args:
        config: API configuration dictionary
        query: Search query

    Returns:
        List of normalized series data
    """
    logger.info(f"Searching MangaUpdates for: {query}")

    results = []

    async with MangaUpdatesAPIClient(config) as client:
        try:
            results = await client.search_series(query)
            logger.info(f"Found {len(results)} series matching '{query}'")

        except MangaUpdatesAPIError as e:
            logger.error(f"MangaUpdates API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in MangaUpdates search: {str(e)}")

    return results


if __name__ == "__main__":
    # Test code
    logging.basicConfig(level=logging.INFO)

    import json

    config = {
        "base_url": "https://api.mangaupdates.com/v1",
        "timeout_seconds": 30,
        "rate_limit": {"requests_per_minute": 30, "retry_delay_seconds": 5},
    }

    async def test():
        releases = await collect_mangaupdates_releases(config, pages=1)
        logger.info(f"Collected {len(releases)} releases")
        if releases:
            logger.info("\nSample release:")
            logger.info(json.dumps(releases[0], indent=2, ensure_ascii=False))

        # Test search
        results = await search_mangaupdates_series(config, "One Piece")
        logger.info(f"\nSearch results: {len(results)}")

    asyncio.run(test())
