"""
Google Calendar API integration for scheduling anime/manga releases.

This module provides functionality to create calendar events for new releases
using the Google Calendar API with OAuth2 authentication.
"""

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional

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


def calendar_retry_on_failure(
    max_retries: int = 3, delay: float = 1.0, exponential_backoff: bool = True
):
    """
    Google Calendar API エラー時のリトライデコレータ

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

                    # Calendar API 固有エラーの判定
                    if hasattr(e, "resp") and hasattr(e.resp, "status"):
                        status_code = e.resp.status
                        # 4xx エラーはリトライしない（認証エラーなど）
                        if (
                            400 <= status_code < 500 and status_code != 429
                        ):  # 429 (Rate limit) はリトライ
                            logger.error(
                                f"Non-retryable Calendar error {status_code} in {func.__name__}: {e}"
                            )
                            raise

                    logger.warning(f"Attempt {attempt + 1} of {func.__name__} failed: {e}")
                    logger.info(f"Retrying in {current_delay:.1f} seconds...")

                    time.sleep(current_delay)

                    if exponential_backoff:
                        current_delay *= 2

            # Should never reach here, but just in case
            raise last_exception

        return wrapper

    return decorator


@dataclass
class CalendarAuthState:
    """Google Calendar認証状態の管理"""

    is_authenticated: bool = False
    last_auth_time: Optional[datetime] = None
    token_expires_at: Optional[datetime] = None
    auth_lock: threading.Lock = field(default_factory=threading.Lock)
    consecutive_auth_failures: int = 0
    last_auth_error: Optional[str] = None
    refresh_in_progress: bool = False
    token_refresh_count: int = 0
    last_refresh_time: Optional[datetime] = None


@dataclass
class CalendarEvent:
    """Data class for calendar event information."""

    title: str
    description: str
    start_datetime: datetime
    end_datetime: datetime
    location: str = ""
    color_id: str = None
    reminders: List[int] = None  # minutes before event

    def __post_init__(self):
        if self.reminders is None:
            self.reminders = [60, 10]  # Default: 1 hour and 10 minutes before


class GoogleCalendarManager:
    """Google Calendar API client for managing anime/manga release events."""

    def __init__(self, config: Dict[str, Any], db_manager=None):
        """
        Initialize Google Calendar manager with enhanced error handling and monitoring.

        Args:
            config: Configuration dictionary with calendar settings
            db_manager: DatabaseManager instance for history recording (optional)
        """
        self.config = config
        self.calendar_config = config.get("google", {}).get("calendar", {})
        self.credentials_file = config.get("google", {}).get("credentials_file", "credentials.json")
        self.token_file = config.get("google", {}).get("token_file", "token.json")
        self.scopes = config.get("google", {}).get(
            "scopes", ["https://www.googleapis.com/auth/calendar.events"]
        )

        self.service = None
        self.auth_state = CalendarAuthState()
        self.calendar_id = self.calendar_config.get("calendar_id", "primary")
        self.db_manager = db_manager

        # Performance monitoring
        self.total_events_created = 0
        self.total_events_updated = 0
        self.total_events_deleted = 0
        self.total_operation_failures = 0
        self.total_auth_attempts = 0
        self.start_time = datetime.now()

        # Rate limiting for Calendar API
        self.rate_limit_requests = []
        self.rate_limit_window = 60  # seconds
        self.max_requests_per_minute = 300  # Calendar API limit (conservative)

        # Color mapping for different content types
        self.color_mapping = {
            "anime": "7",  # Blue
            "manga": "2",  # Green
            "episode": "9",  # Purple for episodes
            "volume": "10",  # Orange for volumes
            "default": "1",  # Light purple
        }

        # Event type mapping
        self.event_type_mapping = {
            "anime_episode": {"color": "7", "icon": "📺"},
            "anime_season": {"color": "4", "icon": "🎬"},
            "manga_volume": {"color": "2", "icon": "📚"},
            "manga_chapter": {"color": "10", "icon": "📖"},
            "default": {"color": "1", "icon": "📅"},
        }

    def _is_token_near_expiry(self, minutes_ahead: int = 10) -> bool:
        """Check if token will expire soon."""
        if not self.auth_state.token_expires_at:
            return True

        expiry_threshold = datetime.now() + timedelta(minutes=minutes_ahead)
        return self.auth_state.token_expires_at <= expiry_threshold

    def _refresh_token_proactively(self) -> bool:
        """Proactively refresh token if it's near expiry."""
        if self.auth_state.refresh_in_progress:
            logger.debug("Calendar token refresh already in progress")
            return True

        if not self._is_token_near_expiry():
            return True

        logger.info("Calendar token is near expiry, attempting proactive refresh")
        return self._refresh_token()

    def _refresh_token(self) -> bool:
        """Refresh OAuth2 token for Calendar API."""
        with self.auth_state.auth_lock:
            if self.auth_state.refresh_in_progress:
                return True

            self.auth_state.refresh_in_progress = True

            try:
                if not os.path.exists(self.token_file):
                    logger.warning("Calendar token file not found for refresh")
                    return False

                creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)

                if not creds.refresh_token:
                    logger.warning("No refresh token available for Calendar")
                    return False

                # Attempt refresh
                creds.refresh(Request())

                # Save refreshed token with secure permissions
                old_umask = os.umask(0o077)
                try:
                    with open(self.token_file, "w") as token:
                        token.write(creds.to_json())
                finally:
                    os.umask(old_umask)

                # Update service with new credentials
                self.service = build("calendar", "v3", credentials=creds, cache_discovery=False)

                # Update auth state
                self.auth_state.token_expires_at = creds.expiry or (
                    datetime.now() + timedelta(hours=1)
                )
                self.auth_state.last_refresh_time = datetime.now()
                self.auth_state.token_refresh_count += 1

                logger.info(
                    f"Calendar token refreshed successfully (refresh count: {self.auth_state.token_refresh_count})"
                )
                return True

            except Exception as e:
                logger.error(f"Calendar token refresh failed: {e}")
                return False
            finally:
                self.auth_state.refresh_in_progress = False

    def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar API using OAuth2 with enhanced error handling and proactive token refresh.

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
                    logger.info("Refreshing expired Calendar credentials")
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Credentials file not found: {self.credentials_file}")
                        return False

                    logger.info("Initiating Google Calendar OAuth2 flow")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes
                    )
                    creds = flow.run_local_server(port=0)

                # Save credentials for next run
                with open(self.token_file, "w") as token:
                    token.write(creds.to_json())
                logger.info("Calendar credentials saved successfully")

            # Build Calendar service
            self.service = build("calendar", "v3", credentials=creds)
            self._authenticated = True
            logger.info("Google Calendar API authentication successful")
            return True

        except Exception as e:
            logger.error(f"Calendar authentication failed: {str(e)}")
            return False

    def create_event(self, event: CalendarEvent, releases_count: int = 1) -> Optional[str]:
        """
        Create a calendar event with history recording.

        Args:
            event: CalendarEvent object with event details
            releases_count: Number of releases in this calendar event

        Returns:
            str: Event ID if created successfully, None otherwise
        """
        success = False
        error_message = None
        event_id = None

        if not self._authenticated:
            error_message = "Calendar not authenticated. Call authenticate() first."
            logger.error(error_message)

            # Record failure in history
            if self.db_manager:
                try:
                    self.db_manager.record_notification_history(
                        notification_type="calendar",
                        success=False,
                        error_message=error_message,
                        releases_count=releases_count,
                    )
                except Exception as db_error:
                    logger.warning(f"Failed to record calendar notification history: {db_error}")

            return None

        try:
            # Prepare event data
            event_body = {
                "summary": event.title,
                "description": event.description,
                "start": {
                    "dateTime": event.start_datetime.isoformat(),
                    "timeZone": "Asia/Tokyo",
                },
                "end": {
                    "dateTime": event.end_datetime.isoformat(),
                    "timeZone": "Asia/Tokyo",
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": reminder} for reminder in event.reminders
                    ],
                },
            }

            # Add location if provided
            if event.location:
                event_body["location"] = event.location

            # Add color if provided
            if event.color_id:
                event_body["colorId"] = event.color_id

            # Create the event
            created_event = (
                self.service.events().insert(calendarId=self.calendar_id, body=event_body).execute()
            )

            event_id = created_event.get("id")
            success = event_id is not None
            logger.info(f"Calendar event created successfully. Event ID: {event_id}")

        except HttpError as error:
            error_message = f"Calendar API error: {error}"
            logger.error(error_message)
        except Exception as e:
            error_message = f"Failed to create calendar event: {str(e)}"
            logger.error(error_message)
        finally:
            # Record history to database
            if self.db_manager:
                try:
                    self.db_manager.record_notification_history(
                        notification_type="calendar",
                        success=success,
                        error_message=error_message,
                        releases_count=releases_count,
                    )
                except Exception as db_error:
                    logger.warning(f"Failed to record calendar notification history: {db_error}")

        return event_id

    def update_event(self, event_id: str, event: CalendarEvent) -> bool:
        """
        Update an existing calendar event.

        Args:
            event_id: ID of the event to update
            event: CalendarEvent object with updated details

        Returns:
            bool: True if updated successfully, False otherwise
        """
        if not self._authenticated:
            logger.error("Calendar not authenticated. Call authenticate() first.")
            return False

        try:
            # Prepare event data
            event_body = {
                "summary": event.title,
                "description": event.description,
                "start": {
                    "dateTime": event.start_datetime.isoformat(),
                    "timeZone": "Asia/Tokyo",
                },
                "end": {
                    "dateTime": event.end_datetime.isoformat(),
                    "timeZone": "Asia/Tokyo",
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": reminder} for reminder in event.reminders
                    ],
                },
            }

            # Add location if provided
            if event.location:
                event_body["location"] = event.location

            # Add color if provided
            if event.color_id:
                event_body["colorId"] = event.color_id

            # Update the event
            self.service.events().update(
                calendarId=self.calendar_id, eventId=event_id, body=event_body
            ).execute()

            logger.info(f"Calendar event updated successfully. Event ID: {event_id}")
            return True

        except HttpError as error:
            logger.error(f"Calendar API error: {error}")
            return False
        except Exception as e:
            logger.error(f"Failed to update calendar event: {str(e)}")
            return False

    def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event.

        Args:
            event_id: ID of the event to delete

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        if not self._authenticated:
            logger.error("Calendar not authenticated. Call authenticate() first.")
            return False

        try:
            self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()

            logger.info(f"Calendar event deleted successfully. Event ID: {event_id}")
            return True

        except HttpError as error:
            if error.resp.status == 410:  # Event already deleted
                logger.info(f"Event already deleted: {event_id}")
                return True
            logger.error(f"Calendar API error: {error}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete calendar event: {str(e)}")
            return False

    def list_events(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List calendar events within a date range.

        Args:
            start_date: Start date for event search (default: now)
            end_date: End date for event search (default: start_date + 30 days)
            max_results: Maximum number of events to return

        Returns:
            List[Dict]: List of calendar events
        """
        if not self._authenticated:
            logger.error("Calendar not authenticated. Call authenticate() first.")
            return []

        try:
            if not start_date:
                start_date = datetime.now()
            if not end_date:
                end_date = start_date + timedelta(days=30)

            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=start_date.isoformat() + "Z",
                    timeMax=end_date.isoformat() + "Z",
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            logger.info(f"Retrieved {len(events)} calendar events")
            return events

        except HttpError as error:
            logger.error(f"Calendar API error: {error}")
            return []
        except Exception as e:
            logger.error(f"Failed to list calendar events: {str(e)}")
            return []

    def create_release_event(self, release: Dict[str, Any]) -> Optional[str]:
        """
        Create a calendar event for an anime/manga release.

        Args:
            release: Release information dictionary

        Returns:
            str: Event ID if created successfully, None otherwise
        """
        try:
            # Extract release information
            title = release.get("title", "不明なタイトル")
            release_type = release.get("type", "unknown")
            number = release.get("number", "")
            platform = release.get("platform", "")
            release_date = release.get("release_date")
            source_url = release.get("source_url", "")

            # Parse release date
            if isinstance(release_date, str):
                try:
                    release_datetime = datetime.fromisoformat(release_date.replace("Z", "+00:00"))
                except ValueError:
                    # Try parsing different date formats
                    for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]:
                        try:
                            release_datetime = datetime.strptime(release_date, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        logger.warning(f"Unable to parse release date: {release_date}")
                        release_datetime = datetime.now()
            elif isinstance(release_date, datetime):
                release_datetime = release_date
            else:
                release_datetime = datetime.now()

            # Create event title
            event_title = title
            if release_type == "anime" and number:
                event_title += f" 第{number}話配信"
            elif release_type == "manga" and number:
                event_title += f" 第{number}巻発売"
            elif platform:
                event_title += f" ({platform})"

            # Create event description
            description_parts = []
            description_parts.append(f"タイトル: {title}")
            if number:
                if release_type == "anime":
                    description_parts.append(f"エピソード: 第{number}話")
                elif release_type == "manga":
                    description_parts.append(f"巻数: 第{number}巻")
            if platform:
                description_parts.append(f"プラットフォーム: {platform}")
            if source_url:
                description_parts.append(f"詳細: {source_url}")
            description_parts.append("\n🤖 MangaAnime情報配信システムにより自動作成")

            event_description = "\n".join(description_parts)

            # Set event duration
            duration_hours = self.calendar_config.get("event_duration_hours", 1)
            end_datetime = release_datetime + timedelta(hours=duration_hours)

            # Get reminder settings
            reminder_minutes = self.calendar_config.get("reminder_minutes", [60, 10])

            # Create calendar event
            calendar_event = CalendarEvent(
                title=event_title,
                description=event_description,
                start_datetime=release_datetime,
                end_datetime=end_datetime,
                location=platform if platform else "",
                color_id=self.color_mapping.get(release_type, self.color_mapping["default"]),
                reminders=reminder_minutes,
            )

            # Create the event
            event_id = self.create_event(calendar_event)

            if event_id:
                logger.info(f"Created calendar event for {title}: {event_id}")

            return event_id

        except Exception as e:
            logger.error(f"Failed to create release event: {str(e)}")
            return None

    def bulk_create_release_events(self, releases: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Create calendar events for multiple releases.

        Args:
            releases: List of release dictionaries

        Returns:
            Dict[str, str]: Mapping of release titles to event IDs
        """
        results = {}

        for release in releases:
            title = release.get("title", "不明なタイトル")
            try:
                event_id = self.create_release_event(release)
                if event_id:
                    results[title] = event_id
                else:
                    logger.warning(f"Failed to create event for: {title}")
            except Exception as e:
                logger.error(f"Error creating event for {title}: {str(e)}")

        logger.info(f"Created {len(results)} calendar events out of {len(releases)} releases")
        return results

    def search_events(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search for calendar events by title.

        Args:
            query: Search query string
            max_results: Maximum number of events to return

        Returns:
            List[Dict]: List of matching calendar events
        """
        if not self._authenticated:
            logger.error("Calendar not authenticated. Call authenticate() first.")
            return []

        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    q=query,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            logger.info(f"Found {len(events)} events matching '{query}'")
            return events

        except HttpError as error:
            logger.error(f"Calendar API error: {error}")
            return []
        except Exception as e:
            logger.error(f"Failed to search calendar events: {str(e)}")
            return []

    def get_calendar_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current calendar.

        Returns:
            Dict: Calendar information, None if error
        """
        if not self._authenticated:
            logger.error("Calendar not authenticated. Call authenticate() first.")
            return None

        try:
            calendar_info = self.service.calendars().get(calendarId=self.calendar_id).execute()

            return {
                "id": calendar_info.get("id"),
                "summary": calendar_info.get("summary"),
                "description": calendar_info.get("description"),
                "timezone": calendar_info.get("timeZone"),
                "access_role": calendar_info.get("accessRole"),
            }

        except HttpError as error:
            logger.error(f"Calendar API error: {error}")
            return None
        except Exception as e:
            logger.error(f"Failed to get calendar info: {str(e)}")
            return None


class CalendarEventFormatter:
    """Utility class for formatting calendar event information."""

    @staticmethod
    def format_anime_event_title(title: str, episode: str = None, platform: str = None) -> str:
        """Format anime event title."""
        formatted_title = title
        if episode:
            formatted_title += f" 第{episode}話配信"
        if platform:
            formatted_title += f" ({platform})"
        return formatted_title

    @staticmethod
    def format_manga_event_title(title: str, volume: str = None, platform: str = None) -> str:
        """Format manga event title."""
        formatted_title = title
        if volume:
            formatted_title += f" 第{volume}巻発売"
        if platform:
            formatted_title += f" ({platform})"
        return formatted_title

    @staticmethod
    def format_event_description(release: Dict[str, Any]) -> str:
        """Format event description from release data."""
        description_parts = []

        title = release.get("title", "不明なタイトル")
        release_type = release.get("type", "")
        number = release.get("number", "")
        platform = release.get("platform", "")
        source_url = release.get("source_url", "")

        description_parts.append(f"タイトル: {title}")

        if number:
            if release_type == "anime":
                description_parts.append(f"エピソード: 第{number}話")
            elif release_type == "manga":
                description_parts.append(f"巻数: 第{number}巻")

        if platform:
            description_parts.append(f"プラットフォーム: {platform}")

        if source_url:
            description_parts.append(f"詳細: {source_url}")

        description_parts.append("\n🤖 MangaAnime情報配信システムにより自動作成")

        return "\n".join(description_parts)


class CalendarManager:
    """
    GoogleCalendarManagerのシンプルラッパー。
    テスト互換性と簡易インターフェース用。

    create_event(title, description, start_time, end_time=None)
    で呼び出せるシンプルなAPIを提供する。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        calendar_config = self.config.get("calendar", {})
        self.calendar_id = calendar_config.get("calendar_id", "primary")
        self._enabled = calendar_config.get("enabled", True)
        self.service = None
        self._authenticated = False

    def authenticate(self) -> bool:
        """Google Calendar認証を行う"""
        if not self._enabled:
            return False
        try:
            from googleapiclient.discovery import build

            self.service = build("calendar", "v3")
            self._authenticated = True
            return True
        except Exception:
            return False

    def create_event(
        self,
        title: str,
        description: str,
        start_time: str,
        end_time: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        カレンダーイベントをシンプルなインターフェースで作成する。

        Args:
            title: イベントタイトル
            description: イベント説明
            start_time: 開始時刻 (ISO 8601形式)
            end_time: 終了時刻 (ISO 8601形式, 省略可)
            location: 場所 (省略可)

        Returns:
            作成されたイベントデータ辞書またはNone
        """
        if not self._enabled:
            return None

        if self.service is None:
            return None

        try:
            start_dt = datetime.fromisoformat(start_time)
            if end_time:
                end_dt = datetime.fromisoformat(end_time)
            else:
                end_dt = start_dt + timedelta(hours=1)

            event_body: Dict[str, Any] = {
                "summary": title,
                "description": description,
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": "Asia/Tokyo",
                },
                "end": {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": "Asia/Tokyo",
                },
            }
            if location:
                event_body["location"] = location

            created = (
                self.service.events().insert(calendarId=self.calendar_id, body=event_body).execute()
            )
            return created
        except Exception as e:
            logger.error(f"CalendarManager.create_event failed: {e}")
            return None

    def create_anime_event(self, anime_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        アニメエピソード用のカレンダーイベントを作成する。

        Args:
            anime_data: アニメデータ辞書 (title, episode, air_date, platform等)

        Returns:
            作成されたイベントデータ辞書またはNone
        """
        title = anime_data.get("title", "Unknown")
        episode = anime_data.get("episode", "")
        platform = anime_data.get("platform", "Unknown")
        air_date = anime_data.get("air_date", "")

        event_title = f"{title} - Episode {episode}" if episode else title
        description = f"New episode of {title} available on {platform}"
        return self.create_event(event_title, description, air_date)

    def create_manga_event(self, manga_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        マンガ新刊用のカレンダーイベントを作成する。

        Args:
            manga_data: マンガデータ辞書 (title, volume, release_date, platform等)

        Returns:
            作成されたイベントデータ辞書またはNone
        """
        title = manga_data.get("title", "Unknown")
        volume = manga_data.get("volume", "")
        release_date = manga_data.get("release_date", "")

        event_title = f"{title} - Volume {volume}" if volume else title
        description = f"New volume of {title} released"
        return self.create_event(event_title, description, release_date)
