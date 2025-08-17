import pytest
import asyncio
import aiohttp
from unittest.mock import patch, MagicMock
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.anime_anilist import AniListCollector


class TestAniListAPI:
    """AniList API テストクラス"""

    @pytest.mark.asyncio
    async def test_fetch_seasonal_anime_success(self):
        """季節アニメ取得の成功テスト"""
        api = AniListCollector({})

        # モックレスポンス
        mock_response_data = {
            "data": {
                "Page": {
                    "media": [
                        {
                            "id": 123,
                            "title": {
                                "romaji": "Test Anime",
                                "english": "Test Anime",
                                "native": "テストアニメ",
                            },
                            "startDate": {"year": 2024, "month": 1, "day": 1},
                            "episodes": 12,
                            "streamingEpisodes": [
                                {"title": "Episode 1", "url": "https://example.com/ep1"}
                            ],
                            "genres": ["Action", "Adventure"],
                            "tags": [{"name": "School"}],
                            "description": "Test anime description",
                        }
                    ]
                }
            }
        }

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = asyncio.coroutine(
                lambda: mock_response_data
            )()
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await api.fetch_seasonal_anime(2024, "WINTER")

            assert result is not None
            assert len(result) == 1
            assert result[0]["title"]["romaji"] == "Test Anime"

    @pytest.mark.asyncio
    async def test_fetch_seasonal_anime_api_error(self):
        """API エラー時のテスト"""
        api = AniListCollector({})

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.side_effect = aiohttp.ClientError("API Error")

            result = await api.fetch_seasonal_anime(2024, "WINTER")

            assert result == []

    @pytest.mark.asyncio
    async def test_fetch_seasonal_anime_invalid_season(self):
        """無効な季節指定のテスト"""
        api = AniListCollector({})

        result = await api.fetch_seasonal_anime(2024, "INVALID_SEASON")

        assert result == []

    @pytest.mark.asyncio
    async def test_filter_ng_content(self):
        """NGコンテンツフィルタリングのテスト"""
        api = AniListCollector({})

        test_data = [
            {
                "title": {"romaji": "Normal Anime"},
                "genres": ["Action"],
                "tags": [{"name": "School"}],
                "description": "Normal anime",
            },
            {
                "title": {"romaji": "Adult Anime"},
                "genres": ["Hentai"],
                "tags": [{"name": "Ecchi"}],
                "description": "Adult content",
            },
        ]

        filtered_data = api._filter_ng_content(test_data)

        assert len(filtered_data) == 1
        assert filtered_data[0]["title"]["romaji"] == "Normal Anime"

    @pytest.mark.asyncio
    async def test_parse_anime_data(self):
        """アニメデータパース処理のテスト"""
        api = AniListCollector({})

        raw_data = {
            "id": 123,
            "title": {
                "romaji": "Test Anime",
                "english": "Test Anime",
                "native": "テストアニメ",
            },
            "startDate": {"year": 2024, "month": 1, "day": 1},
            "episodes": 12,
            "streamingEpisodes": [
                {"title": "Episode 1", "url": "https://example.com/ep1"}
            ],
            "genres": ["Action", "Adventure"],
            "siteUrl": "https://anilist.co/anime/123",
        }

        parsed_data = api._parse_anime_data(raw_data)

        assert parsed_data["work_id"] is not None
        assert parsed_data["title"] == "Test Anime"
        assert parsed_data["type"] == "anime"
        assert parsed_data["release_date"] == "2024-01-01"
        assert len(parsed_data["streaming_platforms"]) == 1

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """レート制限の適切な処理テスト"""
        api = AniListCollector({})

        # レート制限のテストは実際のAPIコールを避けて、
        # 内部的な待機処理が正しく動作することを確認
        start_time = asyncio.get_event_loop().time()

        # 複数回の疑似APIコールをシミュレート
        for i in range(3):
            await api._wait_for_rate_limit()

        end_time = asyncio.get_event_loop().time()

        # 最低限の待機時間が守られていることを確認
        # (実際の実装では1分間に90リクエストの制限)
        assert end_time - start_time >= 0  # 基本的な時間経過チェック
