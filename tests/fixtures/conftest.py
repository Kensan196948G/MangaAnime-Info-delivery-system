"""
Pytest Configuration and Shared Fixtures
=========================================

Global pytest configuration and shared fixtures for all tests.
"""

import pytest
import os
import sys
import tempfile
import sqlite3
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """Return the project root directory path"""
    return project_root


@pytest.fixture(scope="session")
def test_data_dir():
    """Return the test data directory"""
    data_dir = project_root / "tests" / "fixtures" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_database():
    """Create a temporary test database with full schema"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create works table
    cursor.execute("""
        CREATE TABLE works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            title_kana TEXT,
            title_en TEXT,
            type TEXT CHECK(type IN ('anime','manga')),
            official_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create releases table
    cursor.execute("""
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
            UNIQUE(work_id, release_type, number, platform, release_date),
            FOREIGN KEY (work_id) REFERENCES works(id)
        )
    """)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def sample_anime_work():
    """Sample anime work data"""
    return {
        "title": "僕のヒーローアカデミア",
        "title_kana": "ぼくのひーろーあかでみあ",
        "title_en": "My Hero Academia",
        "type": "anime",
        "official_url": "https://heroaca.com"
    }


@pytest.fixture
def sample_manga_work():
    """Sample manga work data"""
    return {
        "title": "ワンピース",
        "title_kana": "わんぴーす",
        "title_en": "One Piece",
        "type": "manga",
        "official_url": "https://one-piece.com"
    }


@pytest.fixture
def sample_release_episode():
    """Sample episode release data"""
    return {
        "release_type": "episode",
        "number": "1",
        "platform": "Netflix",
        "release_date": "2025-12-15",
        "source": "AniList",
        "source_url": "https://anilist.co/anime/1"
    }


@pytest.fixture
def sample_release_volume():
    """Sample volume release data"""
    return {
        "release_type": "volume",
        "number": "105",
        "platform": "BookWalker",
        "release_date": "2025-12-15",
        "source": "RSS",
        "source_url": "https://bookwalker.jp/series/123"
    }


@pytest.fixture
def ng_keywords():
    """Standard NG keywords for filtering tests"""
    return [
        "R18", "R-18", "18禁",
        "成人向け", "アダルト",
        "BL", "ボーイズラブ",
        "百合", "GL",
        "エロ", "18+"
    ]


@pytest.fixture
def ng_genres():
    """Standard NG genres for filtering tests"""
    return ["Hentai", "Ecchi", "Yaoi", "Yuri"]


@pytest.fixture
def mock_anilist_response():
    """Mock AniList API response"""
    return {
        "data": {
            "Page": {
                "media": [
                    {
                        "id": 1,
                        "title": {
                            "romaji": "Test Anime",
                            "english": "Test Anime EN",
                            "native": "テストアニメ"
                        },
                        "startDate": {
                            "year": 2025,
                            "month": 12,
                            "day": 15
                        },
                        "episodes": 12,
                        "genres": ["Action", "Adventure"],
                        "tags": [
                            {"name": "Magic"},
                            {"name": "School"}
                        ],
                        "streamingEpisodes": [
                            {
                                "title": "Episode 1",
                                "url": "https://netflix.com/watch/1",
                                "site": "Netflix"
                            }
                        ]
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_rss_feed():
    """Mock RSS feed XML"""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>BookWalker New Releases</title>
            <link>https://bookwalker.jp</link>
            <description>Latest manga releases</description>
            <item>
                <title>テストマンガ 第1巻</title>
                <link>https://bookwalker.jp/series/12345/vol1</link>
                <pubDate>Mon, 15 Dec 2025 09:00:00 +0900</pubDate>
                <description>新刊情報です</description>
            </item>
        </channel>
    </rss>"""


def pytest_configure(config):
    """Pytest configuration hook"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "api: mark test as requiring external API"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test items during collection"""
    for item in items:
        # Auto-mark tests based on location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark database tests
        if "database" in item.nodeid.lower() or "db" in item.nodeid.lower():
            item.add_marker(pytest.mark.database)


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


# Performance measurement fixtures
@pytest.fixture
def measure_time():
    """Measure execution time of test operations"""
    import time

    class Timer:
        def __init__(self):
            self.times = {}

        def start(self, name):
            self.times[name] = {"start": time.time()}

        def stop(self, name):
            if name in self.times:
                self.times[name]["end"] = time.time()
                self.times[name]["duration"] = self.times[name]["end"] - self.times[name]["start"]

        def get_duration(self, name):
            return self.times.get(name, {}).get("duration")

    return Timer()


# Logging configuration for tests
@pytest.fixture(autouse=True)
def configure_test_logging(caplog):
    """Configure logging for tests"""
    caplog.set_level(logging.DEBUG)
    yield caplog
