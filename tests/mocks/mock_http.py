"""
HTTPリクエストのモッククラス

テストで使用するHTTPリクエスト（requests、AniList、RSS）のモック実装を提供します。
"""

from unittest.mock import Mock
from typing import Dict, Any, Optional, List
import json


class MockHTTPResponse:
    """HTTPレスポンスのモック"""

    def __init__(
        self,
        status_code: int = 200,
        json_data: Optional[Dict] = None,
        text: str = '',
        headers: Optional[Dict] = None,
        raise_for_status_error: Optional[Exception] = None
    ):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.content = text.encode('utf-8')
        self.headers = headers or {}
        self._raise_for_status_error = raise_for_status_error
        self.ok = status_code < 400

    def json(self):
        """JSONデータを返す"""
        if self._json_data is not None:
            return self._json_data
        raise ValueError("No JSON data available")

    def raise_for_status(self):
        """ステータスコードをチェック"""
        if self._raise_for_status_error:
            raise self._raise_for_status_error
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"{self.status_code} Error")


class MockHTTPClient:
    """HTTPクライアントのモック"""

    def __init__(self, default_response: Optional[MockHTTPResponse] = None):
        """
        Args:
            default_response: デフォルトのレスポンス
        """
        self.default_response = default_response or MockHTTPResponse()
        self.request_history: List[Dict[str, Any]] = []
        self.response_queue: List[MockHTTPResponse] = []

    def get(self, url: str, **kwargs) -> MockHTTPResponse:
        """GETリクエストのモック"""
        self.request_history.append({
            'method': 'GET',
            'url': url,
            'kwargs': kwargs
        })

        if self.response_queue:
            return self.response_queue.pop(0)

        return self.default_response

    def post(self, url: str, **kwargs) -> MockHTTPResponse:
        """POSTリクエストのモック"""
        self.request_history.append({
            'method': 'POST',
            'url': url,
            'kwargs': kwargs
        })

        if self.response_queue:
            return self.response_queue.pop(0)

        return self.default_response

    def put(self, url: str, **kwargs) -> MockHTTPResponse:
        """PUTリクエストのモック"""
        self.request_history.append({
            'method': 'PUT',
            'url': url,
            'kwargs': kwargs
        })

        if self.response_queue:
            return self.response_queue.pop(0)

        return self.default_response

    def delete(self, url: str, **kwargs) -> MockHTTPResponse:
        """DELETEリクエストのモック"""
        self.request_history.append({
            'method': 'DELETE',
            'url': url,
            'kwargs': kwargs
        })

        if self.response_queue:
            return self.response_queue.pop(0)

        return self.default_response

    def add_response(self, response: MockHTTPResponse):
        """レスポンスをキューに追加"""
        self.response_queue.append(response)

    def clear_history(self):
        """リクエスト履歴をクリア"""
        self.request_history = []

    def get_last_request(self) -> Optional[Dict[str, Any]]:
        """最後のリクエストを取得"""
        if self.request_history:
            return self.request_history[-1]
        return None


class MockAniListAPI:
    """AniList GraphQL APIのモック"""

    @staticmethod
    def create_success_response(media_count: int = 1) -> MockHTTPResponse:
        """成功レスポンスを作成"""
        media_list = []
        for i in range(media_count):
            media_list.append({
                'id': 10000 + i,
                'title': {
                    'romaji': f'Test Anime {i+1}',
                    'native': f'テストアニメ{i+1}',
                    'english': f'Test Anime {i+1} EN'
                },
                'nextAiringEpisode': {
                    'episode': 1,
                    'airingAt': 1704067200 + (i * 86400)  # 1日ずつずらす
                },
                'genres': ['Action', 'Comedy'],
                'tags': [
                    {'name': 'Shounen', 'rank': 90}
                ],
                'description': f'Test anime {i+1} description',
                'siteUrl': f'https://anilist.co/anime/{10000+i}',
                'streamingEpisodes': [
                    {
                        'title': f'Episode {1}',
                        'thumbnail': 'https://example.com/thumb.jpg',
                        'url': 'https://example.com/watch',
                        'site': 'Crunchyroll'
                    }
                ]
            })

        return MockHTTPResponse(
            status_code=200,
            json_data={
                'data': {
                    'Page': {
                        'pageInfo': {
                            'total': media_count,
                            'currentPage': 1,
                            'lastPage': 1,
                            'hasNextPage': False
                        },
                        'media': media_list
                    }
                }
            }
        )

    @staticmethod
    def create_rate_limit_response() -> MockHTTPResponse:
        """レート制限レスポンスを作成"""
        return MockHTTPResponse(
            status_code=429,
            json_data={
                'errors': [
                    {
                        'message': 'Rate limit exceeded',
                        'status': 429
                    }
                ]
            },
            headers={'Retry-After': '60'}
        )

    @staticmethod
    def create_error_response() -> MockHTTPResponse:
        """エラーレスポンスを作成"""
        return MockHTTPResponse(
            status_code=500,
            json_data={
                'errors': [
                    {
                        'message': 'Internal server error',
                        'status': 500
                    }
                ]
            }
        )

    @staticmethod
    def create_graphql_error_response() -> MockHTTPResponse:
        """GraphQLエラーレスポンスを作成"""
        return MockHTTPResponse(
            status_code=200,
            json_data={
                'errors': [
                    {
                        'message': 'Field error',
                        'locations': [{'line': 1, 'column': 1}],
                        'path': ['Page', 'media']
                    }
                ]
            }
        )


class MockRSSFeed:
    """RSSフィードのモック"""

    @staticmethod
    def create_valid_feed(item_count: int = 1) -> str:
        """有効なRSSフィードを作成"""
        items = []
        for i in range(item_count):
            items.append(f"""
            <item>
                <title>テストマンガ 第{i+1}巻</title>
                <link>https://example.com/manga/{i+1}</link>
                <pubDate>Mon, 0{i+1} Jan 2024 00:00:00 +0000</pubDate>
                <description>テストマンガ第{i+1}巻の説明</description>
                <guid>https://example.com/manga/{i+1}</guid>
            </item>
            """)

        return f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Manga Feed</title>
                <link>https://example.com/</link>
                <description>Test manga RSS feed</description>
                <language>ja</language>
                {''.join(items)}
            </channel>
        </rss>
        """

    @staticmethod
    def create_malformed_feed() -> str:
        """不正なRSSフィードを作成"""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Broken Feed</title>
                <item>
                    <title>Missing closing tag
                    <link>https://example.com/</link>
                </item>
        """

    @staticmethod
    def create_empty_feed() -> str:
        """空のRSSフィードを作成"""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Empty Feed</title>
                <link>https://example.com/</link>
                <description>No items</description>
            </channel>
        </rss>
        """

    @staticmethod
    def create_response(feed_xml: str, status_code: int = 200) -> MockHTTPResponse:
        """RSSフィードレスポンスを作成"""
        return MockHTTPResponse(
            status_code=status_code,
            text=feed_xml,
            headers={'Content-Type': 'application/rss+xml; charset=utf-8'}
        )


class MockHTTPError:
    """HTTPエラーのモックヘルパー"""

    @staticmethod
    def create_timeout_error():
        """タイムアウトエラーを作成"""
        import requests
        return requests.Timeout("Connection timeout")

    @staticmethod
    def create_connection_error():
        """接続エラーを作成"""
        import requests
        return requests.ConnectionError("Failed to establish connection")

    @staticmethod
    def create_ssl_error():
        """SSL証明書エラーを作成"""
        import requests
        return requests.SSLError("SSL certificate verification failed")

    @staticmethod
    def create_http_error(status_code: int = 500):
        """HTTPエラーを作成"""
        import requests
        response = MockHTTPResponse(
            status_code=status_code,
            raise_for_status_error=requests.HTTPError(f"{status_code} Error")
        )
        return requests.HTTPError(f"{status_code} Error", response=response)


def create_mock_http_client(
    success: bool = True,
    response_data: Optional[Dict] = None,
    status_code: int = 200
) -> MockHTTPClient:
    """
    HTTPクライアントモックを作成するファクトリー関数

    Args:
        success: 成功レスポンスかどうか
        response_data: レスポンスデータ
        status_code: HTTPステータスコード

    Returns:
        MockHTTPClient インスタンス
    """
    if success:
        default_response = MockHTTPResponse(
            status_code=status_code,
            json_data=response_data or {'status': 'success'}
        )
    else:
        default_response = MockHTTPResponse(
            status_code=status_code,
            json_data={'error': 'Request failed'}
        )

    return MockHTTPClient(default_response=default_response)


def create_anilist_mock_client(media_count: int = 1) -> MockHTTPClient:
    """
    AniList API用のモッククライアントを作成

    Args:
        media_count: 返すメディア数

    Returns:
        MockHTTPClient インスタンス
    """
    response = MockAniListAPI.create_success_response(media_count)
    client = MockHTTPClient(default_response=response)
    return client


def create_rss_mock_client(item_count: int = 1) -> MockHTTPClient:
    """
    RSS Feed用のモッククライアントを作成

    Args:
        item_count: 返すアイテム数

    Returns:
        MockHTTPClient インスタンス
    """
    feed_xml = MockRSSFeed.create_valid_feed(item_count)
    response = MockRSSFeed.create_response(feed_xml)
    client = MockHTTPClient(default_response=response)
    return client
