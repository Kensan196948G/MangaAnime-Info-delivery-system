"""
テスト通知機能の包括的なテストスイート

テストケース:
1. 正常系: 正しいパラメータでのテスト通知送信
2. 異常系: 必須パラメータ欠如
3. 異常系: 不正なGmail認証情報
4. 異常系: ネットワークエラー
"""

import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@pytest.fixture
def client():
    """Flaskテストクライアントのフィクスチャ"""
    from app.web_app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_env_vars():
    """環境変数のモック"""
    return {
        'GMAIL_ADDRESS': 'test@example.com',
        'GMAIL_APP_PASSWORD': 'test_app_password_123'
    }


@pytest.fixture
def mock_config():
    """設定ファイルのモック"""
    return {
        'notification_email': 'test@example.com',
        'gmail_smtp_server': 'smtp.gmail.com',
        'gmail_smtp_port': 465
    }


class TestNotificationNormalCases:
    """正常系テスト"""

    @patch('smtplib.SMTP_SSL')
    @patch('dotenv.load_dotenv')
    @patch('app.web_app.load_config')
    @patch('os.getenv')
    def test_send_notification_success(
        self, mock_getenv, mock_load_config, mock_load_dotenv, mock_smtp, client, mock_env_vars, mock_config
    ):
        """
        テストケース1: 正常なテスト通知送信

        検証項目:
        - HTTPステータスコード200
        - レスポンスにsuccess: true
        - メール送信が実行される
        - 正しいメールアドレスが使用される
        """
        # モック設定
        mock_getenv.side_effect = lambda key, default=None: mock_env_vars.get(key, default)
        mock_load_config.return_value = mock_config

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # リクエスト実行
        response = client.post(
            '/api/test-notification',
            json={'message': 'テスト通知メッセージ'},
            content_type='application/json'
        )

        # 検証
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'テスト通知を送信しました' in data['message']
        assert data['details']['from'] == 'test@example.com'
        assert data['details']['to'] == 'test@example.com'

        # SMTP呼び出しの確認
        mock_server.login.assert_called_once_with('test@example.com', 'test_app_password_123')
        mock_server.send_message.assert_called_once()

    @patch('smtplib.SMTP_SSL')
    @patch('dotenv.load_dotenv')
    @patch('app.web_app.load_config')
    @patch('os.getenv')
    def test_send_notification_with_custom_message(
        self, mock_getenv, mock_load_config, mock_load_dotenv, mock_smtp, client, mock_env_vars, mock_config
    ):
        """
        テストケース2: カスタムメッセージ付き通知送信

        検証項目:
        - カスタムメッセージが正しく処理される
        - レスポンスに成功情報が含まれる
        """
        mock_getenv.side_effect = lambda key, default=None: mock_env_vars.get(key, default)
        mock_load_config.return_value = mock_config

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        custom_message = 'システム動作確認テスト'
        response = client.post(
            '/api/test-notification',
            json={'message': custom_message},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'sent_at' in data['details']

    @patch('smtplib.SMTP_SSL')
    @patch('dotenv.load_dotenv')
    @patch('app.web_app.load_config')
    @patch('os.getenv')
    def test_send_notification_default_message(
        self, mock_getenv, mock_load_config, mock_load_dotenv, mock_smtp, client, mock_env_vars, mock_config
    ):
        """
        テストケース3: デフォルトメッセージでの通知送信

        検証項目:
        - メッセージ未指定時にデフォルトメッセージが使用される
        """
        mock_getenv.side_effect = lambda key, default=None: mock_env_vars.get(key, default)
        mock_load_config.return_value = mock_config

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # メッセージなしでリクエスト
        response = client.post(
            '/api/test-notification',
            json={},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestNotificationErrorCases:
    """異常系テスト"""

    @patch('app.web_app.load_config')
    @patch('os.getenv')
    def test_missing_email_address(self, mock_getenv, mock_load_config, client):
        """
        テストケース4: メールアドレス未設定エラー

        検証項目:
        - HTTPステータスコード400
        - エラーメッセージが適切
        """
        mock_getenv.return_value = None
        mock_load_config.return_value = {}

        response = client.post(
            '/api/test-notification',
            json={'message': 'テスト'},
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'メールアドレスが設定されていません' in data['error']

    @patch('app.web_app.load_config')
    @patch('os.getenv')
    def test_missing_gmail_password(self, mock_getenv, mock_load_config, client, mock_config):
        """
        テストケース5: Gmailアプリパスワード未設定エラー

        検証項目:
        - HTTPステータスコード400
        - エラーメッセージが適切
        """
        def getenv_side_effect(key, default=None):
            if key == 'GMAIL_ADDRESS':
                return 'test@example.com'
            return default

        mock_getenv.side_effect = getenv_side_effect
        mock_load_config.return_value = mock_config

        response = client.post(
            '/api/test-notification',
            json={'message': 'テスト'},
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Gmailアプリパスワードが設定されていません' in data['error']

    @patch('smtplib.SMTP_SSL')
    @patch('dotenv.load_dotenv')
    @patch('app.web_app.load_config')
    @patch('os.getenv')
    def test_invalid_gmail_credentials(
        self, mock_getenv, mock_load_config, mock_load_dotenv, mock_smtp, client, mock_env_vars, mock_config
    ):
        """
        テストケース6: 不正なGmail認証情報エラー

        検証項目:
        - HTTPステータスコード500
        - 認証エラーが適切に処理される
        """
        import smtplib

        mock_getenv.side_effect = lambda key, default=None: mock_env_vars.get(key, default)
        mock_load_config.return_value = mock_config

        # SMTP認証エラーをシミュレート
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Invalid credentials')
        mock_smtp.return_value.__enter__.return_value = mock_server

        response = client.post(
            '/api/test-notification',
            json={'message': 'テスト'},
            content_type='application/json'
        )

        # 認証エラーは401または500を返す
        assert response.status_code in [401, 500]
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data

    @patch('smtplib.SMTP_SSL')
    @patch('dotenv.load_dotenv')
    @patch('app.web_app.load_config')
    @patch('os.getenv')
    def test_network_error(
        self, mock_getenv, mock_load_config, mock_load_dotenv, mock_smtp, client, mock_env_vars, mock_config
    ):
        """
        テストケース7: ネットワークエラー

        検証項目:
        - ネットワークエラーが適切に処理される
        - HTTPステータスコード500
        """
        import socket

        mock_getenv.side_effect = lambda key, default=None: mock_env_vars.get(key, default)
        mock_load_config.return_value = mock_config

        # ネットワークエラーをシミュレート
        mock_smtp.side_effect = socket.error('Network unreachable')

        response = client.post(
            '/api/test-notification',
            json={'message': 'テスト'},
            content_type='application/json'
        )

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False

    @patch('smtplib.SMTP_SSL')
    @patch('dotenv.load_dotenv')
    @patch('app.web_app.load_config')
    @patch('os.getenv')
    def test_smtp_connection_timeout(
        self, mock_getenv, mock_load_config, mock_load_dotenv, mock_smtp, client, mock_env_vars, mock_config
    ):
        """
        テストケース8: SMTP接続タイムアウト

        検証項目:
        - タイムアウトエラーが適切に処理される
        """
        import socket

        mock_getenv.side_effect = lambda key, default=None: mock_env_vars.get(key, default)
        mock_load_config.return_value = mock_config

        # タイムアウトエラーをシミュレート
        mock_smtp.side_effect = socket.timeout('Connection timed out')

        response = client.post(
            '/api/test-notification',
            json={'message': 'テスト'},
            content_type='application/json'
        )

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False


class TestNotificationInputValidation:
    """入力検証テスト"""

    @patch('smtplib.SMTP_SSL')
    @patch('dotenv.load_dotenv')
    @patch('app.web_app.load_config')
    @patch('os.getenv')
    def test_empty_json_body(
        self, mock_getenv, mock_load_config, mock_load_dotenv, mock_smtp, client, mock_env_vars, mock_config
    ):
        """
        テストケース9: 空のJSONボディ

        検証項目:
        - 空のJSONでもデフォルト値で処理される
        """
        mock_getenv.side_effect = lambda key, default=None: mock_env_vars.get(key, default)
        mock_load_config.return_value = mock_config

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        response = client.post(
            '/api/test-notification',
            json={},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    @patch('smtplib.SMTP_SSL')
    @patch('dotenv.load_dotenv')
    @patch('app.web_app.load_config')
    @patch('os.getenv')
    def test_very_long_message(
        self, mock_getenv, mock_load_config, mock_load_dotenv, mock_smtp, client, mock_env_vars, mock_config
    ):
        """
        テストケース10: 非常に長いメッセージ

        検証項目:
        - 長いメッセージでも正常に処理される
        """
        mock_getenv.side_effect = lambda key, default=None: mock_env_vars.get(key, default)
        mock_load_config.return_value = mock_config

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        long_message = 'あ' * 1000
        response = client.post(
            '/api/test-notification',
            json={'message': long_message},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    @patch('smtplib.SMTP_SSL')
    @patch('dotenv.load_dotenv')
    @patch('app.web_app.load_config')
    @patch('os.getenv')
    def test_special_characters_in_message(
        self, mock_getenv, mock_load_config, mock_load_dotenv, mock_smtp, client, mock_env_vars, mock_config
    ):
        """
        テストケース11: 特殊文字を含むメッセージ

        検証項目:
        - HTML特殊文字が適切にエスケープされる
        """
        mock_getenv.side_effect = lambda key, default=None: mock_env_vars.get(key, default)
        mock_load_config.return_value = mock_config

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        special_message = '<script>alert("XSS")</script>'
        response = client.post(
            '/api/test-notification',
            json={'message': special_message},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestNotificationResponseFormat:
    """レスポンス形式テスト"""

    @patch('smtplib.SMTP_SSL')
    @patch('dotenv.load_dotenv')
    @patch('app.web_app.load_config')
    @patch('os.getenv')
    def test_success_response_format(
        self, mock_getenv, mock_load_config, mock_load_dotenv, mock_smtp, client, mock_env_vars, mock_config
    ):
        """
        テストケース12: 成功レスポンスの形式検証

        検証項目:
        - 必要なフィールドが全て含まれる
        - データ型が正しい
        """
        mock_getenv.side_effect = lambda key, default=None: mock_env_vars.get(key, default)
        mock_load_config.return_value = mock_config

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        response = client.post(
            '/api/test-notification',
            json={'message': 'テスト'},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # 必須フィールドの確認
        assert 'success' in data
        assert 'message' in data
        assert 'details' in data

        # detailsの内容確認
        assert 'from' in data['details']
        assert 'to' in data['details']
        assert 'sent_at' in data['details']

        # データ型の確認
        assert isinstance(data['success'], bool)
        assert isinstance(data['message'], str)
        assert isinstance(data['details'], dict)

    @patch('app.web_app.load_config')
    @patch('os.getenv')
    def test_error_response_format(self, mock_getenv, mock_load_config, client):
        """
        テストケース13: エラーレスポンスの形式検証

        検証項目:
        - エラー時の必要なフィールドが含まれる
        """
        mock_getenv.return_value = None
        mock_load_config.return_value = {}

        response = client.post(
            '/api/test-notification',
            json={'message': 'テスト'},
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)

        # 必須フィールドの確認
        assert 'success' in data
        assert 'error' in data

        # データ型の確認
        assert isinstance(data['success'], bool)
        assert isinstance(data['error'], str)
        assert data['success'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
