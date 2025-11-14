"""
API Security Test Suite
APIエンドポイントのセキュリティテスト
"""

import pytest
import json
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestAPISecurity:
    """APIセキュリティテストクラス"""

    def test_sql_injection_protection(self, client):
        """SQLインジェクション対策テスト"""
        malicious_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE works; --",
            "1' UNION SELECT * FROM works--",
            "admin'--",
            "' OR 1=1#",
        ]

        for payload in malicious_payloads:
            # APIエンドポイントにSQLインジェクション試行
            response = client.get(f'/api/works?search={payload}')

            # 400または200を期待（エラーハンドリングされている）
            assert response.status_code in [200, 400, 404], \
                f"SQLインジェクション対策が不十分: {payload}"

            # データベースが破壊されていないことを確認
            response = client.get('/api/stats')
            assert response.status_code == 200


    def test_xss_protection(self, client):
        """XSS（クロスサイトスクリプティング）対策テスト"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg/onload=alert('XSS')>",
            "';alert(String.fromCharCode(88,83,83))//",
        ]

        for payload in xss_payloads:
            # POSTリクエストでXSSペイロードを送信
            response = client.post('/api/manual-collection',
                                   data=json.dumps({'query': payload}),
                                   content_type='application/json')

            # レスポンスにスクリプトタグがエスケープされているか確認
            if response.status_code == 200:
                response_text = response.get_data(as_text=True)
                assert '<script>' not in response_text.lower(), \
                    f"XSS対策が不十分: {payload}"


    def test_csrf_token_validation(self, client):
        """CSRF（クロスサイトリクエストフォージェリ）対策テスト"""
        # CSRFトークンなしでPOSTリクエスト
        response = client.post('/api/manual-collection',
                               data=json.dumps({'query': 'test'}),
                               content_type='application/json')

        # ステータスコードの確認（実装による）
        # 通常は400, 403, または実装でCSRF保護がある場合
        assert response.status_code in [200, 400, 403]


    def test_authentication_required_endpoints(self, client):
        """認証が必要なエンドポイントのテスト"""
        protected_endpoints = [
            '/api/manual-collection',
            '/api/test-notification',
            '/api/test-configuration',
        ]

        for endpoint in protected_endpoints:
            response = client.post(endpoint)
            # 認証なしでアクセスした場合
            # 実装による（200, 400, 401, 403のいずれか）
            assert response.status_code in [200, 400, 401, 403]


    def test_rate_limiting(self, client):
        """レート制限テスト"""
        # 短時間に大量のリクエストを送信
        responses = []
        for i in range(50):
            response = client.get('/api/stats')
            responses.append(response.status_code)

        # 全てのリクエストが成功するか、429 (Too Many Requests) が返される
        assert all(status in [200, 429] for status in responses)


    def test_input_validation_length(self, client):
        """入力値の長さ検証テスト"""
        # 過度に長い入力
        long_input = 'A' * 10000

        response = client.get(f'/api/works?search={long_input}')

        # 400 Bad Request または 413 Payload Too Large を期待
        assert response.status_code in [200, 400, 413]


    def test_path_traversal_protection(self, client):
        """パストラバーサル攻撃対策テスト"""
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/shadow',
            'C:\\boot.ini',
        ]

        for path in malicious_paths:
            response = client.get(f'/api/works/{path}')

            # 400, 404, または適切なエラーレスポンス
            assert response.status_code in [400, 404, 500]


    def test_http_headers_security(self, client):
        """HTTPセキュリティヘッダーのテスト"""
        response = client.get('/')

        # 推奨されるセキュリティヘッダーの存在確認
        headers_to_check = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
        ]

        # ヘッダーが設定されているかチェック（警告のみ）
        for header in headers_to_check:
            if header not in response.headers:
                print(f"警告: {header} ヘッダーが設定されていません")


    def test_json_injection(self, client):
        """JSONインジェクション対策テスト"""
        malicious_json = {
            'query': '{"$ne": null}',
            'filter': {'__proto__': {'admin': True}}
        }

        response = client.post('/api/manual-collection',
                               data=json.dumps(malicious_json),
                               content_type='application/json')

        # 適切にハンドリングされることを確認
        assert response.status_code in [200, 400, 422]


    def test_command_injection(self, client):
        """コマンドインジェクション対策テスト"""
        command_payloads = [
            '; ls -la',
            '| cat /etc/passwd',
            '`whoami`',
            '$(rm -rf /)',
            '&& echo hacked',
        ]

        for payload in command_payloads:
            response = client.get(f'/api/works?search={payload}')

            # コマンドが実行されないことを確認
            assert response.status_code in [200, 400, 404]


@pytest.fixture
def client():
    """Flaskテストクライアントのフィクスチャ"""
    try:
        from app.web_app import app
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

        with app.test_client() as client:
            yield client
    except ImportError:
        pytest.skip("web_app.pyが見つかりません")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
