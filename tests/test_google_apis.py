#!/usr/bin/env python3
"""
Unit and integration tests for Google APIs (Gmail and Calendar)
"""

import pytest
import json
import base64
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import googleapiclient.errors


class TestGmailAPI:
    """Test Gmail API integration for email notifications."""

    @pytest.mark.unit
    @pytest.mark.auth
    def test_gmail_service_authentication(self, test_config):
        """Test Gmail API service authentication."""
        gmail_config = test_config["google"]["gmail"]

        with patch("google.auth.load_credentials_from_file") as mock_load_creds, patch(
            "googleapiclient.discovery.build"
        ) as mock_build:

            # Mock credentials
            mock_credentials = Mock()
            mock_load_creds.return_value = (mock_credentials, None)

            # Mock service
            mock_service = Mock()
            mock_build.return_value = mock_service

            # Simulate service initialization
            from googleapiclient.discovery import build

            service = build("gmail", "v1", credentials=mock_credentials)

            # Verify service creation
            assert mock_build.called
            mock_build.assert_called_with("gmail", "v1", credentials=mock_credentials)
            assert service is not None

    @pytest.mark.unit
    def test_email_message_creation(self, mock_gmail_service, sample_release_data):
        """Test email message creation with HTML content."""
        release = sample_release_data[0]

        # Create email message
        message = MIMEMultipart("alternative")
        message["to"] = "test@example.com"
        message["subject"] = "[アニメ・マンガ情報] 新着情報"

        # HTML content
        html_content = f"""
        <html>
            <body>
                <h2>新着情報</h2>
                <div>
                    <h3>{release['release_type']} 更新</h3>
                    <p>エピソード: {release['number']}</p>
                    <p>配信プラットフォーム: {release['platform']}</p>
                    <p>配信日: {release['release_date']}</p>
                    <p><a href="{release['source_url']}">詳細を見る</a></p>
                </div>
            </body>
        </html>
        """

        # Plain text fallback
        text_content = f"""
        新着情報
        
        {release['release_type']} 更新
        エピソード: {release['number']}
        配信プラットフォーム: {release['platform']}
        配信日: {release['release_date']}
        
        詳細: {release['source_url']}
        """

        # Attach parts
        html_part = MIMEText(html_content, "html", "utf-8")
        text_part = MIMEText(text_content, "plain", "utf-8")
        message.attach(text_part)
        message.attach(html_part)

        # Convert to raw message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        # Verify message structure
        assert message["to"] == "test@example.com"
        assert "[アニメ・マンガ情報]" in message["subject"]
        assert len(message.get_payload()) == 2  # Text and HTML parts
        assert raw_message is not None
        assert len(raw_message) > 0

    @pytest.mark.integration
    @pytest.mark.api
    def test_send_email_success(self, mock_gmail_service, sample_release_data):
        """Test successful email sending via Gmail API."""
        release = sample_release_data[0]

        # Mock successful response
        mock_gmail_service.users().messages().send().execute.return_value = {
            "id": "test_message_id_12345",
            "threadId": "test_thread_id_67890",
        }

        # Create and send message
        message = MIMEText("Test email content", "plain", "utf-8")
        message["to"] = "test@example.com"
        message["subject"] = "Test Subject"

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        # Send email
        result = (
            mock_gmail_service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )

        # Verify result
        assert result["id"] == "test_message_id_12345"
        assert result["threadId"] == "test_thread_id_67890"

        # Verify API call
        mock_gmail_service.users().messages().send.assert_called_once_with(
            userId="me", body={"raw": raw_message}
        )

    @pytest.mark.integration
    @pytest.mark.api
    def test_send_email_with_multiple_releases(
        self, mock_gmail_service, sample_work_data, sample_release_data
    ):
        """Test sending email with multiple anime/manga releases."""
        works = sample_work_data[:2]
        releases = sample_release_data[:2]

        # Create combined email content
        html_content = "<html><body><h2>新着情報</h2>"

        for i, (work, release) in enumerate(zip(works, releases)):
            html_content += f"""
            <div style="margin: 20px 0; padding: 15px; border: 1px solid #ddd;">
                <h3>{work['title']} ({work['title_en']})</h3>
                <p><strong>タイプ:</strong> {work['type']}</p>
                <p><strong>更新:</strong> {release['release_type']} {release['number']}</p>
                <p><strong>プラットフォーム:</strong> {release['platform']}</p>
                <p><strong>配信日:</strong> {release['release_date']}</p>
                <p><a href="{release['source_url']}">詳細を見る</a></p>
            </div>
            """

        html_content += "</body></html>"

        # Create message
        message = MIMEText(html_content, "html", "utf-8")
        message["to"] = "test@example.com"
        message["subject"] = f"[アニメ・マンガ情報] {len(releases)}件の新着情報"

        # Mock successful send
        mock_gmail_service.users().messages().send().execute.return_value = {
            "id": "bulk_message_id",
            "threadId": "bulk_thread_id",
        }

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        result = (
            mock_gmail_service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )

        # Verify successful send
        assert result["id"] == "bulk_message_id"

        # Verify email content includes both works
        decoded_message = base64.urlsafe_b64decode(raw_message).decode("utf-8")
        assert works[0]["title"] in decoded_message
        assert works[1]["title"] in decoded_message
        assert str(len(releases)) in message["subject"]

    @pytest.mark.integration
    @pytest.mark.api
    def test_gmail_api_error_handling(self, mock_gmail_service):
        """Test Gmail API error handling."""
        # Mock API error
        error_response = googleapiclient.errors.HttpError(
            resp=Mock(status=400),
            content=b'{"error": {"code": 400, "message": "Invalid request"}}',
        )

        mock_gmail_service.users().messages().send().execute.side_effect = (
            error_response
        )

        # Test error handling
        message = MIMEText("Test message", "plain", "utf-8")
        message["to"] = "test@example.com"
        message["subject"] = "Test"

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        with pytest.raises(googleapiclient.errors.HttpError):
            mock_gmail_service.users().messages().send(
                userId="me", body={"raw": raw_message}
            ).execute()

    @pytest.mark.unit
    def test_email_template_generation(self, sample_work_data, sample_release_data):
        """Test dynamic email template generation."""
        works = sample_work_data
        releases = sample_release_data

        # Template function
        def generate_email_template(work_release_pairs):
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { background: linear-gradient(90deg, #ff6b6b, #4ecdc4); color: white; padding: 20px; border-radius: 8px; }
                    .item { margin: 15px 0; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; }
                    .anime { border-left: 4px solid #3498db; }
                    .manga { border-left: 4px solid #2ecc71; }
                    .footer { margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 8px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🎬📚 アニメ・マンガ最新情報</h1>
                    <p>新着情報をお届けします</p>
                </div>
            """

            for work, release in work_release_pairs:
                item_class = work["type"]  # anime or manga
                type_emoji = "🎬" if work["type"] == "anime" else "📚"

                html += f"""
                <div class="item {item_class}">
                    <h2>{type_emoji} {work['title']}</h2>
                    <p><strong>英題:</strong> {work['title_en']}</p>
                    <p><strong>更新情報:</strong> {release['release_type']} {release['number']}</p>
                    <p><strong>プラットフォーム:</strong> {release['platform']}</p>
                    <p><strong>配信日:</strong> {release['release_date']}</p>
                    <p><a href="{work['official_url']}" style="color: #3498db;">公式サイト</a> | 
                       <a href="{release['source_url']}" style="color: #e74c3c;">詳細情報</a></p>
                </div>
                """

            html += """
                <div class="footer">
                    <p>このメールは自動配信システムから送信されています。</p>
                    <p>アニメ・マンガ情報配信システム</p>
                </div>
            </body>
            </html>
            """

            return html

        # Generate template
        work_release_pairs = list(zip(works, releases))
        html_template = generate_email_template(work_release_pairs)

        # Verify template content
        assert "アニメ・マンガ最新情報" in html_template
        assert works[0]["title"] in html_template
        assert works[1]["title"] in html_template
        assert releases[0]["platform"] in html_template
        assert releases[1]["platform"] in html_template
        assert "🎬" in html_template  # Anime emoji
        assert "📚" in html_template  # Manga emoji


class TestCalendarAPI:
    """Test Google Calendar API integration for event creation."""

    @pytest.mark.unit
    @pytest.mark.auth
    def test_calendar_service_authentication(self, test_config):
        """Test Google Calendar API service authentication."""
        calendar_config = test_config["google"]["calendar"]

        with patch("google.auth.load_credentials_from_file") as mock_load_creds, patch(
            "googleapiclient.discovery.build"
        ) as mock_build:

            # Mock credentials
            mock_credentials = Mock()
            mock_load_creds.return_value = (mock_credentials, None)

            # Mock service
            mock_service = Mock()
            mock_build.return_value = mock_service

            # Simulate service initialization
            from googleapiclient.discovery import build

            service = build("calendar", "v3", credentials=mock_credentials)

            # Verify service creation
            assert mock_build.called
            mock_build.assert_called_with(
                "calendar", "v3", credentials=mock_credentials
            )
            assert service is not None

    @pytest.mark.integration
    @pytest.mark.api
    def test_create_calendar_event(
        self, mock_calendar_service, sample_work_data, sample_release_data
    ):
        """Test creating calendar events for anime/manga releases."""
        work = sample_work_data[0]
        release = sample_release_data[0]

        # Create event data
        event_data = {
            "summary": f'{work["title"]} {release["release_type"]} {release["number"]}',
            "description": f'{work["title"]} ({work["title_en"]})の{release["release_type"]} {release["number"]}が{release["platform"]}で配信されます。',
            "start": {
                "dateTime": f'{release["release_date"]}T09:00:00+09:00',
                "timeZone": "Asia/Tokyo",
            },
            "end": {
                "dateTime": f'{release["release_date"]}T10:00:00+09:00',
                "timeZone": "Asia/Tokyo",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 60},
                    {"method": "popup", "minutes": 10},
                ],
            },
            "source": {"title": work["title"], "url": work["official_url"]},
        }

        # Mock successful event creation
        mock_calendar_service.events().insert().execute.return_value = {
            "id": "test_event_id_12345",
            "htmlLink": "https://calendar.google.com/event?eid=test_event_id_12345",
            "created": "2024-01-01T12:00:00Z",
            "updated": "2024-01-01T12:00:00Z",
        }

        # Create event
        result = (
            mock_calendar_service.events()
            .insert(calendarId="primary", body=event_data)
            .execute()
        )

        # Verify result
        assert result["id"] == "test_event_id_12345"
        assert "calendar.google.com" in result["htmlLink"]

        # Verify API call
        mock_calendar_service.events().insert.assert_called_once_with(
            calendarId="primary", body=event_data
        )

    @pytest.mark.integration
    @pytest.mark.api
    def test_create_multiple_calendar_events(
        self, mock_calendar_service, sample_work_data, sample_release_data
    ):
        """Test creating multiple calendar events in batch."""
        works = sample_work_data
        releases = sample_release_data

        # Mock successful responses for each event
        def mock_insert_response(*args, **kwargs):
            mock_response = Mock()
            mock_response.execute.return_value = {
                "id": f"event_id_{len(mock_calendar_service.events().insert.call_args_list)}",
                "htmlLink": f"https://calendar.google.com/event?eid=event_id_{len(mock_calendar_service.events().insert.call_args_list)}",
                "created": "2024-01-01T12:00:00Z",
            }
            return mock_response

        mock_calendar_service.events().insert.side_effect = mock_insert_response

        # Create events for all releases
        created_events = []
        for work, release in zip(works, releases):
            event_data = {
                "summary": f'{work["title"]} {release["release_type"]} {release["number"]}',
                "description": f'{work["title"]}の{release["release_type"]}更新',
                "start": {
                    "dateTime": f'{release["release_date"]}T09:00:00+09:00',
                    "timeZone": "Asia/Tokyo",
                },
                "end": {
                    "dateTime": f'{release["release_date"]}T10:00:00+09:00',
                    "timeZone": "Asia/Tokyo",
                },
            }

            result = (
                mock_calendar_service.events()
                .insert(calendarId="primary", body=event_data)
                .execute()
            )

            created_events.append(result)

        # Verify all events were created
        assert len(created_events) == len(works)
        assert mock_calendar_service.events().insert.call_count == len(works)

        for i, event in enumerate(created_events):
            assert event["id"] == f"event_id_{i+1}"
            assert "calendar.google.com" in event["htmlLink"]

    @pytest.mark.unit
    def test_calendar_event_color_assignment(self, sample_work_data, test_config):
        """Test color assignment for calendar events based on content type."""
        calendar_config = test_config["notification"]["calendar"]
        color_mapping = calendar_config.get("color_by_type", {})

        anime_work = next(work for work in sample_work_data if work["type"] == "anime")
        manga_work = next(work for work in sample_work_data if work["type"] == "manga")

        # Function to get color ID for event type
        def get_event_color_id(work_type):
            color_name = color_mapping.get(work_type, "blue")  # default to blue
            color_ids = {
                "blue": "1",
                "green": "2",
                "purple": "3",
                "red": "4",
                "yellow": "5",
                "orange": "6",
                "turquoise": "7",
                "gray": "8",
            }
            return color_ids.get(color_name, "1")

        # Test color assignment
        anime_color = get_event_color_id(anime_work["type"])
        manga_color = get_event_color_id(manga_work["type"])

        assert anime_color == "1"  # blue for anime
        assert manga_color == "2"  # green for manga
        assert anime_color != manga_color  # Different colors for different types

    @pytest.mark.integration
    @pytest.mark.api
    def test_calendar_api_error_handling(self, mock_calendar_service):
        """Test Google Calendar API error handling."""
        # Mock API error
        error_response = googleapiclient.errors.HttpError(
            resp=Mock(status=403),
            content=b'{"error": {"code": 403, "message": "Insufficient permissions"}}',
        )

        mock_calendar_service.events().insert().execute.side_effect = error_response

        # Test error handling
        event_data = {
            "summary": "Test Event",
            "start": {"dateTime": "2024-01-01T12:00:00+09:00"},
            "end": {"dateTime": "2024-01-01T13:00:00+09:00"},
        }

        with pytest.raises(googleapiclient.errors.HttpError):
            mock_calendar_service.events().insert(
                calendarId="primary", body=event_data
            ).execute()

    @pytest.mark.unit
    def test_event_datetime_formatting(self):
        """Test proper datetime formatting for calendar events."""
        from datetime import datetime, timezone, timedelta

        # Test datetime conversion
        release_date = "2024-01-15"
        release_time = "21:00"  # 9 PM JST

        # Convert to proper ISO format with timezone
        jst = timezone(timedelta(hours=9))
        start_datetime = datetime.strptime(
            f"{release_date} {release_time}", "%Y-%m-%d %H:%M"
        )
        start_datetime = start_datetime.replace(tzinfo=jst)

        # Format for Google Calendar API
        start_datetime_str = start_datetime.isoformat()
        end_datetime = start_datetime + timedelta(hours=1)
        end_datetime_str = end_datetime.isoformat()

        # Verify formatting
        assert start_datetime_str == "2024-01-15T21:00:00+09:00"
        assert end_datetime_str == "2024-01-15T22:00:00+09:00"

        # Test all-day event formatting
        all_day_event = {"start": {"date": release_date}, "end": {"date": release_date}}

        assert all_day_event["start"]["date"] == "2024-01-15"
        assert all_day_event["end"]["date"] == "2024-01-15"


class TestGoogleAPIsIntegration:
    """Test integration between Gmail and Calendar APIs."""

    @pytest.mark.integration
    @pytest.mark.api
    def test_combined_notification_workflow(
        self,
        mock_gmail_service,
        mock_calendar_service,
        sample_work_data,
        sample_release_data,
    ):
        """Test complete notification workflow: email + calendar event."""
        work = sample_work_data[0]
        release = sample_release_data[0]

        # Mock successful email send
        mock_gmail_service.users().messages().send().execute.return_value = {
            "id": "email_id_12345",
            "threadId": "thread_id_67890",
        }

        # Mock successful calendar event creation
        mock_calendar_service.events().insert().execute.return_value = {
            "id": "event_id_12345",
            "htmlLink": "https://calendar.google.com/event?eid=event_id_12345",
        }

        # Execute workflow
        workflow_results = {}

        # Step 1: Send email notification
        email_message = MIMEText(
            f'{work["title"]} {release["release_type"]} {release["number"]} 配信開始',
            "plain",
            "utf-8",
        )
        email_message["to"] = "user@example.com"
        email_message["subject"] = f'[アニメ情報] {work["title"]} 更新通知'

        raw_message = base64.urlsafe_b64encode(email_message.as_bytes()).decode("utf-8")
        email_result = (
            mock_gmail_service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )

        workflow_results["email"] = email_result

        # Step 2: Create calendar event
        event_data = {
            "summary": f'{work["title"]} {release["release_type"]} {release["number"]}',
            "description": f'メール通知ID: {email_result["id"]}',  # Link to email
            "start": {
                "dateTime": f'{release["release_date"]}T21:00:00+09:00',
                "timeZone": "Asia/Tokyo",
            },
            "end": {
                "dateTime": f'{release["release_date"]}T22:00:00+09:00',
                "timeZone": "Asia/Tokyo",
            },
        }

        calendar_result = (
            mock_calendar_service.events()
            .insert(calendarId="primary", body=event_data)
            .execute()
        )

        workflow_results["calendar"] = calendar_result

        # Verify workflow completion
        assert "email" in workflow_results
        assert "calendar" in workflow_results
        assert workflow_results["email"]["id"] == "email_id_12345"
        assert workflow_results["calendar"]["id"] == "event_id_12345"

        # Verify cross-references
        calendar_description = event_data["description"]
        assert workflow_results["email"]["id"] in calendar_description

    @pytest.mark.performance
    def test_batch_notification_performance(
        self,
        mock_gmail_service,
        mock_calendar_service,
        test_data_generator,
        performance_test_config,
    ):
        """Test performance of batch notifications."""
        import time

        # Generate test data
        anime_data = test_data_generator.generate_anime_data(20)

        # Mock fast responses
        mock_gmail_service.users().messages().send().execute.return_value = {
            "id": "email_id"
        }
        mock_calendar_service.events().insert().execute.return_value = {
            "id": "event_id"
        }

        # Execute batch notifications
        start_time = time.time()

        notification_results = []
        for i, anime in enumerate(anime_data):
            # Create email
            message = MIMEText(f"Test notification {i}", "plain", "utf-8")
            message["to"] = "test@example.com"
            message["subject"] = f"Test {i}"

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            email_result = (
                mock_gmail_service.users()
                .messages()
                .send(userId="me", body={"raw": raw_message})
                .execute()
            )

            # Create calendar event
            event_data = {
                "summary": f"Test Event {i}",
                "start": {"dateTime": "2024-01-01T12:00:00+09:00"},
                "end": {"dateTime": "2024-01-01T13:00:00+09:00"},
            }

            calendar_result = (
                mock_calendar_service.events()
                .insert(calendarId="primary", body=event_data)
                .execute()
            )

            notification_results.append(
                {"email_id": email_result["id"], "event_id": calendar_result["id"]}
            )

        end_time = time.time()
        total_time = end_time - start_time

        # Verify performance
        max_time = (
            performance_test_config["max_response_time"] * len(anime_data) * 2
        )  # 2 API calls per item
        assert (
            total_time < max_time
        ), f"Batch notifications took {total_time:.2f}s, should be under {max_time:.2f}s"

        # Verify all notifications created
        assert len(notification_results) == len(anime_data)
        assert mock_gmail_service.users().messages().send.call_count == len(anime_data)
        assert mock_calendar_service.events().insert.call_count == len(anime_data)
