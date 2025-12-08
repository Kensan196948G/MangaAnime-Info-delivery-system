#!/usr/bin/env python3
"""
Enhanced streaming platform integration module.

This module provides enhanced support for:
- Netflix anime catalog integration
- Amazon Prime Video anime information
- Enhanced AniList GraphQL streaming data extraction
- Multi-platform availability tracking
- Release schedule synchronization
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from .models import DataSource, Release, ReleaseType, Work, WorkType


class StreamingPlatform(Enum):
    """Streaming platform enumeration."""

    NETFLIX = "Netflix"
    AMAZON_PRIME = "Amazon Prime Video"
    CRUNCHYROLL = "Crunchyroll"
    HULU = "Hulu"
    DISNEY_PLUS = "Disney+"
    FUNIMATION = "Funimation"
    HIDIVE = "HIDIVE"
    DANIME_STORE = "dアニメストア"
    ABEMA = "ABEMA"
    UNKNOWN = "Unknown"


@dataclass
class StreamingInfo:
    """Streaming platform information."""

    platform: StreamingPlatform
    url: Optional[str] = None
    episode_number: Optional[str] = None
    release_date: Optional[date] = None
    availability_region: Optional[str] = None
    is_simulcast: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlatformAvailability:
    """Platform availability tracking."""

    work_id: int
    title: str
    platforms: List[StreamingInfo]
    last_updated: datetime = field(default_factory=datetime.now)


class EnhancedStreamingCollector:
    """
    Enhanced streaming platform data collector.

    Features:
    - AniList GraphQL streaming episodes extraction
    - Netflix/Prime Video detection and tracking
    - Multi-platform availability aggregation
    - Release schedule synchronization
    """

    # AniList GraphQL query for streaming data
    STREAMING_QUERY = """
    query ($page: Int, $perPage: Int, $season: MediaSeason, $seasonYear: Int, $type: MediaType) {
      Page(page: $page, perPage: $perPage) {
        pageInfo {
          total
          perPage
          currentPage
          lastPage
          hasNextPage
        }
        media(season: $season, seasonYear: $seasonYear, type: $type, sort: POPULARITY_DESC) {
          id
          title {
            romaji
            english
            native
          }
          format
          status
          startDate {
            year
            month
            day
          }
          externalLinks {
            site
            url
            type
          }
          streamingEpisodes {
            title
            thumbnail
            url
            site
          }
        }
      }
    }
    """

    # Platform name mappings
    PLATFORM_MAPPINGS = {
        "netflix": StreamingPlatform.NETFLIX,
        "amazon": StreamingPlatform.AMAZON_PRIME,
        "prime video": StreamingPlatform.AMAZON_PRIME,
        "crunchyroll": StreamingPlatform.CRUNCHYROLL,
        "hulu": StreamingPlatform.HULU,
        "disney": StreamingPlatform.DISNEY_PLUS,
        "disney+": StreamingPlatform.DISNEY_PLUS,
        "funimation": StreamingPlatform.FUNIMATION,
        "hidive": StreamingPlatform.HIDIVE,
        "danime": StreamingPlatform.DANIME_STORE,
        "dアニメ": StreamingPlatform.DANIME_STORE,
        "abema": StreamingPlatform.ABEMA,
    }

    ANILIST_API_URL = "https://graphql.anilist.co"

    def __init__(self, timeout: int = 30):
        """
        Initialize enhanced streaming collector.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.request_count = 0
        self.cache: Dict[str, Any] = {}

        self.logger.info("Enhanced Streaming Collector initialized")

    def _detect_platform(self, site_name: str) -> StreamingPlatform:
        """
        Detect streaming platform from site name.

        Args:
            site_name: Site name from external link or streaming episode

        Returns:
            StreamingPlatform enum
        """
        if not site_name:
            return StreamingPlatform.UNKNOWN

        site_lower = site_name.lower()

        for key, platform in self.PLATFORM_MAPPINGS.items():
            if key in site_lower:
                return platform

        return StreamingPlatform.UNKNOWN

    async def fetch_streaming_data(
        self,
        season: Optional[str] = None,
        year: Optional[int] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Fetch anime streaming data from AniList.

        Args:
            season: Season filter (WINTER, SPRING, SUMMER, FALL)
            year: Year filter
            page: Page number
            per_page: Results per page

        Returns:
            List of anime with streaming information
        """
        self.logger.info(f"Fetching streaming data: season={season}, year={year}, page={page}")

        variables = {"page": page, "perPage": per_page, "type": "ANIME"}

        if season:
            variables["season"] = season.upper()
        if year:
            variables["seasonYear"] = year

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ANILIST_API_URL,
                    json={"query": self.STREAMING_QUERY, "variables": variables},
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    self.request_count += 1

                    if response.status == 200:
                        data = await response.json()

                        if "data" in data and "Page" in data["data"]:
                            media_list = data["data"]["Page"]["media"]
                            self.logger.info(f"Retrieved {len(media_list)} anime entries")
                            return media_list
                        else:
                            self.logger.warning("No data found in response")
                            return []

                    elif response.status == 429:
                        self.logger.warning("Rate limit exceeded, waiting...")
                        await asyncio.sleep(60)
                        return await self.fetch_streaming_data(season, year, page, per_page)

                    else:
                        error_text = await response.text()
                        self.logger.error(f"API request failed: {response.status} - {error_text}")
                        return []

        except Exception as e:
            self.logger.error(f"Error fetching streaming data: {e}")
            return []

    def extract_streaming_info(self, anime_data: Dict[str, Any]) -> List[StreamingInfo]:
        """
        Extract streaming platform information from anime data.

        Args:
            anime_data: AniList anime data

        Returns:
            List of streaming information
        """
        streaming_infos = []

        # Extract from streamingEpisodes
        if "streamingEpisodes" in anime_data:
            for episode in anime_data["streamingEpisodes"]:
                site_name = episode.get("site", "")
                platform = self._detect_platform(site_name)

                # Extract episode number from title
                episode_title = episode.get("title", "")
                episode_number = self._extract_episode_number(episode_title)

                streaming_info = StreamingInfo(
                    platform=platform,
                    url=episode.get("url"),
                    episode_number=episode_number,
                    metadata={
                        "site": site_name,
                        "title": episode_title,
                        "thumbnail": episode.get("thumbnail"),
                    },
                )

                streaming_infos.append(streaming_info)

        # Extract from externalLinks
        if "externalLinks" in anime_data:
            for link in anime_data["externalLinks"]:
                site_name = link.get("site", "")
                link_type = link.get("type", "")

                # Filter for streaming links
                if link_type.upper() == "STREAMING":
                    platform = self._detect_platform(site_name)

                    streaming_info = StreamingInfo(
                        platform=platform,
                        url=link.get("url"),
                        metadata={"site": site_name, "link_type": link_type},
                    )

                    streaming_infos.append(streaming_info)

        return streaming_infos

    def _extract_episode_number(self, title: str) -> Optional[str]:
        """Extract episode number from title."""
        if not title:
            return None

        # Common episode number patterns
        patterns = [
            r"episode\s+(\d+)",
            r"ep\.?\s*(\d+)",
            r"#(\d+)",
            r"第(\d+)話",
        ]

        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def filter_by_platform(
        self, streaming_infos: List[StreamingInfo], platforms: List[StreamingPlatform]
    ) -> List[StreamingInfo]:
        """
        Filter streaming info by platforms.

        Args:
            streaming_infos: List of streaming information
            platforms: Target platforms to filter

        Returns:
            Filtered streaming information
        """
        return [info for info in streaming_infos if info.platform in platforms]

    async def fetch_netflix_prime_anime(
        self, season: Optional[str] = None, year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch anime available on Netflix and Amazon Prime.

        Args:
            season: Season filter
            year: Year filter

        Returns:
            List of anime with Netflix/Prime availability
        """
        self.logger.info("Fetching Netflix and Amazon Prime anime...")

        # Fetch all streaming data
        anime_list = await self.fetch_streaming_data(season, year)

        # Filter for Netflix and Prime
        target_platforms = [StreamingPlatform.NETFLIX, StreamingPlatform.AMAZON_PRIME]
        filtered_anime = []

        for anime in anime_list:
            streaming_infos = self.extract_streaming_info(anime)
            netflix_prime = self.filter_by_platform(streaming_infos, target_platforms)

            if netflix_prime:
                anime["filtered_streaming"] = netflix_prime
                filtered_anime.append(anime)

        self.logger.info(f"Found {len(filtered_anime)} anime on Netflix/Amazon Prime")

        return filtered_anime

    def convert_to_releases(self, anime_data: Dict[str, Any], work_id: int) -> List[Release]:
        """
        Convert anime streaming data to Release models.

        Args:
            anime_data: AniList anime data
            work_id: Associated work ID

        Returns:
            List of releases
        """
        releases = []

        streaming_infos = self.extract_streaming_info(anime_data)

        for info in streaming_infos:
            # Skip unknown platforms
            if info.platform == StreamingPlatform.UNKNOWN:
                continue

            # Determine release date
            release_date_obj = info.release_date
            if not release_date_obj and "startDate" in anime_data:
                start_date = anime_data["startDate"]
                if all(start_date.get(k) for k in ["year", "month", "day"]):
                    try:
                        release_date_obj = date(
                            start_date["year"], start_date["month"], start_date["day"]
                        )
                    except (ValueError, TypeError):
                        release_date_obj = datetime.now().date()
                else:
                    release_date_obj = datetime.now().date()
            elif not release_date_obj:
                release_date_obj = datetime.now().date()

            # Create release
            release = Release(
                work_id=work_id,
                release_type=ReleaseType.EPISODE,
                number=info.episode_number,
                platform=info.platform.value,
                release_date=release_date_obj,
                source=DataSource.ANILIST,
                source_url=info.url,
                metadata={
                    "platform": info.platform.value,
                    "is_simulcast": info.is_simulcast,
                    **info.metadata,
                },
            )

            releases.append(release)

        return releases

    async def fetch_and_convert(
        self,
        season: Optional[str] = None,
        year: Optional[int] = None,
        netflix_prime_only: bool = False,
    ) -> Tuple[List[Work], List[Release]]:
        """
        Fetch streaming data and convert to Work/Release models.

        Args:
            season: Season filter
            year: Year filter
            netflix_prime_only: Only include Netflix/Prime anime

        Returns:
            Tuple of (works, releases)
        """
        if netflix_prime_only:
            anime_list = await self.fetch_netflix_prime_anime(season, year)
        else:
            anime_list = await self.fetch_streaming_data(season, year)

        works = []
        releases = []

        for anime in anime_list:
            # Create Work
            title_data = anime.get("title", {})
            title = (
                title_data.get("english")
                or title_data.get("romaji")
                or title_data.get("native")
                or "Unknown"
            )

            work = Work(
                title=title,
                work_type=WorkType.ANIME,
                title_en=title_data.get("english"),
                title_kana=title_data.get("native"),
                metadata={
                    "anilist_id": anime.get("id"),
                    "format": anime.get("format"),
                    "status": anime.get("status"),
                    "start_date": anime.get("startDate"),
                },
            )

            works.append(work)

            # Create Releases
            work_releases = self.convert_to_releases(anime, 0)
            releases.extend(work_releases)

        self.logger.info(f"Converted to {len(works)} works and {len(releases)} releases")

        return works, releases

    def get_statistics(self) -> Dict[str, Any]:
        """Get collector statistics."""
        return {
            "total_requests": self.request_count,
            "cache_size": len(self.cache),
            "supported_platforms": len(StreamingPlatform),
        }


# Async wrapper functions


async def fetch_netflix_prime_anime(
    season: Optional[str] = None, year: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Fetch anime available on Netflix and Amazon Prime."""
    collector = EnhancedStreamingCollector()
    return await collector.fetch_netflix_prime_anime(season, year)


async def fetch_streaming_works_and_releases(
    season: Optional[str] = None,
    year: Optional[int] = None,
    netflix_prime_only: bool = False,
) -> Tuple[List[Work], List[Release]]:
    """Fetch streaming anime as Work/Release models."""
    collector = EnhancedStreamingCollector()
    return await collector.fetch_and_convert(season, year, netflix_prime_only)


# Synchronous wrappers


def fetch_netflix_prime_anime_sync(
    season: Optional[str] = None, year: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Synchronous wrapper for fetch_netflix_prime_anime."""
    return asyncio.run(fetch_netflix_prime_anime(season, year))


def fetch_streaming_works_and_releases_sync(
    season: Optional[str] = None,
    year: Optional[int] = None,
    netflix_prime_only: bool = False,
) -> Tuple[List[Work], List[Release]]:
    """Synchronous wrapper for fetch_streaming_works_and_releases."""
    return asyncio.run(fetch_streaming_works_and_releases(season, year, netflix_prime_only))
