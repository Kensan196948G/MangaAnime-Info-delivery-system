#!/usr/bin/env python3
"""
Syoboi Calendar (しょぼいカレンダー) API integration module.

This module provides:
- Syoboi Calendar API client for Japanese TV anime schedules
- Program data retrieval and normalization
- Broadcasting channel and time information
- Error handling and retry logic
- Data validation and filtering

Syoboi Calendar: https://cal.syoboi.jp/
API Documentation: https://docs.cal.syoboi.jp/spec/
"""

import asyncio
import json
import logging
import time

logger = logging.getLogger(__name__)
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from .models import DataSource, Release, ReleaseType, Work, WorkType


class SyoboiAPIError(Exception):
    """Custom exception for Syoboi Calendar API errors."""


class SyoboiRateLimitError(SyoboiAPIError):
    """Exception raised when rate limit is exceeded."""


@dataclass
class BroadcastChannel:
    """Broadcasting channel information."""

    channel_id: str
    channel_name: str
    channel_group: Optional[str] = None
    epg_url: Optional[str] = None


@dataclass
class BroadcastProgram:
    """Broadcasting program information from Syoboi Calendar."""

    program_id: str
    title: str
    title_short: Optional[str] = None
    title_en: Optional[str] = None
    title_kana: Optional[str] = None
    channel: BroadcastChannel = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    episode_number: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    official_url: Optional[str] = None
    flags: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)


class SyoboiCalendarClient:
    """
    Syoboi Calendar API client for anime broadcasting schedule.

    Features:
    - Fetch upcoming anime broadcasts
    - Get program details by title/ID
    - Channel and time information
    - Automatic rate limiting
    - Error recovery with retry logic
    """

    BASE_URL = "https://cal.syoboi.jp"
    JSON_API = "/json.php"
    DB_API = "/db.php"

    def __init__(
        self,
        timeout: int = 15,
        max_retries: int = 3,
        retry_delay: int = 2,
        requests_per_minute: int = 60,
    ):
        """
        Initialize Syoboi Calendar client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            requests_per_minute: Rate limit for requests
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.requests_per_minute = requests_per_minute

        self.logger = logging.getLogger(__name__)

        # Rate limiting
        self.request_times: List[float] = []
        self.min_request_interval = 60.0 / requests_per_minute

        # Request statistics
        self.request_count = 0
        self.error_count = 0
        self.cache: Dict[str, Any] = {}

        self.logger.info(
            "Syoboi Calendar client initialized: "
            f"timeout={timeout}s, rate_limit={requests_per_minute}/min"
        )

    async def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits."""
        now = time.time()

        # Clean up old request times
        self.request_times = [t for t in self.request_times if now - t < 60]

        # Check if rate limit reached
        if len(self.request_times) >= self.requests_per_minute:
            oldest_request = min(self.request_times)
            wait_time = 60 - (now - oldest_request)

            if wait_time > 0:
                self.logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                now = time.time()

        # Record this request
        self.request_times.append(now)

    async def _make_request(
        self, endpoint: str, params: Dict[str, Any], retries: int = 0
    ) -> Dict[str, Any]:
        """
        Make API request with retry logic.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            retries: Current retry attempt

        Returns:
            API response as dictionary
        """
        await self._wait_for_rate_limit()

        url = f"{self.BASE_URL}{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    self.request_count += 1

                    if response.status == 200:
                        content_type = response.headers.get("Content-Type", "")

                        if "json" in content_type:
                            data = await response.json()
                        else:
                            # Try to parse as JSON anyway
                            text = await response.text()
                            try:
                                data = json.loads(text)
                            except json.JSONDecodeError:
                                # Return raw text in a dict
                                data = {"raw_text": text}

                        return data

                    elif response.status == 429:  # Too Many Requests
                        raise SyoboiRateLimitError("Rate limit exceeded")

                    else:
                        error_text = await response.text()
                        raise SyoboiAPIError(
                            f"API request failed: {response.status} - {error_text}"
                        )

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            self.error_count += 1

            if retries < self.max_retries:
                wait_time = self.retry_delay * (2**retries)  # Exponential backoff
                self.logger.warning(
                    f"Request failed (attempt {retries + 1}/{self.max_retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
                return await self._make_request(endpoint, params, retries + 1)

            raise SyoboiAPIError(f"Request failed after {self.max_retries} retries: {e}")

    async def get_recent_programs(
        self, days_ahead: int = 7, channels: Optional[List[str]] = None
    ) -> List[BroadcastProgram]:
        """
        Get recent and upcoming anime broadcasts.

        Args:
            days_ahead: Number of days to look ahead
            channels: Optional list of channel IDs to filter

        Returns:
            List of broadcast programs
        """
        self.logger.info(f"Fetching programs for next {days_ahead} days")

        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=days_ahead)

        params = {
            "Req": "ProgramByDate",
            "Start": start_date.strftime("%Y%m%d"),
            "End": end_date.strftime("%Y%m%d"),
        }

        if channels:
            params["ChID"] = ",".join(channels)

        try:
            data = await self._make_request(self.JSON_API, params)
            programs = self._parse_programs(data)

            self.logger.info(f"Retrieved {len(programs)} programs")
            return programs

        except Exception as e:
            self.logger.error(f"Failed to fetch programs: {e}")
            raise

    async def search_program_by_title(self, title: str) -> List[BroadcastProgram]:
        """
        Search for programs by title.

        Args:
            title: Program title to search

        Returns:
            List of matching programs
        """
        self.logger.info(f"Searching for program: {title}")

        params = {"Req": "TitleLookup", "TID": "*", "Title": title}

        try:
            data = await self._make_request(self.JSON_API, params)
            programs = self._parse_programs(data)

            self.logger.info(f"Found {len(programs)} matching programs")
            return programs

        except Exception as e:
            self.logger.error(f"Failed to search programs: {e}")
            return []

    async def get_program_details(self, program_id: str) -> Optional[BroadcastProgram]:
        """
        Get detailed information for a specific program.

        Args:
            program_id: Program/Title ID

        Returns:
            Program details or None if not found
        """
        params = {"Req": "TitleFull", "TID": program_id}

        try:
            data = await self._make_request(self.JSON_API, params)
            programs = self._parse_programs(data)

            if programs:
                return programs[0]

            return None

        except Exception as e:
            self.logger.error(f"Failed to get program details: {e}")
            return None

    def _parse_programs(self, data: Dict[str, Any]) -> List[BroadcastProgram]:
        """
        Parse API response into BroadcastProgram objects.

        Args:
            data: Raw API response

        Returns:
            List of parsed programs
        """
        programs = []

        try:
            # Handle different response formats
            if "Programs" in data:
                program_data = data["Programs"]
            elif "Titles" in data:
                program_data = data["Titles"]
            else:
                # Try to detect program data
                for key in data:
                    if isinstance(data[key], (list, dict)):
                        program_data = data[key]
                        break
                else:
                    self.logger.warning("Could not find program data in response")
                    return programs

            # Parse program entries
            if isinstance(program_data, dict):
                for prog_id, prog_info in program_data.items():
                    program = self._parse_single_program(prog_id, prog_info)
                    if program:
                        programs.append(program)

            elif isinstance(program_data, list):
                for prog_info in program_data:
                    program = self._parse_single_program(
                        prog_info.get("TID", prog_info.get("PID", "")), prog_info
                    )
                    if program:
                        programs.append(program)

        except Exception as e:
            self.logger.error(f"Failed to parse programs: {e}")

        return programs

    def _parse_single_program(
        self, program_id: str, data: Dict[str, Any]
    ) -> Optional[BroadcastProgram]:
        """Parse a single program entry."""
        try:
            # Extract channel info
            channel = None
            if "ChID" in data:
                channel = BroadcastChannel(
                    channel_id=str(data.get("ChID", "")),
                    channel_name=data.get("ChName", ""),
                    channel_group=data.get("ChGroup", None),
                )

            # Parse broadcast times
            start_time = None
            end_time = None

            if "StTime" in data:
                try:
                    start_time = datetime.strptime(data["StTime"], "%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    pass

            if "EdTime" in data:
                try:
                    end_time = datetime.strptime(data["EdTime"], "%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    pass

            # Create program object
            program = BroadcastProgram(
                program_id=str(program_id),
                title=data.get("Title", data.get("TitleYomi", "Unknown")),
                title_short=data.get("ShortTitle", None),
                title_en=data.get("TitleEN", None),
                title_kana=data.get("TitleYomi", None),
                channel=channel,
                start_time=start_time,
                end_time=end_time,
                episode_number=data.get("Count", None),
                subtitle=data.get("SubTitle", None),
                description=data.get("Comment", None),
                official_url=data.get("URL", None),
                flags={
                    "FirstCh": data.get("FirstCh", None),
                    "Cat": data.get("Cat", None),
                    "UserPoint": data.get("UserPoint", None),
                },
                raw_data=data,
            )

            return program

        except Exception as e:
            self.logger.error(f"Failed to parse program {program_id}: {e}")
            return None

    def _convert_to_work(self, program: BroadcastProgram) -> Work:
        """Convert BroadcastProgram to Work model."""
        metadata = {
            "source": DataSource.SYOBOI.value,
            "program_id": program.program_id,
            "channel": program.channel.channel_name if program.channel else None,
            "description": program.description,
            "flags": program.flags,
        }

        work = Work(
            title=program.title,
            work_type=WorkType.ANIME,
            title_kana=program.title_kana,
            title_en=program.title_en,
            official_url=program.official_url,
            metadata=metadata,
        )

        return work

    def _convert_to_release(self, program: BroadcastProgram, work_id: int) -> Optional[Release]:
        """Convert BroadcastProgram to Release model."""
        if not program.start_time:
            return None

        platform = ""
        if program.channel:
            platform = program.channel.channel_name

        metadata = {
            "source": DataSource.SYOBOI.value,
            "program_id": program.program_id,
            "channel_id": program.channel.channel_id if program.channel else None,
            "subtitle": program.subtitle,
            "start_time": program.start_time.isoformat(),
            "end_time": program.end_time.isoformat() if program.end_time else None,
        }

        release = Release(
            work_id=work_id,
            release_type=ReleaseType.EPISODE,
            number=program.episode_number,
            platform=platform,
            release_date=program.start_time.date(),
            source=DataSource.SYOBOI,
            source_url=f"{self.BASE_URL}/tid/{program.program_id}",
            metadata=metadata,
        )

        return release

    async def fetch_and_convert(self, days_ahead: int = 7) -> Tuple[List[Work], List[Release]]:
        """
        Fetch programs and convert to Work/Release models.

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            Tuple of (works, releases)
        """
        programs = await self.get_recent_programs(days_ahead)

        works = []
        releases = []
        work_map: Dict[str, int] = {}  # program_id -> work_id mapping

        for program in programs:
            # Convert to Work
            work = self._convert_to_work(program)
            works.append(work)

            # Track work ID (will be set after DB insert)
            work_map[program.program_id] = len(works) - 1

            # Convert to Release if broadcast time available
            if program.start_time:
                # Use temporary work_id (will be updated after DB insert)
                release = self._convert_to_release(program, 0)
                if release:
                    releases.append(release)

        self.logger.info(
            f"Converted {len(programs)} programs to "
            f"{len(works)} works and {len(releases)} releases"
        )

        return works, releases

    def get_statistics(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "success_rate": (
                (self.request_count - self.error_count) / self.request_count
                if self.request_count > 0
                else 0.0
            ),
            "cache_size": len(self.cache),
        }


# Async wrapper functions for easy integration


async def fetch_syoboi_programs(days_ahead: int = 7, timeout: int = 15) -> List[BroadcastProgram]:
    """
    Fetch anime programs from Syoboi Calendar.

    Args:
        days_ahead: Number of days to look ahead
        timeout: Request timeout in seconds

    Returns:
        List of broadcast programs
    """
    client = SyoboiCalendarClient(timeout=timeout)
    return await client.get_recent_programs(days_ahead)


async def search_syoboi_anime(title: str, timeout: int = 15) -> List[BroadcastProgram]:
    """
    Search for anime by title on Syoboi Calendar.

    Args:
        title: Anime title to search
        timeout: Request timeout in seconds

    Returns:
        List of matching programs
    """
    client = SyoboiCalendarClient(timeout=timeout)
    return await client.search_program_by_title(title)


async def fetch_syoboi_works_and_releases(
    days_ahead: int = 7, timeout: int = 15
) -> Tuple[List[Work], List[Release]]:
    """
    Fetch anime data from Syoboi Calendar as Work/Release models.

    Args:
        days_ahead: Number of days to look ahead
        timeout: Request timeout in seconds

    Returns:
        Tuple of (works, releases)
    """
    client = SyoboiCalendarClient(timeout=timeout)
    return await client.fetch_and_convert(days_ahead)


# Synchronous wrapper for non-async contexts


def fetch_syoboi_programs_sync(days_ahead: int = 7) -> List[BroadcastProgram]:
    """Synchronous wrapper for fetch_syoboi_programs."""
    return asyncio.run(fetch_syoboi_programs(days_ahead))


def search_syoboi_anime_sync(title: str) -> List[BroadcastProgram]:
    """Synchronous wrapper for search_syoboi_anime."""
    return asyncio.run(search_syoboi_anime(title))


def fetch_syoboi_works_and_releases_sync(
    days_ahead: int = 7,
) -> Tuple[List[Work], List[Release]]:
    """Synchronous wrapper for fetch_syoboi_works_and_releases."""
    return asyncio.run(fetch_syoboi_works_and_releases(days_ahead))


# モジュールレベルのfetch_and_store関数（collect_all_data.pyから呼び出される）
def fetch_and_store() -> dict:
    """
    しょぼいカレンダーAPIからアニメデータを収集しデータベースに保存する。

    Returns:
        dict: 収集結果のサマリー
    """
    from .db import get_db

    try:
        # データ収集（同期版を使用）
        works, releases = fetch_syoboi_works_and_releases_sync(days_ahead=14)

        if not works:
            logger.info("しょぼいカレンダーから収集されたデータはありません")
            return {"success": True, "works": 0, "releases": 0}

        # データベースに保存
        db = get_db()
        stored_works = 0
        stored_releases = 0

        # 作品IDのマッピング（Work.id -> DB work_id）
        work_id_map = {}

        for work in works:
            try:
                title = work.title if hasattr(work, "title") else str(work)
                if not title:
                    continue

                work_id = db.get_or_create_work(
                    title=title,
                    work_type="anime",
                    title_kana=getattr(work, "title_kana", None),
                    title_en=getattr(work, "title_en", None),
                    official_url=getattr(work, "official_url", None),
                )
                work_id_map[getattr(work, "id", title)] = work_id
                stored_works += 1
            except Exception as e:
                logger.warning(f"作品保存エラー: {work} - {e}")
                continue

        for release in releases:
            try:
                # 対応する作品IDを取得
                orig_work_id = getattr(release, "work_id", None)
                db_work_id = work_id_map.get(orig_work_id)
                if not db_work_id:
                    continue

                release_date = getattr(release, "release_date", None)
                if release_date and hasattr(release_date, "isoformat"):
                    release_date = release_date.strftime("%Y-%m-%d")

                release_type = getattr(release, "release_type", "episode")
                if hasattr(release_type, "value"):
                    release_type = release_type.value

                db.create_release(
                    work_id=db_work_id,
                    release_type=str(release_type),
                    number=getattr(release, "number", None),
                    platform=getattr(release, "platform", "TV放送"),
                    release_date=release_date,
                    source="syoboi",
                    source_url=getattr(release, "source_url", None),
                )
                stored_releases += 1
            except Exception as e:
                logger.warning(f"リリース保存エラー: {e}")
                continue

        logger.info(
            f"しょぼいカレンダー収集完了: {stored_works}作品, {stored_releases}リリース保存"
        )
        return {"success": True, "works": stored_works, "releases": stored_releases}

    except Exception as e:
        logger.error(f"しょぼいカレンダー fetch_and_store エラー: {e}")
        return {"success": False, "error": str(e)}
