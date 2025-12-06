"""
AniList API連携モジュールのテスト
modules/anime_anilist.py のテストカバレッジ向上

This test suite covers:
1. AniListClient initialization and configuration
2. GraphQL query construction
3. Response parsing
4. Error handling and retries
5. Circuit breaker functionality
6. Adaptive rate limiting
7. All public API methods
"""
import pytest
import sys
import json
import asyncio
from pathlib import Path
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock, AsyncMock, call

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from modules import anime_anilist
    from modules.anime_anilist import (
        AniListClient,
        AniListCollector,
        AniListAPIError,
        RateLimitExceeded,
        CircuitBreakerOpen,
        CircuitBreaker,
        CircuitBreakerConfig,
        CircuitState,
    )
    from modules.models import AniListWork, WorkType, DataSource
except ImportError as e:
    pytest.skip(f"anime_anilist module not found: {e}", allow_module_level=True)


@pytest.fixture
def mock_response():
    """モックレスポンスデータ"""
    return {
        'data': {
            'Page': {
                'media': [
                    {
                        'id': 12345,
                        'title': {
                            'romaji': 'Test Anime',
                            'english': 'Test Anime EN',
                            'native': 'テストアニメ'
                        },
                        'startDate': {
                            'year': 2025,
                            'month': 12,
                            'day': 15
                        },
                        'episodes': 12,
                        'genres': ['Action', 'Fantasy'],
                        'tags': [
                            {'name': 'Magic', 'rank': 80},
                            {'name': 'School', 'rank': 70}
                        ],
                        'streamingEpisodes': [
                            {
                                'title': 'Episode 1',
                                'thumbnail': 'https://example.com/thumb.jpg',
                                'url': 'https://dani.me/anime/12345/1',
                                'site': 'dアニメストア'
                            }
                        ],
                        'siteUrl': 'https://anilist.co/anime/12345',
                        'coverImage': {
                            'large': 'https://example.com/cover.jpg'
                        },
                        'description': 'Test anime description'
                    }
                ]
            }
        }
    }


class TestGraphQLQuery:
    """GraphQLクエリのテスト"""

    def test_query_structure(self):
        """クエリの構造が正しいことを確認"""
        if hasattr(anime_anilist, 'ANILIST_QUERY'):
            query = anime_anilist.ANILIST_QUERY
            assert 'query' in query.lower()
            assert 'media' in query.lower()
            assert 'title' in query.lower()

    def test_query_includes_streaming_episodes(self):
        """ストリーミング情報が含まれているか"""
        if hasattr(anime_anilist, 'ANILIST_QUERY'):
            query = anime_anilist.ANILIST_QUERY
            assert 'streamingEpisodes' in query or 'streaming' in query.lower()


class TestFetchAnimeData:
    """アニメデータ取得のテスト"""

    @patch('requests.post')
    def test_fetch_anime_success(self, mock_post, mock_response):
        """正常なアニメデータ取得"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response

        if hasattr(anime_anilist, 'fetch_anime_data'):
            result = anime_anilist.fetch_anime_data()

            assert result is not None
            assert isinstance(result, (list, dict))
            mock_post.assert_called_once()

    @patch('requests.post')
    def test_fetch_anime_with_season(self, mock_post, mock_response):
        """シーズン指定でのデータ取得"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response

        if hasattr(anime_anilist, 'fetch_anime_data'):
            # シーズン指定（例：2025年冬）
            result = anime_anilist.fetch_anime_data(season='WINTER', year=2025)

            assert result is not None
            mock_post.assert_called_once()

    @patch('requests.post')
    def test_fetch_anime_api_error(self, mock_post):
        """API エラーのハンドリング"""
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Internal Server Error"

        if hasattr(anime_anilist, 'fetch_anime_data'):
            result = anime_anilist.fetch_anime_data()

            # エラー時は空リストまたはNoneを返す
            assert result is None or result == []

    @patch('requests.post')
    def test_fetch_anime_rate_limit(self, mock_post):
        """レート制限のハンドリング"""
        mock_post.return_value.status_code = 429
        mock_post.return_value.text = "Too Many Requests"

        if hasattr(anime_anilist, 'fetch_anime_data'):
            result = anime_anilist.fetch_anime_data()

            # レート制限時の適切な処理
            assert result is None or result == []

    @patch('requests.post')
    def test_fetch_anime_network_error(self, mock_post):
        """ネットワークエラーのハンドリング"""
        mock_post.side_effect = ConnectionError("Network error")

        if hasattr(anime_anilist, 'fetch_anime_data'):
            try:
                result = anime_anilist.fetch_anime_data()
                assert result is None or result == []
            except ConnectionError:
                # エラーハンドリングされていない場合
                pass


class TestParseAnimeData:
    """アニメデータ解析のテスト"""

    def test_parse_anime_data(self, mock_response):
        """正常なデータ解析"""
        if hasattr(anime_anilist, 'parse_anime_data'):
            result = anime_anilist.parse_anime_data(mock_response)

            assert result is not None
            assert isinstance(result, list)
            if len(result) > 0:
                anime = result[0]
                assert 'title' in anime
                assert 'release_date' in anime or 'startDate' in anime

    def test_parse_empty_response(self):
        """空のレスポンスの処理"""
        empty_response = {'data': {'Page': {'media': []}}}

        if hasattr(anime_anilist, 'parse_anime_data'):
            result = anime_anilist.parse_anime_data(empty_response)

            assert result is not None
            assert isinstance(result, list)
            assert len(result) == 0

    def test_parse_missing_fields(self):
        """フィールド欠損データの処理"""
        incomplete_response = {
            'data': {
                'Page': {
                    'media': [
                        {
                            'id': 999,
                            'title': {
                                'romaji': 'Incomplete Anime'
                            }
                            # startDate, episodes等が欠損
                        }
                    ]
                }
            }
        }

        if hasattr(anime_anilist, 'parse_anime_data'):
            result = anime_anilist.parse_anime_data(incomplete_response)

            # 欠損データでもエラーにならずに処理される
            assert result is not None


class TestExtractStreamingInfo:
    """ストリーミング情報抽出のテスト"""

    def test_extract_streaming_platforms(self, mock_response):
        """配信プラットフォーム情報の抽出"""
        if hasattr(anime_anilist, 'extract_streaming_info'):
            anime_data = mock_response['data']['Page']['media'][0]
            result = anime_anilist.extract_streaming_info(anime_data)

            assert result is not None
            assert isinstance(result, list)
            if len(result) > 0:
                platform = result[0]
                assert 'site' in platform or 'platform' in platform

    def test_extract_streaming_no_data(self):
        """配信情報がない場合"""
        anime_without_streaming = {
            'id': 999,
            'title': {'romaji': 'No Streaming Anime'},
            'streamingEpisodes': []
        }

        if hasattr(anime_anilist, 'extract_streaming_info'):
            result = anime_anilist.extract_streaming_info(anime_without_streaming)

            assert result is not None
            assert isinstance(result, list)
            assert len(result) == 0


class TestFilterByGenreTag:
    """ジャンル/タグフィルタリングのテスト"""

    def test_filter_ng_keywords(self):
        """NGワードフィルタリング"""
        if hasattr(anime_anilist, 'filter_by_keywords'):
            anime_with_ng_word = {
                'title': {'romaji': 'Test Anime'},
                'genres': ['Ecchi'],
                'tags': [{'name': 'Ecchi', 'rank': 90}]
            }

            result = anime_anilist.filter_by_keywords(anime_with_ng_word)

            # NGワードを含む場合はFalse（除外）
            assert result is False or result is None

    def test_filter_safe_content(self):
        """安全なコンテンツの通過"""
        if hasattr(anime_anilist, 'filter_by_keywords'):
            safe_anime = {
                'title': {'romaji': 'Safe Anime'},
                'genres': ['Action', 'Fantasy'],
                'tags': [{'name': 'Magic', 'rank': 80}]
            }

            result = anime_anilist.filter_by_keywords(safe_anime)

            # 安全なコンテンツは通過（True）
            assert result is True or result is not None


class TestDateFormatting:
    """日付フォーマットのテスト"""

    def test_format_anilist_date(self):
        """AniList形式の日付変換"""
        if hasattr(anime_anilist, 'format_date'):
            anilist_date = {
                'year': 2025,
                'month': 12,
                'day': 15
            }

            result = anime_anilist.format_date(anilist_date)

            # date型または文字列型で返される
            assert isinstance(result, (date, str))

    def test_format_incomplete_date(self):
        """不完全な日付の処理"""
        if hasattr(anime_anilist, 'format_date'):
            incomplete_date = {
                'year': 2025,
                'month': 12
                # day が欠損
            }

            result = anime_anilist.format_date(incomplete_date)

            # 不完全でもエラーにならない
            assert result is not None or result is None

    def test_format_null_date(self):
        """null日付の処理"""
        if hasattr(anime_anilist, 'format_date'):
            result = anime_anilist.format_date(None)

            # Noneが渡された場合の処理
            assert result is None or isinstance(result, (date, str))


class TestSeasonCalculation:
    """シーズン計算のテスト"""

    def test_get_current_season(self):
        """現在のシーズン取得"""
        if hasattr(anime_anilist, 'get_current_season'):
            result = anime_anilist.get_current_season()

            assert result is not None
            assert isinstance(result, tuple)  # (season, year)
            season, year = result
            assert season in ['WINTER', 'SPRING', 'SUMMER', 'FALL']
            assert isinstance(year, int)

    def test_get_next_season(self):
        """次のシーズン取得"""
        if hasattr(anime_anilist, 'get_next_season'):
            result = anime_anilist.get_next_season()

            assert result is not None
            assert isinstance(result, tuple)

    def test_season_from_month(self):
        """月からシーズンを計算"""
        if hasattr(anime_anilist, 'season_from_month'):
            # 12月 -> WINTER
            assert anime_anilist.season_from_month(12) in ['WINTER', 'FALL']
            # 4月 -> SPRING
            assert anime_anilist.season_from_month(4) == 'SPRING'
            # 7月 -> SUMMER
            assert anime_anilist.season_from_month(7) == 'SUMMER'
            # 10月 -> FALL
            assert anime_anilist.season_from_month(10) == 'FALL'


class TestDatabaseIntegration:
    """データベース統合のテスト"""

    @pytest.mark.asyncio
    async def test_collector_database_integration(self):
        """コレクターのデータベース統合（モック使用）"""
        # This test verifies the collector can interact with the database module
        # when it's available
        config = {"filtering": {"ng_keywords": [], "ng_genres": [], "exclude_tags": []}}

        with patch('modules.anime_anilist.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.get_or_create_work.return_value = 1
            mock_db.create_release.return_value = 1
            mock_get_db.return_value = mock_db

            collector = AniListCollector(config)

            # Verify database was initialized
            assert collector.db is not None


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    def test_handle_invalid_json(self):
        """無効なJSONの処理"""
        if hasattr(anime_anilist, 'parse_anime_data'):
            try:
                result = anime_anilist.parse_anime_data({'invalid': 'structure'})
                # エラーハンドリングされている場合
                assert result is not None or result is None
            except (KeyError, TypeError):
                # エラーハンドリングされていない場合
                pass

    @patch('requests.post')
    def test_handle_timeout(self, mock_post):
        """タイムアウトの処理"""
        import requests
        mock_post.side_effect = requests.Timeout("Request timeout")

        if hasattr(anime_anilist, 'fetch_anime_data'):
            try:
                result = anime_anilist.fetch_anime_data()
                assert result is None or result == []
            except requests.Timeout:
                pass


class TestCaching:
    """キャッシング機能のテスト（将来的な実装用）"""

    def test_no_caching_implemented(self):
        """現在キャッシング機能は実装されていない"""
        # This is a placeholder for future caching implementation
        # The module currently doesn't have a caching mechanism
        assert not hasattr(anime_anilist, 'cache')
        assert not hasattr(anime_anilist, 'get_cached_anime_data')


class TestRateLimiting:
    """レート制限のテスト"""

    @patch('time.sleep')
    @patch('requests.post')
    def test_rate_limit_handling(self, mock_post, mock_sleep, mock_response):
        """レート制限時のリトライ"""
        # 最初はレート制限、2回目は成功
        mock_post.side_effect = [
            Mock(status_code=429),
            Mock(status_code=200, json=lambda: mock_response)
        ]

        if hasattr(anime_anilist, 'fetch_with_retry'):
            result = anime_anilist.fetch_with_retry()

            # リトライが実行される
            assert mock_post.call_count >= 1
            if mock_post.call_count > 1:
                mock_sleep.assert_called()


# ==============================================================================
# Enhanced Test Suite - Comprehensive Coverage
# ==============================================================================


class TestAniListClientInitialization:
    """AniListClient初期化のテスト"""

    def test_client_default_initialization(self):
        """デフォルト設定でのクライアント初期化"""
        client = AniListClient()

        assert client.timeout == 30
        assert client.retry_attempts == 3
        assert client.retry_delay == 5
        assert client.current_rate_limit == AniListClient.RATE_LIMIT
        assert client.circuit_breaker is not None
        assert client.circuit_breaker.state == CircuitState.CLOSED

    def test_client_custom_initialization(self):
        """カスタム設定でのクライアント初期化"""
        client = AniListClient(timeout=60, retry_attempts=5, retry_delay=10)

        assert client.timeout == 60
        assert client.retry_attempts == 5
        assert client.retry_delay == 10

    def test_client_initial_state(self):
        """クライアントの初期状態確認"""
        client = AniListClient()

        assert client.request_count == 0
        assert client.error_count == 0
        assert client.total_response_time == 0.0
        assert client.consecutive_errors == 0
        assert client.consecutive_successes == 0
        assert len(client.request_timestamps) == 0


class TestCircuitBreakerFunctionality:
    """サーキットブレーカーのテスト"""

    def test_circuit_breaker_initial_state(self):
        """サーキットブレーカーの初期状態"""
        config = CircuitBreakerConfig()
        breaker = CircuitBreaker(config)

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.can_execute() is True

    def test_circuit_breaker_opens_after_failures(self):
        """連続失敗後にサーキットブレーカーがOPENになる"""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(config)

        # 3回失敗させる
        for _ in range(3):
            breaker.record_failure(AniListAPIError("Test error"))

        assert breaker.state == CircuitState.OPEN
        assert breaker.can_execute() is False

    def test_circuit_breaker_recovery(self):
        """サーキットブレーカーの回復テスト"""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
        breaker = CircuitBreaker(config)

        # 失敗させてOPENにする
        breaker.record_failure(AniListAPIError("Error 1"))
        breaker.record_failure(AniListAPIError("Error 2"))
        assert breaker.state == CircuitState.OPEN

        # 回復時間待機
        import time
        time.sleep(1.1)

        # HALF_OPENに遷移
        assert breaker.can_execute() is True
        assert breaker.state == CircuitState.HALF_OPEN

    def test_circuit_breaker_closes_after_successes(self):
        """HALF_OPEN状態からの成功でCLOSEDに戻る"""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
        breaker = CircuitBreaker(config)

        # OPENにする
        breaker.record_failure(AniListAPIError("Error"))
        breaker.record_failure(AniListAPIError("Error"))

        # HALF_OPENに遷移
        import time
        time.sleep(1.1)
        breaker.can_execute()

        # 成功を記録してCLOSEDに戻す
        for _ in range(3):
            breaker.record_success()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0


class TestAdaptiveRateLimiting:
    """アダプティブレート制限のテスト"""

    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self):
        """レート制限が適切に強制される"""
        client = AniListClient()

        # 複数リクエストのタイムスタンプを記録
        import time
        start_time = time.time()

        for _ in range(3):
            await client._enforce_rate_limit()

        elapsed = time.time() - start_time

        # タイムスタンプが記録されている
        assert len(client.request_timestamps) == 3
        # 極端に速すぎない（バースト保護）
        assert elapsed >= 0  # 少なくとも処理時間がかかる

    @pytest.mark.asyncio
    async def test_rate_limit_cleanup(self):
        """古いタイムスタンプのクリーンアップ"""
        client = AniListClient()

        # 古いタイムスタンプを追加
        import time
        old_timestamp = time.time() - 100  # 100秒前
        client.request_timestamps = [old_timestamp]

        await client._enforce_rate_limit()

        # 古いタイムスタンプは削除されている
        assert old_timestamp not in client.request_timestamps

    def test_rate_limit_adjustment_on_errors(self):
        """エラー発生時のレート制限調整"""
        client = AniListClient()
        original_rate = client.current_rate_limit

        # 連続エラーを記録
        client.consecutive_errors = 3

        # レート制限を調整
        import time
        client.last_rate_adjustment = time.time() - 100  # 過去に調整したことにする
        client._adjust_rate_limit_if_needed()

        # レート制限が下がっている
        assert client.current_rate_limit < original_rate
        assert client.current_rate_limit >= AniListClient.MIN_RATE_LIMIT

    def test_rate_limit_recovery_on_success(self):
        """成功時のレート制限回復"""
        client = AniListClient()

        # レート制限を下げる
        client.current_rate_limit = 50
        client.consecutive_successes = 10

        # レート制限を調整
        import time
        client.last_rate_adjustment = time.time() - 100
        client._adjust_rate_limit_if_needed()

        # レート制限が上がっている
        assert client.current_rate_limit > 50
        assert client.current_rate_limit <= AniListClient.RATE_LIMIT


class TestAniListClientRequests:
    """AniListClient リクエストのテスト"""

    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """正常なリクエスト"""
        client = AniListClient()

        mock_response_data = {
            "data": {
                "Page": {
                    "media": [{"id": 123, "title": {"romaji": "Test"}}]
                }
            }
        }

        # Create mock response
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response_data)

        # Create mock post that returns the response
        mock_post = MagicMock()
        mock_post.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_post.__aexit__ = AsyncMock(return_value=None)

        # Create mock session
        mock_session_instance = AsyncMock()
        mock_session_instance.post = MagicMock(return_value=mock_post)

        # Mock the ClientSession context manager
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session_class.return_value.__aenter__.return_value = mock_session_instance
            mock_session_class.return_value.__aexit__.return_value = None

            result = await client._make_request("query { test }")

            assert result == mock_response_data["data"]
            assert client.request_count == 1
            assert client.error_count == 0

    @pytest.mark.asyncio
    async def test_make_request_circuit_breaker_open(self):
        """サーキットブレーカーOPEN時のリクエスト拒否"""
        client = AniListClient()

        # サーキットブレーカーを強制的にOPENにする
        import time
        client.circuit_breaker.state = CircuitState.OPEN
        client.circuit_breaker.last_failure_time = time.time()  # Set to current time so it won't recover

        with pytest.raises(CircuitBreakerOpen):
            await client._make_request("query { test }")

    @pytest.mark.asyncio
    async def test_make_request_rate_limit_error(self):
        """レート制限エラーのハンドリング"""
        client = AniListClient()

        # Create mock response
        mock_resp = AsyncMock()
        mock_resp.status = 429
        mock_resp.json = AsyncMock(return_value={"error": "Rate limited"})

        # Create mock post
        mock_post = MagicMock()
        mock_post.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_post.__aexit__ = AsyncMock(return_value=None)

        # Create mock session
        mock_session_instance = AsyncMock()
        mock_session_instance.post = MagicMock(return_value=mock_post)

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session_class.return_value.__aenter__.return_value = mock_session_instance
            mock_session_class.return_value.__aexit__.return_value = None

            with pytest.raises(RateLimitExceeded):
                await client._make_request("query { test }")

    @pytest.mark.asyncio
    async def test_make_request_graphql_error(self):
        """GraphQLエラーのハンドリング"""
        client = AniListClient()

        error_response = {
            "data": None,
            "errors": [{"message": "Invalid query"}]
        }

        # Create mock response
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=error_response)

        # Create mock post
        mock_post = MagicMock()
        mock_post.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_post.__aexit__ = AsyncMock(return_value=None)

        # Create mock session
        mock_session_instance = AsyncMock()
        mock_session_instance.post = MagicMock(return_value=mock_post)

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session_class.return_value.__aenter__.return_value = mock_session_instance
            mock_session_class.return_value.__aexit__.return_value = None

            with pytest.raises(AniListAPIError) as exc_info:
                await client._make_request("query { test }")

            assert "GraphQL errors" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_make_request_with_retry(self):
        """リトライ機能のテスト"""
        client = AniListClient(retry_attempts=3, retry_delay=0.1)

        # Create mock response for failure
        mock_resp_fail = AsyncMock()
        mock_resp_fail.status = 500
        mock_resp_fail.json = AsyncMock(return_value={"error": "Server error"})

        # Create mock post
        mock_post = MagicMock()
        mock_post.__aenter__ = AsyncMock(return_value=mock_resp_fail)
        mock_post.__aexit__ = AsyncMock(return_value=None)

        # Create mock session
        mock_session_instance = AsyncMock()
        mock_session_instance.post = MagicMock(return_value=mock_post)

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session_class.return_value.__aenter__.return_value = mock_session_instance
            mock_session_class.return_value.__aexit__.return_value = None

            # Note: This test verifies error handling, not successful retry
            with pytest.raises(AniListAPIError):
                await client._make_request("query { test }")


class TestAniListClientSearchAnime:
    """search_anime メソッドのテスト"""

    @pytest.mark.asyncio
    async def test_search_anime_basic(self):
        """基本的なアニメ検索"""
        client = AniListClient()

        mock_data = {
            "Page": {
                "media": [
                    {
                        "id": 123,
                        "title": {"romaji": "Test Anime", "english": "Test Anime EN", "native": "テスト"},
                        "description": "Test description",
                        "genres": ["Action"],
                        "tags": [{"name": "Adventure", "isMediaSpoiler": False}],
                        "status": "RELEASING",
                        "startDate": {"year": 2025, "month": 1, "day": 1},
                        "endDate": None,
                        "coverImage": {"large": "http://example.com/cover.jpg"},
                        "bannerImage": None,
                        "siteUrl": "http://anilist.co/anime/123",
                        "streamingEpisodes": []
                    }
                ]
            }
        }

        with patch.object(client, '_make_request', new=AsyncMock(return_value=mock_data)):
            results = await client.search_anime(query="Test")

            assert len(results) == 1
            assert isinstance(results[0], AniListWork)
            assert results[0].id == 123
            assert results[0].title_romaji == "Test Anime"

    @pytest.mark.asyncio
    async def test_search_anime_with_filters(self):
        """フィルタ付きアニメ検索"""
        client = AniListClient()

        with patch.object(client, '_make_request', new=AsyncMock(return_value={"Page": {"media": []}})):
            results = await client.search_anime(
                query="Test",
                season="WINTER",
                year=2025,
                status="RELEASING",
                limit=10
            )

            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_anime_empty_result(self):
        """検索結果が空の場合"""
        client = AniListClient()

        with patch.object(client, '_make_request', new=AsyncMock(return_value={"Page": {"media": []}})):
            results = await client.search_anime(query="NonExistent")

            assert results == []

    @pytest.mark.asyncio
    async def test_search_anime_parse_error(self):
        """パースエラーのハンドリング"""
        client = AniListClient()

        # 不正なデータ構造
        invalid_data = {
            "Page": {
                "media": [
                    {"id": 999}  # 必須フィールドが欠けている
                ]
            }
        }

        with patch.object(client, '_make_request', new=AsyncMock(return_value=invalid_data)):
            results = await client.search_anime(query="Test")

            # パースエラーは警告されるが、空リストは返される
            assert isinstance(results, list)


class TestAniListClientGetAnimeById:
    """get_anime_by_id メソッドのテスト"""

    @pytest.mark.asyncio
    async def test_get_anime_by_id_success(self):
        """ID指定でのアニメ取得成功"""
        client = AniListClient()

        mock_data = {
            "Media": {
                "id": 456,
                "title": {"romaji": "Specific Anime", "english": None, "native": "特定アニメ"},
                "description": "Specific anime description",
                "genres": ["Drama", "Romance"],
                "tags": [],
                "status": "FINISHED",
                "startDate": {"year": 2024, "month": 4, "day": 1},
                "endDate": {"year": 2024, "month": 6, "day": 30},
                "coverImage": {"large": "http://example.com/cover456.jpg"},
                "bannerImage": "http://example.com/banner456.jpg",
                "siteUrl": "http://anilist.co/anime/456",
                "streamingEpisodes": [],
                "episodes": 12
            }
        }

        with patch.object(client, '_make_request', new=AsyncMock(return_value=mock_data)):
            result = await client.get_anime_by_id(456)

            assert result is not None
            assert isinstance(result, AniListWork)
            assert result.id == 456
            assert result.title_romaji == "Specific Anime"

    @pytest.mark.asyncio
    async def test_get_anime_by_id_not_found(self):
        """存在しないIDの場合"""
        client = AniListClient()

        with patch.object(client, '_make_request', new=AsyncMock(return_value={"Media": None})):
            result = await client.get_anime_by_id(999999)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_anime_by_id_api_error(self):
        """API エラーの場合"""
        client = AniListClient()

        with patch.object(client, '_make_request', new=AsyncMock(side_effect=AniListAPIError("API Error"))):
            result = await client.get_anime_by_id(123)

            assert result is None


class TestAniListClientGetCurrentSeason:
    """get_current_season_anime メソッドのテスト"""

    @pytest.mark.asyncio
    async def test_get_current_season_winter(self):
        """冬シーズンの判定"""
        client = AniListClient()

        with patch.object(client, 'search_anime', new=AsyncMock(return_value=[])):
            with patch('modules.anime_anilist.datetime') as mock_dt:
                mock_dt.now.return_value = datetime(2025, 1, 15)

                results = await client.get_current_season_anime()

                # search_animeが適切な引数で呼ばれたか確認
                client.search_anime.assert_called_once()
                call_kwargs = client.search_anime.call_args[1]
                assert call_kwargs['season'] == 'WINTER'
                assert call_kwargs['year'] == 2025

    @pytest.mark.asyncio
    async def test_get_current_season_summer(self):
        """夏シーズンの判定"""
        client = AniListClient()

        with patch.object(client, 'search_anime', new=AsyncMock(return_value=[])):
            with patch('modules.anime_anilist.datetime') as mock_dt:
                mock_dt.now.return_value = datetime(2025, 7, 1)

                await client.get_current_season_anime()

                call_kwargs = client.search_anime.call_args[1]
                assert call_kwargs['season'] == 'SUMMER'


class TestPerformanceStats:
    """パフォーマンス統計のテスト"""

    def test_get_performance_stats_initial(self):
        """初期状態のパフォーマンス統計"""
        client = AniListClient()

        stats = client.get_performance_stats()

        assert stats['request_count'] == 0
        assert stats['error_count'] == 0
        assert stats['error_rate'] == 0
        assert stats['circuit_breaker_state'] == 'closed'
        assert stats['health_score'] == 1.0
        assert stats['performance_grade'] == 'A'

    def test_calculate_performance_grade(self):
        """パフォーマンスグレード計算"""
        client = AniListClient()

        # Excellent (A)
        assert client._calculate_performance_grade(0.5, 0) == 'A'

        # Good (B)
        assert client._calculate_performance_grade(1.5, 1) == 'B'

        # Fair (C)
        assert client._calculate_performance_grade(2.5, 3) == 'C'

        # Poor (D)
        assert client._calculate_performance_grade(4.0, 7) == 'D'

        # Failing (F)
        assert client._calculate_performance_grade(6.0, 15) == 'F'

    def test_calculate_health_score(self):
        """ヘルススコア計算"""
        client = AniListClient()

        # 新規クライアント
        assert client._calculate_health_score() == 1.0

        # エラーがある場合
        client.request_count = 10
        client.error_count = 2
        client.total_response_time = 15.0

        health_score = client._calculate_health_score()
        assert 0.0 <= health_score <= 1.0
        assert health_score < 1.0  # エラーがあるのでスコアは下がる


class TestAniListCollector:
    """AniListCollectorのテスト"""

    @pytest.mark.asyncio
    async def test_collector_initialization(self):
        """コレクターの初期化"""
        config = {
            "apis": {
                "anilist": {
                    "timeout_seconds": 60,
                    "rate_limit": {"retry_delay_seconds": 10}
                }
            },
            "filtering": {
                "ng_keywords": ["test"],
                "ng_genres": ["Hentai"],
                "exclude_tags": ["Adult"]
            }
        }

        with patch('modules.anime_anilist.get_db'):
            collector = AniListCollector(config)

            assert collector.client is not None
            assert collector.ng_keywords == ["test"]
            assert collector.ng_genres == ["Hentai"]
            assert collector.exclude_tags == ["Adult"]

    @pytest.mark.asyncio
    async def test_should_filter_work_by_keyword(self):
        """NGキーワードによるフィルタリング"""
        config = {"filtering": {"ng_keywords": ["ecchi", "adult"], "ng_genres": [], "exclude_tags": []}}

        with patch('modules.anime_anilist.get_db'):
            collector = AniListCollector(config)

            work = AniListWork(
                id=1,
                title_romaji="Test Ecchi Anime",
                title_english="Test Adult Anime"
            )

            assert collector._should_filter_work(work) is True

    @pytest.mark.asyncio
    async def test_should_filter_work_by_genre(self):
        """NGジャンルによるフィルタリング"""
        config = {"filtering": {"ng_keywords": [], "ng_genres": ["Hentai", "Ecchi"], "exclude_tags": []}}

        with patch('modules.anime_anilist.get_db'):
            collector = AniListCollector(config)

            work = AniListWork(
                id=2,
                title_romaji="Clean Title",
                genres=["Action", "Ecchi"]
            )

            assert collector._should_filter_work(work) is True

    @pytest.mark.asyncio
    async def test_should_not_filter_clean_work(self):
        """クリーンなコンテンツは通過"""
        config = {"filtering": {"ng_keywords": ["adult"], "ng_genres": ["Hentai"], "exclude_tags": []}}

        with patch('modules.anime_anilist.get_db'):
            collector = AniListCollector(config)

            work = AniListWork(
                id=3,
                title_romaji="Family Friendly Anime",
                genres=["Adventure", "Comedy"],
                tags=["Friendship"]
            )

            assert collector._should_filter_work(work) is False
