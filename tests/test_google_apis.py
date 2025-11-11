import unittest
from unittest.mock import patch, MagicMock
import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.calendar import add_to_calendar
from modules.mailer import send_email


class TestGoogleAPIs(unittest.TestCase):
    @pytest.mark.asyncio
    @patch("modules.calendar.build")
    @patch("modules.calendar.os.path.exists")
    async def test_calendar_integration_success(self, mock_exists, mock_build):
        """Test successful calendar event creation"""
        # Mock credentials file exists
        mock_exists.return_value = True

        # Mock Calendar service
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.events().insert().execute.return_value = {
            "id": "test_event_id",
            "htmlLink": "https://calendar.google.com/test",
        }

        # Test data
        event_data = {
            "title": "Test Anime Episode 1",
            "description": "New episode release",
            "start_time": "2024-01-01T10:00:00",
            "end_time": "2024-01-01T10:30:00",
        }

        # Execute
        result = await add_to_calendar(event_data)

        # Verify
        self.assertTrue(result)

    @pytest.mark.asyncio
    @patch("modules.calendar.build")
    @patch("modules.calendar.os.path.exists")
    async def test_calendar_integration_failure(self, mock_exists, mock_build):
        """Test calendar event creation failure"""
        # Mock credentials file exists
        mock_exists.return_value = True

        # Mock Calendar service with exception
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.events().insert().execute.side_effect = Exception(
            "Calendar API Error"
        )

        # Test data
        event_data = {
            "title": "Test Anime Episode 1",
            "description": "New episode release",
            "start_time": "2024-01-01T10:00:00",
            "end_time": "2024-01-01T10:30:00",
        }

        # Execute and verify
        result = await add_to_calendar(event_data)
        self.assertFalse(result)

    @pytest.mark.asyncio
    @patch("modules.mailer.build")
    @patch("modules.mailer.os.path.exists")
    async def test_gmail_api_integration(self, mock_exists, mock_build):
        """Test Gmail API integration"""
        # Mock credentials file exists
        mock_exists.return_value = True

        # Mock Gmail service
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users().messages().send().execute.return_value = {
            "id": "test_message_id"
        }

        # Test data
        email_data = {
            "title": "Test Anime",
            "episode": "1",
            "release_date": "2024-01-01",
            "platform": "Netflix",
            "description": "Test description",
        }

        # Execute
        result = await send_email("test@example.com", email_data)

        # Verify
        self.assertTrue(result)

    @pytest.mark.asyncio
    @patch("modules.calendar.build")
    @patch("modules.calendar.os.path.exists")
    async def test_calendar_event_formatting(self, mock_exists, mock_build):
        """Test calendar event data formatting"""
        # Mock credentials file exists
        mock_exists.return_value = True

        # Mock Calendar service
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.events().insert().execute.return_value = {"id": "test_id"}

        # Test complex event data
        event_data = {
            "title": "Attack on Titan Final Season",
            "description": "Episode 25 - The Final Episode",
            "start_time": "2024-01-01T15:30:00",
            "end_time": "2024-01-01T16:00:00",
            "location": "Crunchyroll",
            "url": "https://www.crunchyroll.com/attack-on-titan",
        }

        # Execute
        result = await add_to_calendar(event_data)

        # Verify service was called correctly
        self.assertTrue(result)
        mock_service.events().insert.assert_called_once()


if __name__ == "__main__":
    unittest.main()
