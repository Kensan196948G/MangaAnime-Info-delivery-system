"""
Gmail API integration for sending anime/manga notifications.

This module provides functionality to send HTML emails with release notifications
using the Gmail API with OAuth2 authentication.
"""

import os
import json
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    logger.warning("Google API libraries not available. Install google-auth, google-auth-oauthlib, google-api-python-client")
    GOOGLE_AVAILABLE = False


@dataclass
class EmailNotification:
    """Data class for email notification content."""
    subject: str
    html_content: str
    text_content: str
    attachments: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []


class GmailNotifier:
    """Gmail API client for sending notifications."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Gmail notifier.
        
        Args:
            config: Configuration dictionary with Gmail settings
        """
        self.config = config
        self.gmail_config = config.get('google', {}).get('gmail', {})
        self.credentials_file = config.get('google', {}).get('credentials_file', 'credentials.json')
        self.token_file = config.get('google', {}).get('token_file', 'token.json')
        self.scopes = config.get('google', {}).get('scopes', [
            'https://www.googleapis.com/auth/gmail.send'
        ])
        
        self.service = None
        self._authenticated = False
        
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth2.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        if not GOOGLE_AVAILABLE:
            logger.error("Google API libraries not available")
            return False
            
        try:
            creds = None
            
            # Load existing token
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
            
            # If no valid credentials, authorize user
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired Gmail credentials")
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Credentials file not found: {self.credentials_file}")
                        return False
                    
                    logger.info("Initiating Gmail OAuth2 flow")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                logger.info("Gmail credentials saved successfully")
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            self._authenticated = True
            logger.info("Gmail API authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {str(e)}")
            return False
    
    def create_message(self, to: str, subject: str, html_content: str, 
                      text_content: str = None, attachments: List[Dict] = None) -> Dict[str, Any]:
        """
        Create email message.
        
        Args:
            to: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text content (optional)
            attachments: List of attachments (optional)
            
        Returns:
            dict: Gmail message object
        """
        try:
            # Create multipart message
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['from'] = self.gmail_config.get('from_email', to)
            message['subject'] = subject
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                message.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            message.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    self._add_attachment(message, attachment)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            return {'raw': raw_message}
            
        except Exception as e:
            logger.error(f"Failed to create email message: {str(e)}")
            raise
    
    def _add_attachment(self, message: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message."""
        try:
            attachment_type = attachment.get('type', 'image')
            filename = attachment.get('filename', 'attachment')
            data = attachment.get('data')
            
            if attachment_type == 'image':
                img = MIMEImage(data)
                img.add_header('Content-Disposition', f'attachment; filename={filename}')
                message.attach(img)
            
        except Exception as e:
            logger.warning(f"Failed to add attachment {filename}: {str(e)}")
    
    def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send email message.
        
        Args:
            message: Gmail message object
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self._authenticated:
            logger.error("Gmail not authenticated. Call authenticate() first.")
            return False
        
        try:
            result = self.service.users().messages().send(
                userId='me', body=message).execute()
            
            message_id = result.get('id')
            logger.info(f"Email sent successfully. Message ID: {message_id}")
            return True
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_notification(self, notification: EmailNotification, 
                         recipient: str = None) -> bool:
        """
        Send email notification.
        
        Args:
            notification: EmailNotification object
            recipient: Recipient email (uses config default if None)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if not recipient:
                recipient = self.gmail_config.get('to_email')
                if not recipient:
                    logger.error("No recipient email specified")
                    return False
            
            # Create message
            message = self.create_message(
                to=recipient,
                subject=notification.subject,
                html_content=notification.html_content,
                text_content=notification.text_content,
                attachments=notification.attachments
            )
            
            # Send message
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False


class EmailTemplateGenerator:
    """Generate HTML email templates for anime/manga notifications."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize email template generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.gmail_config = config.get('google', {}).get('gmail', {})
        self.notification_config = config.get('notification', {}).get('email', {})
    
    def generate_release_notification(self, releases: List[Dict[str, Any]], 
                                    date_str: str = None) -> EmailNotification:
        """
        Generate email notification for new releases.
        
        Args:
            releases: List of release dictionaries
            date_str: Date string for the notification
            
        Returns:
            EmailNotification: Generated email notification
        """
        try:
            if not date_str:
                date_str = datetime.now().strftime('%Y年%m月%d日')
            
            # Generate subject
            subject_prefix = self.gmail_config.get('subject_prefix', '[アニメ・マンガ情報]')
            anime_count = len([r for r in releases if r.get('type') == 'anime'])
            manga_count = len([r for r in releases if r.get('type') == 'manga'])
            
            subject = f"{subject_prefix} {date_str} - "
            if anime_count > 0 and manga_count > 0:
                subject += f"アニメ{anime_count}件・マンガ{manga_count}件の新着情報"
            elif anime_count > 0:
                subject += f"アニメ{anime_count}件の新着情報"
            elif manga_count > 0:
                subject += f"マンガ{manga_count}件の新着情報"
            else:
                subject += "新着情報"
            
            # Generate HTML content
            html_content = self._generate_html_template(releases, date_str)
            
            # Generate text content
            text_content = self._generate_text_template(releases, date_str)
            
            return EmailNotification(
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Failed to generate release notification: {str(e)}")
            raise
    
    def _generate_html_template(self, releases: List[Dict[str, Any]], 
                               date_str: str) -> str:
        """Generate HTML email template."""
        
        # Group releases by type
        anime_releases = [r for r in releases if r.get('type') == 'anime']
        manga_releases = [r for r in releases if r.get('type') == 'manga']
        
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>アニメ・マンガ情報 - {date_str}</title>
    <style>
        body {{
            font-family: 'Hiragino Kaku Gothic ProN', 'ヒラギノ角ゴ ProN W3', Meiryo, メイリオ, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #007bff;
        }}
        .header h1 {{
            color: #007bff;
            margin: 0;
            font-size: 2.2em;
        }}
        .date {{
            color: #666;
            font-size: 1.1em;
            margin-top: 10px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #495057;
            border-left: 5px solid #007bff;
            padding-left: 15px;
            margin-bottom: 20px;
            font-size: 1.5em;
        }}
        .release-item {{
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #007bff;
        }}
        .release-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #212529;
            margin-bottom: 8px;
        }}
        .release-details {{
            color: #666;
            font-size: 0.95em;
        }}
        .release-details .badge {{
            background-color: #007bff;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-right: 8px;
        }}
        .release-link {{
            color: #007bff;
            text-decoration: none;
            font-weight: bold;
        }}
        .release-link:hover {{
            text-decoration: underline;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
            font-size: 0.9em;
        }}
        .anime-section .release-item {{
            border-left-color: #28a745;
        }}
        .anime-section h2 {{
            border-left-color: #28a745;
        }}
        .anime-section .badge {{
            background-color: #28a745;
        }}
        .manga-section .release-item {{
            border-left-color: #ffc107;
        }}
        .manga-section h2 {{
            border-left-color: #ffc107;
        }}
        .manga-section .badge {{
            background-color: #ffc107;
            color: #000;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 アニメ・マンガ最新情報</h1>
            <div class="date">{date_str}</div>
        </div>
        
        {self._generate_anime_section(anime_releases) if anime_releases else ""}
        {self._generate_manga_section(manga_releases) if manga_releases else ""}
        
        <div class="footer">
            <p>📧 このメールは自動配信されています</p>
            <p>🤖 Generated with MangaAnime Information System</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_anime_section(self, anime_releases: List[Dict[str, Any]]) -> str:
        """Generate HTML section for anime releases."""
        html = '<div class="section anime-section">\n'
        html += '<h2>📺 アニメ情報</h2>\n'
        
        for release in anime_releases:
            title = release.get('title', '不明なタイトル')
            episode = release.get('number', '')
            platform = release.get('platform', '')
            release_date = release.get('release_date', '')
            source_url = release.get('source_url', '')
            
            html += '<div class="release-item">\n'
            html += f'<div class="release-title">{title}</div>\n'
            html += '<div class="release-details">\n'
            if episode:
                html += f'<span class="badge">第{episode}話</span>'
            if platform:
                html += f'<span class="badge">{platform}</span>'
            if release_date:
                html += f'配信日: {release_date}'
            if source_url:
                html += f' <a href="{source_url}" class="release-link" target="_blank">詳細を見る</a>'
            html += '</div>\n'
            html += '</div>\n'
        
        html += '</div>\n'
        return html
    
    def _generate_manga_section(self, manga_releases: List[Dict[str, Any]]) -> str:
        """Generate HTML section for manga releases."""
        html = '<div class="section manga-section">\n'
        html += '<h2>📚 マンガ情報</h2>\n'
        
        for release in manga_releases:
            title = release.get('title', '不明なタイトル')
            volume = release.get('number', '')
            platform = release.get('platform', '')
            release_date = release.get('release_date', '')
            source_url = release.get('source_url', '')
            
            html += '<div class="release-item">\n'
            html += f'<div class="release-title">{title}</div>\n'
            html += '<div class="release-details">\n'
            if volume:
                html += f'<span class="badge">第{volume}巻</span>'
            if platform:
                html += f'<span class="badge">{platform}</span>'
            if release_date:
                html += f'発売日: {release_date}'
            if source_url:
                html += f' <a href="{source_url}" class="release-link" target="_blank">購入する</a>'
            html += '</div>\n'
            html += '</div>\n'
        
        html += '</div>\n'
        return html
    
    def _generate_text_template(self, releases: List[Dict[str, Any]], 
                               date_str: str) -> str:
        """Generate plain text email template."""
        text = f"アニメ・マンガ最新情報 - {date_str}\n"
        text += "=" * 40 + "\n\n"
        
        # Anime section
        anime_releases = [r for r in releases if r.get('type') == 'anime']
        if anime_releases:
            text += "📺 アニメ情報\n"
            text += "-" * 20 + "\n"
            for release in anime_releases:
                title = release.get('title', '不明なタイトル')
                episode = release.get('number', '')
                platform = release.get('platform', '')
                release_date = release.get('release_date', '')
                
                text += f"• {title}"
                if episode:
                    text += f" 第{episode}話"
                if platform:
                    text += f" ({platform})"
                if release_date:
                    text += f" - 配信日: {release_date}"
                text += "\n"
            text += "\n"
        
        # Manga section
        manga_releases = [r for r in releases if r.get('type') == 'manga']
        if manga_releases:
            text += "📚 マンガ情報\n"
            text += "-" * 20 + "\n"
            for release in manga_releases:
                title = release.get('title', '不明なタイトル')
                volume = release.get('number', '')
                platform = release.get('platform', '')
                release_date = release.get('release_date', '')
                
                text += f"• {title}"
                if volume:
                    text += f" 第{volume}巻"
                if platform:
                    text += f" ({platform})"
                if release_date:
                    text += f" - 発売日: {release_date}"
                text += "\n"
            text += "\n"
        
        text += "=" * 40 + "\n"
        text += "このメールは自動配信されています\n"
        text += "Generated with MangaAnime Information System\n"
        
        return text