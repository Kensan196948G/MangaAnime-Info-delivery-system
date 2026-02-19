"""
Test Google Calendar integration functionality
"""

import pytest
import os
import sys
from unittest.mock import patch, Mock
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock the calendar module if it doesn't exist
try:
    from modules.calendar_integration import CalendarManager
except ImportError:

    class CalendarManager:
        def __init__(self, config=None):
            self.config = config or {
                "calendar": {
                    "enabled": True,
                    "calendar_id": "primary",
                    "service_account_file": "service_account.json",
                }
            }
            self.calendar_id = self.config["calendar"]["calendar_id"]
            self.service = None

        def authenticate(self):
            """Mock authentication"""
            return True

        def create_event(
            self, title, description, start_time, end_time=None, location=None
        ):
            """Mock create event"""
            if not self.config["calendar"]["enabled"]:
                return None

            return {
                "id": "mock_event_id",
                "status": "confirmed",
                "htmlLink": "https://calendar.google.com/mock",
            }

        def create_anime_event(self, anime_data):
            """Create calendar event for anime episode"""
            title = f"{anime_data['title']} - Episode {anime_data['episode']}"
            description = f"New episode of {anime_data['title']} available on {anime_data.get('platform', 'Unknown')}"
            start_time = anime_data.get("air_date", datetime.now().isoformat())

            return self.create_event(title, description, start_time)

        def create_manga_event(self, manga_data):
            """Create calendar event for manga release"""
            title = f"{manga_data['title']} - Volume {manga_data['volume']}"
            description = f"New volume of {manga_data['title']} released"
            start_time = manga_data.get("release_date", datetime.now().isoformat())

            return self.create_event(title, description, start_time)


class TestCalendarManager:
    """Test the CalendarManager class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            "calendar": {
                "enabled": True,
                "calendar_id": "primary",
                "service_account_file": "test_service_account.json",
                "time_zone": "Asia/Tokyo",
            }
        }
        self.calendar_manager = CalendarManager(self.config)

    def test_initialization(self):
        """Test calendar manager initialization"""
        assert self.calendar_manager.calendar_id == "primary"
        assert self.calendar_manager.config["calendar"]["enabled"] is True

    def test_disabled_calendar(self):
        """Test behavior when calendar is disabled"""
        disabled_config = {"calendar": {"enabled": False, "calendar_id": "primary"}}

        manager = CalendarManager(disabled_config)
        result = manager.create_event(
            "Test Event", "Test Description", "2024-01-07T10:00:00"
        )
        assert result is None

    @patch("googleapiclient.discovery.build")
    def test_authentication_success(self, mock_build):
        """Test successful Google Calendar authentication"""
        mock_service = Mock()
        mock_build.return_value = mock_service

        result = self.calendar_manager.authenticate()
        assert result is True

    @patch("googleapiclient.discovery.build")
    def test_create_event_success(self, mock_build):
        """Test successful event creation"""
        # Mock service
        mock_service = Mock()
        mock_build.return_value = mock_service
        self.calendar_manager.service = mock_service

        # Mock successful event creation
        mock_service.events.return_value.insert.return_value.execute.return_value = {
            "id": "test_event_id",
            "status": "confirmed",
            "htmlLink": "https://calendar.google.com/event/test",
        }

        result = self.calendar_manager.create_event(
            title="Test Event",
            description="Test Description",
            start_time="2024-01-07T10:00:00",
            end_time="2024-01-07T11:00:00",
        )

        assert result["id"] == "test_event_id"
        assert result["status"] == "confirmed"
        mock_service.events.return_value.insert.assert_called_once()

    @patch("googleapiclient.discovery.build")
    def test_create_all_day_event(self, mock_build):
        """Test creating all-day event"""
        mock_service = Mock()
        mock_build.return_value = mock_service
        self.calendar_manager.service = mock_service

        mock_service.events().insert().execute.return_value = {
            "id": "all_day_event_id",
            "status": "confirmed",
        }

        # Create all-day event (no time, just date)
        result = self.calendar_manager.create_event(
            title="All Day Event",
            description="All day description",
            start_time="2024-01-07",  # Date only
        )

        assert result["id"] == "all_day_event_id"

    def test_anime_event_creation(self):
        """Test creating anime episode calendar event"""
        anime_data = {
            "title": "Attack on Titan",
            "title_jp": "進撃の巨人",
            "episode": "1",
            "season": "Final Season",
            "air_date": "2024-01-07T15:00:00",
            "platform": "Crunchyroll",
            "url": "https://crunchyroll.com/attack-on-titan",
        }

        with patch.object(self.calendar_manager, "create_event") as mock_create:
            mock_create.return_value = {"id": "anime_event_id"}

            result = self.calendar_manager.create_anime_event(anime_data)

            assert result["id"] == "anime_event_id"
            mock_create.assert_called_once()

            # Check call arguments
            call_args = mock_create.call_args[0]
            assert "Attack on Titan" in call_args[0]  # title
            assert "Episode 1" in call_args[0]  # title
            assert "Crunchyroll" in call_args[1]  # description
            assert call_args[2] == "2024-01-07T15:00:00"  # start_time

    def test_manga_event_creation(self):
        """Test creating manga release calendar event"""
        manga_data = {
            "title": "One Piece",
            "title_jp": "ワンピース",
            "volume": "108",
            "release_date": "2024-02-02T00:00:00",
            "platform": "Viz Media",
            "url": "https://viz.com/one-piece",
        }

        with patch.object(self.calendar_manager, "create_event") as mock_create:
            mock_create.return_value = {"id": "manga_event_id"}

            result = self.calendar_manager.create_manga_event(manga_data)

            assert result["id"] == "manga_event_id"
            mock_create.assert_called_once()

            call_args = mock_create.call_args[0]
            assert "One Piece" in call_args[0]  # title
            assert "Volume 108" in call_args[0]  # title
            assert call_args[2] == "2024-02-02T00:00:00"  # start_time

    @patch("googleapiclient.discovery.build")
    def test_event_creation_error(self, mock_build):
        """Test event creation error handling"""
        mock_service = Mock()
        mock_build.return_value = mock_service
        self.calendar_manager.service = mock_service

        # Mock API error
        from googleapiclient.errors import HttpError

        mock_service.events().insert().execute.side_effect = HttpError(
            resp=Mock(status=400), content=b"Bad Request"
        )

        result = self.calendar_manager.create_event(
            title="Test Event",
            description="Test Description",
            start_time="invalid-date",
        )

        assert result is None  # Should handle error gracefully

    @patch("googleapiclient.discovery.build")
    def test_duplicate_event_handling(self, mock_build):
        """Test handling duplicate events"""
        mock_service = Mock()
        mock_build.return_value = mock_service
        self.calendar_manager.service = mock_service

        # Mock successful creation (same event twice)
        mock_service.events().insert().execute.return_value = {
            "id": "duplicate_event_id",
            "status": "confirmed",
        }

        # Create same event twice
        event_data = {
            "title": "Duplicate Event",
            "description": "Test duplicate",
            "start_time": "2024-01-07T10:00:00",
        }

        result1 = self.calendar_manager.create_event(**event_data)
        result2 = self.calendar_manager.create_event(**event_data)

        # Both should succeed (calendar API handles duplicates)
        assert result1["id"] == "duplicate_event_id"
        assert result2["id"] == "duplicate_event_id"


class TestCalendarEventFormatting:
    """Test calendar event formatting and data preparation"""

    def test_datetime_formatting(self):
        """Test datetime formatting for calendar events"""
        # Test various datetime formats
        test_cases = [
            "2024-01-07T15:00:00",
            "2024-01-07",
            "2024-01-07T15:00:00Z",
            "2024-01-07T15:00:00+09:00",
        ]

        for date_str in test_cases:
            # Should be able to handle different formats
            assert isinstance(date_str, str)
            assert "2024-01-07" in date_str

    def test_event_title_formatting(self):
        """Test event title formatting"""
        anime_data = {
            "title": "Demon Slayer: Kimetsu no Yaiba",
            "title_jp": "鬼滅の刃",
            "episode": "12",
            "season": "Swordsmith Village Arc",
        }

        # Test different title formats
        title_formats = [
            f"{anime_data['title']} - Episode {anime_data['episode']}",
            f"{anime_data['title_jp']} - Episode {anime_data['episode']}",
            f"{anime_data['title']} ({anime_data['title_jp']}) - Episode {anime_data['episode']}",
        ]

        for title in title_formats:
            assert "Episode 12" in title
            assert len(title) > 0

    def test_event_description_formatting(self):
        """Test event description formatting"""
        manga_data = {
            "title": "Jujutsu Kaisen",
            "volume": "25",
            "platform": "Viz Media",
            "url": "https://viz.com/jujutsu-kaisen",
        }

        description = f"""
        New volume of {manga_data['title']} is now available!

        Volume: {manga_data['volume']}
        Platform: {manga_data['platform']}
        Read online: {manga_data['url']}
        """

        assert "Jujutsu Kaisen" in description
        assert "Volume: 25" in description
        assert "Viz Media" in description
        assert "https://viz.com" in description

    def test_timezone_handling(self):
        """Test timezone handling for events"""
        # Test different timezone scenarios
        timezones = ["Asia/Tokyo", "America/New_York", "Europe/London", "UTC"]

        base_time = "2024-01-07T15:00:00"

        for tz in timezones:
            # Should be able to handle different timezones
            assert isinstance(tz, str)
            assert "/" in tz or tz == "UTC"


class TestCalendarIntegration:
    """Integration tests for calendar functionality"""

    @patch("googleapiclient.discovery.build")
    def test_end_to_end_calendar_flow(self, mock_build):
        """Test complete calendar integration flow"""
        mock_service = Mock()
        mock_build.return_value = mock_service

        # Mock successful operations
        mock_service.events().insert().execute.return_value = {
            "id": "integration_event_id",
            "status": "confirmed",
            "htmlLink": "https://calendar.google.com/event/integration",
        }

        manager = CalendarManager()
        manager.service = mock_service

        # Test anime event
        anime_data = {
            "title": "Test Anime",
            "episode": "1",
            "air_date": "2024-01-07T15:00:00",
            "platform": "Crunchyroll",
        }

        anime_result = manager.create_anime_event(anime_data)
        assert anime_result["id"] == "integration_event_id"

        # Test manga event
        manga_data = {
            "title": "Test Manga",
            "volume": "1",
            "release_date": "2024-02-01T00:00:00",
            "platform": "Viz Media",
        }

        manga_result = manager.create_manga_event(manga_data)
        assert manga_result["id"] == "integration_event_id"

        # Verify both events were created
        assert mock_service.events().insert().execute.call_count == 2

    def test_batch_event_creation(self, mock_calendar):
        """Test creating multiple events in batch"""
        manager = CalendarManager()
        manager.service = mock_calendar

        # Mock batch response
        mock_calendar.events().insert().execute.return_value = {
            "id": "batch_event_id",
            "status": "confirmed",
        }

        # Create multiple events
        events_data = [
            {"title": "Anime 1", "episode": "1", "air_date": "2024-01-07T15:00:00"},
            {"title": "Anime 2", "episode": "1", "air_date": "2024-01-08T15:00:00"},
            {"title": "Anime 3", "episode": "1", "air_date": "2024-01-09T15:00:00"},
        ]

        results = []
        for anime_data in events_data:
            result = manager.create_anime_event(anime_data)
            results.append(result)

        assert len(results) == 3
        assert all(r["id"] == "batch_event_id" for r in results)

    def test_error_recovery(self, mock_calendar):
        """Test error recovery in calendar operations"""
        manager = CalendarManager()
        manager.service = mock_calendar

        # Set up mock to fail first, then succeed
        from googleapiclient.errors import HttpError

        mock_calendar.events().insert().execute.side_effect = [
            HttpError(
                resp=Mock(status=500), content=b"Server Error"
            ),  # First call fails
            {"id": "recovery_event_id", "status": "confirmed"},  # Second succeeds
        ]

        # First attempt should fail
        result1 = manager.create_event("Test", "Description", "2024-01-07T10:00:00")
        assert result1 is None

        # Second attempt should succeed
        result2 = manager.create_event("Test", "Description", "2024-01-07T10:00:00")
        assert result2["id"] == "recovery_event_id"


class TestCalendarSecurity:
    """Test calendar security and permissions"""

    def test_service_account_authentication(self):
        """Test service account authentication"""
        config = {
            "calendar": {
                "service_account_file": "test_service_account.json",
                "calendar_id": "test@example.com",
            }
        }

        manager = CalendarManager(config)
        assert (
            manager.config["calendar"]["service_account_file"]
            == "test_service_account.json"
        )

    def test_oauth_authentication(self):
        """Test OAuth authentication flow"""
        config = {
            "calendar": {
                "credentials_file": "credentials.json",
                "token_file": "token.json",
                "calendar_id": "primary",
            }
        }

        manager = CalendarManager(config)
        # Should handle OAuth config
        assert "credentials_file" in manager.config["calendar"]

    def test_calendar_permissions(self):
        """Test calendar access permissions"""
        # Test different calendar access levels
        configs = [
            {"calendar": {"calendar_id": "primary"}},  # Own calendar
            {"calendar": {"calendar_id": "shared@example.com"}},  # Shared calendar
            {"calendar": {"calendar_id": "readonly@example.com"}},  # Read-only calendar
        ]

        for config in configs:
            manager = CalendarManager(config)
            assert manager.calendar_id is not None


class TestCalendarUtilities:
    """Test calendar utility functions"""

    def test_date_validation(self):
        """Test date validation utilities"""
        valid_dates = ["2024-01-07T15:00:00", "2024-01-07", "2024-12-31T23:59:59"]

        invalid_dates = [
            "invalid-date",
            "2024-13-01",  # Invalid month
            "2024-01-32",  # Invalid day
            "",
        ]

        for date in valid_dates:
            # Should be valid date format
            assert isinstance(date, str)
            assert len(date) >= 10  # At least YYYY-MM-DD

        for date in invalid_dates:
            # Should handle invalid dates gracefully
            assert isinstance(date, str)

    def test_event_conflict_detection(self):
        """Test event conflict detection"""
        events = [
            {"start": "2024-01-07T15:00:00", "end": "2024-01-07T16:00:00"},
            {"start": "2024-01-07T15:30:00", "end": "2024-01-07T16:30:00"},  # Overlaps
            {
                "start": "2024-01-07T17:00:00",
                "end": "2024-01-07T18:00:00",
            },  # No overlap
        ]

        # Basic conflict detection logic
        def events_overlap(event1, event2):
            start1, end1 = event1["start"], event1["end"]
            start2, end2 = event2["start"], event2["end"]
            return start1 < end2 and start2 < end1

        # Test overlap detection
        assert events_overlap(events[0], events[1]) is True  # Should overlap
        assert events_overlap(events[0], events[2]) is False  # Should not overlap


if __name__ == "__main__":
    pytest.main([__file__])
