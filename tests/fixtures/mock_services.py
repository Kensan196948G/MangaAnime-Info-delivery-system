#!/usr/bin/env python3
"""
Advanced Mock Services for Comprehensive Testing
Provides realistic mock implementations for external services
"""

from typing import Any, Dict, List
import asyncio
import random
from datetime import datetime, timedelta
import secrets
import time
from unittest.mock import Mock, MagicMock


class MockAniListService:
    """Advanced AniList GraphQL API mock service"""

    def __init__(self):
        self.rate_limit_remaining = 90
        self.rate_limit_reset = datetime.now() + timedelta(minutes=1)
        self.request_count = 0
        self.latency_ms = 50  # Simulated network latency

    async def execute_query(self, query: str, variables: Dict = None) -> Dict[str, Any]:
        """Execute GraphQL query with realistic behavior"""
        # Simulate network latency
        await asyncio.sleep(self.latency_ms / 1000)

        # Rate limiting simulation
        self.request_count += 1
        self.rate_limit_remaining -= 1

        if self.rate_limit_remaining <= 0:
            if datetime.now() < self.rate_limit_reset:
                raise Exception("Rate limit exceeded. Try again later.")
            else:
                self.rate_limit_remaining = 90
                self.rate_limit_reset = datetime.now() + timedelta(minutes=1)

        # Query pattern matching
        if "Page" in query and "media" in query:
            return self._generate_media_page_response(variables)
        elif "streamingEpisodes" in query:
            return self._generate_streaming_episodes_response(variables)
        else:
            return {"data": None, "errors": [{"message": "Unknown query"}]}

    def _generate_media_page_response(self, variables: Dict = None) -> Dict[str, Any]:
        """Generate realistic media page response"""
        page = variables.get("page", 1) if variables else 1
        per_page = variables.get("perPage", 20) if variables else 20

        media_items = []
        for i in range(per_page):
            media_id = (page - 1) * per_page + i + 1
            media_items.append(
                {
                    "id": media_id,
                    "title": {
                        "romaji": f"Test Anime {media_id}",
                        "english": f"Test Anime {media_id} English",
                        "native": f"テストアニメ{media_id}",
                    },
                    "type": "ANIME",
                    "format": secrets.choice(["TV", "OVA", "MOVIE", "SPECIAL"]),
                    "status": secrets.choice(
                        ["RELEASING", "FINISHED", "NOT_YET_RELEASED"]
                    ),
                    "episodes": (
                        random.randint(12, 24)
                        if secrets.choice([True, False])
                        else None
                    ),
                    "genres": random.sample(
                        [
                            "Action",
                            "Adventure",
                            "Comedy",
                            "Drama",
                            "Fantasy",
                            "Romance",
                            "Sci-Fi",
                        ],
                        2,
                    ),
                    "tags": [{"name": "Shounen"}, {"name": "Action"}],
                    "description": f"This is test anime {media_id} description...",
                    "startDate": {
                        "year": random.randint(2020, 2024),
                        "month": random.randint(1, 12),
                        "day": random.randint(1, 28),
                    },
                    "nextAiringEpisode": (
                        {
                            "episode": random.randint(1, 50),
                            "airingAt": int(
                                (
                                    datetime.now()
                                    + timedelta(days=random.randint(0, 7))
                                ).timestamp()
                            ),
                        }
                        if secrets.choice([True, False])
                        else None
                    ),
                    "streamingEpisodes": (
                        [
                            {
                                "title": f"Episode {i+1}",
                                "url": f"https://example.com/anime/{media_id}/episode/{i+1}",
                            }
                            for i in range(3)
                        ]
                        if secrets.choice([True, False])
                        else []
                    ),
                    "siteUrl": f"https://anilist.co/anime/{media_id}",
                }
            )

        return {
            "data": {
                "Page": {
                    "pageInfo": {
                        "total": 1000,
                        "currentPage": page,
                        "lastPage": 50,
                        "hasNextPage": page < 50,
                        "perPage": per_page,
                    },
                    "media": media_items,
                }
            }
        }

    def _generate_streaming_episodes_response(
        self, variables: Dict = None
    ) -> Dict[str, Any]:
        """Generate streaming episodes response"""
        return {
            "data": {
                "media": {
                    "streamingEpisodes": [
                        {
                            "title": "Episode 1",
                            "thumbnail": "https://example.com/thumbnail1.jpg",
                            "url": "https://example.com/episode/1",
                        },
                        {
                            "title": "Episode 2",
                            "thumbnail": "https://example.com/thumbnail2.jpg",
                            "url": "https://example.com/episode/2",
                        },
                    ]
                }
            }
        }


class MockRSSFeedService:
    """Advanced RSS feed mock service"""

    def __init__(self):
        self.feeds = {
            "bookwalker": self._generate_bookwalker_feed(),
            "kindle": self._generate_kindle_feed(),
            "dmm": self._generate_dmm_feed(),
            "manga_kingdom": self._generate_manga_kingdom_feed(),
            "comic_seymour": self._generate_comic_seymour_feed(),
        }
        self.network_delay_ms = 100

    async def fetch_feed(self, feed_name: str) -> str:
        """Fetch RSS feed with network simulation"""
        await asyncio.sleep(self.network_delay_ms / 1000)

        if feed_name not in self.feeds:
            raise Exception(f"Feed {feed_name} not found")

        return self.feeds[feed_name]

    def _generate_bookwalker_feed(self) -> str:
        """Generate BookWalker RSS feed"""
        items = []
        manga_titles = [
            "進撃の巨人",
            "鬼滅の刃",
            "呪術廻戦",
            "チェンソーマン",
            "東京リベンジャーズ",
            "僕のヒーローアカデミア",
            "ワンピース",
            "ナルト",
            "ドラゴンボール",
            "ハンターXハンター",
        ]

        for i, title in enumerate(manga_titles[:5]):
            pub_date = datetime.now() + timedelta(days=i)
            items.append(
                """
                <item>
                    <title>{title} 第{20+i}巻</title>
                    <link>https://bookwalker.jp/manga/{title.replace(' ', '-')}-vol-{20+i}</link>
                    <description>待望の第{20+i}巻がついに発売！新たな展開が始まる。</description>
                    <pubDate>{pub_date.strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>
                    <category>manga</category>
                    <guid>https://bookwalker.jp/manga/{title}-{20+i}</guid>
                </item>
            """
            )

        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>BookWalker新刊情報</title>
                <link>https://bookwalker.jp/</link>
                <description>BookWalkerの最新マンガ情報</description>
                <language>ja-JP</language>
                <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')}</lastBuildDate>
                {''.join(items)}
            </channel>
        </rss>"""

    def _generate_kindle_feed(self) -> str:
        """Generate Kindle RSS feed"""
        items = []
        manga_titles = [
            "呪術廻戦",
            "チェンソーマン",
            "SPY×FAMILY",
            "推しの子",
            "怪獣8号",
        ]

        for i, title in enumerate(manga_titles):
            pub_date = datetime.now() + timedelta(days=i + 1)
            items.append(
                """
                <item>
                    <title>【Kindle版】{title} 第{15+i}巻</title>
                    <link>https://amazon.co.jp/kindle/{title.replace(' ', '-')}-vol-{15+i}</link>
                    <description>Kindle版で今すぐ読める！{title}の最新巻。</description>
                    <pubDate>{pub_date.strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>
                    <category>kindle</category>
                    <guid>https://amazon.co.jp/kindle/{title}-{15+i}</guid>
                </item>
            """
            )

        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Kindle マンガ新刊</title>
                <link>https://amazon.co.jp/kindle</link>
                <description>Kindleで読める最新マンガ情報</description>
                {''.join(items)}
            </channel>
        </rss>"""

    def _generate_dmm_feed(self) -> str:
        """Generate DMM Books RSS feed"""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>DMM BOOKS新刊</title>
                <item>
                    <title>転生したらスライムだった件 第20巻</title>
                    <link>https://book.dmm.com/detail/b123456789/</link>
                    <description>大人気異世界転生ファンタジーの最新巻！</description>
                    <pubDate>Wed, 15 Jan 2024 09:00:00 +0900</pubDate>
                </item>
            </channel>
        </rss>"""

    def _generate_manga_kingdom_feed(self) -> str:
        """Generate まんが王国 RSS feed"""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>まんが王国 新作情報</title>
                <item>
                    <title>約束のネバーランド 番外編</title>
                    <link>https://comic.k-manga.jp/title/12345</link>
                    <description>完結後の番外編がついに登場！</description>
                    <pubDate>Thu, 16 Jan 2024 10:00:00 +0900</pubDate>
                </item>
            </channel>
        </rss>"""

    def _generate_comic_seymour_feed(self) -> str:
        """Generate コミックシーモア RSS feed"""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>コミックシーモア 新刊情報</title>
                <item>
                    <title>五等分の花嫁 キャラクターブック</title>
                    <link>https://cmoa.jp/title/123456/</link>
                    <description>キャラクター設定資料集がついに発売！</description>
                    <pubDate>Fri, 17 Jan 2024 11:00:00 +0900</pubDate>
                </item>
            </channel>
        </rss>"""


class MockGoogleAPIService:
    """Advanced Google APIs mock service (Gmail + Calendar)"""

    def __init__(self):
        self.gmail_service = self._create_mock_gmail_service()
        self.calendar_service = self._create_mock_calendar_service()
        self.auth_service = self._create_mock_auth_service()

    def _create_mock_gmail_service(self) -> Mock:
        """Create mock Gmail service"""
        mock_service = MagicMock()

        # Mock message sending
        mock_send_response = {
            "id": f"msg_{int(time.time())}_{random.randint(1000, 9999)}",
            "threadId": f"thread_{int(time.time())}",
            "labelIds": ["SENT"],
        }
        mock_service.users().messages().send().execute.return_value = mock_send_response

        # Mock message retrieval
        mock_message = {
            "id": "msg_12345",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Email"},
                    {"name": "From", "value": "test@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                ],
                "body": {
                    "data": "VGVzdCBlbWFpbCBjb250ZW50"
                },  # Base64 encoded "Test email content"
            },
        }
        mock_service.users().messages().get().execute.return_value = mock_message

        return mock_service

    def _create_mock_calendar_service(self) -> Mock:
        """Create mock Calendar service"""
        mock_service = MagicMock()

        # Mock event creation
        mock_event_response = {
            "id": f"event_{int(time.time())}_{random.randint(1000, 9999)}",
            "htmlLink": f"https://calendar.google.com/event?eid=test_event_{int(time.time())}",
            "summary": "Test Event",
            "start": {"dateTime": "2024-01-15T18:00:00+09:00"},
            "end": {"dateTime": "2024-01-15T19:00:00+09:00"},
            "status": "confirmed",
        }
        mock_service.events().insert().execute.return_value = mock_event_response

        # Mock event listing
        mock_events_list = {"items": [mock_event_response], "nextPageToken": None}
        mock_service.events().list().execute.return_value = mock_events_list

        # Mock event update
        mock_service.events().update().execute.return_value = mock_event_response

        # Mock event deletion
        mock_service.events().delete().execute.return_value = {}

        return mock_service

    def _create_mock_auth_service(self) -> Mock:
        """Create mock OAuth2 service"""
        mock_service = Mock()

        # Mock token refresh
        mock_service.refresh_token.return_value = {
            "access_token": f"access_token_{int(time.time())}",
            "refresh_token": f"refresh_token_{int(time.time())}",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        return mock_service


class MockDatabaseService:
    """Advanced database mock service"""

    def __init__(self):
        self.data = {"works": [], "releases": []}
        self.next_id = 1
        self.latency_ms = 1  # Database latency simulation

    async def execute_query(
        self, query: str, params: tuple = None
    ) -> List[Dict[str, Any]]:
        """Execute database query with latency simulation"""
        await asyncio.sleep(self.latency_ms / 1000)

        if query.startswith("INSERT INTO works"):
            return self._handle_insert_work(params)
        elif query.startswith("INSERT INTO releases"):
            return self._handle_insert_release(params)
        elif query.startswith("SELECT") and "works" in query:
            return self._handle_select_works(query, params)
        elif query.startswith("SELECT") and "releases" in query:
            return self._handle_select_releases(query, params)
        else:
            return []

    def _handle_insert_work(self, params: tuple) -> List[Dict[str, Any]]:
        """Handle work insertion"""
        work = {
            "id": self.next_id,
            "title": params[0] if params else "Test Work",
            "title_kana": params[1] if len(params) > 1 else None,
            "title_en": params[2] if len(params) > 2 else None,
            "type": params[3] if len(params) > 3 else "anime",
            "official_url": params[4] if len(params) > 4 else None,
            "created_at": datetime.now().isoformat(),
        }
        self.data["works"].append(work)
        self.next_id += 1
        return [work]

    def _handle_insert_release(self, params: tuple) -> List[Dict[str, Any]]:
        """Handle release insertion"""
        release = {
            "id": self.next_id,
            "work_id": params[0] if params else 1,
            "release_type": params[1] if len(params) > 1 else "episode",
            "number": params[2] if len(params) > 2 else "1",
            "platform": params[3] if len(params) > 3 else "test",
            "release_date": (
                params[4] if len(params) > 4 else datetime.now().date().isoformat()
            ),
            "source": params[5] if len(params) > 5 else "test",
            "source_url": params[6] if len(params) > 6 else "https://test.com",
            "notified": 0,
            "created_at": datetime.now().isoformat(),
        }
        self.data["releases"].append(release)
        self.next_id += 1
        return [release]

    def _handle_select_works(self, query: str, params: tuple) -> List[Dict[str, Any]]:
        """Handle work selection"""
        return self.data["works"]

    def _handle_select_releases(
        self, query: str, params: tuple
    ) -> List[Dict[str, Any]]:
        """Handle release selection"""
        if "notified = 0" in query:
            return [r for r in self.data["releases"] if r["notified"] == 0]
        return self.data["releases"]


class PerformanceSimulator:
    """Performance testing simulator"""

    def __init__(self):
        self.base_latency_ms = 50
        self.load_factor = 1.0
        self.memory_usage_mb = 10

    def simulate_load(self, concurrent_requests: int):
        """Simulate system load"""
        self.load_factor = min(concurrent_requests / 10.0, 5.0)

    def get_response_time(self) -> float:
        """Get simulated response time"""
        return (self.base_latency_ms * self.load_factor + random.uniform(0, 50)) / 1000

    def get_memory_usage(self) -> float:
        """Get simulated memory usage"""
        return self.memory_usage_mb * self.load_factor + random.uniform(0, 20)

    def get_cpu_usage(self) -> float:
        """Get simulated CPU usage"""
        return min(25 * self.load_factor + random.uniform(0, 15), 95)


class MockDataFactory:
    """Factory for generating test data sets"""

    @staticmethod
    def create_large_dataset(size: int = 1000) -> Dict[str, Any]:
        """Create large dataset for performance testing"""
        return {
            "anime_data": [
                {
                    "id": i,
                    "title": f"Test Anime {i}",
                    "episodes": random.randint(12, 50),
                    "genres": random.sample(
                        ["Action", "Comedy", "Drama", "Romance"], 2
                    ),
                    "release_date": (
                        datetime.now() - timedelta(days=random.randint(0, 365))
                    ).isoformat(),
                }
                for i in range(1, size + 1)
            ],
            "manga_data": [
                {
                    "id": i,
                    "title": f"Test Manga {i}",
                    "volumes": random.randint(1, 30),
                    "genres": random.sample(
                        ["Action", "Romance", "Fantasy", "Horror"], 2
                    ),
                    "release_date": (
                        datetime.now() - timedelta(days=random.randint(0, 365))
                    ).isoformat(),
                }
                for i in range(1, size + 1)
            ],
        }

    @staticmethod
    def create_edge_case_dataset() -> Dict[str, Any]:
        """Create edge case test data"""
        return {
            "empty_titles": [
                {"title": "", "type": "anime"},
                {"title": None, "type": "manga"},
                {"title": " " * 1000, "type": "anime"},  # Very long title
            ],
            "special_characters": [
                {"title": "特殊文字テスト！@#$%^&*()", "type": "anime"},
                {"title": "Émojis 🎌🗾📺📚", "type": "manga"},
                {"title": "Unicode ñáéíóú ñÑ ü", "type": "anime"},
            ],
            "boundary_values": [
                {"episodes": 0, "type": "anime"},
                {"episodes": 99999, "type": "anime"},
                {"volumes": -1, "type": "manga"},
                {"rating": 11.0, "type": "anime"},  # Out of 10 scale
            ],
        }


# Factory function for easy mock creation
def create_mock_services() -> Dict[str, Any]:
    """Create all mock services"""
    return {
        "anilist": MockAniListService(),
        "rss": MockRSSFeedService(),
        "google": MockGoogleAPIService(),
        "database": MockDatabaseService(),
        "performance": PerformanceSimulator(),
        "data_factory": MockDataFactory(),
    }
