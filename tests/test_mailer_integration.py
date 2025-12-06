import unittest
from unittest.mock import patch, MagicMock
import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from modules.mailer import GmailNotifier
    HAS_MAILER = True
except ImportError:
    GmailNotifier = None
    HAS_MAILER = False


@pytest.mark.skipif(not HAS_MAILER, reason="mailer module not available")
class TestMailerIntegration(unittest.TestCase):
    @pytest.mark.asyncio
    @patch("modules.mailer.build")
    @patch("modules.mailer.os.path.exists")
    async def test_send_email_success(self, mock_exists, mock_build):
        """Test successful email sending"""
        # Mock file exists
        mock_exists.return_value = True

        # Mock Gmail service
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users().messages().send().execute.return_value = {
            "id": "test_message_id"
        }

        # Test data
        test_data = {
            "title": "Test Anime",
            "episode": "1",
            "release_date": "2024-01-01",
            "platform": "Netflix",
        }

        # Execute
        result = await send_email("test@example.com", test_data)

        # Verify
        self.assertTrue(result)

    @pytest.mark.asyncio
    @patch("modules.mailer.build")
    @patch("modules.mailer.os.path.exists")
    async def test_send_email_failure(self, mock_exists, mock_build):
        """Test email sending failure"""
        # Mock file exists
        mock_exists.return_value = True

        # Mock Gmail service with exception
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users().messages().send().execute.side_effect = Exception(
            "API Error"
        )

        # Test data
        test_data = {
            "title": "Test Anime",
            "episode": "1",
            "release_date": "2024-01-01",
            "platform": "Netflix",
        }

        # Execute and verify
        result = await send_email("test@example.com", test_data)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
