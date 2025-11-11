#!/usr/bin/env python3
"""
Advanced test data management and fixtures system
"""

import json
import sqlite3
import tempfile
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Generator, Union
from dataclasses import dataclass, asdict
import secrets
import string
from pathlib import Path
import pytest
import yaml


@dataclass
class WorkTestData:
    """Test data structure for works."""

    title: str
    title_kana: str
    title_en: str
    work_type: str  # 'anime' or 'manga'
    official_url: str
    genres: List[str] = None
    tags: List[str] = None
    description: str = ""
    status: str = "RELEASING"

    def __post_init__(self):
        if self.genres is None:
            self.genres = []
        if self.tags is None:
            self.tags = []


@dataclass
class ReleaseTestData:
    """Test data structure for releases."""

    work_id: int
    release_type: str  # 'episode' or 'volume'
    number: str
    platform: str
    release_date: str
    source: str
    source_url: str
    notified: int = 0


@dataclass
class DataSet:
    """Complete test dataset."""

    name: str
    description: str
    works: List[WorkTestData]
    releases: List[ReleaseTestData]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {
                "created_at": datetime.now().isoformat(),
                "work_count": len(self.works),
                "release_count": len(self.releases),
            }


class DataGenerator:
    """Advanced test data generator with realistic patterns."""

    # Japanese anime/manga title patterns
    ANIME_TITLES = [
        "進撃の巨人",
        "鬼滅の刃",
        "呪術廻戦",
        "僕のヒーローアカデミア",
        "ワンピース",
        "ナルト",
        "ブリーチ",
        "ドラゴンボール",
        "ハンターxハンター",
        "フェアリーテイル",
        "七つの大罪",
        "約束のネバーランド",
        "東京喰種",
        "デスノート",
        "コードギアス",
        "新世紀エヴァンゲリオン",
        "機動戦士ガンダム",
        "涼宮ハルヒの憂鬱",
        "けいおん！",
        "らき☆すた",
    ]

    MANGA_TITLES = [
        "チェンソーマン",
        "東京リベンジャーズ",
        "怪獣8号",
        "SPY×FAMILY",
        "推しの子",
        "ブルーロック",
        "キングダム",
        "五等分の花嫁",
        "かぐや様は告らせたい",
        "Dr.STONE",
        "ヴィンランド・サガ",
        "ゴールデンカムイ",
        "MONSTER",
        "20世紀少年",
        "PLUTO",
    ]

    # Reading patterns for titles
    TITLE_READINGS = {
        "進撃の巨人": "しんげきのきょじん",
        "鬼滅の刃": "きめつのやいば",
        "呪術廻戦": "じゅじゅつかいせん",
        "僕のヒーローアカデミア": "ぼくのひーろーあかでみあ",
        "ワンピース": "わんぴーす",
        "チェンソーマン": "ちぇんそーまん",
        "東京リベンジャーズ": "とうきょうりべんじゃーず",
        "怪獣8号": "かいじゅうはちごう",
        "SPY×FAMILY": "すぱいふぁみりー",
        "推しの子": "おしのこ",
    }

    # English title mappings
    ENGLISH_TITLES = {
        "進撃の巨人": "Attack on Titan",
        "鬼滅の刃": "Demon Slayer",
        "呪術廻戦": "Jujutsu Kaisen",
        "僕のヒーローアカデミア": "My Hero Academia",
        "ワンピース": "One Piece",
        "チェンソーマン": "Chainsaw Man",
        "東京リベンジャーズ": "Tokyo Revengers",
        "怪獣8号": "Kaiju No. 8",
        "SPY×FAMILY": "SPY x FAMILY",
        "推しの子": "Oshi no Ko",
    }

    PLATFORMS = [
        "dアニメストア",
        "Netflix",
        "Amazon Prime Video",
        "Crunchyroll",
        "Funimation",
        "BookWalker",
        "Kindle",
        "コミックシーモア",
        "まんが王国",
        "ebookjapan",
        "楽天Kobo",
        "DMM Books",
        "マガポケ",
        "ジャンプ+",
        "サンデーうぇぶり",
    ]

    GENRES = [
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
    ]

    TAGS = [
        "Shounen",
        "Shoujo",
        "Seinen",
        "Josei",
        "Mecha",
        "School",
        "Military",
        "Magic",
        "Demons",
        "Pirates",
        "Ninja",
        "Samurai",
        "Time Travel",
        "Isekai",
    ]

    def __init__(self, seed: int = None):
        """Initialize generator with optional seed for reproducible data."""
        if seed is not None:
            random.seed(seed)

    def generate_work(
        self, work_type: str = None, title_base: str = None
    ) -> WorkTestData:
        """Generate a single work with realistic data."""

        if work_type is None:
            work_type = secrets.choice(["anime", "manga"])

        if title_base is None:
            source_titles = (
                self.ANIME_TITLES if work_type == "anime" else self.MANGA_TITLES
            )
            title_base = secrets.choice(source_titles)

        # Generate variations for testing
        title = title_base
        if secrets.SystemRandom().random() < 0.3:  # 30% chance of variation
            suffix = secrets.choice(["2期", "劇場版", "OVA", "完結編", "THE FINAL"])
            title = f"{title_base} {suffix}"

        title_kana = self.TITLE_READINGS.get(
            title_base, self._generate_kana(title_base)
        )
        title_en = self.ENGLISH_TITLES.get(title_base, self._romanize_title(title_base))

        # Generate realistic metadata
        genres = random.sample(self.GENRES, secrets.randbelow(2, 5))
        tags = random.sample(self.TAGS, secrets.randbelow(1, 3))

        description = f"{title}の説明文です。{secrets.choice(self.GENRES)}作品として人気を博している。"

        official_url = f"https://example.com/{work_type}/{self._slugify(title_en)}"

        return WorkTestData(
            title=title,
            title_kana=title_kana,
            title_en=title_en,
            work_type=work_type,
            official_url=official_url,
            genres=genres,
            tags=tags,
            description=description,
        )

    def generate_release(
        self, work_id: int, work_type: str, episode_num: int = None
    ) -> ReleaseTestData:
        """Generate a release for a specific work."""

        if work_type == "anime":
            release_type = "episode"
            number = str(episode_num or secrets.randbelow(1, 24))
            platforms = [
                p
                for p in self.PLATFORMS
                if any(x in p for x in ["アニメ", "Netflix", "Prime", "Crunchyroll"])
            ]
        else:
            release_type = "volume"
            number = str(episode_num or secrets.randbelow(1, 15))
            platforms = [
                p
                for p in self.PLATFORMS
                if any(x in p for x in ["Book", "Kindle", "コミック", "まんが"])
            ]

        platform = secrets.choice(platforms)

        # Generate realistic release date (recent past to near future)
        base_date = datetime.now()
        days_offset = secrets.randbelow(-30, 30)
        release_date = (base_date + timedelta(days=days_offset)).date().isoformat()

        source = secrets.choice(["anilist", "rss", "official", "manual"])
        source_url = f"https://example.com/source/{work_id}/{release_type}/{number}"

        notified = secrets.choice([0, 0, 0, 1])  # 75% unnotified, 25% notified

        return ReleaseTestData(
            work_id=work_id,
            release_type=release_type,
            number=number,
            platform=platform,
            release_date=release_date,
            source=source,
            source_url=source_url,
            notified=notified,
        )

    def generate_dataset(
        self,
        name: str,
        work_count: int = 50,
        releases_per_work: int = 3,
        work_type_ratio: float = 0.6,
    ) -> DataSet:
        """Generate a complete test dataset."""

        works = []
        releases = []

        # Generate works
        anime_count = int(work_count * work_type_ratio)
        manga_count = work_count - anime_count

        for i in range(anime_count):
            work = self.generate_work("anime")
            works.append(work)

        for i in range(manga_count):
            work = self.generate_work("manga")
            works.append(work)

        # Generate releases
        for i, work in enumerate(works):
            work_id = i + 1
            for j in range(secrets.randbelow(1, releases_per_work)):
                release = self.generate_release(work_id, work.work_type, j + 1)
                releases.append(release)

        return DataSet(
            name=name,
            description=f"Generated dataset with {work_count} works and {len(releases)} releases",
            works=works,
            releases=releases,
        )

    def _generate_kana(self, title: str) -> str:
        """Generate plausible kana reading."""
        # Simple hiragana mapping for common characters
        kana_map = {
            "進": "しん",
            "撃": "げき",
            "巨": "きょ",
            "人": "じん",
            "鬼": "き",
            "滅": "めつ",
            "刃": "やいば",
            "呪": "じゅ",
            "術": "じゅつ",
            "廻": "かい",
            "戦": "せん",
            "僕": "ぼく",
            "の": "の",
            "ヒ": "ひ",
            "ー": "ー",
            "ロ": "ろ",
            "ー": "ー",
            "ア": "あ",
            "カ": "か",
            "デ": "で",
            "ミ": "み",
            "ア": "あ",
        }

        result = ""
        for char in title:
            result += kana_map.get(char, "て")  # Default to 'te'

        return result

    def _romanize_title(self, title: str) -> str:
        """Generate romanized version of title."""
        # Simple romanization mapping
        roman_map = {
            "進": "Shin",
            "撃": "geki",
            "巨": "Kyo",
            "人": "jin",
            "鬼": "Ki",
            "滅": "metsu",
            "刃": "yaiba",
            "呪": "Ju",
            "術": "jutsu",
            "廻": "kai",
            "戦": "sen",
        }

        words = []
        current_word = ""

        for char in title:
            if char in roman_map:
                current_word += roman_map[char]
            elif char in ["の", " ", "×"]:
                if current_word:
                    words.append(current_word)
                    current_word = ""
                if char == "の":
                    words.append("no")
                elif char == "×":
                    words.append("x")
            else:
                current_word += char

        if current_word:
            words.append(current_word)

        return " ".join(words).title()

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug."""
        return text.lower().replace(" ", "-").replace("×", "x")


class DataManager:
    """Manage test data lifecycle and persistence."""

    def __init__(self, data_dir: str = None):
        """Initialize test data manager."""
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "data")

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.generator = DataGenerator()

    def save_dataset(self, dataset: DataSet, filename: str = None) -> str:
        """Save dataset to file."""
        if filename is None:
            filename = f"{dataset.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.data_dir / filename

        # Convert to serializable format
        data = {
            "name": dataset.name,
            "description": dataset.description,
            "metadata": dataset.metadata,
            "works": [asdict(work) for work in dataset.works],
            "releases": [asdict(release) for release in dataset.releases],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(filepath)

    def load_dataset(self, filename: str) -> DataSet:
        """Load dataset from file."""
        filepath = self.data_dir / filename

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        works = [WorkTestData(**work_data) for work_data in data["works"]]
        releases = [
            ReleaseTestData(**release_data) for release_data in data["releases"]
        ]

        return DataSet(
            name=data["name"],
            description=data["description"],
            works=works,
            releases=releases,
            metadata=data.get("metadata", {}),
        )

    def create_database_from_dataset(
        self, dataset: DataSet, db_path: str = None
    ) -> str:
        """Create SQLite database from dataset."""
        if db_path is None:
            db_fd, db_path = tempfile.mkstemp(suffix=".db")
            os.close(db_fd)

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
                UNIQUE(work_id, release_type, number, platform, release_date)
            );
            
            -- Additional metadata tables for testing
            CREATE TABLE work_genres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_id INTEGER NOT NULL,
                genre TEXT NOT NULL,
                FOREIGN KEY (work_id) REFERENCES works (id)
            );
            
            CREATE TABLE work_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (work_id) REFERENCES works (id)
            );
            
            CREATE TABLE work_metadata (
                work_id INTEGER PRIMARY KEY,
                description TEXT,
                status TEXT DEFAULT 'RELEASING',
                FOREIGN KEY (work_id) REFERENCES works (id)
            );
        """
        )

        # Insert works
        works_data = []
        for work in dataset.works:
            works_data.append(
                (
                    work.title,
                    work.title_kana,
                    work.title_en,
                    work.work_type,
                    work.official_url,
                )
            )

        cursor.executemany(
            """
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (?, ?, ?, ?, ?)
        """,
            works_data,
        )

        # Insert genres and tags
        for i, work in enumerate(dataset.works):
            work_id = i + 1

            # Insert genres
            for genre in work.genres:
                cursor.execute(
                    """
                    INSERT INTO work_genres (work_id, genre) VALUES (?, ?)
                """,
                    (work_id, genre),
                )

            # Insert tags
            for tag in work.tags:
                cursor.execute(
                    """
                    INSERT INTO work_tags (work_id, tag) VALUES (?, ?)
                """,
                    (work_id, tag),
                )

            # Insert metadata
            cursor.execute(
                """
                INSERT INTO work_metadata (work_id, description, status) 
                VALUES (?, ?, ?)
            """,
                (work_id, work.description, work.status),
            )

        # Insert releases
        releases_data = []
        for release in dataset.releases:
            releases_data.append(
                (
                    release.work_id,
                    release.release_type,
                    release.number,
                    release.platform,
                    release.release_date,
                    release.source,
                    release.source_url,
                    release.notified,
                )
            )

        cursor.executemany(
            """
            INSERT INTO releases (work_id, release_type, number, platform, 
                                release_date, source, source_url, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            releases_data,
        )

        conn.commit()
        conn.close()

        return db_path

    def list_datasets(self) -> List[str]:
        """List available datasets."""
        return [f.name for f in self.data_dir.glob("*.json")]

    def delete_dataset(self, filename: str) -> bool:
        """Delete a dataset file."""
        filepath = self.data_dir / filename
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def generate_and_save_preset_datasets(self):
        """Generate and save preset datasets for common testing scenarios."""

        presets = [
            {
                "name": "small_test",
                "works": 10,
                "releases": 2,
                "description": "Small dataset for unit tests",
            },
            {
                "name": "medium_test",
                "works": 100,
                "releases": 5,
                "description": "Medium dataset for integration tests",
            },
            {
                "name": "large_test",
                "works": 1000,
                "releases": 10,
                "description": "Large dataset for performance tests",
            },
            {
                "name": "edge_cases",
                "works": 20,
                "releases": 1,
                "description": "Dataset with edge cases and special characters",
            },
            {
                "name": "regression_baseline",
                "works": 500,
                "releases": 3,
                "description": "Baseline dataset for regression testing",
            },
        ]

        for preset in presets:
            dataset = self.generator.generate_dataset(
                name=preset["name"],
                work_count=preset["works"],
                releases_per_work=preset["releases"],
            )
            dataset.description = preset["description"]

            filename = f"{preset['name']}.json"
            self.save_dataset(dataset, filename)
            print(f"Generated preset dataset: {filename}")


class MockAPIDataManager:
    """Manage mock API response data for testing."""

    def __init__(self, data_dir: str = None):
        """Initialize mock API data manager."""
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "mock_api_data")

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def create_anilist_mock_responses(self, dataset: DataSet) -> Dict[str, Any]:
        """Create realistic AniList API mock responses based on dataset."""

        mock_responses = {}

        # Main query response
        anime_works = [work for work in dataset.works if work.work_type == "anime"]

        media_list = []
        for i, work in enumerate(anime_works[:20]):  # Limit for realistic response
            media_entry = {
                "id": i + 1,
                "title": {
                    "romaji": work.title,
                    "english": work.title_en,
                    "native": work.title,
                },
                "type": "ANIME",
                "format": secrets.choice(["TV", "MOVIE", "OVA", "SPECIAL"]),
                "status": work.status,
                "episodes": secrets.randbelow(12, 24),
                "genres": work.genres,
                "tags": [{"name": tag} for tag in work.tags],
                "description": work.description,
                "startDate": {
                    "year": 2024,
                    "month": secrets.randbelow(1, 12),
                    "day": secrets.randbelow(1, 28),
                },
                "nextAiringEpisode": (
                    {
                        "episode": secrets.randbelow(1, 24),
                        "airingAt": int(
                            (
                                datetime.now()
                                + timedelta(days=secrets.randbelow(0, 30))
                            ).timestamp()
                        ),
                    }
                    if secrets.SystemRandom().random() < 0.7
                    else None
                ),
                "streamingEpisodes": [
                    {
                        "title": f"Episode {j+1}",
                        "url": f"https://example.com/episode/{i+1}/{j+1}",
                    }
                    for j in range(secrets.randbelow(1, 5))
                ],
                "siteUrl": work.official_url,
            }
            media_list.append(media_entry)

        mock_responses["search_anime"] = {
            "data": {
                "Page": {
                    "media": media_list,
                    "pageInfo": {
                        "hasNextPage": len(anime_works) > 20,
                        "currentPage": 1,
                        "lastPage": (len(anime_works) + 19) // 20,
                    },
                }
            }
        }

        # Individual anime responses
        for i, media in enumerate(media_list):
            mock_responses[f"anime_{media['id']}"] = {"data": {"Media": media}}

        return mock_responses

    def create_rss_mock_responses(self, dataset: DataSet) -> Dict[str, str]:
        """Create realistic RSS feed mock responses based on dataset."""

        manga_works = [work for work in dataset.works if work.work_type == "manga"]
        manga_releases = [
            rel for rel in dataset.releases if rel.release_type == "volume"
        ]

        rss_feeds = {}

        # Group releases by platform
        platform_releases = {}
        for release in manga_releases:
            if release.platform not in platform_releases:
                platform_releases[release.platform] = []
            platform_releases[release.platform].append(release)

        for platform, releases in platform_releases.items():
            items = []
            for release in releases[:10]:  # Limit items per feed
                # Find corresponding work
                work = next(
                    (w for i, w in enumerate(manga_works) if i + 1 == release.work_id),
                    None,
                )
                if not work:
                    continue

                pub_date = datetime.fromisoformat(release.release_date).strftime(
                    "%a, %d %b %Y %H:%M:%S %z"
                )
                if not pub_date.endswith(" +0000"):
                    pub_date += " +0000"

                items.append(
                    f"""
                    <item>
                        <title>{work.title} 第{release.number}巻</title>
                        <link>{release.source_url}</link>
                        <description>{work.description} - 第{release.number}巻が配信開始！</description>
                        <pubDate>{pub_date}</pubDate>
                        <category>manga</category>
                        <guid>{release.source_url}</guid>
                    </item>
                """
                )

            rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>{platform} 新刊情報</title>
        <description>{platform}の新刊マンガ配信情報</description>
        <link>https://example.com/{platform.lower()}/rss</link>
        <language>ja</language>
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
        <atom:link href="https://example.com/{platform.lower()}/rss" rel="self" type="application/rss+xml" />
        {''.join(items)}
    </channel>
</rss>"""

            rss_feeds[platform.lower().replace(" ", "_")] = rss_content

        return rss_feeds

    def save_mock_data(
        self, dataset_name: str, anilist_data: Dict[str, Any], rss_data: Dict[str, str]
    ):
        """Save mock API data to files."""

        dataset_dir = self.data_dir / dataset_name
        dataset_dir.mkdir(exist_ok=True)

        # Save AniList mock data
        anilist_file = dataset_dir / "anilist_responses.json"
        with open(anilist_file, "w", encoding="utf-8") as f:
            json.dump(anilist_data, f, ensure_ascii=False, indent=2)

        # Save RSS mock data
        rss_dir = dataset_dir / "rss_feeds"
        rss_dir.mkdir(exist_ok=True)

        for platform, content in rss_data.items():
            rss_file = rss_dir / f"{platform}.xml"
            with open(rss_file, "w", encoding="utf-8") as f:
                f.write(content)

        # Create index file
        index_data = {
            "dataset_name": dataset_name,
            "created_at": datetime.now().isoformat(),
            "anilist_responses": len(anilist_data),
            "rss_feeds": len(rss_data),
            "files": {
                "anilist": str(anilist_file.relative_to(self.data_dir)),
                "rss_feeds": [
                    str(f.relative_to(self.data_dir)) for f in rss_dir.glob("*.xml")
                ],
            },
        }

        index_file = dataset_dir / "index.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        return str(dataset_dir)


# Pytest fixtures for test data management
@pytest.fixture(scope="session")
def test_data_manager():
    """Provide test data manager instance."""
    return DataManager()


@pytest.fixture(scope="session")
def mock_api_data_manager():
    """Provide mock API data manager instance."""
    return MockAPIDataManager()


@pytest.fixture(scope="function")
def small_test_dataset(test_data_manager):
    """Provide small test dataset for unit tests."""
    generator = DataGenerator(seed=42)  # Reproducible data
    return generator.generate_dataset("unit_test", work_count=10, releases_per_work=2)


@pytest.fixture(scope="function")
def medium_test_dataset(test_data_manager):
    """Provide medium test dataset for integration tests."""
    generator = DataGenerator(seed=123)
    return generator.generate_dataset(
        "integration_test", work_count=50, releases_per_work=3
    )


@pytest.fixture(scope="session")
def large_test_dataset(test_data_manager):
    """Provide large test dataset for performance tests."""
    generator = DataGenerator(seed=456)
    return generator.generate_dataset(
        "performance_test", work_count=1000, releases_per_work=5
    )


@pytest.fixture(scope="function")
def test_database_from_dataset(test_data_manager):
    """Create temporary database from test dataset."""

    def _create_db(dataset: DataSet) -> str:
        db_path = test_data_manager.create_database_from_dataset(dataset)
        return db_path

    return _create_db


@pytest.fixture(scope="function")
def realistic_mock_responses(mock_api_data_manager, small_test_dataset):
    """Provide realistic mock API responses based on test dataset."""
    anilist_data = mock_api_data_manager.create_anilist_mock_responses(
        small_test_dataset
    )
    rss_data = mock_api_data_manager.create_rss_mock_responses(small_test_dataset)

    return {"anilist": anilist_data, "rss": rss_data}


if __name__ == "__main__":
    # Generate preset datasets when run directly
    manager = DataManager()
    manager.generate_and_save_preset_datasets()

    mock_manager = MockAPIDataManager()
    generator = DataGenerator(seed=42)

    # Generate mock data for each preset
    for preset_name in ["small_test", "medium_test", "large_test"]:
        try:
            dataset = manager.load_dataset(f"{preset_name}.json")
            anilist_data = mock_manager.create_anilist_mock_responses(dataset)
            rss_data = mock_manager.create_rss_mock_responses(dataset)
            mock_manager.save_mock_data(preset_name, anilist_data, rss_data)
            print(f"Generated mock API data for: {preset_name}")
        except Exception as e:
            print(f"Error generating mock data for {preset_name}: {e}")
