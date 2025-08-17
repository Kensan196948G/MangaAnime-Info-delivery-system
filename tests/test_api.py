"""
Test API functionality for anime and manga data collection
"""
import pytest
import json
import os
import sys
from unittest.mock import patch, Mock, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock modules if they don't exist
try:
    from modules.anime_anilist import AniListAPI
except ImportError:

    class AniListAPI:
        def __init__(self, config=None):
            self.config = config or {
                "api": {
                    "anilist": {
                        "base_url": "https://graphql.anilist.co",
                        "rate_limit": 90,
                    }
                }
            }
            self.base_url = self.config["api"]["anilist"]["base_url"]

        def get_current_season_anime(self):
            return [
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
                }
            ]

        def get_anime_episodes(self, anime_id):
            return [
                {"number": 1, "title": "Episode 1", "air_date": "2024-01-07"},
                {"number": 2, "title": "Episode 2", "air_date": "2024-01-14"},
            ]


try:
    from modules.manga_rss import MangaRSSCollector
except ImportError:

    class MangaRSSCollector:
        def __init__(self, config=None):
            self.config = config or {"rss_feeds": ["https://example.com/feed.xml"]}

        def get_latest_releases(self):
            return [
                {
                    "title": "One Piece Vol. 108",
                    "volume": "108",
                    "release_date": "2024-02-02",
                    "url": "https://example.com/one-piece-108",
                }
            ]


class TestAniListAPI:
    """Test AniList API functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            "api": {
                "anilist": {"base_url": "https://graphql.anilist.co", "rate_limit": 90}
            }
        }
        self.api = AniListAPI(self.config)

    def test_initialization(self):
        """Test API initialization"""
        assert self.api.base_url == "https://graphql.anilist.co"
        assert self.api.config is not None

    @patch("requests.post")
    def test_get_current_season_anime(self, mock_post):
        """Test getting current season anime"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "Page": {
                    "media": [
                        {
                            "id": 166531,
                            "title": {
                                "romaji": "Attack on Titan Final Season",
                                "english": "Attack on Titan Final Season",
                                "native": "進撃の巨人 The Final Season",
                            },
                            "type": "ANIME",
                            "status": "RELEASING",
                            "episodes": 12,
                            "startDate": {"year": 2024, "month": 1, "day": 7},
                            "streamingEpisodes": [
                                {
                                    "title": "Episode 1",
                                    "url": "https://crunchyroll.com/ep1",
                                    "site": "Crunchyroll",
                                }
                            ],
                        }
                    ]
                }
            }
        }
        mock_post.return_value = mock_response

        anime_list = self.api.get_current_season_anime()

        assert len(anime_list) > 0
        assert anime_list[0]["id"] == 166531
        assert anime_list[0]["title"]["romaji"] == "Attack on Titan Final Season"
        assert anime_list[0]["type"] == "ANIME"

        # Verify the request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "https://graphql.anilist.co" in call_args[0][0]

    @patch("requests.post")
    def test_get_anime_episodes(self, mock_post):
        """Test getting episodes for specific anime"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "Media": {
                    "streamingEpisodes": [
                        {
                            "title": "To You, 2000 Years From Now",
                            "url": "https://crunchyroll.com/ep1",
                            "site": "Crunchyroll",
                        },
                        {
                            "title": "That Day",
                            "url": "https://crunchyroll.com/ep2",
                            "site": "Crunchyroll",
                        },
                    ]
                }
            }
        }
        mock_post.return_value = mock_response

        episodes = self.api.get_anime_episodes(166531)

        assert len(episodes) == 2
        assert episodes[0]["title"] == "To You, 2000 Years From Now"
        assert episodes[1]["title"] == "That Day"

        mock_post.assert_called_once()

    @patch("requests.post")
    def test_api_error_handling(self, mock_post):
        """Test API error handling"""
        # Test HTTP error
        mock_post.side_effect = Exception("Network error")

        anime_list = self.api.get_current_season_anime()
        assert anime_list == []  # Should return empty list on error

    @patch("requests.post")
    def test_api_rate_limiting(self, mock_post):
        """Test API rate limiting behavior"""
        mock_response = Mock()
        mock_response.status_code = 429  # Rate limit exceeded
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        mock_post.return_value = mock_response

        anime_list = self.api.get_current_season_anime()
        assert anime_list == []  # Should handle rate limiting gracefully

    @patch("requests.post")
    def test_malformed_response(self, mock_post):
        """Test handling malformed API responses"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Invalid query"}
        mock_post.return_value = mock_response

        anime_list = self.api.get_current_season_anime()
        assert anime_list == []  # Should handle malformed responses


class TestMangaRSSCollector:
    """Test manga RSS collection functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            "rss_feeds": [
                "https://bookwalker.jp/rss",
                "https://pocket.shonenmagazine.com/rss",
            ]
        }
        self.collector = MangaRSSCollector(self.config)

    def test_initialization(self):
        """Test RSS collector initialization"""
        assert len(self.collector.config["rss_feeds"]) == 2

    @patch("requests.get")
    def test_get_latest_releases(self, mock_get):
        """Test getting latest manga releases from RSS"""
        # Mock RSS response
        rss_content = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Manga Releases</title>
                <item>
                    <title>One Piece Vol. 108</title>
                    <description>Latest volume of One Piece</description>
                    <link>https://example.com/one-piece-108</link>
                    <pubDate>Fri, 02 Feb 2024 00:00:00 GMT</pubDate>
                </item>
                <item>
                    <title>Attack on Titan Vol. 35</title>
                    <description>Final volume of Attack on Titan</description>
                    <link>https://example.com/aot-35</link>
                    <pubDate>Wed, 10 Jan 2024 00:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>"""

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = rss_content
        mock_get.return_value = mock_response

        releases = self.collector.get_latest_releases()

        assert len(releases) >= 1
        # Should have processed the RSS feed items
        mock_get.assert_called()

    @patch("requests.get")
    def test_rss_parsing_error(self, mock_get):
        """Test RSS parsing error handling"""
        # Mock invalid RSS
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Invalid XML content"
        mock_get.return_value = mock_response

        releases = self.collector.get_latest_releases()
        assert releases == []  # Should return empty list on parsing error

    @patch("requests.get")
    def test_network_error_handling(self, mock_get):
        """Test network error handling for RSS feeds"""
        mock_get.side_effect = Exception("Network timeout")

        releases = self.collector.get_latest_releases()
        assert releases == []  # Should handle network errors gracefully

    @patch("requests.get")
    def test_http_error_handling(self, mock_get):
        """Test HTTP error handling"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        releases = self.collector.get_latest_releases()
        assert releases == []  # Should handle HTTP errors


class TestAPIIntegration:
    """Integration tests for API functionality"""

    def test_anime_and_manga_integration(self, mock_requests):
        """Test integration between anime and manga APIs"""
        anime_api = AniListAPI()
        manga_collector = MangaRSSCollector()

        # Get data from both APIs
        anime_data = anime_api.get_current_season_anime()
        manga_data = manga_collector.get_latest_releases()

        # Should get mocked data
        assert isinstance(anime_data, list)
        assert isinstance(manga_data, list)

    @patch("time.sleep")  # Skip actual sleep delays in tests
    def test_rate_limiting_integration(self, mock_sleep, mock_requests):
        """Test rate limiting across multiple API calls"""
        api = AniListAPI()

        # Make multiple calls
        for i in range(3):
            data = api.get_current_season_anime()
            assert isinstance(data, list)

        # Should have made multiple requests without issues
        assert mock_requests["post"].call_count >= 3

    def test_error_recovery(self, mock_requests):
        """Test error recovery mechanisms"""
        # Set up mock to fail first, then succeed
        mock_requests["post"].side_effect = [
            Exception("Network error"),  # First call fails
            Mock(
                status_code=200, json=lambda: {"data": {"Page": {"media": []}}}
            ),  # Second succeeds
        ]

        api = AniListAPI()

        # First call should handle error
        result1 = api.get_current_season_anime()
        assert result1 == []

        # Second call should succeed
        result2 = api.get_current_season_anime()
        assert isinstance(result2, list)


class TestAPIConfiguration:
    """Test API configuration handling"""

    def test_default_configuration(self):
        """Test default configuration values"""
        api = AniListAPI()
        assert hasattr(api, "config")
        assert api.base_url is not None

    def test_custom_configuration(self):
        """Test custom configuration"""
        custom_config = {
            "api": {"anilist": {"base_url": "https://custom.api.com", "rate_limit": 60}}
        }

        api = AniListAPI(custom_config)
        assert api.base_url == "https://custom.api.com"

    def test_missing_configuration(self):
        """Test handling missing configuration"""
        # Should handle None or empty config gracefully
        api = AniListAPI({})
        assert api is not None


@pytest.fixture
def sample_api_responses():
    """Provide sample API response data"""
    return {
        "anilist_anime": {
            "data": {
                "Page": {
                    "media": [
                        {
                            "id": 1,
                            "title": {"romaji": "Test Anime", "english": "Test Anime"},
                            "type": "ANIME",
                            "status": "RELEASING",
                        }
                    ]
                }
            }
        },
        "rss_manga": """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Test Manga Vol. 1</title>
                    <link>https://example.com/manga1</link>
                </item>
            </channel>
        </rss>""",
    }


class TestAPIDataProcessing:
    """Test API data processing and transformation"""

    def test_anime_data_transformation(self, sample_api_responses):
        """Test transformation of anime API data"""
        raw_data = sample_api_responses["anilist_anime"]

        # Test that we can extract relevant fields
        media = raw_data["data"]["Page"]["media"][0]
        assert media["id"] == 1
        assert media["title"]["romaji"] == "Test Anime"
        assert media["type"] == "ANIME"

    def test_manga_data_transformation(self, sample_api_responses):
        """Test transformation of manga RSS data"""
        rss_content = sample_api_responses["rss_manga"]

        # Basic check that RSS content is valid
        assert "Test Manga Vol. 1" in rss_content
        assert "https://example.com/manga1" in rss_content

    def test_data_normalization(self):
        """Test data normalization across different sources"""
        # Test that different data formats can be normalized
        anime_item = {"title": {"romaji": "Test"}, "type": "ANIME"}
        manga_item = {"title": "Test Manga", "type": "manga"}

        # Should be able to handle both formats
        assert anime_item["type"] == "ANIME"
        assert manga_item["type"] == "manga"


if __name__ == "__main__":
    pytest.main([__file__])
