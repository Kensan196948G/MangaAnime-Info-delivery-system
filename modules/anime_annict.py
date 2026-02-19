#!/usr/bin/env python3
"""
Annict REST API v1 integration module for anime data collection.

This module provides:
- Annict REST API client with rate limiting
- Anime data retrieval and normalization
- Program/broadcast schedule information
- Episode tracking
- Error handling and retry logic

Annict API Documentation: https://developers.annict.com/docs/rest-api/v1
Rate Limits: 60 requests per minute (recommended)
"""

import asyncio
import json
import logging
import time

logger = logging.getLogger(__name__)
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from .models import DataSource, WorkType


class AnnictAPIError(Exception):
    """Custom exception for Annict API errors."""


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, requests_per_minute: int = 60):
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


class AnnictAPIClient:
    """Annict REST API v1 client with rate limiting and error handling."""

    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "https://api.annict.com/v1")
        # Support both 'access_token' and 'api_key' field names
        self.access_token = config.get("access_token") or config.get("api_key", "")
        self.timeout = config.get("timeout_seconds", 30)
        self.rate_limit_config = config.get("rate_limit", {})
        self.rate_limiter = RateLimiter(self.rate_limit_config.get("requests_per_minute", 60))
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)

        if not self.access_token:
            raise AnnictAPIError(
                "Annict access token is required. Get it from https://annict.com/settings/apps"
            )

    async def __aenter__(self):
        """Async context manager entry."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
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

    async def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to Annict API with rate limiting.

        Args:
            endpoint: API endpoint (e.g., '/works', '/programs')
            params: Query parameters

        Returns:
            API response data

        Raises:
            AnnictAPIError: If request fails
        """
        await self.rate_limiter.wait()

        url = f"{self.base_url}{endpoint}"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 401:
                    raise AnnictAPIError(
                        "Invalid access token. Please check your Annict API credentials."
                    )
                elif response.status == 404:
                    raise AnnictAPIError(f"Endpoint not found: {endpoint}")
                elif response.status != 200:
                    error_text = await response.text()
                    raise AnnictAPIError(
                        f"API request failed with status {response.status}: {error_text}"
                    )

                data = await response.json()
                return data

        except aiohttp.ClientError as e:
            raise AnnictAPIError(f"Network error: {str(e)}")

    async def get_current_season_works(
        self,
        season: Optional[str] = None,
        year: Optional[int] = None,
        per_page: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get anime works for a specific season.

        Args:
            season: Season in format 'YYYY-spring' (e.g., '2025-winter')
                   If not provided, uses current season
            year: Year (used if season not provided)
            per_page: Results per page (max 50)

        Returns:
            List of anime work data
        """
        if not season:
            season = self._get_current_season(year)

        params = {
            "filter_season": season,
            "per_page": min(per_page, 50),
            "sort_watchers_count": "desc",
            "fields": "id,title,title_kana,title_en,media,media_text,season_name,season_name_text,episodes_count,watchers_count,reviews_count,no_episodes,started_on,official_site_url,wikipedia_url,twitter_username,images",
        }

        self.logger.info(f"Fetching Annict works for season: {season}")
        data = await self._make_request("/works", params)

        works = data.get("works", [])
        self.logger.info(f"Retrieved {len(works)} works from Annict")

        return works

    async def get_programs(
        self,
        start_date: Optional[datetime] = None,
        work_ids: Optional[List[int]] = None,
        per_page: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get broadcast programs/schedules.

        Args:
            start_date: Filter programs starting from this date
            work_ids: Filter by specific work IDs
            per_page: Results per page (max 50)

        Returns:
            List of program data with broadcast schedules
        """
        params = {
            "per_page": min(per_page, 50),
            "sort_started_at": "asc",
            "fields": "id,started_at,is_rebroadcast,channel,work,episode",
        }

        if start_date:
            params["filter_started_at_gt"] = start_date.isoformat()

        if work_ids:
            params["filter_work_ids"] = ",".join(map(str, work_ids))

        self.logger.info(f"Fetching Annict programs from {start_date or 'now'}")
        data = await self._make_request("/me/programs", params)

        programs = data.get("programs", [])
        self.logger.info(f"Retrieved {len(programs)} programs from Annict")

        return programs

    async def get_episodes(self, work_id: int, per_page: int = 50) -> List[Dict[str, Any]]:
        """
        Get episodes for a specific work.

        Args:
            work_id: Work ID
            per_page: Results per page (max 50)

        Returns:
            List of episode data
        """
        params = {
            "filter_work_id": work_id,
            "per_page": min(per_page, 50),
            "sort_sort_number": "asc",
            "fields": "id,number,number_text,title,records_count,prev_episode,next_episode",
        }

        self.logger.info(f"Fetching episodes for work ID: {work_id}")
        data = await self._make_request("/episodes", params)

        episodes = data.get("episodes", [])
        self.logger.info(f"Retrieved {len(episodes)} episodes for work {work_id}")

        return episodes

    def _get_current_season(self, year: Optional[int] = None) -> str:
        """
        Get current season in Annict format (YYYY-season).

        Args:
            year: Specific year, defaults to current year

        Returns:
            Season string (e.g., '2025-winter')
        """
        now = datetime.now()
        if not year:
            year = now.year

        month = now.month

        # Determine season based on month
        if month in [1, 2, 3]:
            season = "winter"
        elif month in [4, 5, 6]:
            season = "spring"
        elif month in [7, 8, 9]:
            season = "summer"
        else:  # 10, 11, 12
            season = "fall"

        return f"{year}-{season}"

    def normalize_work_data(self, work: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Annict work data to standard format.

        Args:
            work: Raw work data from Annict

        Returns:
            Normalized work data
        """
        return {
            "source": DataSource.ANNICT.value,
            "source_id": str(work.get("id", "")),
            "title": work.get("title", ""),
            "title_kana": work.get("title_kana", ""),
            "title_en": work.get("title_en", ""),
            "type": WorkType.ANIME.value,
            "media": work.get("media_text", "TV"),
            "episodes_count": work.get("episodes_count", 0),
            "season": work.get("season_name_text", ""),
            "started_on": work.get("started_on", ""),
            "official_url": work.get("official_site_url", ""),
            "wikipedia_url": work.get("wikipedia_url", ""),
            "twitter_username": work.get("twitter_username", ""),
            "images": work.get("images", {}),
            "watchers_count": work.get("watchers_count", 0),
            "reviews_count": work.get("reviews_count", 0),
            "no_episodes": work.get("no_episodes", False),
        }

    def normalize_program_data(self, program: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Annict program data to standard format.

        Args:
            program: Raw program data from Annict

        Returns:
            Normalized program data
        """
        work = program.get("work", {})
        episode = program.get("episode", {})
        channel = program.get("channel", {})

        return {
            "source": DataSource.ANNICT.value,
            "program_id": str(program.get("id", "")),
            "started_at": program.get("started_at", ""),
            "is_rebroadcast": program.get("is_rebroadcast", False),
            "channel_name": channel.get("name", ""),
            "channel_id": channel.get("id", ""),
            "work_id": work.get("id", ""),
            "work_title": work.get("title", ""),
            "episode_number": episode.get("number_text", ""),
            "episode_title": episode.get("title", ""),
            "episode_id": episode.get("id", ""),
        }


async def collect_annict_data(
    config: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Collect anime data from Annict API.

    Args:
        config: Annict API configuration

    Returns:
        Dictionary with 'works', 'programs', and 'episodes' lists
    """
    if not config.get("enabled", False):
        logger.info("Annict API is disabled in config")
        return {"works": [], "programs": [], "episodes": []}

    try:
        async with AnnictAPIClient(config) as client:
            # Get current season works
            works = await client.get_current_season_works()

            # Get upcoming programs
            start_date = datetime.now()
            programs = await client.get_programs(start_date=start_date)

            # Normalize data
            normalized_works = [client.normalize_work_data(w) for w in works]
            normalized_programs = [client.normalize_program_data(p) for p in programs]

            logger.info(
                f"Annict collection complete: {len(normalized_works)} works, "
                f"{len(normalized_programs)} programs"
            )

            return {
                "works": normalized_works,
                "programs": normalized_programs,
                "episodes": [],
            }

    except AnnictAPIError as e:
        logger.error(f"Annict API error: {str(e)}")
        return {"works": [], "programs": [], "episodes": []}
    except Exception as e:
        logger.error(f"Unexpected error collecting Annict data: {str(e)}")
        return {"works": [], "programs": [], "episodes": []}


# For testing
async def main():
    """Test function."""
    import sys

    sys.path.insert(0, "..")

    # Load config
    with open("../config.json", "r", encoding="utf-8") as f:
        config_data = json.load(f)

    annict_config = config_data.get("apis", {}).get("annict", {})

    if not annict_config.get("access_token") and not annict_config.get("api_key"):
        logger.info("⚠️  Please set your Annict access token in config.json")
        logger.info("   Get it from: https://annict.com/settings/apps")
        return

    logger.info("🔍 Testing Annict API integration...")
    result = await collect_annict_data(annict_config)

    logger.info(f"\n📊 Results:")
    logger.info(f"   Works: {len(result['works'])}")
    logger.info(f"   Programs: {len(result['programs'])}")

    if result["works"]:
        logger.info(f"\n📺 Sample work:")
        logger.info(json.dumps(result["works"][0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
