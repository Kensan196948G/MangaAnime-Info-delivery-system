"""
Google Calendar API integration for scheduling anime/manga releases.

This module provides functionality to create calendar events for new releases
using the Google Calendar API with OAuth2 authentication.
"""

import os
import json
import logging
from datetime import datetime, timedelta
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
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Google Calendar manager.
        
        Args:
            config: Configuration dictionary with calendar settings
        """
        self.config = config
        self.calendar_config = config.get('google', {}).get('calendar', {})
        self.credentials_file = config.get('google', {}).get('credentials_file', 'credentials.json')
        self.token_file = config.get('google', {}).get('token_file', 'token.json')
        self.scopes = config.get('google', {}).get('scopes', [
            'https://www.googleapis.com/auth/calendar.events'
        ])
        
        self.service = None
        self._authenticated = False
        self.calendar_id = self.calendar_config.get('calendar_id', 'primary')
        
        # Color mapping for different content types
        self.color_mapping = {
            'anime': '7',    # Blue
            'manga': '2',    # Green
            'default': '1'   # Light purple
        }
        
    def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar API using OAuth2.
        
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
                        self.credentials_file, self.scopes)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                logger.info("Calendar credentials saved successfully")
            
            # Build Calendar service
            self.service = build('calendar', 'v3', credentials=creds)
            self._authenticated = True
            logger.info("Google Calendar API authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Calendar authentication failed: {str(e)}")
            return False
    
    def create_event(self, event: CalendarEvent) -> Optional[str]:
        """
        Create a calendar event.
        
        Args:
            event: CalendarEvent object with event details
            
        Returns:
            str: Event ID if created successfully, None otherwise
        """
        if not self._authenticated:
            logger.error("Calendar not authenticated. Call authenticate() first.")
            return None
        
        try:
            # Prepare event data
            event_body = {
                'summary': event.title,
                'description': event.description,
                'start': {
                    'dateTime': event.start_datetime.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'end': {
                    'dateTime': event.end_datetime.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': reminder}
                        for reminder in event.reminders
                    ],
                },
            }
            
            # Add location if provided
            if event.location:
                event_body['location'] = event.location
            
            # Add color if provided
            if event.color_id:
                event_body['colorId'] = event.color_id
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_body
            ).execute()
            
            event_id = created_event.get('id')
            logger.info(f"Calendar event created successfully. Event ID: {event_id}")
            return event_id
            
        except HttpError as error:
            logger.error(f"Calendar API error: {error}")
            return None
        except Exception as e:
            logger.error(f"Failed to create calendar event: {str(e)}")
            return None
    
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
                'summary': event.title,
                'description': event.description,
                'start': {
                    'dateTime': event.start_datetime.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'end': {
                    'dateTime': event.end_datetime.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': reminder}
                        for reminder in event.reminders
                    ],
                },
            }
            
            # Add location if provided
            if event.location:
                event_body['location'] = event.location
            
            # Add color if provided
            if event.color_id:
                event_body['colorId'] = event.color_id
            
            # Update the event
            self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event_body
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
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
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
    
    def list_events(self, start_date: datetime = None, 
                   end_date: datetime = None, max_results: int = 100) -> List[Dict[str, Any]]:
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
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
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
            title = release.get('title', '不明なタイトル')
            release_type = release.get('type', 'unknown')
            number = release.get('number', '')
            platform = release.get('platform', '')
            release_date = release.get('release_date')
            source_url = release.get('source_url', '')
            
            # Parse release date
            if isinstance(release_date, str):
                try:
                    release_datetime = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                except ValueError:
                    # Try parsing different date formats
                    for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S']:
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
            if release_type == 'anime' and number:
                event_title += f" 第{number}話配信"
            elif release_type == 'manga' and number:
                event_title += f" 第{number}巻発売"
            elif platform:
                event_title += f" ({platform})"
            
            # Create event description
            description_parts = []
            description_parts.append(f"タイトル: {title}")
            if number:
                if release_type == 'anime':
                    description_parts.append(f"エピソード: 第{number}話")
                elif release_type == 'manga':
                    description_parts.append(f"巻数: 第{number}巻")
            if platform:
                description_parts.append(f"プラットフォーム: {platform}")
            if source_url:
                description_parts.append(f"詳細: {source_url}")
            description_parts.append("\n🤖 MangaAnime情報配信システムにより自動作成")
            
            event_description = "\n".join(description_parts)
            
            # Set event duration
            duration_hours = self.calendar_config.get('event_duration_hours', 1)
            end_datetime = release_datetime + timedelta(hours=duration_hours)
            
            # Get reminder settings
            reminder_minutes = self.calendar_config.get('reminder_minutes', [60, 10])
            
            # Create calendar event
            calendar_event = CalendarEvent(
                title=event_title,
                description=event_description,
                start_datetime=release_datetime,
                end_datetime=end_datetime,
                location=platform if platform else "",
                color_id=self.color_mapping.get(release_type, self.color_mapping['default']),
                reminders=reminder_minutes
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
            title = release.get('title', '不明なタイトル')
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
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                q=query,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
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
            calendar_info = self.service.calendars().get(
                calendarId=self.calendar_id
            ).execute()
            
            return {
                'id': calendar_info.get('id'),
                'summary': calendar_info.get('summary'),
                'description': calendar_info.get('description'),
                'timezone': calendar_info.get('timeZone'),
                'access_role': calendar_info.get('accessRole')
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
    def format_anime_event_title(title: str, episode: str = None, 
                               platform: str = None) -> str:
        """Format anime event title."""
        formatted_title = title
        if episode:
            formatted_title += f" 第{episode}話配信"
        if platform:
            formatted_title += f" ({platform})"
        return formatted_title
    
    @staticmethod
    def format_manga_event_title(title: str, volume: str = None, 
                               platform: str = None) -> str:
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
        
        title = release.get('title', '不明なタイトル')
        release_type = release.get('type', '')
        number = release.get('number', '')
        platform = release.get('platform', '')
        source_url = release.get('source_url', '')
        
        description_parts.append(f"タイトル: {title}")
        
        if number:
            if release_type == 'anime':
                description_parts.append(f"エピソード: 第{number}話")
            elif release_type == 'manga':
                description_parts.append(f"巻数: 第{number}巻")
        
        if platform:
            description_parts.append(f"プラットフォーム: {platform}")
        
        if source_url:
            description_parts.append(f"詳細: {source_url}")
        
        description_parts.append("\n🤖 MangaAnime情報配信システムにより自動作成")
        
        return "\n".join(description_parts)