#!/usr/bin/env python3
"""
pytest configuration and shared fixtures for the Manga/Anime info delivery system tests
"""

import pytest
import sqlite3
import tempfile
import os
import json
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
import asyncio
from typing import Dict, Any, List, Generator

# Test configuration
TEST_CONFIG = {
    "system": {
        "name": "Test_MangaAnime情報配信システム",
        "environment": "test",
        "timezone": "Asia/Tokyo",
        "log_level": "DEBUG"
    },
    "database": {
        "path": ":memory:",  # In-memory database for tests
        "backup_enabled": False
    },
    "apis": {
        "anilist": {
            "graphql_url": "https://graphql.anilist.co",
            "rate_limit": {"requests_per_minute": 90},
            "timeout_seconds": 5
        },
        "rss_feeds": {
            "timeout_seconds": 5,
            "user_agent": "TestAgent/1.0"
        }
    },
    "filtering": {
        "ng_keywords": ["エロ", "R18", "成人向け", "BL"],
        "ng_genres": ["Hentai", "Ecchi"]
    },
    "notification": {
        "email": {"enabled": False},
        "calendar": {"enabled": False}
    }
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Provide test configuration."""
    return TEST_CONFIG.copy()

@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
        db_path = temp_file.name
    
    try:
        # Initialize test database structure
        conn = sqlite3.connect(db_path)
        conn.executescript("""
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
                UNIQUE(work_id, release_type, number, platform, release_date)
            );
        """)
        conn.commit()
        conn.close()
        
        yield db_path
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

@pytest.fixture
def mock_anilist_response():
    """Mock AniList GraphQL API responses."""
    return {
        "data": {
            "Page": {
                "media": [
                    {
                        "id": 21,
                        "title": {
                            "romaji": "One Piece",
                            "english": "One Piece",
                            "native": "ワンピース"
                        },
                        "type": "ANIME",
                        "format": "TV",
                        "status": "RELEASING",
                        "episodes": None,
                        "genres": ["Action", "Adventure", "Comedy"],
                        "tags": [{"name": "Pirates"}, {"name": "Shounen"}],
                        "description": "Gol D. Roger was known as the Pirate King...",
                        "startDate": {"year": 1999, "month": 10, "day": 20},
                        "nextAiringEpisode": {
                            "episode": 1050,
                            "airingAt": 1640995200
                        },
                        "streamingEpisodes": [
                            {"title": "Episode 1049", "url": "https://example.com/1049"}
                        ],
                        "siteUrl": "https://anilist.co/anime/21"
                    }
                ]
            }
        }
    }

@pytest.fixture
def mock_rss_feed_data():
    """Mock RSS feed data for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test Manga RSS Feed</title>
            <description>Test manga releases</description>
            <item>
                <title>進撃の巨人 第34巻</title>
                <link>https://example.com/manga/attack-titan-34</link>
                <description>待望の最終巻がついに発売！</description>
                <pubDate>Wed, 09 Jun 2021 00:00:00 +0900</pubDate>
                <category>manga</category>
            </item>
            <item>
                <title>鬼滅の刃 第23巻</title>
                <link>https://example.com/manga/demon-slayer-23</link>
                <description>完結記念特装版</description>
                <pubDate>Fri, 04 Dec 2020 00:00:00 +0900</pubDate>
                <category>manga</category>
            </item>
        </channel>
    </rss>"""

@pytest.fixture
def mock_gmail_service():
    """Mock Gmail API service for testing."""
    mock_service = MagicMock()
    mock_service.users().messages().send().execute.return_value = {
        'id': 'test_message_id',
        'threadId': 'test_thread_id'
    }
    return mock_service

@pytest.fixture
def mock_calendar_service():
    """Mock Google Calendar API service for testing."""
    mock_service = MagicMock()
    mock_service.events().insert().execute.return_value = {
        'id': 'test_event_id',
        'htmlLink': 'https://calendar.google.com/event?eid=test_event_id'
    }
    return mock_service

@pytest.fixture
def sample_work_data():
    """Sample work data for testing."""
    return [
        {
            'id': 1,
            'title': 'ワンピース',
            'title_kana': 'わんぴーす',
            'title_en': 'One Piece',
            'type': 'anime',
            'official_url': 'https://one-piece.com'
        },
        {
            'id': 2,
            'title': '進撃の巨人',
            'title_kana': 'しんげきのきょじん',
            'title_en': 'Attack on Titan',
            'type': 'manga',
            'official_url': 'https://shingeki.tv'
        }
    ]

@pytest.fixture
def sample_release_data():
    """Sample release data for testing."""
    return [
        {
            'work_id': 1,
            'release_type': 'episode',
            'number': '1050',
            'platform': 'dアニメストア',
            'release_date': '2024-01-15',
            'source': 'anilist',
            'source_url': 'https://anilist.co/anime/21',
            'notified': 0
        },
        {
            'work_id': 2,
            'release_type': 'volume',
            'number': '34',
            'platform': 'BookWalker',
            'release_date': '2024-01-20',
            'source': 'rss',
            'source_url': 'https://bookwalker.jp/manga/attack-titan-34',
            'notified': 0
        }
    ]

@pytest.fixture
def mock_requests_session():
    """Mock requests session for HTTP testing."""
    mock_session = Mock()
    
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test_response"}
    mock_response.text = "test response text"
    mock_response.raise_for_status.return_value = None
    
    mock_session.get.return_value = mock_response
    mock_session.post.return_value = mock_response
    
    return mock_session

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables and configurations."""
    # Set test mode environment variable
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    # Mock sensitive credentials for testing
    monkeypatch.setenv("GOOGLE_CREDENTIALS_PATH", "/fake/path/credentials.json")
    monkeypatch.setenv("GOOGLE_TOKEN_PATH", "/fake/path/token.json")

class TestDataGenerator:
    """Test data generator utility class."""
    
    @staticmethod
    def generate_anime_data(count: int = 5) -> List[Dict[str, Any]]:
        """Generate test anime data."""
        anime_titles = [
            "ワンピース", "進撃の巨人", "鬼滅の刃", "呪術廻戦", "僕のヒーローアカデミア",
            "ドラゴンボール超", "ナルト", "ブリーチ", "ハンターxハンター", "フェアリーテイル"
        ]
        
        results = []
        for i in range(min(count, len(anime_titles))):
            results.append({
                "id": i + 1,
                "title": {
                    "romaji": anime_titles[i],
                    "english": f"Test Anime {i+1}",
                    "native": anime_titles[i]
                },
                "type": "ANIME",
                "status": "RELEASING",
                "episodes": 24,
                "genres": ["Action", "Adventure"],
                "tags": [{"name": "Shounen"}],
                "nextAiringEpisode": {
                    "episode": i + 100,
                    "airingAt": int((datetime.now() + timedelta(days=i)).timestamp())
                }
            })
        
        return results
    
    @staticmethod
    def generate_manga_data(count: int = 5) -> List[str]:
        """Generate test manga RSS data."""
        manga_titles = [
            "進撃の巨人", "鬼滅の刃", "呪術廻戦", "チェンソーマン", "東京リベンジャーズ"
        ]
        
        items = []
        for i, title in enumerate(manga_titles[:count]):
            items.append(f"""
                <item>
                    <title>{title} 第{i+20}巻</title>
                    <link>https://example.com/manga/{i+1}</link>
                    <description>第{i+20}巻発売</description>
                    <pubDate>{(datetime.now() + timedelta(days=i)).strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>
                </item>
            """)
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Manga Feed</title>
                {''.join(items)}
            </channel>
        </rss>"""

@pytest.fixture
def test_data_generator():
    """Provide test data generator instance."""
    return TestDataGenerator()

# Performance testing fixtures
@pytest.fixture
def performance_test_config():
    """Configuration for performance testing."""
    return {
        "concurrent_requests": 10,
        "request_timeout": 30,
        "max_response_time": 5.0,  # seconds
        "memory_limit_mb": 100,
        "cpu_usage_limit": 80.0  # percentage
    }

@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        "system": {
            "name": "MangaAnime情報配信システム",
            "environment": "production",
            "timezone": "Asia/Tokyo",
            "log_level": "INFO"
        },
        "database": {
            "path": "db.sqlite3",
            "backup_enabled": True
        },
        "apis": {
            "anilist": {
                "graphql_url": "https://graphql.anilist.co",
                "rate_limit": {"requests_per_minute": 90},
                "timeout_seconds": 30
            },
            "rss_feeds": {
                "timeout_seconds": 30,
                "user_agent": "MangaAnime-Info-System/1.0"
            }
        },
        "email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@gmail.com",
            "use_tls": True
        },
        "notifications": {
            "enabled": True,
            "email_enabled": True,
            "calendar_enabled": True
        },
        "error_notifications": {
            "enabled": True,
            "recipient": "error@example.com"
        },
        "filtering": {
            "ng_keywords": ["エロ", "R18", "成人向け"],
            "ng_genres": ["Hentai", "Ecchi"]
        }
    }

@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_data = {
        "system": {
            "name": "Test System",
            "environment": "test"
        },
        "database": {
            "path": ":memory:"
        }
    }
    
    config_file = tmp_path / "test_config.json"
    config_file.write_text(json.dumps(config_data, indent=2))
    return str(config_file)

# Test markers configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "api: Tests that call external APIs")
    config.addinivalue_line("markers", "auth: Authentication related tests")
    config.addinivalue_line("markers", "db: Database related tests")