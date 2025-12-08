"""
型ヒント用のヘルパー定義
"""

from typing import Literal, Optional, TypedDict

# 作品タイプ
WorkType = Literal["anime", "manga"]

# リリースタイプ
ReleaseType = Literal["episode", "volume"]


class WorkDict(TypedDict, total=False):
    """作品情報の型定義"""

    id: int
    title: str
    title_kana: Optional[str]
    title_en: Optional[str]
    type: WorkType
    official_url: Optional[str]
    created_at: str


class ReleaseDict(TypedDict, total=False):
    """リリース情報の型定義"""

    id: int
    release_id: int
    work_id: int
    title: str
    work_type: WorkType
    release_type: ReleaseType
    number: Optional[str]
    platform: Optional[str]
    release_date: str
    source: Optional[str]
    source_url: Optional[str]
    notified: int
    calendar_synced: int
    created_at: str


class CalendarEventDict(TypedDict):
    """カレンダーイベント情報の型定義"""

    id: int
    release_id: int
    event_id: str
    calendar_id: str
    synced_at: str


class StatisticsDict(TypedDict):
    """統計情報の型定義"""

    total_works: int
    anime_works: int
    manga_works: int
    total_releases: int
    unnotified_releases: int
    unsynced_calendar_releases: int


class AniListMedia(TypedDict, total=False):
    """AniList APIのメディア情報"""

    id: int
    title: dict
    startDate: dict
    episodes: Optional[int]
    status: str
    siteUrl: str
    streamingEpisodes: list


class RSSItem(TypedDict, total=False):
    """RSSアイテムの型定義"""

    title: str
    link: str
    published: str
    description: Optional[str]
