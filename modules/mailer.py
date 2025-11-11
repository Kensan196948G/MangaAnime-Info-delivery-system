"""
Gmail API integration for sending anime/manga notifications.

This module provides functionality to send HTML emails with release notifications
using the Gmail API with OAuth2 authentication.
"""

import os
import base64
import logging
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import threading
from functools import wraps

logger = logging.getLogger(__name__)

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    GOOGLE_AVAILABLE = True
except ImportError:
    logger.warning(
        "Google API libraries not available. Install google-auth, google-auth-oauthlib, google-api-python-client"
    )
    GOOGLE_AVAILABLE = False


def retry_on_failure(
    max_retries: int = 3, delay: float = 1.0, exponential_backoff: bool = True
):
    """
    Gmail API エラー時のリトライデコレータ

    Args:
        max_retries: 最大リトライ回数
        delay: 初期遅延時間（秒）
        exponential_backoff: 指数バックオフを使用するか
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # 最後の試行の場合は例外を再発生
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise

                    # Gmail API 固有エラーの判定
                    if hasattr(e, "resp") and hasattr(e.resp, "status"):
                        status_code = e.resp.status
                        # 4xx エラーはリトライしない（認証エラーなど）
                        if (
                            400 <= status_code < 500 and status_code != 429
                        ):  # 429 (Rate limit) はリトライ
                            logger.error(
                                f"Non-retryable error {status_code} in {func.__name__}: {e}"
                            )
                            raise

                    logger.warning(
                        f"Attempt {attempt + 1} of {func.__name__} failed: {e}"
                    )
                    logger.info(f"Retrying in {current_delay:.1f} seconds...")

                    time.sleep(current_delay)

                    if exponential_backoff:
                        current_delay *= 2

            # Should never reach here, but just in case
            raise last_exception

        return wrapper

    return decorator


@dataclass
class EmailNotification:
    """Data class for email notification content."""

    subject: str
    html_content: str
    text_content: str
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    priority: str = "normal"  # 'low', 'normal', 'high'
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []


@dataclass
class AuthenticationState:
    """Gmail認証状態の管理"""

    is_authenticated: bool = False
    last_auth_time: Optional[datetime] = None
    token_expires_at: Optional[datetime] = None
    auth_lock: threading.Lock = field(default_factory=threading.Lock)
    consecutive_auth_failures: int = 0
    last_auth_error: Optional[str] = None
    refresh_in_progress: bool = False
    token_refresh_count: int = 0
    last_refresh_time: Optional[datetime] = None


class GmailNotifier:
    """Gmail API client for sending notifications."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Gmail notifier with enhanced error handling and monitoring.

        Args:
            config: Configuration dictionary with Gmail settings
        """
        self.config = config
        self.gmail_config = config.get("google", {}).get("gmail", {})
        self.credentials_file = config.get("google", {}).get(
            "credentials_file", "credentials.json"
        )
        self.token_file = config.get("google", {}).get("token_file", "token.json")
        self.scopes = config.get("google", {}).get(
            "scopes", ["https://www.googleapis.com/auth/gmail.send"]
        )

        self.service = None
        self.auth_state = AuthenticationState()

        # Performance monitoring
        self.total_emails_sent = 0
        self.total_send_failures = 0
        self.total_auth_attempts = 0
        self.start_time = datetime.now()

        # Rate limiting for Gmail API
        self.rate_limit_requests = []
        self.rate_limit_window = 60  # seconds
        self.max_requests_per_minute = 250  # Gmail API limit

    def _is_token_near_expiry(self, minutes_ahead: int = 10) -> bool:
        """Check if token will expire soon."""
        if not self.auth_state.token_expires_at:
            return True

        expiry_threshold = datetime.now() + timedelta(minutes=minutes_ahead)
        return self.auth_state.token_expires_at <= expiry_threshold

    def _refresh_token_proactively(self) -> bool:
        """Proactively refresh token if it's near expiry."""
        if self.auth_state.refresh_in_progress:
            logger.debug("Token refresh already in progress")
            return True

        if not self._is_token_near_expiry():
            return True

        logger.info("Token is near expiry, attempting proactive refresh")
        return self._refresh_token()

    def _refresh_token(self) -> bool:
        """Refresh OAuth2 token."""
        with self.auth_state.auth_lock:
            if self.auth_state.refresh_in_progress:
                return True

            self.auth_state.refresh_in_progress = True

            try:
                if not os.path.exists(self.token_file):
                    logger.warning("Token file not found for refresh")
                    return False

                creds = Credentials.from_authorized_user_file(
                    self.token_file, self.scopes
                )

                if not creds.refresh_token:
                    logger.warning("No refresh token available")
                    return False

                # Attempt refresh
                creds.refresh(Request())

                # Save refreshed token
                with open(self.token_file, "w") as token:
                    token.write(creds.to_json())

                # Update service with new credentials
                self.service = build(
                    "gmail", "v1", credentials=creds, cache_discovery=False
                )

                # Update auth state
                self.auth_state.token_expires_at = creds.expiry or (
                    datetime.now() + timedelta(hours=1)
                )
                self.auth_state.last_refresh_time = datetime.now()
                self.auth_state.token_refresh_count += 1

                logger.info(
                    f"Token refreshed successfully (refresh count: {self.auth_state.token_refresh_count})"
                )
                return True

            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                return False
            finally:
                self.auth_state.refresh_in_progress = False

    @retry_on_failure(max_retries=3, delay=2.0)
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth2 with enhanced error handling and proactive token refresh.

        Returns:
            bool: True if authentication successful, False otherwise
        """
        with self.auth_state.auth_lock:
            self.total_auth_attempts += 1

            if not GOOGLE_AVAILABLE:
                error_msg = "Google API libraries not available"
                logger.error(error_msg)
                self.auth_state.last_auth_error = error_msg
                return False

            try:
                # Check if already authenticated and valid (with proactive refresh)
                if (
                    self.auth_state.is_authenticated
                    and self.auth_state.token_expires_at
                ):
                    if self._is_token_near_expiry():
                        logger.info("Token near expiry, attempting refresh")
                        if self._refresh_token():
                            return True
                        # If refresh failed, continue with full re-authentication
                    else:
                        logger.debug("Using existing valid authentication")
                        return True

                creds = None

                # Load existing token with validation
                if os.path.exists(self.token_file):
                    try:
                        creds = Credentials.from_authorized_user_file(
                            self.token_file, self.scopes
                        )
                        logger.debug("Loaded existing credentials from token file")
                    except Exception as e:
                        logger.warning(f"Failed to load existing token: {e}")
                        # Remove invalid token file
                        try:
                            os.remove(self.token_file)
                            logger.info("Removed invalid token file")
                        except OSError:
                            pass

                # If no valid credentials, handle refresh or re-authorization
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        logger.info("Refreshing expired Gmail credentials")
                        try:
                            creds.refresh(Request())
                            self.auth_state.token_refresh_count += 1
                            self.auth_state.last_refresh_time = datetime.now()
                            logger.info(
                                f"Successfully refreshed credentials (count: {self.auth_state.token_refresh_count})"
                            )
                        except Exception as refresh_error:
                            logger.warning(f"Token refresh failed: {refresh_error}")
                            # Try full re-authentication
                            creds = None

                    if not creds or not creds.valid:
                        if not os.path.exists(self.credentials_file):
                            error_msg = (
                                f"Credentials file not found: {self.credentials_file}"
                            )
                            logger.error(error_msg)
                            self.auth_state.last_auth_error = error_msg
                            self.auth_state.consecutive_auth_failures += 1
                            return False

                        logger.info("Initiating Gmail OAuth2 flow")
                        try:
                            flow = InstalledAppFlow.from_client_secrets_file(
                                self.credentials_file, self.scopes
                            )
                            creds = flow.run_local_server(
                                port=0,
                                timeout_seconds=300,  # 5分タイムアウト
                                access_type="offline",
                                prompt="consent",
                            )
                            logger.info("OAuth2 flow completed successfully")
                        except Exception as oauth_error:
                            error_msg = f"OAuth2 flow failed: {oauth_error}"
                            logger.error(error_msg)
                            self.auth_state.last_auth_error = error_msg
                            self.auth_state.consecutive_auth_failures += 1
                            raise

                    # Save credentials for next run with secure permissions
                    try:
                        # Set secure file permissions (owner read/write only)
                        old_umask = os.umask(0o077)
                        try:
                            with open(self.token_file, "w") as token:
                                token.write(creds.to_json())
                        finally:
                            os.umask(old_umask)
                        logger.info("Gmail credentials saved securely")
                    except Exception as save_error:
                        logger.warning(f"Failed to save credentials: {save_error}")
                        # Continue anyway if we have valid creds in memory

                # Build Gmail service with timeout
                try:
                    self.service = build(
                        "gmail", "v1", credentials=creds, cache_discovery=False
                    )
                    logger.info("Gmail service built successfully")
                except Exception as service_error:
                    error_msg = f"Failed to build Gmail service: {service_error}"
                    logger.error(error_msg)
                    self.auth_state.last_auth_error = error_msg
                    raise

                # Test the service
                try:
                    profile = self.service.users().getProfile(userId="me").execute()
                    email_address = profile.get("emailAddress", "unknown")
                    logger.info(
                        f"Gmail API authentication successful for: {email_address}"
                    )
                except Exception as test_error:
                    error_msg = f"Gmail service test failed: {test_error}"
                    logger.error(error_msg)
                    self.auth_state.last_auth_error = error_msg
                    raise

                # Update authentication state
                self.auth_state.is_authenticated = True
                self.auth_state.last_auth_time = datetime.now()
                self.auth_state.consecutive_auth_failures = 0
                self.auth_state.last_auth_error = None

                # Calculate token expiration with buffer for proactive refresh
                if creds.expiry:
                    self.auth_state.token_expires_at = creds.expiry
                else:
                    # Default to 1 hour if no expiry info
                    self.auth_state.token_expires_at = datetime.now() + timedelta(
                        hours=1
                    )

                return True

            except Exception as e:
                error_msg = f"Gmail authentication failed: {str(e)}"
                logger.error(error_msg)
                self.auth_state.last_auth_error = error_msg
                self.auth_state.consecutive_auth_failures += 1
                self.auth_state.is_authenticated = False

                # Reset service on failure
                self.service = None

                raise

    def _enforce_rate_limit(self):
        """Gmail API レート制限を強制"""
        now = time.time()

        # 古いリクエストタイムスタンプを削除
        self.rate_limit_requests = [
            req_time
            for req_time in self.rate_limit_requests
            if now - req_time < self.rate_limit_window
        ]

        # レート制限チェック
        if len(self.rate_limit_requests) >= self.max_requests_per_minute:
            sleep_time = (
                self.rate_limit_window - (now - self.rate_limit_requests[0]) + 1
            )
            logger.info(
                f"Gmail API rate limit reached, sleeping for {sleep_time:.1f} seconds"
            )
            time.sleep(sleep_time)

            # タイムスタンプを再度クリーンアップ
            now = time.time()
            self.rate_limit_requests = [
                req_time
                for req_time in self.rate_limit_requests
                if now - req_time < self.rate_limit_window
            ]

        # このリクエストを記録
        self.rate_limit_requests.append(now)

    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計情報を取得"""
        uptime = datetime.now() - self.start_time

        return {
            "total_emails_sent": self.total_emails_sent,
            "total_send_failures": self.total_send_failures,
            "total_auth_attempts": self.total_auth_attempts,
            "success_rate": (
                self.total_emails_sent
                / (self.total_emails_sent + self.total_send_failures)
                if (self.total_emails_sent + self.total_send_failures) > 0
                else 1.0
            ),
            "uptime_seconds": uptime.total_seconds(),
            "is_authenticated": self.auth_state.is_authenticated,
            "consecutive_auth_failures": self.auth_state.consecutive_auth_failures,
            "last_auth_error": self.auth_state.last_auth_error,
            "rate_limit_requests_count": len(self.rate_limit_requests),
            "rate_limit_utilization": len(self.rate_limit_requests)
            / self.max_requests_per_minute,
        }

    def create_message(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: str = None,
        attachments: List[Dict] = None,
    ) -> Dict[str, Any]:
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
            message = MIMEMultipart("alternative")
            message["to"] = to
            message["from"] = self.gmail_config.get("from_email", to)
            message["subject"] = subject

            # Add text content
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    self._add_attachment(message, attachment)

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            return {"raw": raw_message}

        except Exception as e:
            logger.error(f"Failed to create email message: {str(e)}")
            raise

    def _add_attachment(self, message: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message."""
        try:
            attachment_type = attachment.get("type", "image")
            filename = attachment.get("filename", "attachment")
            data = attachment.get("data")

            if attachment_type == "image":
                img = MIMEImage(data)
                img.add_header(
                    "Content-Disposition", f"attachment; filename={filename}"
                )
                message.attach(img)

        except Exception as e:
            logger.warning(f"Failed to add attachment {filename}: {str(e)}")

    @retry_on_failure(max_retries=3, delay=1.0)
    def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send email message with enhanced error handling, rate limiting, and proactive token refresh.

        Args:
            message: Gmail message object

        Returns:
            bool: True if sent successfully, False otherwise
        """
        # Check authentication status and proactively refresh if needed
        if not self.auth_state.is_authenticated:
            logger.info("Not authenticated, attempting authentication...")
            if not self.authenticate():
                logger.error("Authentication failed, cannot send email")
                self.total_send_failures += 1
                return False
        elif self._is_token_near_expiry():
            logger.info(
                "Token near expiry, attempting proactive refresh before sending"
            )
            if not self._refresh_token_proactively():
                logger.warning(
                    "Proactive token refresh failed, will try to send anyway"
                )

        # Double-check authentication after potential refresh
        if not self.auth_state.is_authenticated:
            logger.error("Authentication lost, cannot send email")
            self.total_send_failures += 1
            return False

        # Enforce rate limiting
        self._enforce_rate_limit()

        try:
            start_time = time.time()

            # Validate message structure
            if not message or "raw" not in message:
                raise ValueError("Invalid message format: missing 'raw' field")

            # Send message
            result = (
                self.service.users()
                .messages()
                .send(userId="me", body=message)
                .execute()
            )

            send_time = time.time() - start_time
            message_id = result.get("id")

            # Success metrics
            self.total_emails_sent += 1

            logger.info(
                f"Email sent successfully in {send_time:.2f}s. Message ID: {message_id}"
            )

            # Log slow sends
            if send_time > 5.0:
                logger.warning(f"Slow email send: {send_time:.2f}s")

            return True

        except HttpError as error:
            self.total_send_failures += 1

            # Handle specific Gmail API errors
            status_code = error.resp.status if hasattr(error, "resp") else "unknown"
            error_details = (
                error.error_details if hasattr(error, "error_details") else []
            )

            if status_code == 401:  # Unauthorized
                logger.warning(
                    "Gmail API unauthorized error, attempting re-authentication"
                )
                self.auth_state.is_authenticated = False
                self.service = None
                # Re-authenticate will be attempted on retry
                raise  # Trigger retry
            elif status_code == 403:  # Forbidden
                if any("rate" in str(detail).lower() for detail in error_details):
                    logger.warning(
                        "Gmail API rate limit error, will retry with backo"
                    )
                    time.sleep(2)  # Additional delay
                    raise  # Trigger retry
                else:
                    logger.error(f"Gmail API forbidden error (non-retryable): {error}")
                    return False
            elif status_code == 429:  # Too Many Requests
                logger.warning("Gmail API rate limit exceeded, backing o")
                time.sleep(5)  # Longer delay for rate limit
                raise  # Trigger retry
            elif 500 <= status_code < 600:  # Server errors
                logger.warning(f"Gmail API server error {status_code}, retrying")
                raise  # Trigger retry
            else:
                logger.error(f"Gmail API error {status_code}: {error}")
                return False

        except Exception as e:
            self.total_send_failures += 1

            # Check for network-related errors that should trigger retry
            error_str = str(e).lower()
            if any(
                keyword in error_str for keyword in ["timeout", "connection", "network"]
            ):
                logger.warning(f"Network-related error, retrying: {e}")
                raise  # Trigger retry
            else:
                logger.error(f"Failed to send email (non-retryable): {e}")
                return False

    def send_notification(
        self, notification: EmailNotification, recipient: str = None
    ) -> bool:
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
                recipient = self.gmail_config.get("to_email")
                if not recipient:
                    logger.error("No recipient email specified")
                    return False

            # Create message
            message = self.create_message(
                to=recipient,
                subject=notification.subject,
                html_content=notification.html_content,
                text_content=notification.text_content,
                attachments=notification.attachments,
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
        self.gmail_config = config.get("google", {}).get("gmail", {})
        self.notification_config = config.get("notification", {}).get("email", {})

    def generate_release_notification(
        self,
        releases: List[Dict[str, Any]],
        date_str: str = None,
        subject_prefix: str = None,
    ) -> EmailNotification:
        """
        Generate email notification for new releases.

        Args:
            releases: List of release dictionaries
            date_str: Date string for the notification
            subject_prefix: Custom subject prefix for batched delivery

        Returns:
            EmailNotification: Generated email notification
        """
        try:
            if not date_str:
                date_str = datetime.now().strftime("%Y年%m月%d日")

            # Generate subject
            if subject_prefix is None:
                subject_prefix = self.gmail_config.get(
                    "subject_prefix", "[アニメ・マンガ情報]"
                )
            anime_count = len([r for r in releases if r.get("type") == "anime"])
            manga_count = len([r for r in releases if r.get("type") == "manga"])

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
                subject=subject, html_content=html_content, text_content=text_content
            )

        except Exception as e:
            logger.error(f"Failed to generate release notification: {str(e)}")
            raise

    def _generate_html_template(
        self, releases: List[Dict[str, Any]], date_str: str
    ) -> str:
        """Generate HTML email template."""

        # Group releases by type
        anime_releases = [r for r in releases if r.get("type") == "anime"]
        manga_releases = [r for r in releases if r.get("type") == "manga"]

        html = """
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
        html += "<h2>📺 アニメ情報</h2>\n"

        for release in anime_releases:
            title = release.get("title", "不明なタイトル")
            episode = release.get("number", "")
            platform = release.get("platform", "")
            release_date = release.get("release_date", "")
            source_url = release.get("source_url", "")

            html += '<div class="release-item">\n'
            html += f'<div class="release-title">{title}</div>\n'
            html += '<div class="release-details">\n'
            if episode:
                html += f'<span class="badge">第{episode}話</span>'
            if platform:
                html += f'<span class="badge">{platform}</span>'
            if release_date:
                html += f"配信日: {release_date}"
            if source_url:
                html += f' <a href="{source_url}" class="release-link" target="_blank">詳細を見る</a>'
            html += "</div>\n"
            html += "</div>\n"

        html += "</div>\n"
        return html

    def _generate_manga_section(self, manga_releases: List[Dict[str, Any]]) -> str:
        """Generate HTML section for manga releases."""
        html = '<div class="section manga-section">\n'
        html += "<h2>📚 マンガ情報</h2>\n"

        for release in manga_releases:
            title = release.get("title", "不明なタイトル")
            volume = release.get("number", "")
            platform = release.get("platform", "")
            release_date = release.get("release_date", "")
            source_url = release.get("source_url", "")

            html += '<div class="release-item">\n'
            html += f'<div class="release-title">{title}</div>\n'
            html += '<div class="release-details">\n'
            if volume:
                html += f'<span class="badge">第{volume}巻</span>'
            if platform:
                html += f'<span class="badge">{platform}</span>'
            if release_date:
                html += f"発売日: {release_date}"
            if source_url:
                html += f' <a href="{source_url}" class="release-link" target="_blank">購入する</a>'
            html += "</div>\n"
            html += "</div>\n"

        html += "</div>\n"
        return html

    def _generate_text_template(
        self, releases: List[Dict[str, Any]], date_str: str
    ) -> str:
        """Generate plain text email template."""
        text = f"アニメ・マンガ最新情報 - {date_str}\n"
        text += "=" * 40 + "\n\n"

        # Anime section
        anime_releases = [r for r in releases if r.get("type") == "anime"]
        if anime_releases:
            text += "📺 アニメ情報\n"
            text += "-" * 20 + "\n"
            for release in anime_releases:
                title = release.get("title", "不明なタイトル")
                episode = release.get("number", "")
                platform = release.get("platform", "")
                release_date = release.get("release_date", "")

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
        manga_releases = [r for r in releases if r.get("type") == "manga"]
        if manga_releases:
            text += "📚 マンガ情報\n"
            text += "-" * 20 + "\n"
            for release in manga_releases:
                title = release.get("title", "不明なタイトル")
                volume = release.get("number", "")
                platform = release.get("platform", "")
                release_date = release.get("release_date", "")

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
