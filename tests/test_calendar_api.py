#!/usr/bin/env python3
"""
Google Calendar API ラッパーのテストコード
Phase 17: カレンダー統合実装
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime, timedelta
import json
import sys
import os

# パスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.calendar_api import (
    GoogleCalendarAPI,
    GoogleCalendarAPIError,
    AuthenticationError,
    QuotaExceededError,
    EventNotFoundError,
    create_reminder,
    format_event_summary
)


class TestGoogleCalendarAPI(unittest.TestCase):
    """GoogleCalendarAPI のユニットテスト"""

    def setUp(self):
        """テストのセットアップ"""
        # モックデータ
        self.mock_token_data = {
            'token': 'mock_access_token',
            'refresh_token': 'mock_refresh_token',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': 'mock_client_id',
            'client_secret': 'mock_client_secret',
            'scopes': ['https://www.googleapis.com/auth/calendar']
        }

        self.mock_event = {
            'id': 'test_event_123',
            'summary': 'Test Event',
            'start': {
                'dateTime': '2025-12-10T12:00:00+09:00',
                'timeZone': 'Asia/Tokyo'
            },
            'end': {
                'dateTime': '2025-12-10T13:00:00+09:00',
                'timeZone': 'Asia/Tokyo'
            },
            'description': 'Test Description',
            'location': 'Test Location'
        }

    @patch('modules.calendar_api.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('modules.calendar_api.build')
    @patch('modules.calendar_api.Credentials')
    def test_initialization_success(
        self,
        mock_credentials,
        mock_build,
        mock_file,
        mock_exists
    ):
        """初期化の成功テスト"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(
            self.mock_token_data
        )

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.return_value = mock_creds

        calendar = GoogleCalendarAPI(
            token_file='auth/calendar_token.json'
        )

        self.assertIsNotNone(calendar.service)
        self.assertEqual(calendar.calendar_id, 'primary')

    @patch('modules.calendar_api.Path.exists')
    def test_initialization_no_token_file(self, mock_exists):
        """トークンファイルが存在しない場合のテスト"""
        mock_exists.return_value = False

        with self.assertRaises(AuthenticationError):
            GoogleCalendarAPI(token_file='nonexistent.json')

    @patch('modules.calendar_api.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('modules.calendar_api.build')
    @patch('modules.calendar_api.Credentials')
    def test_create_event_success(
        self,
        mock_credentials,
        mock_build,
        mock_file,
        mock_exists
    ):
        """イベント作成の成功テスト"""
        # モックのセットアップ
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(
            self.mock_token_data
        )

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # イベント挿入のモック
        mock_insert = MagicMock()
        mock_insert.execute.return_value = self.mock_event
        mock_service.events().insert.return_value = mock_insert

        # テスト実行
        calendar = GoogleCalendarAPI()
        event = calendar.create_event(
            summary='Test Event',
            start_time=datetime(2025, 12, 10, 12, 0),
            duration_minutes=60,
            description='Test Description'
        )

        self.assertEqual(event['id'], 'test_event_123')
        self.assertEqual(event['summary'], 'Test Event')

    @patch('modules.calendar_api.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('modules.calendar_api.build')
    @patch('modules.calendar_api.Credentials')
    def test_get_event_success(
        self,
        mock_credentials,
        mock_build,
        mock_file,
        mock_exists
    ):
        """イベント取得の成功テスト"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(
            self.mock_token_data
        )

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # イベント取得のモック
        mock_get = MagicMock()
        mock_get.execute.return_value = self.mock_event
        mock_service.events().get.return_value = mock_get

        calendar = GoogleCalendarAPI()
        event = calendar.get_event('test_event_123')

        self.assertEqual(event['id'], 'test_event_123')

    @patch('modules.calendar_api.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('modules.calendar_api.build')
    @patch('modules.calendar_api.Credentials')
    def test_get_event_not_found(
        self,
        mock_credentials,
        mock_build,
        mock_file,
        mock_exists
    ):
        """存在しないイベントの取得テスト"""
        from googleapiclient.errors import HttpError

        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(
            self.mock_token_data
        )

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # 404エラーのモック
        mock_resp = MagicMock()
        mock_resp.status = 404
        http_error = HttpError(mock_resp, b'Not Found')

        mock_get = MagicMock()
        mock_get.execute.side_effect = http_error
        mock_service.events().get.return_value = mock_get

        calendar = GoogleCalendarAPI()

        with self.assertRaises(EventNotFoundError):
            calendar.get_event('nonexistent_id')

    @patch('modules.calendar_api.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('modules.calendar_api.build')
    @patch('modules.calendar_api.Credentials')
    def test_update_event_success(
        self,
        mock_credentials,
        mock_build,
        mock_file,
        mock_exists
    ):
        """イベント更新の成功テスト"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(
            self.mock_token_data
        )

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # 既存イベント取得のモック
        mock_get = MagicMock()
        mock_get.execute.return_value = self.mock_event.copy()
        mock_service.events().get.return_value = mock_get

        # 更新のモック
        updated_event = self.mock_event.copy()
        updated_event['summary'] = 'Updated Event'
        mock_update = MagicMock()
        mock_update.execute.return_value = updated_event
        mock_service.events().update.return_value = mock_update

        calendar = GoogleCalendarAPI()
        result = calendar.update_event(
            'test_event_123',
            {'summary': 'Updated Event'}
        )

        self.assertEqual(result['summary'], 'Updated Event')

    @patch('modules.calendar_api.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('modules.calendar_api.build')
    @patch('modules.calendar_api.Credentials')
    def test_delete_event_success(
        self,
        mock_credentials,
        mock_build,
        mock_file,
        mock_exists
    ):
        """イベント削除の成功テスト"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(
            self.mock_token_data
        )

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_delete = MagicMock()
        mock_delete.execute.return_value = None
        mock_service.events().delete.return_value = mock_delete

        calendar = GoogleCalendarAPI()
        result = calendar.delete_event('test_event_123')

        self.assertTrue(result)

    @patch('modules.calendar_api.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('modules.calendar_api.build')
    @patch('modules.calendar_api.Credentials')
    def test_list_events_success(
        self,
        mock_credentials,
        mock_build,
        mock_file,
        mock_exists
    ):
        """イベント一覧取得の成功テスト"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(
            self.mock_token_data
        )

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_events = {
            'items': [self.mock_event, self.mock_event]
        }
        mock_list = MagicMock()
        mock_list.execute.return_value = mock_events
        mock_service.events().list.return_value = mock_list

        calendar = GoogleCalendarAPI()
        events = calendar.list_events(
            time_min=datetime(2025, 12, 1),
            time_max=datetime(2025, 12, 31)
        )

        self.assertEqual(len(events), 2)

    @patch('modules.calendar_api.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('modules.calendar_api.build')
    @patch('modules.calendar_api.Credentials')
    def test_search_events_success(
        self,
        mock_credentials,
        mock_build,
        mock_file,
        mock_exists
    ):
        """イベント検索の成功テスト"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(
            self.mock_token_data
        )

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_events = {
            'items': [self.mock_event]
        }
        mock_list = MagicMock()
        mock_list.execute.return_value = mock_events
        mock_service.events().list.return_value = mock_list

        calendar = GoogleCalendarAPI()
        events = calendar.search_events('Test Event')

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['summary'], 'Test Event')

    @patch('modules.calendar_api.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('modules.calendar_api.build')
    @patch('modules.calendar_api.Credentials')
    @patch('time.sleep')
    def test_batch_create_events(
        self,
        mock_sleep,
        mock_credentials,
        mock_build,
        mock_file,
        mock_exists
    ):
        """バッチイベント作成のテスト"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(
            self.mock_token_data
        )

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_insert = MagicMock()
        mock_insert.execute.return_value = self.mock_event
        mock_service.events().insert.return_value = mock_insert

        calendar = GoogleCalendarAPI()

        events_data = [
            {
                'summary': f'Event {i}',
                'start_time': datetime(2025, 12, 10 + i, 12, 0),
                'duration_minutes': 60
            }
            for i in range(3)
        ]

        success, failed, errors = calendar.batch_create_events(
            events_data,
            batch_size=2
        )

        self.assertEqual(success, 3)
        self.assertEqual(failed, 0)
        self.assertEqual(len(errors), 0)

    def test_convert_to_iso(self):
        """datetime → ISO変換のテスト"""
        # モック環境でテスト
        dt = datetime(2025, 12, 10, 12, 30, 0)
        expected = '2025-12-10T12:30:00'

        with patch('modules.calendar_api.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(self.mock_token_data))), \
             patch('modules.calendar_api.build'), \
             patch('modules.calendar_api.Credentials'):

            calendar = GoogleCalendarAPI()
            result = calendar._convert_to_iso(dt)

            self.assertEqual(result, expected)

    def test_validate_event_data_valid(self):
        """有効なイベントデータの検証テスト"""
        with patch('modules.calendar_api.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(self.mock_token_data))), \
             patch('modules.calendar_api.build'), \
             patch('modules.calendar_api.Credentials'):

            calendar = GoogleCalendarAPI()

            valid_data = {
                'summary': 'Test',
                'start': {'dateTime': '2025-12-10T12:00:00'},
                'end': {'dateTime': '2025-12-10T13:00:00'}
            }

            self.assertTrue(calendar._validate_event_data(valid_data))

    def test_validate_event_data_invalid(self):
        """無効なイベントデータの検証テスト"""
        with patch('modules.calendar_api.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(self.mock_token_data))), \
             patch('modules.calendar_api.build'), \
             patch('modules.calendar_api.Credentials'):

            calendar = GoogleCalendarAPI()

            # summaryが欠落
            invalid_data = {
                'start': {'dateTime': '2025-12-10T12:00:00'},
                'end': {'dateTime': '2025-12-10T13:00:00'}
            }

            self.assertFalse(calendar._validate_event_data(invalid_data))


class TestHelperFunctions(unittest.TestCase):
    """ヘルパー関数のテスト"""

    def test_create_reminder(self):
        """リマインダー作成のテスト"""
        reminder = create_reminder('popup', 30)

        self.assertEqual(reminder['method'], 'popup')
        self.assertEqual(reminder['minutes'], 30)

    def test_create_reminder_email(self):
        """メールリマインダー作成のテスト"""
        reminder = create_reminder('email', 60)

        self.assertEqual(reminder['method'], 'email')
        self.assertEqual(reminder['minutes'], 60)

    def test_format_event_summary_with_episode(self):
        """エピソード付きタイトルフォーマットのテスト"""
        result = format_event_summary('呪術廻戦', '第10話')

        self.assertEqual(result, '呪術廻戦 第10話')

    def test_format_event_summary_without_episode(self):
        """エピソードなしタイトルフォーマットのテスト"""
        result = format_event_summary('呪術廻戦')

        self.assertEqual(result, '呪術廻戦')


class TestErrorHandling(unittest.TestCase):
    """エラーハンドリングのテスト"""

    @patch('modules.calendar_api.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('modules.calendar_api.build')
    @patch('modules.calendar_api.Credentials')
    def test_http_error_401(
        self,
        mock_credentials,
        mock_build,
        mock_file,
        mock_exists
    ):
        """401エラーのハンドリングテスト"""
        from googleapiclient.errors import HttpError

        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps({
            'token': 'mock_token',
            'refresh_token': 'mock_refresh',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': 'mock_id',
            'client_secret': 'mock_secret',
            'scopes': []
        })

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_resp = MagicMock()
        mock_resp.status = 401
        http_error = HttpError(mock_resp, b'Unauthorized')

        calendar = GoogleCalendarAPI()

        with self.assertRaises(AuthenticationError):
            calendar._handle_http_error(http_error)

    @patch('modules.calendar_api.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('modules.calendar_api.build')
    @patch('modules.calendar_api.Credentials')
    def test_http_error_429(
        self,
        mock_credentials,
        mock_build,
        mock_file,
        mock_exists
    ):
        """429エラー（レート制限）のハンドリングテスト"""
        from googleapiclient.errors import HttpError

        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps({
            'token': 'mock_token',
            'refresh_token': 'mock_refresh',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': 'mock_id',
            'client_secret': 'mock_secret',
            'scopes': []
        })

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_resp = MagicMock()
        mock_resp.status = 429
        http_error = HttpError(mock_resp, b'Rate Limit Exceeded')

        calendar = GoogleCalendarAPI()

        with self.assertRaises(QuotaExceededError):
            calendar._handle_http_error(http_error)


if __name__ == '__main__':
    # テスト実行
    unittest.main(verbosity=2)
