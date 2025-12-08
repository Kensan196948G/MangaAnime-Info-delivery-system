"""
Gmail APIのモッククラス

テストで使用するGmail APIのモック実装を提供します。
"""

from unittest.mock import MagicMock, Mock
from typing import Dict, Any, Optional
import base64


class MockGmailMessage:
    """Gmail メッセージのモック"""

    def __init__(self, message_id: str = 'test_msg_id', thread_id: str = 'test_thread_id'):
        self.id = message_id
        self.threadId = thread_id
        self.labelIds = ['SENT']

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'threadId': self.threadId,
            'labelIds': self.labelIds
        }


class MockGmailService:
    """Gmail APIサービスのモック"""

    def __init__(self, simulate_error: Optional[str] = None):
        """
        Args:
            simulate_error: シミュレートするエラータイプ
                - 'auth': 認証エラー
                - 'rate_limit': レート制限エラー
                - 'network': ネットワークエラー
                - None: 正常動作
        """
        self.simulate_error = simulate_error
        self.sent_messages = []
        self.call_count = 0

    def users(self):
        """usersリソースを返す"""
        return self

    def messages(self):
        """messagesリソースを返す"""
        return self

    def send(self, userId: str = 'me', body: Optional[Dict] = None):
        """メッセージ送信のモック"""
        self.call_count += 1

        if self.simulate_error == 'auth':
            from google.auth.exceptions import RefreshError
            raise RefreshError("Token has been expired or revoked")

        if self.simulate_error == 'rate_limit':
            from googleapiclient.errors import HttpError
            resp = Mock()
            resp.status = 429
            error_content = b'{"error": {"code": 429, "message": "Rate limit exceeded"}}'
            raise HttpError(resp, error_content)

        if self.simulate_error == 'network':
            import requests
            raise requests.ConnectionError("Network unreachable")

        # 正常系
        message = MockGmailMessage()
        self.sent_messages.append(body)
        return MockExecute(message.to_dict())

    def create(self, userId: str = 'me', body: Optional[Dict] = None):
        """メッセージ作成のモック"""
        return self.send(userId, body)

    def execute(self):
        """execute()のモック"""
        if self.simulate_error:
            raise RuntimeError(f"Simulated error: {self.simulate_error}")
        return {'id': 'mock_message_id', 'threadId': 'mock_thread_id'}


class MockExecute:
    """execute()メソッドのモック"""

    def __init__(self, return_value: Dict[str, Any]):
        self.return_value = return_value

    def execute(self):
        return self.return_value


class MockGmailClient:
    """Gmail クライアント全体のモック"""

    def __init__(self, credentials=None):
        self.credentials = credentials or self._create_mock_credentials()
        self.service = MockGmailService()

    @staticmethod
    def _create_mock_credentials():
        """モック認証情報を作成"""
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.refresh_token = 'mock_refresh_token'
        return mock_creds

    def send_message(self, to: str, subject: str, body: str, html: bool = False) -> Dict[str, Any]:
        """
        メール送信のヘルパーメソッド

        Args:
            to: 宛先メールアドレス
            subject: 件名
            body: 本文
            html: HTMLメールかどうか

        Returns:
            送信結果の辞書
        """
        message = self._create_message(to, subject, body, html)
        result = self.service.users().messages().send(
            userId='me',
            body={'raw': message}
        ).execute()

        return result

    @staticmethod
    def _create_message(to: str, subject: str, body: str, html: bool = False) -> str:
        """
        MIMEメッセージを作成（簡易版）

        Returns:
            base64エンコードされたメッセージ
        """
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        if html:
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['subject'] = subject
            html_part = MIMEText(body, 'html')
            message.attach(html_part)
        else:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject

        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode('utf-8')

        return raw_message


class MockGmailAPIError:
    """Gmail APIエラーのモックヘルパー"""

    @staticmethod
    def create_auth_error():
        """認証エラーを作成"""
        from google.auth.exceptions import RefreshError
        return RefreshError("Token has been expired or revoked")

    @staticmethod
    def create_rate_limit_error():
        """レート制限エラーを作成"""
        from googleapiclient.errors import HttpError
        resp = Mock()
        resp.status = 429
        error_content = b'{"error": {"code": 429, "message": "Rate limit exceeded"}}'
        return HttpError(resp, error_content)

    @staticmethod
    def create_quota_exceeded_error():
        """クォータ超過エラーを作成"""
        from googleapiclient.errors import HttpError
        resp = Mock()
        resp.status = 403
        error_content = b'{"error": {"code": 403, "message": "Quota exceeded"}}'
        return HttpError(resp, error_content)

    @staticmethod
    def create_invalid_recipient_error():
        """無効な宛先エラーを作成"""
        from googleapiclient.errors import HttpError
        resp = Mock()
        resp.status = 400
        error_content = b'{"error": {"code": 400, "message": "Invalid recipient"}}'
        return HttpError(resp, error_content)


def create_mock_gmail_service(error_type: Optional[str] = None) -> MockGmailService:
    """
    Gmail APIサービスモックを作成するファクトリー関数

    Args:
        error_type: シミュレートするエラータイプ

    Returns:
        MockGmailService インスタンス
    """
    return MockGmailService(simulate_error=error_type)
