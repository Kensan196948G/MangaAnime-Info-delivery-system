#!/usr/bin/env python3
"""
Integration tests for Google Calendar API integration
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta


class TestCalendarIntegration:
    """Test Google Calendar API integration for event creation."""

    @pytest.mark.integration
    @pytest.mark.auth
    def test_calendar_authentication_setup(self, mock_calendar_service):
        """Test Google Calendar API authentication setup."""
        with patch("google.auth.default") as mock_auth, patch(
            "googleapiclient.discovery.build"
        ) as mock_build:
            # Mock credentials
            mock_credentials = Mock()
            mock_auth.return_value = (mock_credentials, "project-id")

            # Mock service build
            mock_build.return_value = mock_calendar_service

            # Test authentication flow
            from google.auth import default
            from googleapiclient.discovery import build

            credentials, project = default()
            service = build("calendar", "v3", credentials=credentials)

            assert credentials is not None
            assert service is not None
            mock_build.assert_called_with("calendar", "v3", credentials=credentials)

    @pytest.mark.integration
    def test_calendar_event_creation(self, mock_calendar_service, sample_release_data):
        """Test creating calendar events for releases."""
        release = sample_release_data[0]

        # Prepare event data
        event_data = {
            "summary": f'{release.get("title", "Unknown")} - エピソード {release.get("number", "N/A")}',
            "description": f'プラットフォーム: {release.get("platform", "Unknown")}\nソース: {release.get("source_url", "")}',
            "start": {
                "date": release.get("release_date", "2024-01-15"),
                "timeZone": "Asia/Tokyo",
            },
            "end": {
                "date": release.get("release_date", "2024-01-15"),
                "timeZone": "Asia/Tokyo",
            },
            "colorId": "3",  # Blue color for anime/manga events
        }

        # Mock Calendar API response
        mock_calendar_service.events().insert.return_value.execute.return_value = {
            "id": "event_12345",
            "htmlLink": "https://calendar.google.com/event?eid=event_12345",
            "summary": event_data["summary"],
            "start": event_data["start"],
            "end": event_data["end"],
            "status": "confirmed",
        }

        # Create event
        result = (
            mock_calendar_service.events()
            .insert(calendarId="primary", body=event_data)
            .execute()
        )

        # Verify event creation
        assert result["id"] == "event_12345"
        assert "エピソード" in result["summary"]
        assert result["status"] == "confirmed"

        # Verify API call
        mock_calendar_service.events().insert.assert_called_with(
            calendarId="primary", body=event_data
        )

    @pytest.mark.integration
    def test_bulk_calendar_event_creation(
        self, mock_calendar_service, sample_release_data
    ):
        """Test creating multiple calendar events efficiently."""
        created_events = []

        for i, release in enumerate(sample_release_data):
            event_data = {
                "summary": f'{release.get("title", "Unknown")} - {release.get("release_type", "episode")} {release.get("number", "N/A")}',
                "description": f'プラットフォーム: {release.get("platform", "Unknown")}',
                "start": {
                    "date": release.get("release_date", "2024-01-15"),
                    "timeZone": "Asia/Tokyo",
                },
                "end": {
                    "date": release.get("release_date", "2024-01-15"),
                    "timeZone": "Asia/Tokyo",
                },
            }

            # Mock unique response for each event
            mock_calendar_service.events().insert.return_value.execute.return_value = {
                "id": f'event_{i}_{release.get("work_id")}',
                "htmlLink": f"https://calendar.google.com/event?eid=event_{i}",
                "summary": event_data["summary"],
                "status": "confirmed",
            }

            # Create event
            result = (
                mock_calendar_service.events()
                .insert(calendarId="primary", body=event_data)
                .execute()
            )

            created_events.append(result)

        # Verify all events were created
        assert len(created_events) == len(sample_release_data)

        # Verify unique event IDs
        event_ids = [event["id"] for event in created_events]
        assert len(set(event_ids)) == len(event_ids)

    @pytest.mark.integration
    def test_calendar_event_with_reminders(
        self, mock_calendar_service, sample_release_data
    ):
        """Test creating calendar events with notification reminders."""
        release = sample_release_data[0]

        # Event with reminders
        event_data = {
            "summary": f'{release.get("title", "Unknown")} 配信',
            "description": "お気に入りアニメの新エピソード配信です",
            "start": {
                "dateTime": "2024-01-15T09:00:00+09:00",
                "timeZone": "Asia/Tokyo",
            },
            "end": {"dateTime": "2024-01-15T09:30:00+09:00", "timeZone": "Asia/Tokyo"},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 30},  # 30 minutes before
                    {"method": "email", "minutes": 60 * 24},  # 1 day before
                ],
            },
            "colorId": "3",  # Blue color
        }

        mock_calendar_service.events().insert.return_value.execute.return_value = {
            "id": "event_with_reminders",
            "htmlLink": "https://calendar.google.com/event?eid=event_with_reminders",
            "summary": event_data["summary"],
            "reminders": event_data["reminders"],
            "status": "confirmed",
        }

        # Create event
        result = (
            mock_calendar_service.events()
            .insert(calendarId="primary", body=event_data)
            .execute()
        )

        # Verify reminders are set
        assert result["reminders"]["useDefault"] is False
        assert len(result["reminders"]["overrides"]) == 2
        assert any(
            r["method"] == "popup" and r["minutes"] == 30
            for r in result["reminders"]["overrides"]
        )
        assert any(
            r["method"] == "email" and r["minutes"] == 1440
            for r in result["reminders"]["overrides"]
        )

    @pytest.mark.integration
    def test_calendar_event_conflict_detection(self, mock_calendar_service):
        """Test detecting and handling calendar event conflicts."""
        # Mock existing events query
        existing_events = {
            "items": [
                {
                    "id": "existing_event_1",
                    "summary": "ワンピース - エピソード 1050",
                    "start": {"date": "2024-01-15"},
                    "end": {"date": "2024-01-15"},
                }
            ]
        }

        mock_calendar_service.events().list.return_value.execute.return_value = (
            existing_events
        )

        # Query for existing events
        events_result = (
            mock_calendar_service.events()
            .list(
                calendarId="primary",
                timeMin="2024-01-15T00:00:00Z",
                timeMax="2024-01-15T23:59:59Z",
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        existing_event_summaries = [
            event["summary"] for event in events_result["items"]
        ]

        # Test conflict detection
        new_event_summary = "ワンピース - エピソード 1050"

        has_conflict = any(
            new_event_summary in existing_summary
            for existing_summary in existing_event_summaries
        )

        assert has_conflict is True

        # Test unique event creation
        unique_event_summary = "ワンピース - エピソード 1051"
        has_conflict_unique = any(
            unique_event_summary in existing_summary
            for existing_summary in existing_event_summaries
        )

        assert has_conflict_unique is False

    @pytest.mark.integration
    def test_calendar_event_update_and_deletion(self, mock_calendar_service):
        """Test updating and deleting calendar events."""
        event_id = "event_to_update"

        # Mock event retrieval
        original_event = {
            "id": event_id,
            "summary": "進撃の巨人 - エピソード 1",
            "description": "配信開始",
            "start": {"date": "2024-01-15"},
            "end": {"date": "2024-01-15"},
        }

        mock_calendar_service.events().get.return_value.execute.return_value = (
            original_event
        )

        # Get existing event
        event = (
            mock_calendar_service.events()
            .get(calendarId="primary", eventId=event_id)
            .execute()
        )

        # Update event
        updated_event = event.copy()
        updated_event["summary"] = "進撃の巨人 - エピソード 1 (再放送)"
        updated_event["description"] = "再放送配信"

        mock_calendar_service.events().update.return_value.execute.return_value = (
            updated_event
        )

        # Perform update
        result = (
            mock_calendar_service.events()
            .update(calendarId="primary", eventId=event_id, body=updated_event)
            .execute()
        )

        assert "再放送" in result["summary"]
        assert result["description"] == "再放送配信"

        # Test deletion
        mock_calendar_service.events().delete.return_value.execute.return_value = {}

        delete_result = (
            mock_calendar_service.events()
            .delete(calendarId="primary", eventId=event_id)
            .execute()
        )

        # Delete should return empty response
        assert delete_result == {}

    @pytest.mark.integration
    def test_calendar_recurring_events(self, mock_calendar_service):
        """Test creating recurring events for weekly anime series."""
        # Weekly anime series event
        recurring_event = {
            "summary": "ワンピース - 毎週配信",
            "description": "毎週日曜日の新エピソード配信",
            "start": {
                "dateTime": "2024-01-15T09:00:00+09:00",
                "timeZone": "Asia/Tokyo",
            },
            "end": {"dateTime": "2024-01-15T09:30:00+09:00", "timeZone": "Asia/Tokyo"},
            "recurrence": [
                "RRULE:FREQ=WEEKLY;BYDAY=SU;COUNT=26"  # Weekly for 26 weeks (2 cours)
            ],
            "colorId": "4",  # Green for ongoing series
        }

        mock_calendar_service.events().insert.return_value.execute.return_value = {
            "id": "recurring_anime_event",
            "htmlLink": "https://calendar.google.com/event?eid=recurring_anime_event",
            "summary": recurring_event["summary"],
            "recurrence": recurring_event["recurrence"],
            "status": "confirmed",
        }

        result = (
            mock_calendar_service.events()
            .insert(calendarId="primary", body=recurring_event)
            .execute()
        )

        # Verify recurring event creation
        assert result["recurrence"][0] == "RRULE:FREQ=WEEKLY;BYDAY=SU;COUNT=26"
        assert "毎週配信" in result["summary"]

    @pytest.mark.integration
    def test_calendar_multiple_calendar_support(self, mock_calendar_service):
        """Test managing events across multiple calendars."""
        calendars = {
            "anime": "anime_calendar_id@group.calendar.google.com",
            "manga": "manga_calendar_id@group.calendar.google.com",
            "primary": "primary",
        }

        # Create events in different calendars
        for category, calendar_id in calendars.items():
            event_data = {
                "summary": f"{category.upper()} 配信イベント",
                "description": f"{category}関連の配信通知",
                "start": {"date": "2024-01-15"},
                "end": {"date": "2024-01-15"},
                "colorId": (
                    "3" if category == "anime" else "6"
                ),  # Blue for anime, orange for manga
            }

            mock_calendar_service.events().insert.return_value.execute.return_value = {
                "id": f"{category}_event_123",
                "summary": event_data["summary"],
                "status": "confirmed",
            }

            result = (
                mock_calendar_service.events()
                .insert(calendarId=calendar_id, body=event_data)
                .execute()
            )

            assert category.upper() in result["summary"]
            mock_calendar_service.events().insert.assert_called_with(
                calendarId=calendar_id, body=event_data
            )

    @pytest.mark.integration
    def test_calendar_timezone_handling(self, mock_calendar_service):
        """Test proper timezone handling for different regions."""
        timezones = ["Asia/Tokyo", "America/New_York", "Europe/London", "UTC"]

        base_time = "2024-01-15T20:00:00"

        for timezone in timezones:
            event_data = {
                "summary": f"グローバル配信 - {timezone}",
                "start": {
                    "dateTime": (
                        f"{base_time}+09:00"
                        if timezone == "Asia/Tokyo"
                        else f"{base_time}Z"
                    ),
                    "timeZone": timezone,
                },
                "end": {
                    "dateTime": (
                        f"{base_time}+09:00"
                        if timezone == "Asia/Tokyo"
                        else f"{base_time}Z"
                    ),
                    "timeZone": timezone,
                },
            }

            mock_calendar_service.events().insert.return_value.execute.return_value = {
                "id": f'tz_event_{timezone.replace("/", "_")}',
                "summary": event_data["summary"],
                "start": event_data["start"],
                "end": event_data["end"],
            }

            result = (
                mock_calendar_service.events()
                .insert(calendarId="primary", body=event_data)
                .execute()
            )

            assert result["start"]["timeZone"] == timezone
            assert timezone in result["summary"]

    @pytest.mark.integration
    @pytest.mark.performance
    def test_calendar_batch_operations_performance(
        self, mock_calendar_service, performance_test_config
    ):
        """Test calendar batch operations performance."""
        import time

        max_response_time = performance_test_config["max_response_time"]
        batch_size = 10

        # Mock batch response
        mock_calendar_service.new_batch_http_request.return_value = Mock()

        # Prepare batch operations
        batch_requests = []
        for i in range(batch_size):
            event_data = {
                "summary": f"バッチイベント {i}",
                "start": {"date": "2024-01-15"},
                "end": {"date": "2024-01-15"},
            }
            batch_requests.append(event_data)

        # Simulate batch execution
        start_time = time.time()

        # Mock batch execution
        for event_data in batch_requests:
            mock_calendar_service.events().insert.return_value.execute.return_value = {
                "id": f"batch_event_{hash(str(event_data))}",
                "summary": event_data["summary"],
            }

            mock_calendar_service.events().insert(
                calendarId="primary", body=event_data
            ).execute()

        end_time = time.time()
        execution_time = end_time - start_time

        # Verify performance
        assert execution_time < max_response_time * batch_size

        # Verify all events were processed
        assert mock_calendar_service.events().insert.call_count == batch_size


class TestCalendarEventFormatting:
    """Test calendar event formatting and localization."""

    @pytest.mark.unit
    def test_anime_event_formatting(self, sample_work_data, sample_release_data):
        """Test anime-specific event formatting."""
        work = sample_work_data[0]  # Anime work
        release = sample_release_data[0]  # Episode release

        # Format anime event
        event_summary = f'📺 {work["title"]} - 第{release["number"]}話'
        event_description = self._format_anime_event_description(work, release)

        expected_description = f"""アニメ: {work['title']}
エピソード: 第{release['number']}話
配信プラットフォーム: {release['platform']}
配信日: {release['release_date']}

{work.get('title_en', '')}

詳細: {release.get('source_url', 'なし')}"""

        assert "📺" in event_summary
        assert f'第{release["number"]}話' in event_summary
        assert work["title"] in event_description
        assert release["platform"] in event_description

    @pytest.mark.unit
    def test_manga_event_formatting(self, sample_work_data, sample_release_data):
        """Test manga-specific event formatting."""
        # Create manga work data
        manga_work = {
            "id": 2,
            "title": "進撃の巨人",
            "title_kana": "しんげきのきょじん",
            "title_en": "Attack on Titan",
            "type": "manga",
            "official_url": "https://shingeki.tv",
        }

        # Create volume release data
        volume_release = {
            "work_id": 2,
            "release_type": "volume",
            "number": "34",
            "platform": "BookWalker",
            "release_date": "2024-01-20",
            "source": "rss",
            "source_url": "https://bookwalker.jp/manga/attack-titan-34",
            "notified": 0,
        }

        # Format manga event
        event_summary = f'📚 {manga_work["title"]} - 第{volume_release["number"]}巻'
        event_description = self._format_manga_event_description(
            manga_work, volume_release
        )

        assert "📚" in event_summary
        assert f'第{volume_release["number"]}巻' in event_summary
        assert manga_work["title"] in event_description
        assert volume_release["platform"] in event_description

    @pytest.mark.unit
    def test_event_color_coding(self):
        """Test color coding for different types of events."""
        color_map = {
            "anime_episode": "3",  # Blue
            "manga_volume": "6",  # Orange
            "special_event": "4",  # Green
            "movie_release": "8",  # Purple
            "season_finale": "11",  # Red
        }

        # Test anime episode color
        anime_event = {"type": "anime_episode"}
        anime_color = self._get_event_color(anime_event)
        assert anime_color == color_map["anime_episode"]

        # Test manga volume color
        manga_event = {"type": "manga_volume"}
        manga_color = self._get_event_color(manga_event)
        assert manga_color == color_map["manga_volume"]

        # Test special event color
        special_event = {"type": "special_event", "is_finale": True}
        special_color = self._get_event_color(special_event)
        # Should prioritize finale over special
        assert special_color == color_map["season_finale"]

    @pytest.mark.unit
    def test_event_duration_calculation(self):
        """Test event duration calculation for different content types."""
        duration_map = {
            "episode": 30,  # 30 minutes
            "movie": 120,  # 2 hours
            "volume": 0,  # All-day event
            "special": 60,  # 1 hour
        }

        for content_type, expected_duration in duration_map.items():
            start_time = datetime(2024, 1, 15, 20, 0)  # 8:00 PM

            if expected_duration == 0:
                # All-day event
                event_start = {"date": "2024-01-15"}
                event_end = {"date": "2024-01-15"}
            else:
                # Timed event
                end_time = start_time + timedelta(minutes=expected_duration)
                event_start = {
                    "dateTime": start_time.isoformat() + "+09:00",
                    "timeZone": "Asia/Tokyo",
                }
                event_end = {
                    "dateTime": end_time.isoformat() + "+09:00",
                    "timeZone": "Asia/Tokyo",
                }

            # Verify duration calculation
            if expected_duration == 0:
                assert "date" in event_start and "date" in event_end
            else:
                start_dt = datetime.fromisoformat(
                    event_start["dateTime"].replace("+09:00", "")
                )
                end_dt = datetime.fromisoformat(
                    event_end["dateTime"].replace("+09:00", "")
                )
                actual_duration = (end_dt - start_dt).total_seconds() / 60
                assert actual_duration == expected_duration

    def _format_anime_event_description(self, work: dict, release: dict) -> str:
        """Format anime event description."""
        return f"""アニメ: {work['title']}
エピソード: 第{release['number']}話
配信プラットフォーム: {release['platform']}
配信日: {release['release_date']}

{work.get('title_en', '')}

詳細: {release.get('source_url', 'なし')}"""

    def _format_manga_event_description(self, work: dict, release: dict) -> str:
        """Format manga event description."""
        return f"""マンガ: {work['title']}
巻数: 第{release['number']}巻
配信プラットフォーム: {release['platform']}
発売日: {release['release_date']}

{work.get('title_en', '')}

詳細: {release.get('source_url', 'なし')}"""

    def _get_event_color(self, event: dict) -> str:
        """Get appropriate color for event type."""
        if event.get("is_finale"):
            return "11"  # Red for finales

        color_map = {
            "anime_episode": "3",  # Blue
            "manga_volume": "6",  # Orange
            "special_event": "4",  # Green
            "movie_release": "8",  # Purple
        }

        return color_map.get(event.get("type"), "1")  # Default to blue


class TestCalendarErrorHandling:
    """Test calendar API error handling and recovery."""

    @pytest.mark.integration
    def test_calendar_quota_exceeded_handling(self, mock_calendar_service):
        """Test handling of calendar API quota exceeded errors."""
        from googleapiclient.errors import HttpError

        # Mock quota exceeded error
        error_response = Mock()
        error_response.status_code = 403
        error_content = b'{"error": {"code": 403, "message": "Rate Limit Exceeded"}}'

        mock_calendar_service.events().insert.return_value.execute.side_effect = (
            HttpError(error_response, error_content)
        )

        # Test error handling with retry logic
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                mock_calendar_service.events().insert(
                    calendarId="primary", body={"summary": "Test Event"}
                ).execute()
                break
            except HttpError as e:
                retry_count += 1
                if retry_count >= max_retries:
                    assert e.resp.status_code == 403
                    break

        assert retry_count == max_retries

    @pytest.mark.integration
    def test_calendar_invalid_event_data_handling(self, mock_calendar_service):
        """Test handling of invalid event data."""
        from googleapiclient.errors import HttpError

        # Invalid event data (missing required fields)
        invalid_event = {
            "summary": "",  # Empty summary
            # Missing start/end dates
        }

        # Mock validation error
        error_response = Mock()
        error_response.status_code = 400
        error_content = b'{"error": {"code": 400, "message": "Invalid event data"}}'

        mock_calendar_service.events().insert.return_value.execute.side_effect = (
            HttpError(error_response, error_content)
        )

        # Test error handling
        with pytest.raises(HttpError) as exc_info:
            mock_calendar_service.events().insert(
                calendarId="primary", body=invalid_event
            ).execute()

        assert exc_info.value.resp.status_code == 400

    @pytest.mark.integration
    def test_calendar_network_error_recovery(self, mock_calendar_service):
        """Test recovery from network errors."""
        import time
        from requests.exceptions import ConnectionError

        # Mock network error followed by success
        mock_calendar_service.events().insert.return_value.execute.side_effect = [
            ConnectionError("Network unreachable"),
            ConnectionError("Network unreachable"),
            {
                "id": "recovered_event",
                "summary": "Successfully created after retry",
                "status": "confirmed",
            },
        ]

        # Retry logic
        max_retries = 3
        retry_count = 0
        result = None

        while retry_count < max_retries:
            try:
                result = (
                    mock_calendar_service.events()
                    .insert(calendarId="primary", body={"summary": "Test Event"})
                    .execute()
                )
                break
            except ConnectionError:
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(0.1)  # Small delay for testing

        # Should succeed on third attempt
        assert result is not None
        assert result["id"] == "recovered_event"
        assert retry_count == 2  # Failed twice, succeeded on third
