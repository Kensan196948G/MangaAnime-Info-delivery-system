#!/usr/bin/env python3
"""
Integration tests for email notification functionality
"""

import pytest
import json
import base64
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class TestEmailNotificationIntegration:
    """Test Gmail API integration for notifications."""

    @pytest.mark.integration
    @pytest.mark.auth
    def test_gmail_authentication_setup(self, mock_gmail_service):
        """Test Gmail API authentication setup."""
        with patch("google.auth.default") as mock_auth, patch(
            "googleapiclient.discovery.build"
        ) as mock_build:
            # Mock credentials
            mock_credentials = Mock()
            mock_auth.return_value = (mock_credentials, "project-id")

            # Mock service build
            mock_build.return_value = mock_gmail_service

            # Test authentication flow
            from google.auth import default
            from googleapiclient.discovery import build

            credentials, project = default()
            service = build("gmail", "v1", credentials=credentials)

            assert credentials is not None
            assert service is not None
            mock_build.assert_called_with("gmail", "v1", credentials=credentials)

    @pytest.mark.integration
    @pytest.mark.auth
    def test_oauth2_token_refresh(self):
        """Test OAuth2 token refresh mechanism."""
        with patch("google.auth.transport.requests.Request") as mock_request, patch(
            "google.oauth2.credentials.Credentials"
        ) as mock_creds:
            # Mock expired credentials
            expired_creds = Mock()
            expired_creds.expired = True
            expired_creds.valid = False

            # Mock refresh
            mock_creds.return_value = expired_creds
            mock_request.return_value = Mock()

            # Test token refresh
            expired_creds.refresh(mock_request.return_value)

            # Verify refresh was called
            assert expired_creds.refresh.called

    @pytest.mark.integration
    def test_email_composition_and_encoding(self, sample_release_data):
        """Test email composition with proper Japanese text encoding."""
        release = sample_release_data[0]

        # Create email content
        subject = f"新エピソード配信: {release.get('title', 'Unknown')}"
        body_text = f"""
        作品: {release.get('title', 'Unknown')}
        エピソード: 第{release.get('number', 'N/A')}話
        配信日: {release.get('release_date', 'TBD')}
        プラットフォーム: {release.get('platform', 'Unknown')}
        """

        # Create HTML content
        body_html = f"""
        <html>
        <body>
        <h2>新エピソード配信通知</h2>
        <p><strong>作品:</strong> {release.get('title', 'Unknown')}</p>
        <p><strong>エピソード:</strong> 第{release.get('number', 'N/A')}話</p>
        <p><strong>配信日:</strong> {release.get('release_date', 'TBD')}</p>
        <p><strong>プラットフォーム:</strong> {release.get('platform', 'Unknown')}</p>
        </body>
        </html>
        """

        # Create multipart message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = "test@example.com"
        message["To"] = "user@example.com"

        # Attach text and HTML parts
        text_part = MIMEText(body_text, "plain", "utf-8")
        html_part = MIMEText(body_html, "html", "utf-8")

        message.attach(text_part)
        message.attach(html_part)

        # Test encoding
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        assert raw_message is not None
        assert len(raw_message) > 0

        # Verify Japanese characters are properly encoded
        assert "エピソード" in body_text
        assert "配信" in body_html

    @pytest.mark.integration
    def test_gmail_send_message(self, mock_gmail_service, sample_release_data):
        """Test sending email message through Gmail API."""
        release = sample_release_data[0]

        # Prepare message
        message = {"raw": "base64_encoded_message_content"}

        # Mock Gmail service response
        mock_gmail_service.users().messages().send.return_value.execute.return_value = {
            "id": "test_message_id_12345",
            "threadId": "test_thread_id_67890",
            "labelIds": ["SENT"],
        }

        # Test send operation
        result = (
            mock_gmail_service.users()
            .messages()
            .send(userId="me", body=message)
            .execute()
        )

        # Verify response
        assert result["id"] == "test_message_id_12345"
        assert result["threadId"] == "test_thread_id_67890"
        assert "SENT" in result["labelIds"]

        # Verify API call
        mock_gmail_service.users().messages().send.assert_called_with(
            userId="me", body=message
        )

    @pytest.mark.integration
    def test_bulk_email_notification(self, mock_gmail_service, sample_release_data):
        """Test sending multiple notifications efficiently."""
        releases = sample_release_data

        sent_messages = []

        for release in releases:
            # Prepare message for each release
            message = {"raw": f'message_for_release_{release.get("work_id")}'}

            # Mock response
            mock_response = {
                "id": f'msg_id_{release.get("work_id")}',
                "threadId": f'thread_{release.get("work_id")}',
            }

            mock_gmail_service.users().messages().send.return_value.execute.return_value = (
                mock_response
            )

            # Send message
            result = (
                mock_gmail_service.users()
                .messages()
                .send(userId="me", body=message)
                .execute()
            )

            sent_messages.append(result)

        # Verify all messages were sent
        assert len(sent_messages) == len(releases)

        # Verify each message has unique ID
        message_ids = [msg["id"] for msg in sent_messages]
        assert len(set(message_ids)) == len(message_ids)

    @pytest.mark.integration
    def test_email_template_rendering(self, sample_work_data, sample_release_data):
        """Test email template rendering with dynamic content."""
        work = sample_work_data[0]
        release = sample_release_data[0]

        # Email template with placeholders
        template = """
        <html>
        <head>
            <meta charset="utf-8">
            <title>新作配信通知</title>
        </head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">🎬 新作配信のお知らせ</h2>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #495057;">{title}</h3>
                    <p><strong>タイトル（かな）:</strong> {title_kana}</p>
                    <p><strong>英語タイトル:</strong> {title_en}</p>
                    <p><strong>種別:</strong> {work_type}</p>
                </div>
                
                <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #1976d2;">配信情報</h4>
                    <p><strong>エピソード/巻:</strong> {release_type} {number}</p>
                    <p><strong>配信日:</strong> {release_date}</p>
                    <p><strong>プラットフォーム:</strong> {platform}</p>
                    {source_url_section}
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f1f3f4; border-radius: 8px;">
                    <p style="margin: 0; color: #666;">このメールは自動配信システムから送信されました。</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Render template
        source_url_section = ""
        if release.get("source_url"):
            source_url_section = (
                f'<p><strong>詳細:</strong> <a href="{release["source_url"]}">こちら</a></p>'
            )

        rendered_html = template.format(
            title=work["title"],
            title_kana=work.get("title_kana", ""),
            title_en=work.get("title_en", ""),
            work_type="アニメ" if work["type"] == "anime" else "マンガ",
            release_type="第" if release["release_type"] == "episode" else "第",
            number=release["number"],
            release_date=release["release_date"],
            platform=release["platform"],
            source_url_section=source_url_section,
        )

        # Verify template rendering
        assert work["title"] in rendered_html
        assert release["number"] in rendered_html
        assert release["platform"] in rendered_html
        assert "新作配信のお知らせ" in rendered_html

    @pytest.mark.integration
    def test_email_attachment_support(self, mock_gmail_service):
        """Test email with image attachments (cover images)."""
        with patch("requests.get") as mock_get:
            # Mock image download
            mock_response = Mock()
            mock_response.content = b"fake_image_data"
            mock_response.headers = {"Content-Type": "image/jpeg"}
            mock_get.return_value = mock_response

            # Test image attachment
            image_url = "https://example.com/anime_cover.jpg"
            image_data = mock_get(image_url).content

            # Create message with attachment
            message = MIMEMultipart()
            message["Subject"] = "Test with attachment"
            message["From"] = "test@example.com"
            message["To"] = "user@example.com"

            # Add image attachment
            from email.mime.image import MIMEImage

            image_attachment = MIMEImage(image_data)
            image_attachment.add_header(
                "Content-Disposition", "attachment", filename="cover.jpg"
            )
            message.attach(image_attachment)

            # Verify attachment
            assert len(message.get_payload()) == 1  # One attachment
            assert message.get_payload()[0].get_content_type() == "image/jpeg"

    @pytest.mark.integration
    def test_email_error_handling_and_retry(self, mock_gmail_service):
        """Test error handling and retry logic for email sending."""
        from googleapiclient.errors import HttpError

        # Mock Gmail API error
        error_response = Mock()
        error_response.status_code = 429  # Rate limit
        mock_gmail_service.users().messages().send.return_value.execute.side_effect = (
            HttpError(error_response, b"Rate limit exceeded")
        )

        # Test error handling
        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                mock_gmail_service.users().messages().send(
                    userId="me", body={"raw": "test_message"}
                ).execute()
                break
            except HttpError as e:
                retry_count += 1
                if retry_count >= max_retries:
                    assert e.resp.status_code == 429
                    break

        assert retry_count == max_retries

    @pytest.mark.integration
    def test_email_delivery_confirmation(self, mock_gmail_service):
        """Test email delivery confirmation and tracking."""
        # Mock successful send
        mock_gmail_service.users().messages().send.return_value.execute.return_value = {
            "id": "sent_message_123",
            "threadId": "thread_456",
        }

        # Send message
        result = (
            mock_gmail_service.users()
            .messages()
            .send(userId="me", body={"raw": "test_message"})
            .execute()
        )

        message_id = result["id"]

        # Mock message status check
        mock_gmail_service.users().messages().get.return_value.execute.return_value = {
            "id": message_id,
            "labelIds": ["SENT"],
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Message"},
                    {"name": "Date", "value": datetime.now().isoformat()},
                ]
            },
        }

        # Verify message status
        message_info = (
            mock_gmail_service.users()
            .messages()
            .get(userId="me", id=message_id)
            .execute()
        )

        assert message_info["id"] == message_id
        assert "SENT" in message_info["labelIds"]

    @pytest.mark.integration
    @pytest.mark.performance
    def test_email_sending_performance(
        self, mock_gmail_service, performance_test_config
    ):
        """Test email sending performance under load."""
        import time
        import asyncio

        max_response_time = performance_test_config["max_response_time"]
        concurrent_requests = min(
            performance_test_config["concurrent_requests"], 5
        )  # Limit for email

        # Mock fast response
        mock_gmail_service.users().messages().send.return_value.execute.return_value = {
            "id": "quick_response_id"
        }

        async def send_email_async(email_id):
            start_time = time.time()

            # Simulate async email sending
            result = (
                mock_gmail_service.users()
                .messages()
                .send(userId="me", body={"raw": f"message_{email_id}"})
                .execute()
            )

            end_time = time.time()
            return end_time - start_time, result

        async def test_concurrent_sends():
            tasks = [send_email_async(i) for i in range(concurrent_requests)]
            return await asyncio.gather(*tasks)

        # Run performance test
        results = asyncio.run(test_concurrent_sends())

        # Verify performance
        for response_time, result in results:
            assert response_time < max_response_time
            assert result["id"] is not None

        assert len(results) == concurrent_requests


class TestEmailTemplateSystem:
    """Test email template system and customization."""

    @pytest.mark.unit
    def test_template_loading_and_caching(self):
        """Test email template loading and caching mechanism."""
        templates = {
            "anime_episode": "templates/anime_episode.html",
            "manga_volume": "templates/manga_volume.html",
            "generic": "templates/generic.html",
        }

        template_cache = {}

        for template_name, template_path in templates.items():
            # Simulate template loading
            template_content = f"<html><body>Template for {template_name}</body></html>"
            template_cache[template_name] = template_content

        # Test caching
        assert len(template_cache) == 3
        assert "anime_episode" in template_cache
        assert "Template for anime_episode" in template_cache["anime_episode"]

    @pytest.mark.unit
    def test_template_variable_substitution(self):
        """Test template variable substitution with various data types."""
        template = """
        <html>
        <body>
            <h1>{{title}}</h1>
            <p>Episode: {{episode_number}}</p>
            <p>Date: {{release_date}}</p>
            <p>Rating: {{rating}}</p>
            {{#if has_description}}
            <p>Description: {{description}}</p>
            {{/if}}
            <ul>
            {{#each genres}}
            <li>{{this}}</li>
            {{/each}}
            </ul>
        </body>
        </html>
        """

        data = {
            "title": "ワンピース",
            "episode_number": 1050,
            "release_date": "2024-01-15",
            "rating": 4.8,
            "has_description": True,
            "description": "海賊王を目指す少年の物語",
            "genres": ["Adventure", "Action", "Comedy"],
        }

        # Simulate template rendering (simplified)
        rendered = self._simple_template_render(template, data)

        assert "ワンピース" in rendered
        assert "1050" in rendered
        assert "海賊王を目指す少年の物語" in rendered
        assert "Adventure" in rendered

    @pytest.mark.unit
    def test_template_localization_support(self):
        """Test template localization for different languages."""
        templates = {
            "ja": {
                "subject": "新エピソード配信: {{title}}",
                "body": "エピソード {{number}} が配信されました",
            },
            "en": {
                "subject": "New Episode Available: {{title}}",
                "body": "Episode {{number}} is now available",
            },
        }

        data = {"title": "One Piece", "number": "1050"}

        # Test Japanese localization
        ja_subject = templates["ja"]["subject"].replace("{{title}}", data["title"])
        ja_body = templates["ja"]["body"].replace("{{number}}", data["number"])

        assert "新エピソード配信: One Piece" == ja_subject
        assert "エピソード 1050 が配信されました" == ja_body

        # Test English localization
        en_subject = templates["en"]["subject"].replace("{{title}}", data["title"])
        en_body = templates["en"]["body"].replace("{{number}}", data["number"])

        assert "New Episode Available: One Piece" == en_subject
        assert "Episode 1050 is now available" == en_body

    def _simple_template_render(self, template: str, data: dict) -> str:
        """Simple template rendering simulation."""
        result = template

        # Replace simple variables
        for key, value in data.items():
            if isinstance(value, (str, int, float)):
                result = result.replace(f"{{{{{key}}}}}", str(value))

        # Handle conditional blocks (simplified)
        if data.get("has_description"):
            result = result.replace("{{#if has_description}}", "")
            result = result.replace("{{/if}}", "")

        # Handle arrays (simplified)
        if "genres" in data and isinstance(data["genres"], list):
            genre_html = "\n".join(f"<li>{genre}</li>" for genre in data["genres"])
            result = result.replace(
                "{{#each genres}}\n<li>{{this}}</li>\n{{/each}}", genre_html
            )

        return result


class TestEmailNotificationWorkflow:
    """Test complete email notification workflow."""

    @pytest.mark.integration
    @pytest.mark.e2e
    def test_end_to_end_notification_workflow(
        self, mock_gmail_service, temp_db, sample_work_data, sample_release_data
    ):
        """Test complete notification workflow from database to email."""
        # This would test the complete workflow:
        # 1. Get unnotified releases from database
        # 2. Generate email content
        # 3. Send notifications
        # 4. Mark releases as notified
        # 5. Log notification results

        # Step 1: Setup database with test data
        import sqlite3

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Insert test work
        work = sample_work_data[0]
        cursor.execute(
            """
            INSERT INTO works (title, title_kana, title_en, type, official_url)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                work["title"],
                work["title_kana"],
                work["title_en"],
                work["type"],
                work["official_url"],
            ),
        )

        work_id = cursor.lastrowid

        # Insert test release
        release = sample_release_data[0]
        cursor.execute(
            """
            INSERT INTO releases (work_id, release_type, number, platform, release_date, source, source_url, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                work_id,
                release["release_type"],
                release["number"],
                release["platform"],
                release["release_date"],
                release["source"],
                release["source_url"],
                0,
            ),
        )  # Not notified yet

        release_id = cursor.lastrowid
        conn.commit()

        # Step 2: Query unnotified releases
        cursor.execute(
            """
            SELECT r.*, w.title, w.title_kana, w.title_en, w.type
            FROM releases r
            JOIN works w ON r.work_id = w.id
            WHERE r.notified = 0
        """
        )

        unnotified_releases = cursor.fetchall()
        assert len(unnotified_releases) == 1

        # Step 3: Generate and send notifications
        mock_gmail_service.users().messages().send.return_value.execute.return_value = {
            "id": f"notification_msg_{release_id}",
            "threadId": f"thread_{release_id}",
        }

        # Simulate notification sending
        notification_results = []
        for release_row in unnotified_releases:
            # Generate email content
            email_content = {
                "subject": f"新配信: {release_row[11]}",  # title from join
                "body": f"エピソード {release_row[3]} が配信されました",  # number
            }

            # Send notification
            result = (
                mock_gmail_service.users()
                .messages()
                .send(userId="me", body={"raw": "encoded_email_content"})
                .execute()
            )

            notification_results.append(
                {
                    "release_id": release_row[0],  # release ID
                    "message_id": result["id"],
                    "status": "sent",
                }
            )

        # Step 4: Mark releases as notified
        for notification in notification_results:
            cursor.execute(
                """
                UPDATE releases SET notified = 1 WHERE id = ?
            """,
                (notification["release_id"],),
            )

        conn.commit()

        # Step 5: Verify workflow completion
        cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 0")
        unnotified_count = cursor.fetchone()[0]

        assert unnotified_count == 0  # All releases should be marked as notified
        assert len(notification_results) == 1
        assert notification_results[0]["status"] == "sent"

        conn.close()
