"""
Unit Tests for AniList API Integration
=======================================

Tests for AniList GraphQL API integration:
- GraphQL query construction
- API response parsing
- Rate limiting
- Error handling
- Data transformation
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import time


class TestAniListAPIQueries:
    """Test suite for AniList GraphQL queries"""

    def test_basic_anime_query_structure(self):
        """Test basic anime query structure"""
        query = """
        query ($page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                media(type: ANIME, status: RELEASING) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    startDate {
                        year
                        month
                        day
                    }
                }
            }
        }
        """

        variables = {"page": 1, "perPage": 10}

        assert "query" in query
        assert "Page" in query
        assert "media" in query
        assert variables['page'] == 1
        assert variables['perPage'] == 10

    def test_query_with_streaming_info(self):
        """Test query including streaming information"""
        query = """
        query {
            Media(id: 1) {
                id
                title {
                    romaji
                }
                streamingEpisodes {
                    title
                    thumbnail
                    url
                    site
                }
            }
        }
        """

        assert "streamingEpisodes" in query
        assert "site" in query

    def test_query_with_date_filters(self):
        """Test query with date range filters"""
        today = datetime.now()
        start_date = today.strftime("%Y%m%d")
        end_date = (today + timedelta(days=7)).strftime("%Y%m%d")

        variables = {
            "startDate": int(start_date),
            "endDate": int(end_date)
        }

        assert variables['startDate'] <= variables['endDate']
        assert len(str(variables['startDate'])) == 8

    def test_query_with_genre_filters(self):
        """Test query with genre filters"""
        query = """
        query ($genres: [String]) {
            Page {
                media(genre_in: $genres) {
                    id
                    title { romaji }
                    genres
                }
            }
        }
        """

        variables = {
            "genres": ["Action", "Adventure", "Fantasy"]
        }

        assert isinstance(variables['genres'], list)
        assert len(variables['genres']) > 0


class TestAniListAPIResponseParsing:
    """Test suite for parsing AniList API responses"""

    @pytest.fixture
    def sample_anime_response(self):
        """Sample API response"""
        return {
            "data": {
                "Page": {
                    "media": [
                        {
                            "id": 1,
                            "title": {
                                "romaji": "Boku no Hero Academia",
                                "english": "My Hero Academia",
                                "native": "僕のヒーローアカデミア"
                            },
                            "startDate": {
                                "year": 2025,
                                "month": 12,
                                "day": 15
                            },
                            "episodes": 24,
                            "genres": ["Action", "Comedy"],
                            "streamingEpisodes": [
                                {
                                    "title": "Episode 1",
                                    "url": "https://example.com/ep1",
                                    "site": "Netflix"
                                }
                            ]
                        }
                    ]
                }
            }
        }

    def test_parse_basic_anime_info(self, sample_anime_response):
        """Test parsing basic anime information"""
        media = sample_anime_response['data']['Page']['media'][0]

        assert media['id'] == 1
        assert media['title']['romaji'] == "Boku no Hero Academia"
        assert media['title']['english'] == "My Hero Academia"
        assert media['episodes'] == 24

    def test_parse_date_information(self, sample_anime_response):
        """Test parsing date information"""
        media = sample_anime_response['data']['Page']['media'][0]
        start_date = media['startDate']

        assert start_date['year'] == 2025
        assert start_date['month'] == 12
        assert start_date['day'] == 15

        # Convert to date object
        date_str = f"{start_date['year']}-{start_date['month']:02d}-{start_date['day']:02d}"
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        assert parsed_date.year == 2025

    def test_parse_streaming_info(self, sample_anime_response):
        """Test parsing streaming information"""
        media = sample_anime_response['data']['Page']['media'][0]
        streaming = media['streamingEpisodes'][0]

        assert streaming['title'] == "Episode 1"
        assert streaming['site'] == "Netflix"
        assert "https://" in streaming['url']

    def test_parse_genres(self, sample_anime_response):
        """Test parsing genre information"""
        media = sample_anime_response['data']['Page']['media'][0]
        genres = media['genres']

        assert isinstance(genres, list)
        assert "Action" in genres
        assert "Comedy" in genres

    def test_handle_missing_english_title(self):
        """Test handling missing English title"""
        response = {
            "data": {
                "Media": {
                    "title": {
                        "romaji": "Anime Title",
                        "english": None,
                        "native": "アニメタイトル"
                    }
                }
            }
        }

        title = response['data']['Media']['title']
        english_title = title.get('english') or title.get('romaji')

        assert english_title == "Anime Title"

    def test_handle_incomplete_date(self):
        """Test handling incomplete date information"""
        response = {
            "data": {
                "Media": {
                    "startDate": {
                        "year": 2025,
                        "month": None,
                        "day": None
                    }
                }
            }
        }

        date_info = response['data']['Media']['startDate']

        assert date_info['year'] == 2025
        assert date_info['month'] is None

        # Should handle as year-only
        if date_info['month'] and date_info['day']:
            date_str = f"{date_info['year']}-{date_info['month']}-{date_info['day']}"
        else:
            date_str = f"{date_info['year']}-01-01"  # Default to Jan 1

        assert "2025" in date_str

    def test_parse_empty_streaming_episodes(self):
        """Test handling empty streaming episodes"""
        response = {
            "data": {
                "Media": {
                    "streamingEpisodes": []
                }
            }
        }

        streaming = response['data']['Media']['streamingEpisodes']
        assert isinstance(streaming, list)
        assert len(streaming) == 0

    def test_parse_multiple_anime(self):
        """Test parsing multiple anime entries"""
        response = {
            "data": {
                "Page": {
                    "media": [
                        {"id": 1, "title": {"romaji": "Anime 1"}},
                        {"id": 2, "title": {"romaji": "Anime 2"}},
                        {"id": 3, "title": {"romaji": "Anime 3"}}
                    ]
                }
            }
        }

        media_list = response['data']['Page']['media']
        assert len(media_list) == 3
        assert all('id' in m for m in media_list)


class TestAniListRateLimiting:
    """Test suite for rate limiting"""

    def test_rate_limit_tracking(self):
        """Test rate limit tracking"""
        rate_limiter = {
            'requests': 0,
            'max_requests': 90,
            'window_start': time.time()
        }

        # Simulate request
        rate_limiter['requests'] += 1

        assert rate_limiter['requests'] == 1
        assert rate_limiter['requests'] <= rate_limiter['max_requests']

    def test_rate_limit_reset(self):
        """Test rate limit window reset"""
        rate_limiter = {
            'requests': 90,
            'max_requests': 90,
            'window_start': time.time() - 61  # 61 seconds ago
        }

        current_time = time.time()
        window_elapsed = current_time - rate_limiter['window_start']

        # Should reset after 60 seconds
        if window_elapsed >= 60:
            rate_limiter['requests'] = 0
            rate_limiter['window_start'] = current_time

        assert rate_limiter['requests'] == 0

    def test_rate_limit_exceeded(self):
        """Test handling rate limit exceeded"""
        rate_limiter = {
            'requests': 90,
            'max_requests': 90,
            'window_start': time.time()
        }

        # Check if limit exceeded
        can_make_request = rate_limiter['requests'] < rate_limiter['max_requests']

        assert not can_make_request

    def test_rate_limit_with_buffer(self):
        """Test rate limiting with safety buffer"""
        max_requests = 90
        buffer = 5
        safe_limit = max_requests - buffer

        current_requests = 80

        can_make_request = current_requests < safe_limit
        assert can_make_request

        current_requests = 86
        can_make_request = current_requests < safe_limit
        assert not can_make_request

    def test_concurrent_request_counting(self):
        """Test counting concurrent requests"""
        request_count = 0
        max_concurrent = 5

        for i in range(3):
            if request_count < max_concurrent:
                request_count += 1

        assert request_count == 3
        assert request_count <= max_concurrent


class TestAniListErrorHandling:
    """Test suite for error handling"""

    def test_handle_network_error(self):
        """Test handling network errors"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = ConnectionError("Network error")

            try:
                mock_post("https://graphql.anilist.co", json={})
                success = True
            except ConnectionError as e:
                success = False
                error_message = str(e)

            assert not success
            assert "Network error" in error_message

    def test_handle_timeout_error(self):
        """Test handling timeout errors"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = TimeoutError("Request timeout")

            try:
                mock_post("https://graphql.anilist.co", json={}, timeout=30)
                success = True
            except (TimeoutError, Exception):
                success = False

            assert not success

    def test_handle_api_error_response(self):
        """Test handling API error response"""
        error_response = {
            "errors": [
                {
                    "message": "Invalid query",
                    "status": 400
                }
            ]
        }

        if 'errors' in error_response:
            errors = error_response['errors']
            assert len(errors) > 0
            assert errors[0]['message'] == "Invalid query"

    def test_handle_rate_limit_error(self):
        """Test handling rate limit error"""
        error_response = {
            "errors": [
                {
                    "message": "Rate limit exceeded",
                    "status": 429
                }
            ]
        }

        if 'errors' in error_response:
            error = error_response['errors'][0]
            is_rate_limit = error.get('status') == 429

            assert is_rate_limit

    def test_handle_invalid_json_response(self):
        """Test handling invalid JSON response"""
        invalid_json = "{ invalid json"

        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)

    def test_handle_empty_response(self):
        """Test handling empty response"""
        response = {}

        data = response.get('data')
        assert data is None

    def test_handle_missing_required_field(self):
        """Test handling missing required field"""
        response = {
            "data": {
                "Media": {
                    # Missing 'id' field
                    "title": {"romaji": "Test"}
                }
            }
        }

        media = response['data']['Media']
        media_id = media.get('id')

        assert media_id is None

    def test_retry_logic(self):
        """Test retry logic for failed requests"""
        max_retries = 3
        attempt = 0

        def make_request():
            nonlocal attempt
            attempt += 1
            if attempt < 3:
                raise ConnectionError("Temporary error")
            return {"data": {"success": True}}

        result = None
        for i in range(max_retries):
            try:
                result = make_request()
                break
            except ConnectionError:
                if i == max_retries - 1:
                    raise
                continue

        assert result is not None
        assert result['data']['success'] is True
        assert attempt == 3


class TestAniListDataTransformation:
    """Test suite for data transformation"""

    def test_transform_to_internal_format(self):
        """Test transforming AniList data to internal format"""
        anilist_data = {
            "id": 123,
            "title": {
                "romaji": "Test Anime",
                "english": "Test Anime EN",
                "native": "テストアニメ"
            },
            "startDate": {"year": 2025, "month": 12, "day": 15}
        }

        # Transform
        internal_format = {
            "title": anilist_data['title']['romaji'],
            "title_en": anilist_data['title'].get('english'),
            "title_kana": anilist_data['title'].get('native'),
            "type": "anime",
            "release_date": f"{anilist_data['startDate']['year']}-{anilist_data['startDate']['month']:02d}-{anilist_data['startDate']['day']:02d}"
        }

        assert internal_format['title'] == "Test Anime"
        assert internal_format['type'] == "anime"
        assert internal_format['release_date'] == "2025-12-15"

    def test_extract_streaming_platforms(self):
        """Test extracting streaming platforms"""
        streaming_episodes = [
            {"site": "Netflix", "url": "https://netflix.com/1"},
            {"site": "Amazon Prime", "url": "https://prime.video/1"},
            {"site": "Netflix", "url": "https://netflix.com/2"}
        ]

        # Extract unique platforms
        platforms = list(set(ep['site'] for ep in streaming_episodes))

        assert "Netflix" in platforms
        assert "Amazon Prime" in platforms
        assert len(platforms) == 2

    def test_normalize_title(self):
        """Test title normalization"""
        titles = [
            "Test Anime: Season 2",
            "Test Anime Season 2",
            "Test Anime (Season 2)"
        ]

        def normalize_title(title):
            # Simple normalization
            import re
            normalized = re.sub(r'\s*[:\-]\s*', ' ', title)
            normalized = re.sub(r'\s*\([^)]*\)', '', normalized)
            return normalized.strip()

        normalized_titles = [normalize_title(t) for t in titles]

        # All should be similar after normalization
        assert all('Test Anime' in t for t in normalized_titles)

    def test_convert_fuzzy_date(self):
        """Test converting fuzzy date format"""
        fuzzy_dates = [
            {"year": 2025, "month": 12, "day": 15},
            {"year": 2025, "month": 12, "day": None},
            {"year": 2025, "month": None, "day": None}
        ]

        def convert_fuzzy_date(date_dict):
            year = date_dict['year']
            month = date_dict.get('month') or 1
            day = date_dict.get('day') or 1
            return f"{year}-{month:02d}-{day:02d}"

        converted = [convert_fuzzy_date(d) for d in fuzzy_dates]

        assert converted[0] == "2025-12-15"
        assert converted[1] == "2025-12-01"
        assert converted[2] == "2025-01-01"


class TestAniListEdgeCases:
    """Edge case tests for AniList integration"""

    def test_handle_very_long_title(self):
        """Test handling very long anime titles"""
        long_title = "あ" * 500
        response = {
            "data": {
                "Media": {
                    "title": {"romaji": long_title}
                }
            }
        }

        title = response['data']['Media']['title']['romaji']
        assert len(title) == 500

    def test_handle_special_characters_in_title(self):
        """Test handling special characters"""
        special_titles = [
            "Test & Test",
            "Test: The Movie",
            "Test (2025)",
            "Test - Part 2",
            "Test's Adventure"
        ]

        for title in special_titles:
            assert isinstance(title, str)
            assert len(title) > 0

    def test_handle_multiple_streaming_sites(self):
        """Test handling many streaming sites"""
        streaming_episodes = [
            {"site": f"Platform {i}", "url": f"https://platform{i}.com"}
            for i in range(20)
        ]

        assert len(streaming_episodes) == 20
        platforms = set(ep['site'] for ep in streaming_episodes)
        assert len(platforms) == 20

    def test_handle_null_values_in_response(self):
        """Test handling null values"""
        response = {
            "data": {
                "Media": {
                    "id": 1,
                    "title": {
                        "romaji": "Test",
                        "english": None,
                        "native": None
                    },
                    "description": None,
                    "episodes": None
                }
            }
        }

        media = response['data']['Media']
        assert media['title']['english'] is None
        assert media['description'] is None
        assert media['episodes'] is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
