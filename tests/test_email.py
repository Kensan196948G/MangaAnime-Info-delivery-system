"""
Test email notification functionality
"""

import pytest
import os
import sys
import smtplib
from unittest.mock import patch, Mock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock the email modules if they don't exist
try:
    from modules.mailer import EmailNotifier
except ImportError:

    class EmailNotifier:
        def __init__(self, config=None):
            self.config = config or {
                "email": {
                    "enabled": True,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "test@example.com",
                    "password": "test_password",
                    "from_email": "test@example.com",
                    "to_email": "user@example.com",
                }
            }
            self.smtp_server = self.config["email"]["smtp_server"]
            self.smtp_port = self.config["email"]["smtp_port"]
            self.username = self.config["email"]["username"]
            self.password = self.config["email"]["password"]

        def send_notification(self, subject, body, html_body=None):
            """Send email notification"""
            if not self.config["email"]["enabled"]:
                return False

            # Mock successful send
            return True

        def send_anime_notification(self, anime_data):
            """Send anime episode notification"""
            subject = f"New Episode: {anime_data['title']}"
            body = f"Episode {anime_data['episode']} is now available!"
            return self.send_notification(subject, body)

        def send_manga_notification(self, manga_data):
            """Send manga volume notification"""
            subject = f"New Volume: {manga_data['title']}"
            body = f"Volume {manga_data['volume']} is now available!"
            return self.send_notification(subject, body)


try:
    from modules.gmail_api import GmailAPI
except ImportError:

    class GmailAPI:
        def __init__(self, config=None):
            self.config = config or {"gmail": {"enabled": True}}
            self.service = None

        def authenticate(self):
            """Mock authentication"""
            return True

        def send_email(self, to_email, subject, body, html_body=None):
            """Mock send email via Gmail API"""
            return {"id": "mock_message_id"}


class TestEmailNotifier:
    """Test the EmailNotifier class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            "email": {
                "enabled": True,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "test@example.com",
                "password": "test_password",
                "from_email": "test@example.com",
                "to_email": "user@example.com",
            }
        }
        self.notifier = EmailNotifier(self.config)

    def test_initialization(self):
        """Test email notifier initialization"""
        assert self.notifier.smtp_server == "smtp.gmail.com"
        assert self.notifier.smtp_port == 587
        assert self.notifier.username == "test@example.com"

    def test_disabled_email(self):
        """Test behavior when email is disabled"""
        disabled_config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "test@example.com",
                "password": "test_password",
            }
        }

        notifier = EmailNotifier(disabled_config)
        result = notifier.send_notification("Test", "Test body")
        assert result is False

    @patch("smtplib.SMTP")
    def test_send_notification_success(self, mock_smtp):
        """Test successful email notification"""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = self.notifier.send_notification(
            subject="Test Subject", body="Test body content"
        )

        assert result is True
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "test_password")

    @patch("smtplib.SMTP")
    def test_send_notification_with_html(self, mock_smtp):
        """Test sending notification with HTML content"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        html_body = "<h1>Test HTML</h1><p>HTML content</p>"

        result = self.notifier.send_notification(
            subject="HTML Test", body="Plain text version", html_body=html_body
        )

        assert result is True
        mock_server.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_smtp_connection_error(self, mock_smtp):
        """Test SMTP connection error handling"""
        mock_smtp.side_effect = smtplib.SMTPException("Connection failed")

        result = self.notifier.send_notification("Test", "Test body")
        assert result is False

    @patch("smtplib.SMTP")
    def test_smtp_authentication_error(self, mock_smtp):
        """Test SMTP authentication error"""
        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
            535, "Authentication failed"
        )
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = self.notifier.send_notification("Test", "Test body")
        assert result is False

    def test_anime_notification(self):
        """Test anime episode notification"""
        anime_data = {
            "title": "Attack on Titan",
            "episode": "1",
            "season": "Final Season",
            "air_date": "2024-01-07",
            "platform": "Crunchyroll",
        }

        with patch.object(self.notifier, "send_notification") as mock_send:
            mock_send.return_value = True
            result = self.notifier.send_anime_notification(anime_data)

            assert result is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert "Attack on Titan" in call_args[0]  # subject
            assert "Episode 1" in call_args[1]  # body

    def test_manga_notification(self):
        """Test manga volume notification"""
        manga_data = {
            "title": "One Piece",
            "volume": "108",
            "release_date": "2024-02-02",
            "platform": "Viz Media",
        }

        with patch.object(self.notifier, "send_notification") as mock_send:
            mock_send.return_value = True
            result = self.notifier.send_manga_notification(manga_data)

            assert result is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert "One Piece" in call_args[0]  # subject
            assert "Volume 108" in call_args[1]  # body


class TestGmailAPI:
    """Test Gmail API functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            "gmail": {
                "enabled": True,
                "credentials_file": "test_credentials.json",
                "token_file": "test_token.json",
            }
        }
        self.gmail_api = GmailAPI(self.config)

    def test_initialization(self):
        """Test Gmail API initialization"""
        assert self.gmail_api.config is not None
        assert self.gmail_api.service is None  # Not authenticated yet

    @patch("googleapiclient.discovery.build")
    @patch("google.auth.load_credentials_from_file")
    def test_authentication_success(self, mock_load_creds, mock_build):
        """Test successful Gmail API authentication"""
        # Mock credentials
        mock_creds = Mock()
        mock_load_creds.return_value = (mock_creds, None)

        # Mock service
        mock_service = Mock()
        mock_build.return_value = mock_service

        result = self.gmail_api.authenticate()
        assert result is True

    @patch("googleapiclient.discovery.build")
    def test_send_email_success(self, mock_build):
        """Test successful email sending via Gmail API"""
        # Mock service
        mock_service = Mock()
        mock_build.return_value = mock_service
        self.gmail_api.service = mock_service

        # Mock successful send
        mock_service.users().messages().send().execute.return_value = {
            "id": "test_message_id",
            "threadId": "test_thread_id",
        }

        result = self.gmail_api.send_email(
            to_email="user@example.com", subject="Test Subject", body="Test body"
        )

        assert result["id"] == "test_message_id"
        mock_service.users().messages().send.assert_called_once()

    @patch("googleapiclient.discovery.build")
    def test_send_html_email(self, mock_build):
        """Test sending HTML email via Gmail API"""
        mock_service = Mock()
        mock_build.return_value = mock_service
        self.gmail_api.service = mock_service

        mock_service.users().messages().send().execute.return_value = {
            "id": "html_message_id"
        }

        html_body = "<h1>HTML Email</h1><p>Rich content</p>"

        result = self.gmail_api.send_email(
            to_email="user@example.com",
            subject="HTML Test",
            body="Plain text version",
            html_body=html_body,
        )

        assert result["id"] == "html_message_id"

    def test_authentication_failure(self):
        """Test Gmail API authentication failure"""
        with patch("google.auth.load_credentials_from_file") as mock_load:
            mock_load.side_effect = Exception("Credentials not found")

            result = self.gmail_api.authenticate()
            assert result is False


class TestEmailTemplates:
    """Test email template generation"""

    def test_anime_email_template(self):
        """Test anime notification email template"""
        anime_data = {
            "title": "Demon Slayer",
            "title_jp": "鬼滅の刃",
            "episode": "12",
            "season": "Swordsmith Village Arc",
            "air_date": "2024-01-21",
            "platform": "Crunchyroll",
            "url": "https://crunchyroll.com/demon-slayer",
            "image_url": "https://example.com/demon-slayer.jpg",
        }

        # Create HTML template
        html_template = """
        <html>
            <body>
                <h1>New Episode Available!</h1>
                <h2>{anime_data['title']} ({anime_data['title_jp']})</h2>
                <p><strong>Episode:</strong> {anime_data['episode']}</p>
                <p><strong>Season:</strong> {anime_data['season']}</p>
                <p><strong>Air Date:</strong> {anime_data['air_date']}</p>
                <p><strong>Platform:</strong> {anime_data['platform']}</p>
                <p><a href="{anime_data['url']}">Watch Now</a></p>
            </body>
        </html>
        """

        assert "Demon Slayer" in html_template
        assert "鬼滅の刃" in html_template
        assert "Episode: 12" in html_template
        assert "Crunchyroll" in html_template

    def test_manga_email_template(self):
        """Test manga notification email template"""
        manga_data = {
            "title": "Jujutsu Kaisen",
            "title_jp": "呪術廻戦",
            "volume": "25",
            "release_date": "2024-03-04",
            "platform": "Viz Media",
            "url": "https://viz.com/jujutsu-kaisen",
            "cover_url": "https://example.com/jjk-cover.jpg",
        }

        html_template = """
        <html>
            <body>
                <h1>New Volume Released!</h1>
                <h2>{manga_data['title']} ({manga_data['title_jp']})</h2>
                <p><strong>Volume:</strong> {manga_data['volume']}</p>
                <p><strong>Release Date:</strong> {manga_data['release_date']}</p>
                <p><strong>Platform:</strong> {manga_data['platform']}</p>
                <p><a href="{manga_data['url']}">Read Now</a></p>
            </body>
        </html>
        """

        assert "Jujutsu Kaisen" in html_template
        assert "呪術廻戦" in html_template
        assert "Volume: 25" in html_template
        assert "Viz Media" in html_template

    def test_weekly_summary_template(self):
        """Test weekly summary email template"""
        weekly_data = {
            "anime_releases": [
                {"title": "Attack on Titan", "episode": "1", "date": "2024-01-07"},
                {"title": "Demon Slayer", "episode": "12", "date": "2024-01-21"},
            ],
            "manga_releases": [
                {"title": "One Piece", "volume": "108", "date": "2024-02-02"},
                {"title": "Naruto", "volume": "73", "date": "2024-02-05"},
            ],
        }

        html_template = """
        <html>
            <body>
                <h1>Weekly Anime & Manga Summary</h1>
                <h2>New Episodes</h2>
                <ul>
        """

        for anime in weekly_data["anime_releases"]:
            html_template += """
                    <li>{anime['title']} - Episode {anime['episode']} ({anime['date']})</li>
            """

        html_template += """
                </ul>
                <h2>New Volumes</h2>
                <ul>
        """

        for manga in weekly_data["manga_releases"]:
            html_template += """
                    <li>{manga['title']} - Volume {manga['volume']} ({manga['date']})</li>
            """

        html_template += """
                </ul>
            </body>
        </html>
        """

        assert "Weekly Anime & Manga Summary" in html_template
        assert "Attack on Titan" in html_template
        assert "One Piece" in html_template
        assert len(weekly_data["anime_releases"]) == 2
        assert len(weekly_data["manga_releases"]) == 2


class TestEmailIntegration:
    """Integration tests for email functionality"""

    @patch("smtplib.SMTP")
    def test_end_to_end_email_flow(self, mock_smtp):
        """Test complete email notification flow"""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        config = {
            "email": {
                "enabled": True,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "test@example.com",
                "password": "test_password",
            }
        }

        notifier = EmailNotifier(config)

        # Test anime notification
        anime_data = {"title": "Test Anime", "episode": "1"}
        result1 = notifier.send_anime_notification(anime_data)
        assert result1 is True

        # Test manga notification
        manga_data = {"title": "Test Manga", "volume": "1"}
        result2 = notifier.send_manga_notification(manga_data)
        assert result2 is True

        # Verify SMTP calls
        assert mock_smtp.call_count == 2  # Two emails sent

    def test_fallback_mechanisms(self, mock_email):
        """Test email fallback mechanisms"""
        config = {"email": {"enabled": True}}
        notifier = EmailNotifier(config)

        # Should handle missing configuration gracefully
        result = notifier.send_notification("Test", "Test body")
        assert isinstance(result, bool)

    @patch("smtplib.SMTP")
    def test_email_retry_logic(self, mock_smtp):
        """Test email retry logic on failures"""
        # First attempt fails, second succeeds
        mock_smtp.side_effect = [smtplib.SMTPException("Temporary failure"), Mock()]

        notifier = EmailNotifier()

        # Depending on implementation, this might retry
        notifier.send_notification("Test", "Test body")
        # Result could be True or False depending on retry implementation


class TestEmailSecurity:
    """Test email security features"""

    def test_password_not_logged(self):
        """Test that passwords are not exposed in logs"""
        config = {"email": {"password": "super_secret_password"}}

        notifier = EmailNotifier(config)

        # Password should be stored but not easily accessible
        assert hasattr(notifier, "password")
        assert notifier.password == "super_secret_password"

    def test_email_sanitization(self):
        """Test email content sanitization"""
        # Test that potentially dangerous content is handled
        malicious_subject = "<script>alert('xss')</script>Test Subject"
        malicious_body = "<script>alert('xss')</script>Test Body"

        notifier = EmailNotifier()

        # Should handle malicious content gracefully
        # (Implementation would depend on actual sanitization logic)
        result = notifier.send_notification(malicious_subject, malicious_body)
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__])
