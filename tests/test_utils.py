#!/usr/bin/env python3
"""
Test utilities and helper functions for the anime/manga notification system tests
"""

import os
import random
import secrets
import json
import tempfile
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock
import uuid
import faker


class DataFactory:
    """Factory class for generating test data with realistic content."""

    def __init__(self):
        """Initialize the test data factory."""
        self.fake = faker.Faker(["ja_JP", "en_US"])
        self.anime_titles = [
            "ワンピース",
            "進撃の巨人",
            "鬼滅の刃",
            "呪術廻戦",
            "僕のヒーローアカデミア",
            "ドラゴンボール超",
            "ナルト",
            "ブリーチ",
            "ハンターxハンター",
            "フェアリーテイル",
            "デスノート",
            "フルメタル・パニック",
            "コードギアス",
            "エヴァンゲリオン",
            "ガンダム",
            "七つの大罪",
            "約束のネバーランド",
            "Dr.STONE",
            "炎炎ノ消防隊",
            "チェンソーマン",
            "スパイファミリー",
            "東京リベンジャーズ",
            "五等分の花嫁",
            "かぐや様は告らせたい",
            "転生したらスライムだった件",
            "オーバーロード",
            "Re:ゼロから始める異世界生活",
        ]

        self.manga_titles = [
            "進撃の巨人",
            "鬼滅の刃",
            "呪術廻戦",
            "チェンソーマン",
            "東京リベンジャーズ",
            "五等分の花嫁",
            "かぐや様は告らせたい",
            "キングダム",
            "ワンパンマン",
            "モブサイコ100",
            "僕のヒーローアカデミア",
            "ハイキュー!!",
            "黒子のバスケ",
            "テニスの王子様",
            "スラムダンク",
            "ジョジョの奇妙な冒険",
            "ベルセルク",
            "バガボンド",
            "MONSTER",
            "20世紀少年",
            "デスノート",
            "約束のネバーランド",
            "Dr.STONE",
            "石器時代",
            "宇宙兄弟",
        ]

        self.platforms = {
            "anime": [
                "dアニメストア",
                "Netflix",
                "Amazon Prime Video",
                "Crunchyroll",
                "Hulu",
                "U-NEXT",
                "Funimation",
                "ABEMA",
                "ニコニコ動画",
                "YouTube",
            ],
            "manga": [
                "BookWalker",
                "Kindle",
                "楽天Kobo",
                "DMMブックス",
                "まんが王国",
                "コミックシーモア",
                "ebook japan",
                "LINEマンガ",
                "ピッコマ",
                "マンガBANG!",
            ],
        }

        self.sources = [
            "anilist",
            "rss_bookwalker",
            "rss_danime",
            "rss_netflix",
            "manual",
        ]

        self.genres = {
            "anime": [
                "Action",
                "Adventure",
                "Comedy",
                "Drama",
                "Fantasy",
                "Horror",
                "Mystery",
                "Romance",
                "Sci-Fi",
                "Slice of Life",
                "Sports",
                "Supernatural",
                "Thriller",
                "Mecha",
                "School",
                "Military",
                "Historical",
                "Music",
            ],
            "manga": [
                "Action",
                "Adventure",
                "Comedy",
                "Drama",
                "Fantasy",
                "Horror",
                "Mystery",
                "Romance",
                "Sci-Fi",
                "Slice of Life",
                "Sports",
                "Supernatural",
                "Seinen",
                "Shoujo",
                "Shounen",
                "Josei",
                "Yaoi",
                "Yuri",
            ],
        }

    def generate_work_data(
        self, work_type: str = None, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Generate realistic work data."""
        works = []

        for _ in range(count):
            if work_type is None:
                work_type = secrets.choice(["anime", "manga"])

            # Choose title from appropriate list
            title_pool = (
                self.anime_titles if work_type == "anime" else self.manga_titles
            )
            base_title = secrets.choice(title_pool)

            # Generate variations
            title = base_title
            title_kana = self._generate_kana_reading(base_title)
            title_en = self._generate_english_title(base_title)

            # Add some variety with suffixes for sequels/seasons
            if secrets.SystemRandom().random() < 0.3:
                season_num = secrets.randbelow(2, 4)
                title += f" 第{season_num}期" if work_type == "anime" else " 続編"
                title_en += (
                    f" Season {season_num}" if work_type == "anime" else " Sequel"
                )

            work = {
                "title": title,
                "title_kana": title_kana,
                "title_en": title_en,
                "type": work_type,
                "official_url": f"https://example.com/{work_type}/{uuid.uuid4().hex[:8]}",
                "description": self._generate_description(work_type),
                "genres": random.sample(
                    self.genres[work_type], k=secrets.randbelow(2, 5)
                ),
                "image_url": f"https://example.com/images/{uuid.uuid4().hex[:8]}.jpg",
                "created_at": self.fake.date_time_between(
                    start_date="-2y", end_date="now"
                ).isoformat(),
            }

            works.append(work)

        return works

    def generate_release_data(
        self, work_id: int, work_type: str, count: int = 1
    ) -> List[Dict[str, Any]]:
        """Generate realistic release data for a given work."""
        releases = []

        release_type = "episode" if work_type == "anime" else "volume"
        platform_pool = self.platforms[work_type]

        base_date = self.fake.date_between(start_date="-30d", end_date="+30d")

        for i in range(count):
            # Calculate release date (weekly for anime episodes, monthly for manga volumes)
            if work_type == "anime":
                release_date = base_date + timedelta(weeks=i)
            else:
                release_date = base_date + timedelta(days=30 * i)

            release = {
                "work_id": work_id,
                "release_type": release_type,
                "number": str(i + 1),
                "platform": secrets.choice(platform_pool),
                "release_date": release_date.isoformat(),
                "source": secrets.choice(self.sources),
                "source_url": f"https://example.com/releases/{uuid.uuid4().hex[:8]}",
                "notified": secrets.choice([0, 0, 0, 1]),  # 75% unnotified
                "created_at": self.fake.date_time_between(
                    start_date="-1y", end_date="now"
                ).isoformat(),
                "description": self._generate_release_description(work_type, i + 1),
            }

            releases.append(release)

        return releases

    def generate_anilist_response(self, media_count: int = 5) -> Dict[str, Any]:
        """Generate realistic AniList GraphQL API response."""
        media_list = []

        for _ in range(media_count):
            work = self.generate_work_data("anime", 1)[0]

            # Convert to AniList format
            anilist_media = {
                "id": secrets.randbelow(1000, 99999),
                "title": {
                    "romaji": work["title"],
                    "english": work["title_en"],
                    "native": work["title"],
                },
                "description": work["description"],
                "genres": work["genres"],
                "tags": [
                    {
                        "name": genre,
                        "description": f"{genre} genre",
                        "isMediaSpoiler": False,
                    }
                    for genre in work["genres"][:3]
                ],
                "status": secrets.choice(["RELEASING", "FINISHED", "NOT_YET_RELEASED"]),
                "startDate": {
                    "year": secrets.randbelow(2020, 2024),
                    "month": secrets.randbelow(1, 12),
                    "day": secrets.randbelow(1, 28),
                },
                "endDate": (
                    None
                    if secrets.SystemRandom().random() < 0.5
                    else {
                        "year": secrets.randbelow(2024, 2025),
                        "month": secrets.randbelow(1, 12),
                        "day": secrets.randbelow(1, 28),
                    }
                ),
                "coverImage": {
                    "large": work["image_url"],
                    "medium": work["image_url"].replace(".jpg", "_medium.jpg"),
                },
                "bannerImage": work["image_url"].replace(".jpg", "_banner.jpg"),
                "siteUrl": work["official_url"],
                "streamingEpisodes": self._generate_streaming_episodes(),
                "episodes": secrets.randbelow(12, 26),
                "nextAiringEpisode": (
                    self._generate_next_airing_episode()
                    if secrets.SystemRandom().random() < 0.7
                    else None
                ),
            }

            media_list.append(anilist_media)

        return {
            "data": {
                "Page": {
                    "pageInfo": {
                        "total": media_count,
                        "currentPage": 1,
                        "lastPage": 1,
                        "hasNextPage": False,
                    },
                    "media": media_list,
                }
            }
        }

    def generate_rss_feed_data(
        self, entry_count: int = 10, feed_type: str = "manga"
    ) -> str:
        """Generate realistic RSS feed XML data."""
        entries = []

        for i in range(entry_count):
            if feed_type == "manga":
                work = secrets.choice(self.manga_titles)
                volume_num = secrets.randbelow(1, 30)
                title = f"{work} 第{volume_num}巻"
                description = f"{work}の第{volume_num}巻が発売されました！"
                category = "manga"
            else:
                work = secrets.choice(self.anime_titles)
                episode_num = secrets.randbelow(1, 26)
                title = f"{work} 第{episode_num}話"
                description = f"{work}の第{episode_num}話が配信開始！"
                category = "anime"

            pub_date = (
                datetime.now() - timedelta(days=secrets.randbelow(0, 30))
            ).strftime("%a, %d %b %Y %H:%M:%S %z")
            link = f"https://example.com/{feed_type}/{uuid.uuid4().hex[:8]}"

            entries.append(
                """
        <item>
            <title>{title}</title>
            <link>{link}</link>
            <description>{description}</description>
            <pubDate>{pub_date}</pubDate>
            <category>{category}</category>
            <guid>{uuid.uuid4()}</guid>
        </item>
            """
            )

        feed_xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>Test {feed_type.title()} RSS Feed</title>
        <description>Test RSS feed for {feed_type} releases</description>
        <link>https://example.com/{feed_type}/rss</link>
        <atom:link href="https://example.com/{feed_type}/rss" rel="sel" type="application/rss+xml" />
        <language>ja</language>
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')}</lastBuildDate>
        {''.join(entries)}
    </channel>
</rss>"""

        return feed_xml

    def generate_config_data(self, environment: str = "test") -> Dict[str, Any]:
        """Generate realistic configuration data."""
        return {
            "system": {
                "name": f"MangaAnime情報配信システム ({environment})",
                "environment": environment,
                "timezone": "Asia/Tokyo",
                "log_level": "DEBUG" if environment == "test" else "INFO",
            },
            "database": {
                "path": ":memory:" if environment == "test" else "./db.sqlite3",
                "backup_enabled": environment != "test",
                "backup_interval_hours": 24,
            },
            "apis": {
                "anilist": {
                    "graphql_url": "https://graphql.anilist.co",
                    "rate_limit": {"requests_per_minute": 90, "retry_delay_seconds": 1},
                    "timeout_seconds": 30,
                },
                "rss_feeds": {
                    "enabled_feeds": self._generate_rss_feed_config(),
                    "timeout_seconds": 20,
                    "user_agent": "MangaAnimeNotifier-Test/1.0",
                },
            },
            "filtering": {
                "ng_keywords": ["エロ", "R18", "成人向け", "BL", "百合", "アダルト"],
                "ng_genres": ["Hentai", "Ecchi"],
                "exclude_tags": ["Adult Cast", "Mature Themes", "Sexual Content"],
            },
            "notification": {
                "email": {
                    "enabled": environment != "test",
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "sender_email": "test@example.com",
                    "recipient_email": "user@example.com",
                },
                "calendar": {
                    "enabled": environment != "test",
                    "calendar_id": "primary",
                    "timezone": "Asia/Tokyo",
                },
            },
            "scheduling": {
                "collection_interval_hours": 8,
                "cleanup_interval_days": 90,
                "notification_batch_size": 50,
            },
        }

    def _generate_kana_reading(self, title: str) -> str:
        """Generate a plausible kana reading for a title."""
        # Simplified kana generation - in reality this would be much more complex
        kana_map = {
            "ワンピース": "わんぴーす",
            "進撃の巨人": "しんげきのきょじん",
            "鬼滅の刃": "きめつのやいば",
            "呪術廻戦": "じゅじつかいせん",
            "僕のヒーローアカデミア": "ぼくのひーろーあかでみあ",
        }

        # Remove season suffixes for lookup
        base_title = title.split(" 第")[0]
        return kana_map.get(base_title, "てすとたいとる")

    def _generate_english_title(self, title: str) -> str:
        """Generate a plausible English title."""
        english_map = {
            "ワンピース": "One Piece",
            "進撃の巨人": "Attack on Titan",
            "鬼滅の刃": "Demon Slayer",
            "呪術廻戦": "Jujutsu Kaisen",
            "僕のヒーローアカデミア": "My Hero Academia",
            "ドラゴンボール超": "Dragon Ball Super",
            "ナルト": "Naruto",
            "ブリーチ": "Bleach",
            "ハンターxハンター": "Hunter x Hunter",
            "フェアリーテイル": "Fairy Tail",
        }

        base_title = title.split(" 第")[0]
        return english_map.get(base_title, f"Test Title {uuid.uuid4().hex[:4].upper()}")

    def _generate_description(self, work_type: str) -> str:
        """Generate a plausible description."""
        if work_type == "anime":
            templates = [
                "主人公が冒険の旅に出る物語。仲間たちと共に困難に立ち向かう。",
                "学園を舞台にした青春ストーリー。友情と成長を描く。",
                "異世界に転生した主人公の活躍を描くファンタジー作品。",
                "現代を舞台にした超能力バトルアクション。",
                "日常系コメディ。ほのぼのとした雰囲気が魅力。",
            ]
        else:
            templates = [
                "人気マンガの最新巻。ストーリーがますます面白くなる。",
                "長期連載マンガの完結編。感動の最終回。",
                "新進気鋭の作者による話題作。注目の新シリーズ。",
                "アニメ化決定で話題沸騰中の作品。",
                "読者投票で人気急上昇中のマンガシリーズ。",
            ]

        return secrets.choice(templates)

    def _generate_release_description(self, work_type: str, number: int) -> str:
        """Generate release-specific description."""
        if work_type == "anime":
            return f"第{number}話の配信が開始されました。今回のエピソードは見逃せない内容です！"
        else:
            return f"第{number}巻が発売されました。ストーリーの展開に注目です。"

    def _generate_streaming_episodes(self) -> List[Dict[str, Any]]:
        """Generate streaming episodes data for AniList response."""
        episodes = []
        platforms = ["Netflix", "Crunchyroll", "Funimation"]

        for i in range(secrets.randbelow(0, 3)):
            episode = {
                "title": f"Episode {i + 1}",
                "thumbnail": f"https://example.com/thumbnails/{uuid.uuid4().hex[:8]}.jpg",
                "url": f"https://example.com/watch/{uuid.uuid4().hex[:8]}",
                "site": secrets.choice(platforms),
            }
            episodes.append(episode)

        return episodes

    def _generate_next_airing_episode(self) -> Dict[str, Any]:
        """Generate next airing episode data."""
        next_date = datetime.now() + timedelta(days=secrets.randbelow(0, 7))
        return {
            "episode": secrets.randbelow(1, 26),
            "airingAt": int(next_date.timestamp()),
        }

    def _generate_rss_feed_config(self) -> List[Dict[str, Any]]:
        """Generate RSS feed configuration."""
        return [
            {
                "name": "BookWalker",
                "url": "https://bookwalker.jp/rss/manga",
                "category": "manga",
                "enabled": True,
            },
            {
                "name": "dアニメストア",
                "url": "https://anime.dmkt-sp.jp/animestore/CF/rss/",
                "category": "anime",
                "enabled": True,
            },
            {
                "name": "Netflix Anime",
                "url": "https://example.com/netflix/anime/rss",
                "category": "anime",
                "enabled": False,
            },
            {
                "name": "楽天Kobo",
                "url": "https://kobo.rakuten.co.jp/rss/manga",
                "category": "manga",
                "enabled": True,
            },
        ]


class MockServiceFactory:
    """Factory for creating mock services and API responses."""

    @staticmethod
    def create_mock_gmail_service() -> Mock:
        """Create a mock Gmail API service."""
        mock_service = Mock()

        # Mock successful email send
        mock_service.users().messages().send.return_value.execute.return_value = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "threadId": f"thread_{uuid.uuid4().hex[:8]}",
            "labelIds": ["SENT"],
        }

        # Mock message retrieval
        mock_service.users().messages().get.return_value.execute.return_value = {
            "id": "test_message",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Email"},
                    {"name": "From", "value": "test@example.com"},
                    {"name": "To", "value": "user@example.com"},
                ]
            },
            "labelIds": ["SENT"],
        }

        return mock_service

    @staticmethod
    def create_mock_calendar_service() -> Mock:
        """Create a mock Google Calendar API service."""
        mock_service = Mock()

        # Mock successful event creation
        mock_service.events().insert.return_value.execute.return_value = {
            "id": f"event_{uuid.uuid4().hex[:8]}",
            "htmlLink": f"https://calendar.google.com/event?eid={uuid.uuid4().hex[:8]}",
            "summary": "Test Event",
            "start": {"date": "2024-01-15", "timeZone": "Asia/Tokyo"},
            "end": {"date": "2024-01-15", "timeZone": "Asia/Tokyo"},
            "status": "confirmed",
        }

        # Mock event retrieval
        mock_service.events().get.return_value.execute.return_value = {
            "id": "test_event",
            "summary": "Test Event",
            "status": "confirmed",
        }

        # Mock event listing
        mock_service.events().list.return_value.execute.return_value = {
            "items": [
                {
                    "id": f"event_{i}",
                    "summary": f"Test Event {i}",
                    "start": {"date": "2024-01-15"},
                    "end": {"date": "2024-01-15"},
                }
                for i in range(3)
            ]
        }

        return mock_service

    @staticmethod
    def create_mock_anilist_client() -> AsyncMock:
        """Create a mock AniList API client."""
        mock_client = AsyncMock()

        # Mock successful API responses
        mock_client.search_anime.return_value = DataFactory().generate_work_data(
            "anime", 5
        )
        mock_client.get_anime_by_id.return_value = DataFactory().generate_work_data(
            "anime", 1
        )[0]
        mock_client.get_current_season_anime.return_value = (
            DataFactory().generate_work_data("anime", 10)
        )
        mock_client.get_upcoming_releases.return_value = [
            {
                "anilist_id": i,
                "title": f"Test Anime {i}",
                "episode_number": secrets.randbelow(1, 26),
                "airing_at": int((datetime.now() + timedelta(days=i)).timestamp()),
                "airing_date": (datetime.now() + timedelta(days=i)).date(),
                "site_url": f"https://anilist.co/anime/{i}",
                "streaming_platforms": ["Netflix", "Crunchyroll"],
            }
            for i in range(5)
        ]

        return mock_client

    @staticmethod
    def create_mock_requests_session() -> Mock:
        """Create a mock requests session for HTTP calls."""
        mock_session = Mock()

        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/xml"}
        mock_response.content = DataFactory().generate_rss_feed_data().encode("utf-8")
        mock_response.text = DataFactory().generate_rss_feed_data()
        mock_response.raise_for_status.return_value = None

        mock_session.get.return_value = mock_response
        mock_session.post.return_value = mock_response

        return mock_session


class DatabaseTestHelper:
    """Helper class for database-related test operations."""

    @staticmethod
    def setup_test_database(db_path: str) -> None:
        """Setup a test database with schema."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.executescript(
            """
            CREATE TABLE works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                title_kana TEXT,
                title_en TEXT,
                type TEXT CHECK(type IN ('anime','manga')),
                official_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE releases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_id INTEGER NOT NULL,
                release_type TEXT CHECK(release_type IN ('episode','volume')),
                number TEXT,
                platform TEXT,
                release_date DATE,
                source TEXT,
                source_url TEXT,
                notified INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (work_id) REFERENCES works (id) ON DELETE CASCADE,
                UNIQUE(work_id, release_type, number, platform, release_date)
            );

            -- Indexes for performance
            CREATE INDEX idx_works_title ON works(title);
            CREATE INDEX idx_works_type ON works(type);
            CREATE INDEX idx_releases_work_id ON releases(work_id);
            CREATE INDEX idx_releases_date ON releases(release_date);
            CREATE INDEX idx_releases_notified ON releases(notified);
        """
        )

        conn.commit()
        conn.close()

    @staticmethod
    def populate_test_data(
        db_path: str, work_count: int = 10, releases_per_work: int = 3
    ) -> None:
        """Populate test database with realistic data."""
        factory = DataFactory()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Generate and insert works
        works = factory.generate_work_data(count=work_count)

        for work in works:
            cursor.execute(
                """
                INSERT INTO works (title, title_kana, title_en, type, official_url)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    work["title"],
                    work["title_kana"],
                    work["title_en"],
                    work["type"],
                    work["official_url"],
                ),
            )

            work_id = cursor.lastrowid

            # Generate and insert releases for this work
            releases = factory.generate_release_data(
                work_id, work["type"], releases_per_work
            )

            for release in releases:
                cursor.execute(
                    """
                    INSERT INTO releases (work_id, release_type, number, platform, release_date, source, source_url, notified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        release["work_id"],
                        release["release_type"],
                        release["number"],
                        release["platform"],
                        release["release_date"],
                        release["source"],
                        release["source_url"],
                        release["notified"],
                    ),
                )

        conn.commit()
        conn.close()

    @staticmethod
    def get_test_statistics(db_path: str) -> Dict[str, Any]:
        """Get statistics about test database content."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        stats = {}

        # Count works by type
        cursor.execute("SELECT type, COUNT(*) FROM works GROUP BY type")
        work_counts = dict(cursor.fetchall())
        stats["works"] = work_counts

        # Count releases by type and notification status
        cursor.execute(
            """
            SELECT r.release_type, r.notified, COUNT(*)
            FROM releases r
            GROUP BY r.release_type, r.notified
        """
        )

        release_stats = {}
        for release_type, notified, count in cursor.fetchall():
            if release_type not in release_stats:
                release_stats[release_type] = {}
            release_stats[release_type][
                f"{'notified' if notified else 'unnotified'}"
            ] = count

        stats["releases"] = release_stats

        # Platform distribution
        cursor.execute("SELECT platform, COUNT(*) FROM releases GROUP BY platform")
        platform_counts = dict(cursor.fetchall())
        stats["platforms"] = platform_counts

        conn.close()
        return stats

    @staticmethod
    def cleanup_test_data(db_path: str) -> None:
        """Clean up test database data."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM releases")
        cursor.execute("DELETE FROM works")

        conn.commit()
        conn.close()


class AssertionHelpers:
    """Helper functions for common test assertions."""

    @staticmethod
    def assert_valid_work_data(work_data: Dict[str, Any]) -> None:
        """Assert that work data has valid structure and content."""
        required_fields = ["title", "type"]
        for field in required_fields:
            assert field in work_data, f"Missing required field: {field}"

        assert work_data["type"] in [
            "anime",
            "manga",
        ], f"Invalid work type: {work_data['type']}"
        assert len(work_data["title"]) > 0, "Title cannot be empty"

        if "official_url" in work_data:
            assert work_data["official_url"].startswith("http"), "Invalid URL format"

    @staticmethod
    def assert_valid_release_data(release_data: Dict[str, Any]) -> None:
        """Assert that release data has valid structure and content."""
        required_fields = ["work_id", "release_type"]
        for field in required_fields:
            assert field in release_data, f"Missing required field: {field}"

        assert release_data["release_type"] in [
            "episode",
            "volume",
        ], f"Invalid release type: {release_data['release_type']}"
        assert isinstance(release_data["work_id"], int), "work_id must be integer"

        if "release_date" in release_data:
            # Basic date format validation
            date_str = release_data["release_date"]
            assert len(date_str) == 10, "Date should be in YYYY-MM-DD format"
            assert date_str.count("-") == 2, "Date should have two hyphens"

    @staticmethod
    def assert_valid_email_content(email_data: Dict[str, Any]) -> None:
        """Assert that email content is valid."""
        required_fields = ["subject", "body"]
        for field in required_fields:
            assert field in email_data, f"Missing required email field: {field}"

        assert len(email_data["subject"]) > 0, "Email subject cannot be empty"
        assert len(email_data["body"]) > 0, "Email body cannot be empty"

        # Check for Japanese content (basic validation)
        import re

        has_japanese = bool(
            re.search(
                r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]",
                email_data["subject"] + email_data["body"],
            )
        )
        assert has_japanese, "Email should contain Japanese content"

    @staticmethod
    def assert_valid_calendar_event(event_data: Dict[str, Any]) -> None:
        """Assert that calendar event data is valid."""
        required_fields = ["summary", "start", "end"]
        for field in required_fields:
            assert field in event_data, f"Missing required calendar field: {field}"

        assert len(event_data["summary"]) > 0, "Event summary cannot be empty"

        # Validate date/time fields
        start = event_data["start"]
        end = event_data["end"]

        assert (
            "date" in start or "dateTime" in start
        ), "Start must have date or dateTime"
        assert "date" in end or "dateTime" in end, "End must have date or dateTime"

        if "timeZone" in start:
            assert (
                "timeZone" in end
            ), "Both start and end should have timeZone if one does"

    @staticmethod
    def assert_performance_metrics(
        metrics: Dict[str, float], thresholds: Dict[str, float]
    ) -> None:
        """Assert that performance metrics meet specified thresholds."""
        for metric_name, actual_value in metrics.items():
            if metric_name in thresholds:
                threshold = thresholds[metric_name]
                assert (
                    actual_value <= threshold
                ), f"{metric_name}: {actual_value} exceeds threshold {threshold}"

    @staticmethod
    def assert_rate_limit_compliance(
        request_times: List[float], max_requests_per_minute: int
    ) -> None:
        """Assert that request timing complies with rate limits."""
        if len(request_times) < 2:
            return  # Not enough requests to validate rate limiting

        # Check intervals between requests
        min_interval = 60.0 / max_requests_per_minute

        for i in range(1, len(request_times)):
            interval = request_times[i] - request_times[i - 1]
            assert (
                interval >= min_interval - 0.1
            ), f"Request interval {interval:.2f}s violates rate limit"

        # Check overall rate
        if len(request_times) >= max_requests_per_minute:
            window_start = request_times[-max_requests_per_minute]
            window_end = request_times[-1]
            window_duration = window_end - window_start

            assert (
                window_duration >= 60.0 - 1.0
            ), f"Too many requests in 60s window: {max_requests_per_minute} requests in {window_duration:.1f}s"


class EnvironmentManager:
    """Manager for test environment setup and cleanup."""

    def __init__(self):
        """Initialize the test environment manager."""
        self.temp_files = []
        self.temp_databases = []
        self.mock_patches = []

    def create_temp_database(self, populate: bool = True, work_count: int = 10) -> str:
        """Create a temporary database for testing."""
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_path = temp_file.name
        temp_file.close()

        self.temp_databases.append(db_path)

        # Setup schema
        DatabaseTestHelper.setup_test_database(db_path)

        # Populate with test data if requested
        if populate:
            DatabaseTestHelper.populate_test_data(db_path, work_count)

        return db_path

    def create_temp_config_file(self, config_data: Dict[str, Any] = None) -> str:
        """Create a temporary configuration file."""
        if config_data is None:
            config_data = DataFactory().generate_config_data()

        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump(config_data, temp_file, indent=2, ensure_ascii=False)
        temp_file.close()

        self.temp_files.append(temp_file.name)
        return temp_file.name

    def cleanup(self):
        """Clean up all temporary resources."""
        # Remove temp files
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except OSError:
                pass

        # Remove temp databases
        for db_path in self.temp_databases:
            try:
                if os.path.exists(db_path):
                    os.unlink(db_path)
            except OSError:
                pass

        # Stop all mock patches
        for patch in self.mock_patches:
            try:
                patch.stop()
            except RuntimeError:
                pass

        self.temp_files.clear()
        self.temp_databases.clear()
        self.mock_patches.clear()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
