"""
Googleカレンダー連携モジュール（型ヒント付き）
"""

import logging
import os
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_service(
    credentials_path: str = "config/credentials.json",
    token_path: str = "config/calendar_token.json",
) -> Resource:
    """
    Google Calendar APIサービスを取得

    Args:
        credentials_path: 認証情報ファイルのパス
        token_path: トークンファイルのパス

    Returns:
        Resource: Calendar APIサービスオブジェクト
    """
    creds: Optional[Credentials] = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    service: Resource = build("calendar", "v3", credentials=creds)
    return service


def create_event_body(
    title: str,
    date: str,
    description: Optional[str] = None,
    location: Optional[str] = None,
    color_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    カレンダーイベントボディを作成

    Args:
        title: イベントタイトル
        date: 日付（YYYY-MM-DD形式）
        description: イベント説明
        location: 場所
        color_id: カラーID（1-11）

    Returns:
        Dict[str, Any]: イベントボディ
    """
    event: Dict[str, Any] = {
        "summary": title,
        "start": {
            "date": date,
            "timeZone": "Asia/Tokyo",
        },
        "end": {
            "date": date,
            "timeZone": "Asia/Tokyo",
        },
    }

    if description:
        event["description"] = description

    if location:
        event["location"] = location

    if color_id:
        event["colorId"] = color_id

    return event


def add_event(
    service: Resource, event_body: Dict[str, Any], calendar_id: str = "primary"
) -> Dict[str, Any]:
    """
    カレンダーにイベントを追加

    Args:
        service: Calendar APIサービス
        event_body: イベントボディ
        calendar_id: カレンダーID

    Returns:
        Dict[str, Any]: 作成されたイベント
    """
    try:
        event: Dict[str, Any] = (
            service.events().insert(calendarId=calendar_id, body=event_body).execute()
        )

        logger.info(f"イベント追加成功: {event.get('summary')} (ID: {event.get('id')})")
        return event

    except Exception as e:
        logger.error(f"イベント追加エラー: {e}")
        raise


def generate_release_event_title(release: Dict[str, Any]) -> str:
    """
    リリース情報からイベントタイトルを生成

    Args:
        release: リリース情報

    Returns:
        str: イベントタイトル
    """
    title = release.get("title", "不明")
    release_type = release.get("release_type", "episode")
    number = release.get("number", "?")

    type_emoji = "🎬" if release.get("work_type") == "anime" else "📚"
    type_text = "話" if release_type == "episode" else "巻"

    return f"{type_emoji} {title} 第{number}{type_text}"


def generate_release_description(release: Dict[str, Any]) -> str:
    """
    リリース情報からイベント説明を生成

    Args:
        release: リリース情報

    Returns:
        str: イベント説明
    """
    description_parts: List[str] = []

    work_type = release.get("work_type")
    if work_type:
        description_parts.append(f"種別: {'アニメ' if work_type == 'anime' else 'マンガ'}")

    platform = release.get("platform")
    if platform:
        description_parts.append(f"配信: {platform}")

    source = release.get("source")
    if source:
        description_parts.append(f"ソース: {source}")

    source_url = release.get("source_url")
    if source_url:
        description_parts.append(f"\n詳細: {source_url}")

    return "\n".join(description_parts)


def get_color_id_for_work_type(work_type: str) -> str:
    """
    作品タイプに応じたカラーIDを取得

    Args:
        work_type: 作品タイプ（anime/manga）

    Returns:
        str: カラーID
    """
    # Google Calendarのカラーパレット
    # 1: Lavender, 2: Sage, 3: Grape, 4: Flamingo, 5: Banana
    # 6: Tangerine, 7: Peacock, 8: Graphite, 9: Blueberry, 10: Basil, 11: Tomato
    color_map = {"anime": "9", "manga": "10"}  # Blueberry (青系)  # Basil (緑系)

    return color_map.get(work_type, "1")


def add_release_to_calendar(
    release: Dict[str, Any],
    calendar_id: str = "primary",
    credentials_path: str = "config/credentials.json",
    token_path: str = "config/calendar_token.json",
) -> Optional[str]:
    """
    リリース情報をカレンダーに追加

    Args:
        release: リリース情報
        calendar_id: カレンダーID
        credentials_path: 認証情報ファイルのパス
        token_path: トークンファイルのパス

    Returns:
        Optional[str]: イベントID（エラー時はNone）
    """
    try:
        service = get_calendar_service(credentials_path, token_path)

        title = generate_release_event_title(release)
        description = generate_release_description(release)
        date = release.get("release_date", "")
        work_type = release.get("work_type", "anime")
        color_id = get_color_id_for_work_type(work_type)

        event_body = create_event_body(
            title=title, date=date, description=description, color_id=color_id
        )

        event = add_event(service, event_body, calendar_id)
        event_id = event.get("id")

        if event_id:
            logger.info(f"カレンダー追加成功: {title}")
            return str(event_id)
        else:
            logger.error("イベントIDが取得できませんでした")
            return None

    except Exception as e:
        logger.error(f"カレンダー追加エラー: {e}")
        return None


def add_releases_to_calendar(
    releases: List[Dict[str, Any]],
    calendar_id: str = "primary",
    credentials_path: str = "config/credentials.json",
    token_path: str = "config/calendar_token.json",
) -> List[Dict[str, Any]]:
    """
    複数のリリース情報をカレンダーに追加

    Args:
        releases: リリース情報のリスト
        calendar_id: カレンダーID
        credentials_path: 認証情報ファイルのパス
        token_path: トークンファイルのパス

    Returns:
        List[Dict[str, Any]]: 追加結果のリスト（release_id, event_id, success）
    """
    if not releases:
        logger.info("追加するリリース情報がありません")
        return []

    results: List[Dict[str, Any]] = []

    try:
        service = get_calendar_service(credentials_path, token_path)

        for release in releases:
            try:
                title = generate_release_event_title(release)
                description = generate_release_description(release)
                date = release.get("release_date", "")
                work_type = release.get("work_type", "anime")
                color_id = get_color_id_for_work_type(work_type)

                event_body = create_event_body(
                    title=title, date=date, description=description, color_id=color_id
                )

                event = add_event(service, event_body, calendar_id)
                event_id = event.get("id")

                results.append(
                    {
                        "release_id": release.get("release_id"),
                        "event_id": str(event_id) if event_id else None,
                        "success": bool(event_id),
                    }
                )

            except Exception as e:
                logger.error(f"個別イベント追加エラー: {e}")
                results.append(
                    {"release_id": release.get("release_id"), "event_id": None, "success": False}
                )

        success_count = sum(1 for r in results if r["success"])
        logger.info(f"カレンダー追加完了: {success_count}/{len(releases)}件成功")

        return results

    except Exception as e:
        logger.error(f"カレンダー一括追加エラー: {e}")
        return []


def delete_event(service: Resource, event_id: str, calendar_id: str = "primary") -> bool:
    """
    カレンダーからイベントを削除

    Args:
        service: Calendar APIサービス
        event_id: イベントID
        calendar_id: カレンダーID

    Returns:
        bool: 削除成功したかどうか
    """
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

        logger.info(f"イベント削除成功: {event_id}")
        return True

    except Exception as e:
        logger.error(f"イベント削除エラー: {e}")
        return False


def get_events(
    service: Resource,
    calendar_id: str = "primary",
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 100,
) -> List[Dict[str, Any]]:
    """
    カレンダーからイベントを取得

    Args:
        service: Calendar APIサービス
        calendar_id: カレンダーID
        time_min: 開始日時（RFC3339形式）
        time_max: 終了日時（RFC3339形式）
        max_results: 最大取得件数

    Returns:
        List[Dict[str, Any]]: イベントのリスト
    """
    try:
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events: List[Dict[str, Any]] = events_result.get("items", [])
        logger.info(f"イベント取得成功: {len(events)}件")

        return events

    except Exception as e:
        logger.error(f"イベント取得エラー: {e}")
        return []
