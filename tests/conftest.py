"""
Common test fixtures and configuration for the MangaAnime Info Delivery System
"""

import pytest
import os
import sys
import sqlite3
from unittest.mock import Mock, patch

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ============================================================
# テスト環境用の環境変数を設定（モジュールインポート前に設定必須）
# ============================================================
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("DEFAULT_ADMIN_PASSWORD", "test-admin-password-12345")
os.environ.setdefault("GMAIL_CREDENTIALS_PATH", "test_credentials.json")
os.environ.setdefault("CALENDAR_CREDENTIALS_PATH", "test_calendar_credentials.json")
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("DATABASE_PATH", ":memory:")


@pytest.fixture
def mock_config():
    """Mock configuration for tests"""
    return {
        "database": {"path": ":memory:"},
        "email": {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "test_password",
        },
        "api": {
            "enabled": False,
            "anilist": {"base_url": "https://graphql.anilist.co", "rate_limit": 90},
            "shoboical": {"base_url": "https://cal.syoboi.jp", "tid": "12345"},
        },
        "calendar": {
            "enabled": False,
            "calendar_id": "primary",
            "service_account_file": "test_service_account.json",
        },
        "notification": {"enabled": False, "check_interval": 3600},
    }


@pytest.fixture
def temp_db():
    """Create a temporary in-memory database for testing"""
    conn = sqlite3.connect(":memory:")

    # Create tables
    conn.execute(
        """
        CREATE TABLE works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            title_kana TEXT,
            title_en TEXT,
            type TEXT CHECK(type IN ('anime','manga')),
            official_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.execute(
        """
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
        )
    """
    )

    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def mock_requests():
    """Mock requests for API calls"""
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post:
        # AniList API mock response
        anilist_response = {
            "data": {
                "Page": {
                    "media": [
                        {
                            "id": 1,
                            "title": {
                                "romaji": "Test Anime",
                                "english": "Test Anime",
                                "native": "テストアニメ",
                            },
                            "type": "ANIME",
                            "status": "RELEASING",
                            "episodes": 12,
                            "startDate": {"year": 2024, "month": 1, "day": 1},
                            "streamingEpisodes": [
                                {
                                    "title": "Episode 1",
                                    "url": "https://example.com/ep1",
                                    "site": "Crunchyroll",
                                }
                            ],
                        }
                    ]
                }
            }
        }

        # Shoboical API mock response
        shoboical_response = [
            {
                "TID": "12345",
                "Title": "テストアニメ",
                "TitleEN": "Test Anime",
                "Cat": "アニメ",
                "FirstCh": "テレビ東京",
                "FirstYear": "2024",
                "FirstMonth": "1",
                "FirstEndYear": "2024",
                "FirstEndMonth": "3",
            }
        ]

        # Default responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = anilist_response

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = anilist_response

        # Handle different URLs
        def side_effect(url, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200

            if "anilist.co" in url:
                mock_response.json.return_value = anilist_response
            elif "syoboi.jp" in url or "cal.syoboi.jp" in url:
                mock_response.json.return_value = shoboical_response
            else:
                mock_response.json.return_value = {"status": "ok", "data": []}

            return mock_response

        mock_get.side_effect = side_effect
        mock_post.side_effect = side_effect

        yield {"get": mock_get, "post": mock_post}


@pytest.fixture
def mock_email():
    """Mock email functionality"""
    with patch("smtplib.SMTP") as mock_smtp, patch("smtplib.SMTP_SSL") as mock_smtp_ssl:
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        # Mock successful email operations
        mock_server.login.return_value = None
        mock_server.send_message.return_value = {}
        mock_server.quit.return_value = None

        yield mock_server


@pytest.fixture
def mock_gmail_api():
    """Mock Gmail API"""
    with patch("googleapiclient.discovery.build") as mock_build:
        mock_service = Mock()
        mock_build.return_value = mock_service

        # Mock successful email send
        mock_service.users().messages().send().execute.return_value = {
            "id": "test_message_id",
            "threadId": "test_thread_id",
        }

        yield mock_service


@pytest.fixture
def mock_calendar():
    """Mock Google Calendar API"""
    with patch("googleapiclient.discovery.build") as mock_build:
        mock_service = Mock()
        mock_build.return_value = mock_service

        # Mock successful event creation
        mock_service.events().insert().execute.return_value = {
            "id": "test_event_id",
            "status": "confirmed",
            "htmlLink": "https://calendar.google.com/test",
        }

        # Mock event list
        mock_service.events().list().execute.return_value = {"items": []}

        yield mock_service


@pytest.fixture
def mock_file_system():
    """Mock file system operations"""
    with patch("builtins.open", create=True) as mock_open, patch(
        "os.path.exists"
    ) as mock_exists, patch("os.makedirs") as mock_makedirs:
        # Mock config file content
        mock_config_content = """
{
    "database": {"path": "test.db"},
    "email": {"enabled": false},
    "api": {"enabled": false},
    "calendar": {"enabled": false}
}
"""

        mock_open.return_value.__enter__.return_value.read.return_value = (
            mock_config_content
        )
        mock_exists.return_value = True

        yield {"open": mock_open, "exists": mock_exists, "makedirs": mock_makedirs}


@pytest.fixture
def sample_anime_data():
    """Sample anime data for testing"""
    return [
        {
            "id": 1,
            "title": "Attack on Titan",
            "title_en": "Attack on Titan",
            "title_jp": "進撃の巨人",
            "type": "anime",
            "episodes": [
                {
                    "number": 1,
                    "title": "To You, 2000 Years From Now",
                    "air_date": "2024-01-07",
                    "platform": "Crunchyroll",
                }
            ],
        },
        {
            "id": 2,
            "title": "One Piece",
            "title_en": "One Piece",
            "title_jp": "ワンピース",
            "type": "manga",
            "volumes": [
                {
                    "number": 108,
                    "title": "Volume 108",
                    "release_date": "2024-02-02",
                    "platform": "Viz Media",
                }
            ],
        },
    ]


@pytest.fixture
def sample_rss_data():
    """Sample RSS feed data for testing"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Test Manga Feed</title>
        <description>Test RSS feed for manga releases</description>
        <item>
            <title>One Piece Vol. 108</title>
            <description>New volume of One Piece manga</description>
            <link>https://example.com/one-piece-108</link>
            <pubDate>Fri, 02 Feb 2024 00:00:00 GMT</pubDate>
        </item>
    </channel>
</rss>"""


@pytest.fixture(autouse=True)
def prevent_external_calls():
    """Prevent any external network calls during testing"""
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post, patch(
        "urllib.request.urlopen"
    ) as mock_urlopen:
        # Default mock responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "data": []}
        mock_response.text = '{"status": "ok", "data": []}'

        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            b'{"status": "ok"}'
        )

        yield
