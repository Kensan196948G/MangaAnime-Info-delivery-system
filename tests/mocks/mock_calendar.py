"""
Google Calendar APIのモッククラス

テストで使用するGoogle Calendar APIのモック実装を提供します。
"""

from unittest.mock import MagicMock, Mock
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class MockCalendarEvent:
    """カレンダーイベントのモック"""

    def __init__(
        self,
        event_id: str = 'test_event_id',
        summary: str = 'Test Event',
        start: datetime = None,
        end: datetime = None,
        description: str = '',
        location: str = ''
    ):
        self.id = event_id
        self.summary = summary
        self.start = start or datetime(2024, 1, 1, 0, 0, 0)
        self.end = end or (self.start + timedelta(hours=1))
        self.description = description
        self.location = location
        self.htmlLink = f'https://calendar.google.com/event/{event_id}'

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'summary': self.summary,
            'start': {
                'dateTime': self.start.isoformat() + 'Z',
                'timeZone': 'Asia/Tokyo'
            },
            'end': {
                'dateTime': self.end.isoformat() + 'Z',
                'timeZone': 'Asia/Tokyo'
            },
            'description': self.description,
            'location': self.location,
            'htmlLink': self.htmlLink,
            'status': 'confirmed',
            'created': datetime.now().isoformat() + 'Z',
            'updated': datetime.now().isoformat() + 'Z'
        }


class MockCalendarService:
    """Google Calendar APIサービスのモック"""

    def __init__(self, simulate_error: Optional[str] = None):
        """
        Args:
            simulate_error: シミュレートするエラータイプ
                - 'auth': 認証エラー
                - 'permission': 権限エラー
                - 'not_found': カレンダーが見つからない
                - 'duplicate': 重複イベント
                - None: 正常動作
        """
        self.simulate_error = simulate_error
        self.events_storage: List[Dict[str, Any]] = []
        self.call_count = 0

    def events(self):
        """eventsリソースを返す"""
        return self

    def calendars(self):
        """calendarsリソースを返す"""
        return self

    def insert(self, calendarId: str = 'primary', body: Optional[Dict] = None):
        """イベント挿入のモック"""
        self.call_count += 1

        if self.simulate_error == 'auth':
            from google.auth.exceptions import RefreshError
            raise RefreshError("Token has been expired or revoked")

        if self.simulate_error == 'permission':
            from googleapiclient.errors import HttpError
            resp = Mock()
            resp.status = 403
            error_content = b'{"error": {"code": 403, "message": "Forbidden"}}'
            raise HttpError(resp, error_content)

        if self.simulate_error == 'not_found':
            from googleapiclient.errors import HttpError
            resp = Mock()
            resp.status = 404
            error_content = b'{"error": {"code": 404, "message": "Calendar not found"}}'
            raise HttpError(resp, error_content)

        if self.simulate_error == 'duplicate':
            # 重複チェック（同じsummaryとstartが存在）
            for event in self.events_storage:
                if (event.get('summary') == body.get('summary') and
                    event.get('start') == body.get('start')):
                    return MockExecute({
                        'error': 'Duplicate event detected',
                        'existing_event': event
                    })

        # 正常系
        event = MockCalendarEvent(
            event_id=f'event_{len(self.events_storage)}',
            summary=body.get('summary', 'Untitled'),
            start=datetime.fromisoformat(body.get('start', {}).get('dateTime', '2024-01-01T00:00:00').rstrip('Z')),
            end=datetime.fromisoformat(body.get('end', {}).get('dateTime', '2024-01-01T01:00:00').rstrip('Z')),
            description=body.get('description', ''),
            location=body.get('location', '')
        )

        event_dict = event.to_dict()
        self.events_storage.append(event_dict)

        return MockExecute(event_dict)

    def list(self, calendarId: str = 'primary', **kwargs):
        """イベント一覧取得のモック"""
        self.call_count += 1

        if self.simulate_error == 'auth':
            from google.auth.exceptions import RefreshError
            raise RefreshError("Token has been expired or revoked")

        # フィルタリング
        filtered_events = self.events_storage

        # 時刻範囲でフィルタ
        if 'timeMin' in kwargs:
            time_min = datetime.fromisoformat(kwargs['timeMin'].rstrip('Z'))
            filtered_events = [
                e for e in filtered_events
                if datetime.fromisoformat(e['start']['dateTime'].rstrip('Z')) >= time_min
            ]

        if 'timeMax' in kwargs:
            time_max = datetime.fromisoformat(kwargs['timeMax'].rstrip('Z'))
            filtered_events = [
                e for e in filtered_events
                if datetime.fromisoformat(e['start']['dateTime'].rstrip('Z')) <= time_max
            ]

        # 検索クエリでフィルタ
        if 'q' in kwargs:
            query = kwargs['q'].lower()
            filtered_events = [
                e for e in filtered_events
                if query in e.get('summary', '').lower() or query in e.get('description', '').lower()
            ]

        return MockExecute({
            'items': filtered_events,
            'kind': 'calendar#events',
            'summary': calendarId
        })

    def get(self, calendarId: str = 'primary', eventId: str = ''):
        """特定イベント取得のモック"""
        self.call_count += 1

        for event in self.events_storage:
            if event['id'] == eventId:
                return MockExecute(event)

        # イベントが見つからない場合
        from googleapiclient.errors import HttpError
        resp = Mock()
        resp.status = 404
        error_content = b'{"error": {"code": 404, "message": "Event not found"}}'
        raise HttpError(resp, error_content)

    def update(self, calendarId: str = 'primary', eventId: str = '', body: Optional[Dict] = None):
        """イベント更新のモック"""
        self.call_count += 1

        for i, event in enumerate(self.events_storage):
            if event['id'] == eventId:
                # 既存イベントを更新
                updated_event = event.copy()
                updated_event.update(body)
                updated_event['updated'] = datetime.now().isoformat() + 'Z'
                self.events_storage[i] = updated_event
                return MockExecute(updated_event)

        # イベントが見つからない場合
        from googleapiclient.errors import HttpError
        resp = Mock()
        resp.status = 404
        error_content = b'{"error": {"code": 404, "message": "Event not found"}}'
        raise HttpError(resp, error_content)

    def delete(self, calendarId: str = 'primary', eventId: str = ''):
        """イベント削除のモック"""
        self.call_count += 1

        for i, event in enumerate(self.events_storage):
            if event['id'] == eventId:
                self.events_storage.pop(i)
                return MockExecute({'status': 'deleted'})

        # イベントが見つからない場合
        from googleapiclient.errors import HttpError
        resp = Mock()
        resp.status = 404
        error_content = b'{"error": {"code": 404, "message": "Event not found"}}'
        raise HttpError(resp, error_content)

    def execute(self):
        """execute()のモック"""
        if self.simulate_error:
            raise RuntimeError(f"Simulated error: {self.simulate_error}")
        return {}


class MockExecute:
    """execute()メソッドのモック"""

    def __init__(self, return_value: Dict[str, Any]):
        self.return_value = return_value

    def execute(self):
        return self.return_value


class MockCalendarClient:
    """Calendar クライアント全体のモック"""

    def __init__(self, credentials=None, calendar_id: str = 'primary'):
        self.credentials = credentials or self._create_mock_credentials()
        self.service = MockCalendarService()
        self.calendar_id = calendar_id

    @staticmethod
    def _create_mock_credentials():
        """モック認証情報を作成"""
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.refresh_token = 'mock_refresh_token'
        return mock_creds

    def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        description: str = '',
        location: str = ''
    ) -> Dict[str, Any]:
        """
        イベント作成のヘルパーメソッド

        Args:
            summary: イベント名
            start: 開始時刻
            end: 終了時刻
            description: 説明
            location: 場所

        Returns:
            作成されたイベントの辞書
        """
        event_body = {
            'summary': summary,
            'start': {
                'dateTime': start.isoformat() + 'Z',
                'timeZone': 'Asia/Tokyo'
            },
            'end': {
                'dateTime': end.isoformat() + 'Z',
                'timeZone': 'Asia/Tokyo'
            },
            'description': description,
            'location': location
        }

        result = self.service.events().insert(
            calendarId=self.calendar_id,
            body=event_body
        ).execute()

        return result

    def find_duplicate_event(self, summary: str, start: datetime) -> Optional[Dict[str, Any]]:
        """
        重複イベントを検索

        Args:
            summary: イベント名
            start: 開始時刻

        Returns:
            重複イベントがあればその辞書、なければNone
        """
        time_min = (start - timedelta(hours=1)).isoformat() + 'Z'
        time_max = (start + timedelta(hours=1)).isoformat() + 'Z'

        events = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            q=summary
        ).execute()

        for event in events.get('items', []):
            if event.get('summary') == summary:
                return event

        return None


class MockCalendarAPIError:
    """Calendar APIエラーのモックヘルパー"""

    @staticmethod
    def create_auth_error():
        """認証エラーを作成"""
        from google.auth.exceptions import RefreshError
        return RefreshError("Token has been expired or revoked")

    @staticmethod
    def create_permission_error():
        """権限エラーを作成"""
        from googleapiclient.errors import HttpError
        resp = Mock()
        resp.status = 403
        error_content = b'{"error": {"code": 403, "message": "Forbidden"}}'
        return HttpError(resp, error_content)

    @staticmethod
    def create_not_found_error():
        """カレンダーが見つからないエラーを作成"""
        from googleapiclient.errors import HttpError
        resp = Mock()
        resp.status = 404
        error_content = b'{"error": {"code": 404, "message": "Calendar not found"}}'
        return HttpError(resp, error_content)

    @staticmethod
    def create_quota_exceeded_error():
        """クォータ超過エラーを作成"""
        from googleapiclient.errors import HttpError
        resp = Mock()
        resp.status = 403
        error_content = b'{"error": {"code": 403, "message": "Quota exceeded"}}'
        return HttpError(resp, error_content)


def create_mock_calendar_service(error_type: Optional[str] = None) -> MockCalendarService:
    """
    Calendar APIサービスモックを作成するファクトリー関数

    Args:
        error_type: シミュレートするエラータイプ

    Returns:
        MockCalendarService インスタンス
    """
    return MockCalendarService(simulate_error=error_type)
