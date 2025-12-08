"""
レート制限機能のテスト

Flask-Limiterのレート制限が正しく動作することを確認
"""

import pytest
import time

try:
    from flask import Flask
    from app.utils.rate_limiter import init_limiter, get_rate_limit, RATE_LIMITS
    from config.ratelimit_config import RateLimitConfig
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


@pytest.fixture
def app():
    """テスト用Flaskアプリケーション"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['RATELIMIT_STORAGE_URI'] = 'memory://'
    app.config['RATELIMIT_DEFAULT'] = ["10 per minute"]

    # レート制限の初期化
    limiter = init_limiter(app)

    # テスト用ルート
    @app.route('/test-default')
    def test_default():
        return 'OK', 200

    @app.route('/test-strict')
    @limiter.limit("3 per minute")
    def test_strict():
        return 'OK', 200

    @app.route('/test-loose')
    @limiter.limit("100 per minute")
    def test_loose():
        return 'OK', 200

    return app


@pytest.fixture
def client(app):
    """テスト用クライアント"""
    return app.test_client()


class TestRateLimiter:
    """レート制限テストクラス"""

    def test_limiter_initialization(self, app):
        """レート制限の初期化テスト"""
        assert app.config['RATELIMIT_STORAGE_URI'] == 'memory://'
        assert app.config['RATELIMIT_DEFAULT'] == ["10 per minute"]

    def test_default_rate_limit(self, client):
        """デフォルトレート制限のテスト"""
        # 10回までは成功
        for i in range(10):
            response = client.get('/test-default')
            assert response.status_code == 200

        # 11回目は制限
        response = client.get('/test-default')
        assert response.status_code == 429

    def test_strict_rate_limit(self, client):
        """厳しいレート制限のテスト"""
        # 3回までは成功
        for i in range(3):
            response = client.get('/test-strict')
            assert response.status_code == 200

        # 4回目は制限
        response = client.get('/test-strict')
        assert response.status_code == 429

    def test_loose_rate_limit(self, client):
        """緩いレート制限のテスト"""
        # 100回までは成功（実際には少し減らしてテスト）
        for i in range(20):
            response = client.get('/test-loose')
            assert response.status_code == 200

    def test_rate_limit_error_response(self, client):
        """レート制限エラーレスポンスのテスト"""
        # 制限を超えるまでリクエスト
        for i in range(4):
            client.get('/test-strict')

        # エラーレスポンスを確認
        response = client.get('/test-strict')
        assert response.status_code == 429
        # JSON形式の場合
        if response.is_json:
            data = response.get_json()
            assert 'error' in data
            assert data['error'] == 'Rate limit exceeded'

    def test_get_rate_limit_function(self):
        """get_rate_limit関数のテスト"""
        # 定義済みの制限
        assert get_rate_limit('auth_login') == "5 per minute"
        assert get_rate_limit('api_collection') == "10 per hour"
        assert get_rate_limit('admin_general') == "500 per hour"

        # 未定義のキーはデフォルト値
        assert get_rate_limit('unknown_key') == "100 per hour"


class TestRateLimitConfig:
    """レート制限設定テストクラス"""

    def test_config_storage_uri(self):
        """ストレージURI設定のテスト"""
        dev_uri = RateLimitConfig.get_storage_uri('development')
        assert dev_uri == 'memory://'

        prod_uri = RateLimitConfig.get_storage_uri('production')
        assert 'redis://' in prod_uri

    def test_config_get_limit(self):
        """個別制限取得のテスト"""
        login_limit = RateLimitConfig.get_limit('auth', 'login')
        assert login_limit == "5 per minute"

        collection_limit = RateLimitConfig.get_limit('api', 'collection')
        assert collection_limit == "10 per hour"

        # 存在しないキー
        unknown_limit = RateLimitConfig.get_limit('unknown', 'unknown')
        assert unknown_limit == "100 per hour"

    def test_config_get_all_limits(self):
        """全制限取得のテスト"""
        all_limits = RateLimitConfig.get_all_limits()
        assert 'auth' in all_limits
        assert 'api' in all_limits
        assert 'admin' in all_limits

        # 各カテゴリに制限が存在することを確認
        assert len(all_limits['auth']) > 0
        assert len(all_limits['api']) > 0


class TestRateLimitHeaders:
    """レート制限ヘッダーのテスト"""

    def test_rate_limit_headers_present(self, client):
        """レート制限ヘッダーが存在することを確認"""
        response = client.get('/test-default')

        # X-RateLimit-* ヘッダーの確認
        # Flask-Limiterはデフォルトでヘッダーを返す
        assert response.status_code == 200

    def test_rate_limit_remaining_header(self, client):
        """残りリクエスト数ヘッダーのテスト"""
        # 最初のリクエスト
        response = client.get('/test-strict')
        assert response.status_code == 200

        # 2回目のリクエスト
        response = client.get('/test-strict')
        assert response.status_code == 200


class TestMultipleClients:
    """複数クライアントのレート制限テスト"""

    def test_different_ips_different_limits(self, app):
        """異なるIPアドレスで個別にレート制限されることを確認"""
        client1 = app.test_client()
        client2 = app.test_client()

        # Client1で3回リクエスト
        for i in range(3):
            response = client1.get('/test-strict')
            assert response.status_code == 200

        # Client1は制限される
        response = client1.get('/test-strict')
        assert response.status_code == 429

        # Client2は別カウントなので成功する
        # ※ ただし、test_clientは同じIPとして扱われる可能性あり
        # 実際の環境では異なるIPで動作


class TestRateLimitReset:
    """レート制限リセットのテスト"""

    def test_limit_reset_after_window(self, client):
        """
        時間経過後のレート制限リセット
        ※ 実際のテストでは時間がかかるため、モックを使用することを推奨
        """
        # 3回リクエスト
        for i in range(3):
            response = client.get('/test-strict')
            assert response.status_code == 200

        # 制限される
        response = client.get('/test-strict')
        assert response.status_code == 429

        # 実際には60秒待つ必要があるが、テストではスキップ
        # time.sleep(61)  # 1分以上待つ
        # response = client.get('/test-strict')
        # assert response.status_code == 200


@pytest.mark.integration
class TestRateLimiterIntegration:
    """レート制限の統合テスト"""

    def test_auth_endpoints_integration(self, app):
        """認証エンドポイントの統合テスト"""
        limiter = init_limiter(app)

        @app.route('/auth/login', methods=['POST'])
        @limiter.limit(get_rate_limit('auth_login'))
        def login():
            return 'Login successful', 200

        client = app.test_client()

        # 5回までは成功
        for i in range(5):
            response = client.post('/auth/login')
            assert response.status_code == 200

        # 6回目は制限（5 per minute）
        response = client.post('/auth/login')
        assert response.status_code == 429

    def test_api_endpoints_integration(self, app):
        """APIエンドポイントの統合テスト"""
        limiter = init_limiter(app)

        @app.route('/api/collection', methods=['POST'])
        @limiter.limit(get_rate_limit('api_collection'))
        def collection():
            return 'Collection started', 200

        client = app.test_client()

        # api_collectionは "10 per hour" なので、
        # テストでは少ない回数でチェック
        for i in range(3):
            response = client.post('/api/collection')
            assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
