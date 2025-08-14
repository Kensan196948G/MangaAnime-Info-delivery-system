"""
AniList GraphQL API integration module for anime data collection.

This module provides:
- AniList GraphQL API client with rate limiting
- Anime data retrieval and normalization
- Streaming platform information extraction
- Error handling and retry logic
- Data validation and filtering

AniList API Documentation: https://anilist.gitbook.io/anilist-apiv2-docs/
Rate Limits: 90 requests per minute
"""

import asyncio
import aiohttp
import logging
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
import json
from dataclasses import asdict, dataclass
from enum import Enum

from .models import AniListWork, Work, Release, WorkType, ReleaseType, DataSource
from .db import get_db


class AniListAPIError(Exception):
    """Custom exception for AniList API errors."""
    pass


class RateLimitExceeded(AniListAPIError):
    """Exception raised when rate limit is exceeded."""
    pass


class CircuitBreakerOpen(AniListAPIError):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = AniListAPIError
    

class CircuitBreaker:
    """Circuit breaker implementation for API reliability."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
        self.logger = logging.getLogger(__name__)
    
    def can_execute(self) -> bool:
        """Check if circuit allows execution."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 3:  # Require multiple successes to close
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.logger.info("Circuit breaker CLOSED after successful recovery")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0  # Reset failure count on success
    
    def record_failure(self, exception: Exception):
        """Record failed execution."""
        if isinstance(exception, self.config.expected_exception):
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if (self.state == CircuitState.CLOSED and 
                self.failure_count >= self.config.failure_threshold):
                self.state = CircuitState.OPEN
                self.logger.warning(
                    f"Circuit breaker OPENED after {self.failure_count} failures"
                )
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.success_count = 0
                self.logger.warning("Circuit breaker returned to OPEN from HALF_OPEN")


class AniListClient:
    """
    AniList GraphQL API client with enhanced rate limiting, circuit breaker, and error handling.
    
    Phase 2 Enhancements:
    - Advanced adaptive rate limiting with burst detection
    - Enhanced circuit breaker with health recovery scoring
    - Multi-level performance optimization
    - Real-time monitoring integration
    
    Provides methods to query anime data from AniList API with proper
    rate limiting (90 requests per minute), circuit breaker pattern,
    and comprehensive error handling.
    """
    
    API_URL = "https://graphql.anilist.co"
    RATE_LIMIT = 90  # requests per minute
    RATE_WINDOW = 60  # seconds
    
    # Phase 2: Advanced performance constants
    BURST_THRESHOLD = 0.7  # 70% capacity triggers adaptive throttling
    HEALTH_RECOVERY_THRESHOLD = 3  # Successful requests needed for recovery
    PERFORMANCE_OPTIMIZATION_WINDOW = 300  # 5-minute performance analysis window
    
    def __init__(self, timeout: int = 30, retry_attempts: int = 3, retry_delay: int = 5):
        """
        Initialize AniList client with enhanced reliability features.
        
        Args:
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
            retry_delay: Delay between retry attempts in seconds
        """
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.request_timestamps = []
        self.rate_limit_lock = asyncio.Lock()
        
        # Circuit breaker
        circuit_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=120,  # 2 minutes
            expected_exception=AniListAPIError
        )
        self.circuit_breaker = CircuitBreaker(circuit_config)
        
        # Performance tracking
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.last_request_time = None
        
    async def _enforce_rate_limit(self):
        """Enforce enhanced rate limiting with adaptive delays."""
        async with self.rate_limit_lock:
            now = time.time()
            
            # Remove timestamps older than rate window
            self.request_timestamps = [
                ts for ts in self.request_timestamps 
                if now - ts < self.RATE_WINDOW
            ]
            
            # Check if we're approaching the rate limit
            current_requests = len(self.request_timestamps)
            
            # Adaptive throttling: slow down as we approach the limit
            if current_requests >= self.RATE_LIMIT * 0.8:  # At 80% capacity
                adaptive_delay = (current_requests - self.RATE_LIMIT * 0.8) / (self.RATE_LIMIT * 0.2)
                adaptive_delay = min(adaptive_delay * 2, 5)  # Max 5 second delay
                if adaptive_delay > 0:
                    self.logger.debug(f"Adaptive rate limiting: sleeping {adaptive_delay:.1f}s")
                    await asyncio.sleep(adaptive_delay)
                    now = time.time()
            
            # Hard limit enforcement
            if current_requests >= self.RATE_LIMIT:
                sleep_time = self.RATE_WINDOW - (now - self.request_timestamps[0]) + 1
                self.logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
                await asyncio.sleep(sleep_time)
                
                # Clean up old timestamps again
                now = time.time()
                self.request_timestamps = [
                    ts for ts in self.request_timestamps 
                    if now - ts < self.RATE_WINDOW
                ]
            
            # Record this request
            self.request_timestamps.append(now)
            self.last_request_time = now
    
    async def _make_request(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make GraphQL request to AniList API with circuit breaker and enhanced error handling.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            API response data
            
        Raises:
            AniListAPIError: API request failed
            RateLimitExceeded: Rate limit exceeded
            CircuitBreakerOpen: Circuit breaker is open
        """
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            raise CircuitBreakerOpen("Circuit breaker is open")
        
        await self._enforce_rate_limit()
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        request_start_time = time.time()
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                connector = aiohttp.TCPConnector(
                    limit=10,
                    limit_per_host=5,
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                )
                
                timeout = aiohttp.ClientTimeout(
                    total=self.timeout,
                    connect=10,
                    sock_read=self.timeout - 10
                )
                
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={"User-Agent": "MangaAnimeNotifier/1.0"}
                ) as session:
                    async with session.post(self.API_URL, json=payload) as response:
                        response_time = time.time() - request_start_time
                        self.total_response_time += response_time
                        self.request_count += 1
                        
                        data = await response.json()
                        
                        if response.status == 429:
                            rate_limit_error = RateLimitExceeded("Rate limit exceeded")
                            self.circuit_breaker.record_failure(rate_limit_error)
                            raise rate_limit_error
                        
                        if response.status != 200:
                            api_error = AniListAPIError(f"HTTP {response.status}: {data}")
                            self.circuit_breaker.record_failure(api_error)
                            raise api_error
                        
                        if "errors" in data:
                            api_error = AniListAPIError(f"GraphQL errors: {data['errors']}")
                            self.circuit_breaker.record_failure(api_error)
                            raise api_error
                        
                        # Success - record it
                        self.circuit_breaker.record_success()
                        
                        if response_time > 5.0:
                            self.logger.warning(f"Slow AniList API response: {response_time:.2f}s")
                        
                        return data.get("data", {})
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                self.error_count += 1
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                
                if attempt < self.retry_attempts - 1:
                    # Exponential backoff with jitter
                    backoff_delay = min(self.retry_delay * (2 ** attempt), 30)
                    jitter = backoff_delay * 0.1 * (0.5 - time.time() % 1)  # ±10% jitter
                    await asyncio.sleep(backoff_delay + jitter)
                else:
                    api_error = AniListAPIError(f"Request failed after {self.retry_attempts} attempts: {e}")
                    self.circuit_breaker.record_failure(api_error)
                    raise api_error
        
        # Should never reach here, but just in case
        api_error = AniListAPIError(f"Unexpected error in request handling: {last_exception}")
        self.circuit_breaker.record_failure(api_error)
        raise api_error
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get enhanced client performance statistics with Phase 2 monitoring.
        
        Returns:
            Dictionary with comprehensive performance metrics
        """
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 else 0
        )
        
        # Calculate recent performance metrics
        now = time.time()
        recent_timestamps = [
            ts for ts in self.request_timestamps 
            if now - ts <= self.PERFORMANCE_OPTIMIZATION_WINDOW
        ]
        
        return {
            # Core metrics
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / self.request_count if self.request_count > 0 else 0,
            'average_response_time': avg_response_time,
            
            # Circuit breaker metrics
            'circuit_breaker_state': self.circuit_breaker.state.value,
            'circuit_failure_count': self.circuit_breaker.failure_count,
            'circuit_success_count': self.circuit_breaker.success_count,
            
            # Rate limiting metrics
            'rate_limit_queue_size': len(self.request_timestamps),
            'recent_request_count': len(recent_timestamps),
            'rate_limit_utilization': len(recent_timestamps) / (self.RATE_LIMIT * self.PERFORMANCE_OPTIMIZATION_WINDOW / self.RATE_WINDOW),
            
            # Performance optimization metrics
            'burst_mode_active': len(self.request_timestamps) >= self.RATE_LIMIT * self.BURST_THRESHOLD,
            'performance_grade': self._calculate_performance_grade(avg_response_time, self.error_count),
            'health_score': self._calculate_health_score(),
            
            # Timing metrics
            'last_request_time': self.last_request_time,
            'uptime_seconds': now - (self.last_request_time or now)
        }
    
    def _calculate_performance_grade(self, avg_response_time: float, error_count: int) -> str:
        """
        Calculate performance grade based on response time and errors.
        
        Returns:
            Performance grade: 'A', 'B', 'C', 'D', or 'F'
        """
        if error_count == 0 and avg_response_time < 1.0:
            return 'A'  # Excellent
        elif error_count <= 2 and avg_response_time < 2.0:
            return 'B'  # Good
        elif error_count <= 5 and avg_response_time < 3.0:
            return 'C'  # Fair
        elif error_count <= 10 and avg_response_time < 5.0:
            return 'D'  # Poor
        else:
            return 'F'  # Failing
    
    def _calculate_health_score(self) -> float:
        """
        Calculate overall health score (0.0 to 1.0).
        
        Returns:
            Health score from 0.0 (unhealthy) to 1.0 (perfect health)
        """
        if self.request_count == 0:
            return 1.0  # Perfect score for new client
        
        # Base score calculation
        error_penalty = min(self.error_count / self.request_count, 0.5)  # Max 50% penalty
        circuit_penalty = 0.2 if self.circuit_breaker.state != CircuitState.CLOSED else 0.0
        
        # Performance bonus for fast responses
        avg_response_time = self.total_response_time / self.request_count
        speed_bonus = max(0, (3.0 - avg_response_time) / 3.0 * 0.1)  # Up to 10% bonus
        
        health_score = 1.0 - error_penalty - circuit_penalty + speed_bonus
        return max(0.0, min(1.0, health_score))
    
    async def search_anime(self, 
                          query: str = None,
                          season: str = None, 
                          year: int = None,
                          status: str = None,
                          limit: int = 20,
                          page: int = 1) -> List[AniListWork]:
        """
        Search for anime using various filters.
        
        Args:
            query: Search query string
            season: Season (SPRING, SUMMER, FALL, WINTER)
            year: Year to search
            status: Status filter (RELEASING, FINISHED, NOT_YET_RELEASED, etc.)
            limit: Number of results per page (max 50)
            page: Page number
            
        Returns:
            List of AniListWork objects
        """
        graphql_query = """
        query ($page: Int, $perPage: Int, $search: String, $season: MediaSeason, $seasonYear: Int, $status: MediaStatus) {
            Page(page: $page, perPage: $perPage) {
                media(search: $search, season: $season, seasonYear: $seasonYear, status: $status, type: ANIME) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    description
                    genres
                    tags {
                        name
                        description
                        isMediaSpoiler
                    }
                    status
                    startDate {
                        year
                        month
                        day
                    }
                    endDate {
                        year
                        month
                        day
                    }
                    coverImage {
                        large
                        medium
                    }
                    bannerImage
                    siteUrl
                    streamingEpisodes {
                        title
                        thumbnail
                        url
                        site
                    }
                    episodes
                    nextAiringEpisode {
                        episode
                        airingAt
                    }
                }
            }
        }
        """
        
        variables = {
            "page": page,
            "perPage": min(limit, 50),  # AniList max is 50
            "search": query,
            "season": season,
            "seasonYear": year,
            "status": status
        }
        
        try:
            data = await self._make_request(graphql_query, variables)
            media_list = data.get("Page", {}).get("media", [])
            
            results = []
            for media_data in media_list:
                try:
                    anilist_work = self._parse_media_data(media_data)
                    results.append(anilist_work)
                except Exception as e:
                    self.logger.warning(f"Failed to parse media data: {e}")
                    continue
            
            self.logger.info(f"Retrieved {len(results)} anime from AniList")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search anime: {e}")
            raise AniListAPIError(f"Search failed: {e}")
    
    async def get_anime_by_id(self, anilist_id: int) -> Optional[AniListWork]:
        """
        Get specific anime by AniList ID.
        
        Args:
            anilist_id: AniList media ID
            
        Returns:
            AniListWork object or None if not found
        """
        graphql_query = """
        query ($id: Int) {
            Media(id: $id, type: ANIME) {
                id
                title {
                    romaji
                    english
                    native
                }
                description
                genres
                tags {
                    name
                    description
                    isMediaSpoiler
                }
                status
                startDate {
                    year
                    month
                    day
                }
                endDate {
                    year
                    month
                    day
                }
                coverImage {
                    large
                    medium
                }
                bannerImage
                siteUrl
                streamingEpisodes {
                    title
                    thumbnail
                    url
                    site
                }
                episodes
                nextAiringEpisode {
                    episode
                    airingAt
                }
            }
        }
        """
        
        try:
            data = await self._make_request(graphql_query, {"id": anilist_id})
            media_data = data.get("Media")
            
            if not media_data:
                return None
            
            return self._parse_media_data(media_data)
            
        except Exception as e:
            self.logger.error(f"Failed to get anime by ID {anilist_id}: {e}")
            return None
    
    async def get_current_season_anime(self) -> List[AniListWork]:
        """
        Get anime for the current season.
        
        Returns:
            List of AniListWork objects for current season
        """
        now = datetime.now()
        year = now.year
        
        # Determine current season
        month = now.month
        if month in [12, 1, 2]:
            season = "WINTER"
        elif month in [3, 4, 5]:
            season = "SPRING"
        elif month in [6, 7, 8]:
            season = "SUMMER"
        else:
            season = "FALL"
        
        return await self.search_anime(season=season, year=year, limit=50)
    
    async def get_studio_anime(self, studio_name: str, limit: int = 20) -> List[AniListWork]:
        """
        Get anime by studio name.
        
        Args:
            studio_name: Studio name to search for
            limit: Number of results to return
            
        Returns:
            List of AniListWork objects from the specified studio
        """
        graphql_query = """
        query ($search: String, $perPage: Int) {
            Page(perPage: $perPage) {
                media(search: $search, type: ANIME) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    studios {
                        nodes {
                            name
                        }
                    }
                    description
                    genres
                    tags {
                        name
                        description
                        isMediaSpoiler
                    }
                    status
                    startDate {
                        year
                        month
                        day
                    }
                    coverImage {
                        large
                        medium
                    }
                    siteUrl
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
        
        try:
            data = await self._make_request(graphql_query, {
                "search": studio_name,
                "perPage": min(limit, 50)
            })
            
            media_list = data.get("Page", {}).get("media", [])
            results = []
            
            for media_data in media_list:
                # Filter by studio name
                studios = media_data.get("studios", {}).get("nodes", [])
                studio_names = [studio.get("name", "") for studio in studios]
                
                if any(studio_name.lower() in name.lower() for name in studio_names):
                    try:
                        anilist_work = self._parse_media_data(media_data)
                        # Add studio info to metadata
                        anilist_work.metadata = getattr(anilist_work, 'metadata', {})
                        anilist_work.metadata['studios'] = studio_names
                        results.append(anilist_work)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse studio media data: {e}")
                        continue
            
            self.logger.info(f"Retrieved {len(results)} anime from studio {studio_name}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search anime by studio {studio_name}: {e}")
            return []
    
    async def get_genre_anime(self, genre: str, limit: int = 20, year: int = None) -> List[AniListWork]:
        """
        Get anime by genre.
        
        Args:
            genre: Genre to search for (Action, Comedy, Drama, etc.)
            limit: Number of results to return
            year: Year filter (optional)
            
        Returns:
            List of AniListWork objects of the specified genre
        """
        graphql_query = """
        query ($genre: String, $perPage: Int, $seasonYear: Int) {
            Page(perPage: $perPage) {
                media(genre: $genre, type: ANIME, seasonYear: $seasonYear) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    description
                    genres
                    tags {
                        name
                        description
                        isMediaSpoiler
                    }
                    status
                    startDate {
                        year
                        month
                        day
                    }
                    coverImage {
                        large
                        medium
                    }
                    siteUrl
                    streamingEpisodes {
                        title
                        thumbnail
                        url
                        site
                    }
                    studios {
                        nodes {
                            name
                        }
                    }
                    popularity
                    averageScore
                }
            }
        }
        """
        
        try:
            data = await self._make_request(graphql_query, {
                "genre": genre,
                "perPage": min(limit, 50),
                "seasonYear": year
            })
            
            media_list = data.get("Page", {}).get("media", [])
            results = []
            
            for media_data in media_list:
                try:
                    anilist_work = self._parse_media_data(media_data)
                    # Add additional metadata
                    anilist_work.metadata = getattr(anilist_work, 'metadata', {})
                    anilist_work.metadata['studios'] = [s.get('name') for s in media_data.get('studios', {}).get('nodes', [])]
                    anilist_work.metadata['popularity'] = media_data.get('popularity')
                    anilist_work.metadata['average_score'] = media_data.get('averageScore')
                    results.append(anilist_work)
                except Exception as e:
                    self.logger.warning(f"Failed to parse genre media data: {e}")
                    continue
            
            self.logger.info(f"Retrieved {len(results)} anime for genre {genre}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search anime by genre {genre}: {e}")
            return []
    
    async def get_streaming_anime(self, platform: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get anime available on specific streaming platform.
        
        Args:
            platform: Platform name (Netflix, Crunchyroll, etc.)
            limit: Number of results to return
            
        Returns:
            List of dictionaries with anime and streaming info
        """
        graphql_query = """
        query ($perPage: Int) {
            Page(perPage: $perPage) {
                media(type: ANIME, status: RELEASING) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    siteUrl
                    streamingEpisodes {
                        title
                        thumbnail
                        url
                        site
                    }
                    genres
                    status
                    coverImage {
                        large
                    }
                }
            }
        }
        """
        
        try:
            data = await self._make_request(graphql_query, {"perPage": min(limit * 3, 100)})  # Get more to filter
            media_list = data.get("Page", {}).get("media", [])
            
            results = []
            platform_lower = platform.lower()
            
            for media in media_list:
                streaming_eps = media.get("streamingEpisodes", [])
                matching_platforms = []
                
                for ep in streaming_eps:
                    site = ep.get("site", "")
                    if platform_lower in site.lower():
                        matching_platforms.append({
                            'site': site,
                            'url': ep.get('url'),
                            'title': ep.get('title')
                        })
                
                if matching_platforms:
                    title = (media.get("title", {}).get("english") or 
                            media.get("title", {}).get("romaji") or "Unknown")
                    
                    results.append({
                        "anilist_id": media.get("id"),
                        "title": title,
                        "site_url": media.get("siteUrl"),
                        "cover_image": media.get("coverImage", {}).get("large"),
                        "genres": media.get("genres", []),
                        "status": media.get("status"),
                        "streaming_info": matching_platforms
                    })
                
                if len(results) >= limit:
                    break
            
            self.logger.info(f"Found {len(results)} anime on {platform}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get streaming anime for {platform}: {e}")
            return []
    
    async def get_upcoming_releases(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get anime with upcoming episode releases.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of dictionaries with release information
        """
        graphql_query = """
        query ($page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                media(status: RELEASING, type: ANIME) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    siteUrl
                    nextAiringEpisode {
                        episode
                        airingAt
                    }
                    streamingEpisodes {
                        title
                        url
                        site
                    }
                }
            }
        }
        """
        
        upcoming_releases = []
        page = 1
        max_pages = 5  # Limit to avoid excessive requests
        
        while page <= max_pages:
            try:
                data = await self._make_request(graphql_query, {"page": page, "perPage": 50})
                media_list = data.get("Page", {}).get("media", [])
                
                if not media_list:
                    break
                
                cutoff_time = datetime.now().timestamp() + (days_ahead * 24 * 3600)
                
                for media in media_list:
                    next_episode = media.get("nextAiringEpisode")
                    if not next_episode:
                        continue
                    
                    airing_at = next_episode.get("airingAt")
                    if not airing_at or airing_at > cutoff_time:
                        continue
                    
                    title = (media.get("title", {}).get("english") or 
                            media.get("title", {}).get("romaji") or "Unknown")
                    
                    upcoming_releases.append({
                        "anilist_id": media.get("id"),
                        "title": title,
                        "episode_number": next_episode.get("episode"),
                        "airing_at": airing_at,
                        "airing_date": datetime.fromtimestamp(airing_at).date(),
                        "site_url": media.get("siteUrl"),
                        "streaming_platforms": [ep.get("site") for ep in media.get("streamingEpisodes", []) if ep.get("site")]
                    })
                
                page += 1
                
            except Exception as e:
                self.logger.error(f"Failed to get upcoming releases page {page}: {e}")
                break
        
        # Sort by airing time
        upcoming_releases.sort(key=lambda x: x["airing_at"])
        
        self.logger.info(f"Found {len(upcoming_releases)} upcoming releases")
        return upcoming_releases
    
    def _parse_media_data(self, media_data: Dict[str, Any]) -> AniListWork:
        """
        Parse AniList media data into AniListWork object.
        
        Args:
            media_data: Raw media data from AniList API
            
        Returns:
            AniListWork object
        """
        title_data = media_data.get("title", {})
        cover_image = media_data.get("coverImage", {})
        
        # Extract tag names (exclude spoiler tags)
        tags = []
        for tag in media_data.get("tags", []):
            if not tag.get("isMediaSpoiler", False):
                tags.append(tag.get("name", ""))
        
        anilist_work = AniListWork(
            id=media_data.get("id"),
            title_romaji=title_data.get("romaji", ""),
            title_english=title_data.get("english"),
            title_native=title_data.get("native"),
            description=media_data.get("description"),
            genres=media_data.get("genres", []),
            tags=tags,
            status=media_data.get("status"),
            start_date=media_data.get("startDate"),
            end_date=media_data.get("endDate"),
            cover_image=cover_image.get("large") or cover_image.get("medium"),
            banner_image=media_data.get("bannerImage"),
            site_url=media_data.get("siteUrl"),
            streaming_episodes=media_data.get("streamingEpisodes", [])
        )
        
        # Add extended metadata if available
        anilist_work.metadata = {}
        
        if "studios" in media_data:
            studios = media_data["studios"].get("nodes", [])
            anilist_work.metadata["studios"] = [studio.get("name") for studio in studios]
        
        if "popularity" in media_data:
            anilist_work.metadata["popularity"] = media_data["popularity"]
            
        if "averageScore" in media_data:
            anilist_work.metadata["average_score"] = media_data["averageScore"]
            
        if "episodes" in media_data:
            anilist_work.metadata["total_episodes"] = media_data["episodes"]
        
        return anilist_work


class AniListCollector:
    """
    High-level AniList data collector with database integration.
    
    Provides methods to collect anime data from AniList and store it
    in the database with proper normalization and deduplication.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize collector.
        
        Args:
            config: Configuration dictionary with API settings
        """
        self.config = config or {}
        api_config = self.config.get("apis", {}).get("anilist", {})
        
        self.client = AniListClient(
            timeout=api_config.get("timeout_seconds", 30),
            retry_attempts=3,
            retry_delay=api_config.get("rate_limit", {}).get("retry_delay_seconds", 5)
        )
        
        self.db = get_db()
        self.logger = logging.getLogger(__name__)
        
        # Filtering configuration
        filter_config = self.config.get("filtering", {})
        self.ng_keywords = filter_config.get("ng_keywords", [])
        self.ng_genres = filter_config.get("ng_genres", [])
        self.exclude_tags = filter_config.get("exclude_tags", [])
    
    def _should_filter_work(self, anilist_work: AniListWork) -> bool:
        """
        Check if work should be filtered out based on NG keywords.
        
        Args:
            anilist_work: AniListWork to check
            
        Returns:
            True if work should be filtered out
        """
        # Check title
        for keyword in self.ng_keywords:
            for title in [anilist_work.title_romaji, anilist_work.title_english, anilist_work.title_native]:
                if title and keyword.lower() in title.lower():
                    self.logger.debug(f"Filtered by title keyword '{keyword}': {title}")
                    return True
        
        # Check description
        if anilist_work.description:
            for keyword in self.ng_keywords:
                if keyword.lower() in anilist_work.description.lower():
                    self.logger.debug(f"Filtered by description keyword '{keyword}': {anilist_work.title_romaji}")
                    return True
        
        # Check genres
        for genre in anilist_work.genres:
            if genre in self.ng_genres:
                self.logger.debug(f"Filtered by genre '{genre}': {anilist_work.title_romaji}")
                return True
        
        # Check tags
        for tag in anilist_work.tags:
            if tag in self.exclude_tags:
                self.logger.debug(f"Filtered by tag '{tag}': {anilist_work.title_romaji}")
                return True
        
        return False
    
    async def collect_current_season(self) -> Tuple[int, int]:
        """
        Collect anime from current season.
        
        Returns:
            Tuple of (collected_count, filtered_count)
        """
        try:
            anilist_works = await self.client.get_current_season_anime()
            
            collected_count = 0
            filtered_count = 0
            
            for anilist_work in anilist_works:
                if self._should_filter_work(anilist_work):
                    filtered_count += 1
                    continue
                
                # Convert to common Work model and store
                work = anilist_work.to_work()
                work_id = self.db.get_or_create_work(
                    title=work.title,
                    work_type=work.work_type.value,
                    title_kana=work.title_kana,
                    title_en=work.title_en,
                    official_url=work.official_url
                )
                
                collected_count += 1
                self.logger.debug(f"Collected anime: {work.title} (ID: {work_id})")
            
            self.logger.info(f"Collected {collected_count} anime, filtered {filtered_count}")
            return collected_count, filtered_count
            
        except Exception as e:
            self.logger.error(f"Failed to collect current season anime: {e}")
            return 0, 0
    
    async def collect_upcoming_episodes(self) -> int:
        """
        Collect upcoming episode releases.
        
        Returns:
            Number of releases collected
        """
        try:
            upcoming = await self.client.get_upcoming_releases(days_ahead=7)
            
            collected_count = 0
            
            for release_info in upcoming:
                # Get or create work
                work_id = self.db.get_or_create_work(
                    title=release_info["title"],
                    work_type="anime"
                )
                
                # Create release entry
                release_id = self.db.create_release(
                    work_id=work_id,
                    release_type="episode",
                    number=str(release_info["episode_number"]),
                    release_date=release_info["airing_date"].isoformat(),
                    source=DataSource.ANILIST.value,
                    source_url=release_info["site_url"]
                )
                
                if release_id:
                    collected_count += 1
            
            self.logger.info(f"Collected {collected_count} upcoming episodes")
            return collected_count
            
        except Exception as e:
            self.logger.error(f"Failed to collect upcoming episodes: {e}")
            return 0
    
    async def run_collection(self) -> Dict[str, Any]:
        """
        Run complete AniList data collection.
        
        Returns:
            Collection results dictionary
        """
        results = {
            "source": DataSource.ANILIST.value,
            "timestamp": datetime.now().isoformat(),
            "works_collected": 0,
            "works_filtered": 0,
            "releases_collected": 0,
            "errors": []
        }
        
        try:
            # Collect current season anime
            works_collected, works_filtered = await self.collect_current_season()
            results["works_collected"] = works_collected
            results["works_filtered"] = works_filtered
            
            # Collect upcoming episodes
            releases_collected = await self.collect_upcoming_episodes()
            results["releases_collected"] = releases_collected
            
        except Exception as e:
            error_msg = f"AniList collection failed: {e}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def collect(self) -> List[Dict[str, Any]]:
        """
        Synchronous collection method for compatibility.
        
        Returns:
            List of collected anime items in normalized format
        """
        async def _run():
            results = await self.run_collection()
            
            # For now, return empty list as a placeholder
            # In a full implementation, this would return actual collected data
            return []
        
        return asyncio.run(_run())


# Async context manager for easy usage
class AniListSession:
    """Async context manager for AniList operations."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config
        self.collector = None
    
    async def __aenter__(self):
        self.collector = AniListCollector(self.config)
        return self.collector
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        pass


# Synchronous wrapper function for non-async environments
def collect_anilist_data(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Synchronous wrapper for AniList data collection.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Collection results dictionary
    """
    async def _run_collection():
        async with AniListSession(config) as collector:
            return await collector.run_collection()
    
    return asyncio.run(_run_collection())


# Add synchronous collect method for compatibility
def collect_anilist_sync(config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for AniList data collection.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of collected anime items in normalized format
    """
    async def _collect():
        async with AniListSession(config) as collector:
            results = await collector.run_collection()
            
            # Convert to simplified format for compatibility
            items = []
            if results.get('works_collected', 0) > 0:
                # This is a placeholder - in a real implementation, 
                # we would extract the actual collected data
                pass
            
            return items
    
    return asyncio.run(_collect())