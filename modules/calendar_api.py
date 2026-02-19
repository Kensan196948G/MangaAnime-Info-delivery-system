#!/usr/bin/env python3
"""
Google Calendar API ラッパーモジュール
Phase 17: カレンダー統合実装

機能:
- Google Calendar API の認証とトークン管理
- イベントのCRUD操作（作成・取得・更新・削除）
- バッチ処理によるレート制限対策
- エラーハンドリングと自動リトライ
- イベント検索と日付範囲クエリ
"""

import json
import logging
import time

logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleCalendarAPIError(Exception):
    """Google Calendar API エラーの基底クラス"""


class AuthenticationError(GoogleCalendarAPIError):
    """認証エラー"""


class QuotaExceededError(GoogleCalendarAPIError):
    """クォータ超過エラー"""


class EventNotFoundError(GoogleCalendarAPIError):
    """イベント未検出エラー"""


class GoogleCalendarAPI:
    """
    Google Calendar API ラッパークラス

    主要機能:
    - OAuth2.0認証管理
    - イベントのCRUD操作
    - バッチ処理
    - エラーハンドリングとリトライ

    Example:
        >>> calendar = GoogleCalendarAPI()
        >>> event = calendar.create_event(
        ...     summary="新作アニメ配信",
        ...     start_time=datetime(2025, 12, 10, 12, 0),
        ...     duration_minutes=30
        ... )
    """

    # API設定
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    API_SERVICE_NAME = "calendar"
    API_VERSION = "v3"

    # リトライ設定
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1.0  # 秒
    BACKOFF_MULTIPLIER = 2.0

    # バッチ処理設定
    DEFAULT_BATCH_SIZE = 50
    BATCH_DELAY = 1.0  # 秒

    def __init__(self, token_file: str = "auth/calendar_token.json", calendar_id: str = "primary"):
        """
        初期化

        Args:
            token_file: OAuth2.0トークンファイルのパス
            calendar_id: 操作対象のカレンダーID（デフォルト: primary）

        Raises:
            AuthenticationError: 認証に失敗した場合
        """
        self.token_file = token_file
        self.calendar_id = calendar_id
        self.credentials = None
        self.service = None

        # 認証とサービス初期化
        self._initialize()

        logger.info(f"GoogleCalendarAPI initialized: calendar_id={calendar_id}")

    def _initialize(self) -> None:
        """認証とAPIサービスの初期化"""
        try:
            self.credentials = self._load_credentials()
            self.service = build(
                self.API_SERVICE_NAME, self.API_VERSION, credentials=self.credentials
            )
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar API: {e}")
            raise AuthenticationError(f"Authentication failed: {e}")

    def _load_credentials(self) -> Credentials:
        """
        OAuth2.0認証情報の読み込み

        Returns:
            Credentials: 認証情報オブジェクト

        Raises:
            AuthenticationError: 認証情報の読み込みに失敗した場合
        """
        token_path = Path(self.token_file)

        if not token_path.exists():
            raise AuthenticationError(
                f"Token file not found: {self.token_file}\n"
                "Please run authentication setup first."
            )

        try:
            with open(token_path, "r", encoding="utf-8") as f:
                token_data = json.load(f)

            credentials = Credentials(
                token=token_data.get("token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri=token_data.get("token_uri"),
                client_id=token_data.get("client_id"),
                client_secret=token_data.get("client_secret"),
                scopes=token_data.get("scopes", self.SCOPES),
            )

            # トークンの有効性チェックと更新
            if not credentials.valid:
                self._refresh_token_if_needed(credentials)

            return credentials

        except json.JSONDecodeError as e:
            raise AuthenticationError(f"Invalid token file format: {e}")
        except Exception as e:
            raise AuthenticationError(f"Failed to load credentials: {e}")

    def _refresh_token_if_needed(self, credentials: Optional[Credentials] = None) -> bool:
        """
        必要に応じてトークンをリフレッシュ

        Args:
            credentials: 認証情報（Noneの場合はself.credentialsを使用）

        Returns:
            bool: トークンをリフレッシュした場合True
        """
        creds = credentials or self.credentials

        if not creds:
            return False

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())

                # トークンファイルを更新
                self._save_credentials(creds)

                logger.info("Access token refreshed successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                raise AuthenticationError(f"Token refresh failed: {e}")

        return False

    def _save_credentials(self, credentials: Credentials) -> None:
        """
        認証情報をファイルに保存

        Args:
            credentials: 保存する認証情報
        """
        token_path = Path(self.token_file)
        token_path.parent.mkdir(parents=True, exist_ok=True)

        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
        }

        with open(token_path, "w", encoding="utf-8") as f:
            json.dump(token_data, f, ensure_ascii=False, indent=2)

        logger.debug(f"Credentials saved to {self.token_file}")

    # ========================================
    # イベント基本操作
    # ========================================

    def create_event(
        self,
        summary: str,
        start_time: datetime,
        duration_minutes: int = 60,
        description: str = "",
        location: str = "",
        color_id: Optional[str] = None,
        reminders: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        カレンダーイベントを作成

        Args:
            summary: イベントタイトル
            start_time: 開始日時
            duration_minutes: イベント時間（分）
            description: イベント詳細
            location: 場所
            color_id: カラーID（1-11）
            reminders: リマインダー設定

        Returns:
            dict: 作成されたイベント情報

        Raises:
            GoogleCalendarAPIError: イベント作成に失敗した場合

        Example:
            >>> event = calendar.create_event(
            ...     summary="呪術廻戦 第10話",
            ...     start_time=datetime(2025, 12, 10, 23, 0),
            ...     duration_minutes=30,
            ...     description="dアニメストアで配信"
            ... )
        """
        end_time = start_time + timedelta(minutes=duration_minutes)

        event_data = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {
                "dateTime": self._convert_to_iso(start_time),
                "timeZone": "Asia/Tokyo",
            },
            "end": {
                "dateTime": self._convert_to_iso(end_time),
                "timeZone": "Asia/Tokyo",
            },
        }

        # カラー設定
        if color_id:
            event_data["colorId"] = str(color_id)

        # リマインダー設定
        if reminders:
            event_data["reminders"] = {"useDefault": False, "overrides": reminders}
        else:
            event_data["reminders"] = {"useDefault": True}

        # イベントデータ検証
        if not self._validate_event_data(event_data):
            raise GoogleCalendarAPIError("Invalid event data")

        # API呼び出し
        def _create():
            return (
                self.service.events().insert(calendarId=self.calendar_id, body=event_data).execute()
            )

        try:
            event = self._retry_with_backoff(_create)
            logger.info(f"Event created: {summary} at {start_time} " f"(ID: {event.get('id')})")
            return event

        except Exception as e:
            logger.error(f"Failed to create event '{summary}': {e}")
            raise GoogleCalendarAPIError(f"Event creation failed: {e}")

    def get_event(self, event_id: str) -> Dict[str, Any]:
        """
        イベントIDからイベント情報を取得

        Args:
            event_id: イベントID

        Returns:
            dict: イベント情報

        Raises:
            EventNotFoundError: イベントが見つからない場合
        """

        def _get():
            return (
                self.service.events().get(calendarId=self.calendar_id, eventId=event_id).execute()
            )

        try:
            event = self._retry_with_backoff(_get)
            logger.debug(f"Event retrieved: {event_id}")
            return event

        except HttpError as e:
            if e.resp.status == 404:
                raise EventNotFoundError(f"Event not found: {event_id}")
            raise GoogleCalendarAPIError(f"Failed to get event: {e}")

    def update_event(self, event_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        既存イベントを更新

        Args:
            event_id: イベントID
            updates: 更新内容（summary, description, start, end等）

        Returns:
            dict: 更新後のイベント情報

        Raises:
            EventNotFoundError: イベントが見つからない場合
        """
        # 既存イベントを取得
        event = self.get_event(event_id)

        # 更新内容をマージ
        event.update(updates)

        def _update():
            return (
                self.service.events()
                .update(calendarId=self.calendar_id, eventId=event_id, body=event)
                .execute()
            )

        try:
            updated_event = self._retry_with_backoff(_update)
            logger.info(f"Event updated: {event_id}")
            return updated_event

        except Exception as e:
            logger.error(f"Failed to update event {event_id}: {e}")
            raise GoogleCalendarAPIError(f"Event update failed: {e}")

    def delete_event(self, event_id: str) -> bool:
        """
        イベントを削除

        Args:
            event_id: イベントID

        Returns:
            bool: 削除成功時True

        Raises:
            EventNotFoundError: イベントが見つからない場合
        """

        def _delete():
            return (
                self.service.events()
                .delete(calendarId=self.calendar_id, eventId=event_id)
                .execute()
            )

        try:
            self._retry_with_backoff(_delete)
            logger.info(f"Event deleted: {event_id}")
            return True

        except HttpError as e:
            if e.resp.status == 404:
                raise EventNotFoundError(f"Event not found: {event_id}")
            raise GoogleCalendarAPIError(f"Failed to delete event: {e}")

    # ========================================
    # イベント一覧・検索
    # ========================================

    def list_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100,
        order_by: str = "startTime",
        single_events: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        イベント一覧を取得

        Args:
            time_min: 検索開始日時（Noneの場合は現在時刻）
            time_max: 検索終了日時
            max_results: 最大取得件数
            order_by: ソート順（'startTime' or 'updated'）
            single_events: 繰り返しイベントを展開するか

        Returns:
            list: イベント情報のリスト
        """
        if time_min is None:
            time_min = datetime.now()

        params = {
            "calendarId": self.calendar_id,
            "timeMin": self._convert_to_iso(time_min),
            "maxResults": max_results,
            "singleEvents": single_events,
            "orderBy": order_by,
        }

        if time_max:
            params["timeMax"] = self._convert_to_iso(time_max)

        def _list():
            return self.service.events().list(**params).execute()

        try:
            result = self._retry_with_backoff(_list)
            events = result.get("items", [])

            logger.info(
                f"Retrieved {len(events)} events " f"(time_min={time_min}, time_max={time_max})"
            )
            return events

        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            raise GoogleCalendarAPIError(f"Event listing failed: {e}")

    def search_events(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        キーワードでイベントを検索

        Args:
            query: 検索キーワード
            max_results: 最大取得件数

        Returns:
            list: 検索結果のイベントリスト
        """

        def _search():
            return (
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

        try:
            result = self._retry_with_backoff(_search)
            events = result.get("items", [])

            logger.info(f"Found {len(events)} events for query: '{query}'")
            return events

        except Exception as e:
            logger.error(f"Failed to search events: {e}")
            raise GoogleCalendarAPIError(f"Event search failed: {e}")

    def get_events_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        日付範囲でイベントを取得

        Args:
            start_date: 開始日
            end_date: 終了日

        Returns:
            list: 指定期間内のイベントリスト
        """
        return self.list_events(time_min=start_date, time_max=end_date, max_results=250)

    # ========================================
    # バッチ操作
    # ========================================

    def batch_create_events(
        self, events_data: List[Dict[str, Any]], batch_size: int = DEFAULT_BATCH_SIZE
    ) -> Tuple[int, int, List[str]]:
        """
        複数イベントを一括作成（バッチ処理）

        Args:
            events_data: イベントデータのリスト
            batch_size: バッチサイズ（デフォルト: 50）

        Returns:
            tuple: (成功件数, 失敗件数, エラーメッセージリスト)

        Example:
            >>> events = [
            ...     {
            ...         'summary': 'イベント1',
            ...         'start_time': datetime(2025, 12, 10, 12, 0),
            ...         'duration_minutes': 30
            ...     },
            ...     {
            ...         'summary': 'イベント2',
            ...         'start_time': datetime(2025, 12, 11, 15, 0),
            ...         'duration_minutes': 60
            ...     }
            ... ]
            >>> success, failed, errors = calendar.batch_create_events(events)
        """
        total = len(events_data)
        success_count = 0
        failed_count = 0
        errors = []

        logger.info(f"Starting batch event creation: {total} events, " f"batch_size={batch_size}")

        # バッチ処理
        for i in range(0, total, batch_size):
            batch = events_data[i : i + batch_size]
            batch_num = i // batch_size + 1

            logger.debug(f"Processing batch {batch_num}: " f"{len(batch)} events")

            for event_data in batch:
                try:
                    self.create_event(**event_data)
                    success_count += 1

                except Exception as e:
                    failed_count += 1
                    error_msg = f"Failed to create '{event_data.get('summary')}': {e}"
                    errors.append(error_msg)
                    logger.warning(error_msg)

            # バッチ間の待機（レート制限対策）
            if i + batch_size < total:
                time.sleep(self.BATCH_DELAY)

        logger.info(f"Batch creation completed: " f"success={success_count}, failed={failed_count}")

        return success_count, failed_count, errors

    def batch_update_events(
        self, updates_data: List[Tuple[str, Dict[str, Any]]]
    ) -> Tuple[int, int]:
        """
        複数イベントを一括更新

        Args:
            updates_data: (event_id, updates)のタプルリスト

        Returns:
            tuple: (成功件数, 失敗件数)
        """
        success_count = 0
        failed_count = 0

        logger.info(f"Starting batch update: {len(updates_data)} events")

        for event_id, updates in updates_data:
            try:
                self.update_event(event_id, updates)
                success_count += 1

            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to update {event_id}: {e}")

        logger.info(f"Batch update completed: " f"success={success_count}, failed={failed_count}")

        return success_count, failed_count

    def batch_delete_events(self, event_ids: List[str]) -> Tuple[int, int]:
        """
        複数イベントを一括削除

        Args:
            event_ids: イベントIDのリスト

        Returns:
            tuple: (成功件数, 失敗件数)
        """
        success_count = 0
        failed_count = 0

        logger.info(f"Starting batch deletion: {len(event_ids)} events")

        for event_id in event_ids:
            try:
                self.delete_event(event_id)
                success_count += 1

            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to delete {event_id}: {e}")

        logger.info(f"Batch deletion completed: " f"success={success_count}, failed={failed_count}")

        return success_count, failed_count

    # ========================================
    # エラーハンドリング
    # ========================================

    def _handle_http_error(self, error: HttpError) -> None:
        """
        HTTP エラーのハンドリング

        Args:
            error: HttpErrorオブジェクト

        Raises:
            適切な例外クラス
        """
        status = error.resp.status

        if status == 401:
            raise AuthenticationError("Authentication failed. Please re-authenticate.")
        elif status == 403:
            raise QuotaExceededError("API quota exceeded or permission denied")
        elif status == 404:
            raise EventNotFoundError("Event or calendar not found")
        elif status == 429:
            raise QuotaExceededError("Rate limit exceeded")
        else:
            raise GoogleCalendarAPIError(f"HTTP {status}: {error}")

    def _retry_with_backoff(self, func, max_retries: int = MAX_RETRIES) -> Any:
        """
        指数バックオフによるリトライ処理

        Args:
            func: 実行する関数
            max_retries: 最大リトライ回数

        Returns:
            関数の実行結果

        Raises:
            最後のエラー
        """
        backoff = self.INITIAL_BACKOFF

        for attempt in range(max_retries):
            try:
                return func()

            except HttpError as e:
                # 404や401など、リトライしても意味がないエラー
                if e.resp.status in [401, 404]:
                    self._handle_http_error(e)

                # リトライ可能なエラー（429, 503等）
                if attempt < max_retries - 1:
                    logger.warning(
                        f"API call failed (attempt {attempt + 1}/{max_retries}): "
                        f"{e}. Retrying in {backoff}s..."
                    )
                    time.sleep(backoff)
                    backoff *= self.BACKOFF_MULTIPLIER
                else:
                    logger.error(f"API call failed after {max_retries} retries: {e}")
                    self._handle_http_error(e)

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise

        raise GoogleCalendarAPIError("Max retries exceeded")

    # ========================================
    # ユーティリティ
    # ========================================

    def _convert_to_iso(self, dt: datetime) -> str:
        """
        datetimeをISO 8601形式に変換

        Args:
            dt: datetime オブジェクト

        Returns:
            str: ISO 8601形式の文字列
        """
        return dt.isoformat()

    def _validate_event_data(self, event_data: Dict[str, Any]) -> bool:
        """
        イベントデータの検証

        Args:
            event_data: 検証するイベントデータ

        Returns:
            bool: 有効な場合True
        """
        required_fields = ["summary", "start", "end"]

        for field in required_fields:
            if field not in event_data:
                logger.error(f"Missing required field: {field}")
                return False

        # 開始・終了時刻の検証
        if "dateTime" not in event_data["start"]:
            logger.error("Missing 'dateTime' in start")
            return False

        if "dateTime" not in event_data["end"]:
            logger.error("Missing 'dateTime' in end")
            return False

        return True

    def get_calendar_info(self) -> Dict[str, Any]:
        """
        カレンダー情報を取得

        Returns:
            dict: カレンダー情報
        """

        def _get_calendar():
            return self.service.calendars().get(calendarId=self.calendar_id).execute()

        try:
            calendar_info = self._retry_with_backoff(_get_calendar)
            logger.info(
                f"Calendar info: {calendar_info.get('summary')} " f"(ID: {self.calendar_id})"
            )
            return calendar_info

        except Exception as e:
            logger.error(f"Failed to get calendar info: {e}")
            raise GoogleCalendarAPIError(f"Failed to get calendar info: {e}")

    def get_color_definitions(self) -> Dict[str, Any]:
        """
        利用可能なカラー定義を取得

        Returns:
            dict: カラー定義
        """

        def _get_colors():
            return self.service.colors().get().execute()

        try:
            colors = self._retry_with_backoff(_get_colors)
            logger.debug("Color definitions retrieved")
            return colors

        except Exception as e:
            logger.error(f"Failed to get color definitions: {e}")
            raise GoogleCalendarAPIError(f"Failed to get colors: {e}")


# ========================================
# ヘルパー関数
# ========================================


def create_reminder(method: str = "popup", minutes: int = 30) -> Dict[str, Any]:
    """
    リマインダー設定を作成

    Args:
        method: 通知方法（'popup' or 'email'）
        minutes: 何分前に通知するか

    Returns:
        dict: リマインダー設定

    Example:
        >>> reminder = create_reminder('popup', 60)
        >>> event = calendar.create_event(
        ...     summary="重要なイベント",
        ...     start_time=datetime.now() + timedelta(days=1),
        ...     reminders=[reminder]
        ... )
    """
    return {"method": method, "minutes": minutes}


def format_event_summary(title: str, episode: Optional[str] = None) -> str:
    """
    イベントタイトルをフォーマット

    Args:
        title: 作品タイトル
        episode: エピソード番号

    Returns:
        str: フォーマット済みタイトル

    Example:
        >>> format_event_summary("呪術廻戦", "第10話")
        '呪術廻戦 第10話'
    """
    if episode:
        return f"{title} {episode}"
    return title


if __name__ == "__main__":
    # 簡易テスト
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("Google Calendar API Wrapper Module")
    print("=" * 50)
    print("\nThis is a library module. Please import and use it in your code.")
    print("\nExample:")
    print("  from modules.calendar_api import GoogleCalendarAPI")
    print("  calendar = GoogleCalendarAPI()")
    print("  event = calendar.create_event(...)")
