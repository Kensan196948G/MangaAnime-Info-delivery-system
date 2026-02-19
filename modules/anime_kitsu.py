#!/usr/bin/env python3
"""
Kitsu API integration module for anime and manga data collection.

This module provides:
- Kitsu REST API client with rate limiting
- Anime and manga data retrieval and normalization
- Streaming platform information extraction
- Error handling and retry logic
- Data validation and filtering

Kitsu API Documentation: https://kitsu.docs.apiary.io/
Rate Limits: 90 requests per minute
"""

import asyncio
import logging
import time

logger = logging.getLogger(__name__)
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from .models import DataSource, WorkType


class KitsuAPIError(Exception):
    """Custom exception for Kitsu API errors."""


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, requests_per_minute: int = 90):
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


class KitsuAPIClient:
    """Kitsu API client with rate limiting and error handling."""

    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "https://kitsu.io/api/edge")
        self.timeout = config.get("timeout_seconds", 30)
        self.rate_limit_config = config.get("rate_limit", {})
        self.rate_limiter = RateLimiter(self.rate_limit_config.get("requests_per_minute", 90))
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

    async def get_seasonal_anime(
        self, season: str, year: int, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get seasonal anime from Kitsu API.

        Args:
            season: Season name (winter, spring, summer, fall)
            year: Year
            limit: Maximum number of results

        Returns:
            List of anime data dictionaries
        """
        await self.rate_limiter.wait()

        # Calculate season dates
        season_start, season_end = self._get_season_dates(season, year)

        params = {
            "filter[seasonYear]": year,
            "filter[season]": season,
            "page[limit]": limit,
            "sort": "-startDate",
        }

        try:
            async with self.session.get(f"{self.base_url}/anime", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_anime_list(data.get("data", []))
                elif response.status == 429:
                    self.logger.warning("Rate limit exceeded, waiting...")
                    await asyncio.sleep(5)
                    return await self.get_seasonal_anime(season, year, limit)
                else:
                    self.logger.error(
                        f"Kitsu API error: {response.status} - {await response.text()}"
                    )
                    raise KitsuAPIError(f"API request failed with status {response.status}")

        except asyncio.TimeoutError:
            self.logger.error("Kitsu API request timeout")
            raise KitsuAPIError("Request timeout")
        except Exception as e:
            self.logger.error(f"Kitsu API request error: {str(e)}")
            raise KitsuAPIError(f"Request failed: {str(e)}")

    async def get_trending_anime(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get trending anime from Kitsu API.

        Args:
            limit: Maximum number of results

        Returns:
            List of anime data dictionaries
        """
        await self.rate_limiter.wait()

        params = {"page[limit]": limit, "sort": "-userCount"}

        try:
            async with self.session.get(
                f"{self.base_url}/trending/anime", params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_anime_list(data.get("data", []))
                else:
                    self.logger.error(f"Kitsu API error: {response.status}")
                    raise KitsuAPIError(f"API request failed with status {response.status}")

        except Exception as e:
            self.logger.error(f"Kitsu API request error: {str(e)}")
            raise KitsuAPIError(f"Request failed: {str(e)}")

    async def get_manga_updates(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent manga updates from Kitsu API.

        Args:
            limit: Maximum number of results

        Returns:
            List of manga data dictionaries
        """
        await self.rate_limiter.wait()

        params = {"page[limit]": limit, "sort": "-updatedAt"}

        try:
            async with self.session.get(f"{self.base_url}/manga", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_manga_list(data.get("data", []))
                else:
                    self.logger.error(f"Kitsu API error: {response.status}")
                    raise KitsuAPIError(f"API request failed with status {response.status}")

        except Exception as e:
            self.logger.error(f"Kitsu API request error: {str(e)}")
            raise KitsuAPIError(f"Request failed: {str(e)}")

    def _normalize_anime_list(self, anime_list: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize anime data from Kitsu API format."""
        normalized = []

        for anime in anime_list:
            try:
                attrs = anime.get("attributes", {})
                normalized_item = {
                    "id": anime.get("id"),
                    "title": attrs.get("canonicalTitle", ""),
                    "title_ja": attrs.get("titles", {}).get("ja_jp", ""),
                    "title_en": attrs.get("titles", {}).get("en", ""),
                    "type": WorkType.ANIME.value,
                    "status": attrs.get("status", ""),
                    "episode_count": attrs.get("episodeCount", 0),
                    "start_date": attrs.get("startDate", ""),
                    "end_date": attrs.get("endDate", ""),
                    "synopsis": attrs.get("synopsis", ""),
                    "cover_image": attrs.get("posterImage", {}).get("original", ""),
                    "average_rating": attrs.get("averageRating", ""),
                    "popularity_rank": attrs.get("popularityRank", 0),
                    "age_rating": attrs.get("ageRating", ""),
                    "subtype": attrs.get("subtype", ""),  # TV, OVA, movie, etc.
                    "source": DataSource.KITSU.value,
                    "source_url": f"https://kitsu.io/anime/{anime.get('id')}",
                }
                normalized.append(normalized_item)
            except Exception as e:
                self.logger.warning(f"Failed to normalize anime data: {str(e)}")
                continue

        return normalized

    def _normalize_manga_list(self, manga_list: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize manga data from Kitsu API format."""
        normalized = []

        for manga in manga_list:
            try:
                attrs = manga.get("attributes", {})
                normalized_item = {
                    "id": manga.get("id"),
                    "title": attrs.get("canonicalTitle", ""),
                    "title_ja": attrs.get("titles", {}).get("ja_jp", ""),
                    "title_en": attrs.get("titles", {}).get("en", ""),
                    "type": WorkType.MANGA.value,
                    "status": attrs.get("status", ""),
                    "chapter_count": attrs.get("chapterCount", 0),
                    "volume_count": attrs.get("volumeCount", 0),
                    "start_date": attrs.get("startDate", ""),
                    "end_date": attrs.get("endDate", ""),
                    "synopsis": attrs.get("synopsis", ""),
                    "cover_image": attrs.get("posterImage", {}).get("original", ""),
                    "average_rating": attrs.get("averageRating", ""),
                    "popularity_rank": attrs.get("popularityRank", 0),
                    "age_rating": attrs.get("ageRating", ""),
                    "subtype": attrs.get("subtype", ""),  # manga, novel, manhua, etc.
                    "source": DataSource.KITSU.value,
                    "source_url": f"https://kitsu.io/manga/{manga.get('id')}",
                }
                normalized.append(normalized_item)
            except Exception as e:
                self.logger.warning(f"Failed to normalize manga data: {str(e)}")
                continue

        return normalized

    def _get_season_dates(self, season: str, year: int) -> Tuple[str, str]:
        """
        Get start and end dates for a season.

        Args:
            season: Season name (winter, spring, summer, fall)
            year: Year

        Returns:
            Tuple of (start_date, end_date) in YYYY-MM-DD format
        """
        season_map = {
            "winter": ("01-01", "03-31"),
            "spring": ("04-01", "06-30"),
            "summer": ("07-01", "09-30"),
            "fall": ("10-01", "12-31"),
        }

        start_month_day, end_month_day = season_map.get(season.lower(), ("01-01", "12-31"))
        start_date = f"{year}-{start_month_day}"
        end_date = f"{year}-{end_month_day}"

        return start_date, end_date


async def collect_kitsu_anime(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Collect anime data from Kitsu API.

    Args:
        config: API configuration dictionary

    Returns:
        List of normalized anime data
    """
    logger.info("Starting Kitsu anime collection...")

    all_anime = []
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    # Determine current season
    if current_month in [1, 2, 3]:
        current_season = "winter"
    elif current_month in [4, 5, 6]:
        current_season = "spring"
    elif current_month in [7, 8, 9]:
        current_season = "summer"
    else:
        current_season = "fall"

    async with KitsuAPIClient(config) as client:
        try:
            # Get current season anime
            seasonal_anime = await client.get_seasonal_anime(current_season, current_year, limit=20)
            all_anime.extend(seasonal_anime)
            logger.info(f"Collected {len(seasonal_anime)} seasonal anime")

            # Get trending anime
            trending_anime = await client.get_trending_anime(limit=20)
            all_anime.extend(trending_anime)
            logger.info(f"Collected {len(trending_anime)} trending anime")

        except KitsuAPIError as e:
            logger.error(f"Kitsu API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Kitsu anime collection: {str(e)}")

    logger.info(f"Kitsu anime collection complete: {len(all_anime)} total items")
    return all_anime


async def collect_kitsu_manga(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Collect manga data from Kitsu API.

    Args:
        config: API configuration dictionary

    Returns:
        List of normalized manga data
    """
    logger.info("Starting Kitsu manga collection...")

    all_manga = []

    async with KitsuAPIClient(config) as client:
        try:
            # Get recent manga updates
            manga_updates = await client.get_manga_updates(limit=50)
            all_manga.extend(manga_updates)
            logger.info(f"Collected {len(manga_updates)} manga updates")

        except KitsuAPIError as e:
            logger.error(f"Kitsu API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Kitsu manga collection: {str(e)}")

    logger.info(f"Kitsu manga collection complete: {len(all_manga)} total items")
    return all_manga


if __name__ == "__main__":
    # Test code
    logging.basicConfig(level=logging.INFO)

    config = {
        "base_url": "https://kitsu.io/api/edge",
        "timeout_seconds": 30,
        "rate_limit": {"requests_per_minute": 90, "retry_delay_seconds": 3},
    }

    async def test():
        anime_data = await collect_kitsu_anime(config)
        manga_data = await collect_kitsu_manga(config)
        logger.info(f"Collected {len(anime_data)} anime and {len(manga_data)} manga")

    asyncio.run(test())
