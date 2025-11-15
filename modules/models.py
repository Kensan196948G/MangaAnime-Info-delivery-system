"""
Data models and structures for the Anime/Manga information delivery system.

This module defines:
- Common data structures for works and releases
- API response models
- Data validation and normalization utilities
- Type definitions for consistent data handling
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
import re
from urllib.parse import urlparse


class WorkType(Enum):
    """Work type enumeration."""

    ANIME = "anime"
    MANGA = "manga"


class ReleaseType(Enum):
    """Release type enumeration."""

    EPISODE = "episode"
    VOLUME = "volume"


class DataSource(Enum):
    """Data source enumeration."""

    ANILIST = "anilist"
    SYOBOI = "syoboi_calendar"
    KITSU = "kitsu"
    ANNICT = "annict"
    MANGADEX = "mangadex"
    MANGAUPDATES = "mangaupdates"
    RSS_DANIME = "danime_rss"
    RSS_BOOKWALKER = "bookwalker_rss"
    RSS_GENERAL = "rss_general"


@dataclass
class Work:
    """
    Work data model representing an anime or manga title.

    Attributes:
        title: Main title (required)
        work_type: WorkType enum (anime/manga)
        id: Database ID (optional, set after creation)
        title_kana: Katakana reading
        title_en: English title
        official_url: Official website URL
        created_at: Creation timestamp
        metadata: Additional metadata from sources
    """

    title: str
    work_type: WorkType
    id: Optional[int] = None
    title_kana: Optional[str] = None
    title_en: Optional[str] = None
    official_url: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if not self.title or not self.title.strip():
            raise ValueError("Title is required and cannot be empty")

        self.title = self.title.strip()

        if isinstance(self.work_type, str):
            try:
                self.work_type = WorkType(self.work_type.lower())
            except ValueError:
                raise ValueError(f"Invalid work_type: {self.work_type}")

        # Validate URL if provided
        if self.official_url and not self._is_valid_url(self.official_url):
            self.official_url = None

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations."""
        return {
            "id": self.id,
            "title": self.title,
            "title_kana": self.title_kana,
            "title_en": self.title_en,
            "type": self.work_type.value,
            "official_url": self.official_url,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Work":
        """Create Work instance from dictionary."""
        metadata = {
            k: v
            for k, v in data.items()
            if k
            not in (
                "id",
                "title",
                "title_kana",
                "title_en",
                "type",
                "official_url",
                "created_at",
            )
        }

        return cls(
            id=data.get("id"),
            title=data["title"],
            work_type=WorkType(data["type"]),
            title_kana=data.get("title_kana"),
            title_en=data.get("title_en"),
            official_url=data.get("official_url"),
            created_at=data.get("created_at"),
            metadata=metadata,
        )


@dataclass
class Release:
    """
    Release data model representing an episode or volume release.

    Attributes:
        work_id: ID of associated work
        release_type: ReleaseType enum (episode/volume)
        id: Database ID (optional, set after creation)
        number: Episode/volume number
        platform: Release platform
        release_date: Release date
        source: Data source name
        source_url: Source URL
        notified: Whether notification was sent
        created_at: Creation timestamp
        metadata: Additional metadata from sources
    """

    work_id: int
    release_type: ReleaseType
    id: Optional[int] = None
    number: Optional[str] = None
    platform: Optional[str] = None
    release_date: Optional[date] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    notified: bool = False
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if not self.work_id or self.work_id <= 0:
            raise ValueError("Valid work_id is required")

        if isinstance(self.release_type, str):
            try:
                self.release_type = ReleaseType(self.release_type.lower())
            except ValueError:
                raise ValueError(f"Invalid release_type: {self.release_type}")

        # Normalize number field
        if self.number:
            self.number = str(self.number).strip()

        # Validate and parse release_date
        if isinstance(self.release_date, str):
            self.release_date = self._parse_date(self.release_date)

    @staticmethod
    def _parse_date(date_str: str) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None

        # Common date formats
        date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y", "%Y年%m月%d日"]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations."""
        return {
            "id": self.id,
            "work_id": self.work_id,
            "release_type": self.release_type.value,
            "number": self.number,
            "platform": self.platform,
            "release_date": (
                self.release_date.isoformat() if self.release_date else None
            ),
            "source": self.source,
            "source_url": self.source_url,
            "notified": 1 if self.notified else 0,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Release":
        """Create Release instance from dictionary."""
        metadata = {
            k: v
            for k, v in data.items()
            if k
            not in (
                "id",
                "work_id",
                "release_type",
                "number",
                "platform",
                "release_date",
                "source",
                "source_url",
                "notified",
                "created_at",
            )
        }

        return cls(
            id=data.get("id"),
            work_id=data["work_id"],
            release_type=ReleaseType(data["release_type"]),
            number=data.get("number"),
            platform=data.get("platform"),
            release_date=data.get("release_date"),
            source=data.get("source"),
            source_url=data.get("source_url"),
            notified=bool(data.get("notified", 0)),
            created_at=data.get("created_at"),
            metadata=metadata,
        )


@dataclass
class AniListWork:
    """
    AniList specific work data model.

    Attributes:
        id: AniList ID
        title_romaji: Romaji title
        title_english: English title
        title_native: Native title
        description: Work description
        genres: List of genres
        tags: List of tags
        status: Current status
        start_date: Start date
        end_date: End date
        cover_image: Cover image URL
        banner_image: Banner image URL
        site_url: AniList URL
        streaming_episodes: Streaming platform info
    """

    id: int
    title_romaji: str
    title_english: Optional[str] = None
    title_native: Optional[str] = None
    description: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    status: Optional[str] = None
    start_date: Optional[Dict[str, int]] = None
    end_date: Optional[Dict[str, int]] = None
    cover_image: Optional[str] = None
    banner_image: Optional[str] = None
    site_url: Optional[str] = None
    streaming_episodes: List[Dict[str, Any]] = field(default_factory=list)

    def to_work(self) -> Work:
        """Convert to common Work model."""
        # Determine primary title
        title = self.title_romaji
        if self.title_english and len(self.title_english) > 0:
            title = self.title_english

        # Extract metadata
        metadata = {
            "anilist_id": self.id,
            "description": self.description,
            "genres": self.genres,
            "tags": self.tags,
            "status": self.status,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "cover_image": self.cover_image,
            "banner_image": self.banner_image,
            "streaming_episodes": self.streaming_episodes,
        }

        return Work(
            title=title,
            work_type=WorkType.ANIME,
            title_en=self.title_english,
            title_kana=self.title_native,
            official_url=self.site_url,
            metadata=metadata,
        )


@dataclass
class RSSFeedItem:
    """
    RSS feed item data model.

    Attributes:
        title: Item title
        link: Item URL
        description: Item description
        published: Publication date
        guid: Unique identifier
        category: Item category
        author: Author information
    """

    title: str
    link: Optional[str] = None
    description: Optional[str] = None
    published: Optional[datetime] = None
    guid: Optional[str] = None
    category: Optional[str] = None
    author: Optional[str] = None

    def extract_work_info(self) -> Optional[Dict[str, Any]]:
        """
        Extract work and release information from RSS item.

        Returns:
            Dictionary with extracted work and release info, or None if extraction fails
        """
        if not self.title:
            return None

        # Common patterns for anime/manga titles in RSS feeds
        patterns = [
            r"「([^」]+)」",  # Japanese brackets
            r'"([^"]+)"',  # English quotes
            r"【([^】]+)】",  # Japanese square brackets
            r"\[([^\]]+)\]",  # Square brackets
        ]

        extracted_title = self.title
        for pattern in patterns:
            match = re.search(pattern, self.title)
            if match:
                extracted_title = match.group(1)
                break

        # Try to extract episode/volume number
        episode_patterns = [
            r"第(\d+)話",
            r"#(\d+)",
            r"Episode\s*(\d+)",
            r"ep\.?\s*(\d+)",
            r"(\d+)話",
        ]

        volume_patterns = [
            r"第(\d+)巻",
            r"Vol\.?\s*(\d+)",
            r"Volume\s*(\d+)",
            r"(\d+)巻",
        ]

        number = None
        release_type = None

        for pattern in episode_patterns:
            match = re.search(pattern, self.title, re.IGNORECASE)
            if match:
                number = match.group(1)
                release_type = ReleaseType.EPISODE
                break

        if not number:
            for pattern in volume_patterns:
                match = re.search(pattern, self.title, re.IGNORECASE)
                if match:
                    number = match.group(1)
                    release_type = ReleaseType.VOLUME
                    break

        return {
            "title": extracted_title.strip(),
            "number": number,
            "release_type": release_type,
            "release_date": self.published.date() if self.published else None,
            "source_url": self.link,
            "description": self.description,
        }


class DataValidator:
    """Data validation utilities."""

    @staticmethod
    def validate_work(work_data: Dict[str, Any]) -> List[str]:
        """
        Validate work data.

        Args:
            work_data: Work data dictionary

        Returns:
            List of validation error messages
        """
        errors = []

        if not work_data.get("title"):
            errors.append("Title is required")

        work_type = work_data.get("type") or work_data.get("work_type")
        if not work_type or work_type not in ["anime", "manga"]:
            errors.append("Valid work_type (anime/manga) is required")

        return errors

    @staticmethod
    def validate_release(release_data: Dict[str, Any]) -> List[str]:
        """
        Validate release data.

        Args:
            release_data: Release data dictionary

        Returns:
            List of validation error messages
        """
        errors = []

        if not release_data.get("work_id"):
            errors.append("work_id is required")

        release_type = release_data.get("release_type")
        if not release_type or release_type not in ["episode", "volume"]:
            errors.append("Valid release_type (episode/volume) is required")

        return errors


class DataNormalizer:
    """Data normalization utilities."""

    @staticmethod
    def normalize_title(title: str) -> str:
        """
        Normalize title for consistent storage and comparison.

        Args:
            title: Raw title string

        Returns:
            Normalized title
        """
        if not title:
            return ""

        # Remove extra whitespace
        title = re.sub(r"\s+", " ", title.strip())

        # Remove common prefixes/suffixes that don't affect identity
        prefixes_to_remove = [r"^\[.*?\]\s*", r"^【.*?】\s*"]
        for prefix in prefixes_to_remove:
            title = re.sub(prefix, "", title)

        return title.strip()

    @staticmethod
    def extract_season_info(title: str) -> Dict[str, Any]:
        """
        Extract season information from title.

        Args:
            title: Title string

        Returns:
            Dictionary with season info (season_number, is_sequel, etc.)
        """
        season_patterns = [
            (r"第(\d+)期", "season_number"),
            (r"Season\s*(\d+)", "season_number"),
            (r"(\d+)期", "season_number"),
            (r"続編|2nd|second", "is_sequel"),
            (r"完結編|final|最終", "is_final"),
        ]

        info = {}
        for pattern, key in season_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                if key == "season_number":
                    info[key] = int(match.group(1))
                else:
                    info[key] = True

        return info
