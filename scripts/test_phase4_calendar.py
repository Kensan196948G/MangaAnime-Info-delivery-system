#!/usr/bin/env python3
"""
Phase 4: Google Calendar 開発モード・エンドツーエンドテスト

credentials.json が未取得の状況でも、カレンダーイベント登録機能を
エンドツーエンドでテストできる「開発モード」を提供します。

使用方法:
    python -X utf8 scripts/test_phase4_calendar.py           # --save --list を実行
    python -X utf8 scripts/test_phase4_calendar.py --save    # AniListから取得してDBに保存
    python -X utf8 scripts/test_phase4_calendar.py --list    # 保存済みイベント一覧を表示
    python -X utf8 scripts/test_phase4_calendar.py --sync    # GoogleカレンダーAPIに同期

機能:
    - AniList GraphQL API から今期アニメを取得 (asyncio 使用)
    - 取得データを pending_calendar_events テーブルに保存
    - 保存済みイベントの一覧表示
    - credentials.json が存在する場合は Google Calendar に同期
"""

import io
import sys

# Windows 環境での UTF-8 強制出力
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import argparse
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ロギング設定（WARNING以上のみ表示してスクリプト出力を見やすく）
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────
# 定数
# ─────────────────────────────────────────────────

CREDENTIALS_PATH = project_root / "credentials.json"
TOKEN_PATH = project_root / "token.json"
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]

NG_KEYWORDS = ["エロ", "R18", "成人向け", "BL", "百合", "ボーイズラブ", "Hentai"]
NG_GENRES = ["Hentai", "Ecchi"]

ANILIST_GRAPHQL_URL = "https://graphql.anilist.co"

ANILIST_QUERY = """
query ($season: MediaSeason, $year: Int) {
  Page(perPage: 15) {
    media(
      season: $season
      seasonYear: $year
      type: ANIME
      status: RELEASING
      sort: POPULARITY_DESC
    ) {
      id
      title { native romaji english }
      genres
      averageScore
      episodes
      nextAiringEpisode {
        airingAt
        episode
      }
      streamingEpisodes {
        title
        site
        url
      }
      siteUrl
    }
  }
}
"""


# ─────────────────────────────────────────────────
# ユーティリティ
# ─────────────────────────────────────────────────

def print_section(title: str):
    """区切りセクションヘッダーを表示する"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def _current_season_vars() -> dict:
    """現在の季節と年を AniList API 変数として返す"""
    now = datetime.now()
    month = now.month
    if month in [12, 1, 2]:
        season = "WINTER"
    elif month in [3, 4, 5]:
        season = "SPRING"
    elif month in [6, 7, 8]:
        season = "SUMMER"
    else:
        season = "FALL"
    return {"season": season, "year": now.year}


def _should_filter(anime: dict) -> bool:
    """NG キーワードまたはジャンルに一致する場合 True を返す"""
    title_native = anime.get("title", {}).get("native") or ""
    title_romaji = anime.get("title", {}).get("romaji") or ""
    title_en = anime.get("title", {}).get("english") or ""
    combined = (title_native + title_romaji + title_en).lower()

    if any(kw.lower() in combined for kw in NG_KEYWORDS):
        return True

    genres = anime.get("genres", [])
    if any(g in NG_GENRES for g in genres):
        return True

    return False


def _build_event_data(anime: dict) -> dict:
    """
    AniList レスポンスの1件をカレンダーイベント辞書に変換する。

    Returns:
        pending_calendar_events に渡せる辞書
    """
    title_native = (
        anime.get("title", {}).get("native")
        or anime.get("title", {}).get("romaji")
        or "Unknown"
    )
    title_en = anime.get("title", {}).get("english") or ""

    next_ep = anime.get("nextAiringEpisode")
    if next_ep and next_ep.get("airingAt"):
        airing_ts = next_ep["airingAt"]
        ep_num = next_ep.get("episode", "?")
        start_dt = datetime.fromtimestamp(airing_ts)
        start_datetime_str = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
        end_dt = start_dt + timedelta(minutes=30)
        end_datetime_str = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
        event_label = f"第{ep_num}話 配信予定"
    else:
        # 次回放送情報がない場合は翌週の同曜日をプレースホルダとして使用
        placeholder = datetime.now() + timedelta(days=7)
        start_datetime_str = placeholder.strftime("%Y-%m-%dT%H:00:00")
        end_dt = placeholder + timedelta(minutes=30)
        end_datetime_str = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
        ep_num = "?"
        event_label = "配信予定"

    # イベントタイトル
    event_title = f"{title_native} {event_label}"

    # ディスクリプション
    genres = anime.get("genres", [])
    score = anime.get("averageScore")
    platforms = sorted({
        ep.get("site", "")
        for ep in anime.get("streamingEpisodes", [])
        if ep.get("site")
    })
    platform_str = ", ".join(platforms) if platforms else "不明"
    site_url = anime.get("siteUrl", "")

    desc_parts = []
    if title_en:
        desc_parts.append(f"英語タイトル: {title_en}")
    if genres:
        desc_parts.append(f"ジャンル: {', '.join(genres[:5])}")
    if score:
        desc_parts.append(f"スコア: {score}/100")
    desc_parts.append(f"配信プラットフォーム: {platform_str}")
    if site_url:
        desc_parts.append(f"AniList: {site_url}")
    description = "\n".join(desc_parts)

    return {
        "title": event_title,
        "description": description,
        "start_datetime": start_datetime_str,
        "end_datetime": end_datetime_str,
        "event_type": "anime",
    }


# ─────────────────────────────────────────────────
# AniList 取得 & DB 保存
# ─────────────────────────────────────────────────

async def fetch_anilist_anime() -> list:
    """
    AniList GraphQL API から今期放送中のアニメを非同期で取得する。

    Returns:
        フィルタ済みの raw アニメデータリスト
    """
    import aiohttp

    vars_ = _current_season_vars()
    timeout = aiohttp.ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                ANILIST_GRAPHQL_URL,
                json={"query": ANILIST_QUERY, "variables": vars_},
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    logger.error(f"AniList API returned status {response.status}")
                    return []
                data = await response.json()

        media_list = (
            data.get("data", {}).get("Page", {}).get("media", [])
        )
        filtered = [m for m in media_list if not _should_filter(m)]
        return filtered

    except Exception as exc:
        logger.error(f"AniList fetch failed: {exc}")
        return []


def save_events_to_db(anime_list: list) -> list:
    """
    アニメリストをカレンダーイベントに変換して DB に保存する。

    Args:
        anime_list: AniList から取得した raw アニメ辞書のリスト

    Returns:
        保存したイベント辞書のリスト（id 付き）
    """
    from modules.db import DatabaseManager

    db = DatabaseManager(db_path=str(project_root / "db.sqlite3"))
    saved = []

    for anime in anime_list:
        event_data = _build_event_data(anime)
        event_id = db.save_calendar_event(event_data)
        if event_id is not None:
            event_data["id"] = event_id
            saved.append(event_data)

    db.close_connections()
    return saved


# ─────────────────────────────────────────────────
# イベント一覧表示
# ─────────────────────────────────────────────────

def list_saved_events() -> list:
    """
    pending_calendar_events から未同期イベントを取得して返す。

    Returns:
        イベント辞書のリスト
    """
    from modules.db import DatabaseManager

    db = DatabaseManager(db_path=str(project_root / "db.sqlite3"))
    events = db.get_pending_calendar_events(synced=False)
    db.close_connections()
    return events


def print_events(events: list):
    """イベント一覧を整形して出力する"""
    if not events:
        print("  (保存済みイベントはありません)")
        return

    for ev in events:
        synced_mark = "[同期済]" if ev.get("synced") else "[未同期]"
        ev_type = ev.get("event_type", "unknown")
        type_icon = "TV" if ev_type == "anime" else "Book"
        print(
            f"  ID={ev['id']:>4}  {synced_mark}  [{type_icon}]  "
            f"{ev['start_datetime'][:16]}  {ev['title']}"
        )
        if ev.get("description"):
            # 1行目だけ表示
            first_line = ev["description"].split("\n")[0]
            print(f"             {first_line}")


# ─────────────────────────────────────────────────
# Google Calendar 同期（credentials.json が存在する場合のみ）
# ─────────────────────────────────────────────────

def sync_to_google_calendar(events: list) -> int:
    """
    未同期イベントを Google Calendar API に登録する。

    credentials.json がない場合はスキップして 0 を返す。

    Args:
        events: get_pending_calendar_events() が返すイベントリスト

    Returns:
        同期に成功したイベント数
    """
    if not CREDENTIALS_PATH.exists():
        print("  [スキップ] credentials.json が見つかりません。")
        print(f"    パス: {CREDENTIALS_PATH}")
        print("  Google Calendar 同期をスキップします。")
        return 0

    # google-auth ライブラリを遅延インポート（インストール済みの環境のみ）
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError as exc:
        print(f"  [スキップ] Google API ライブラリが未インストールです: {exc}")
        print("    pip install google-auth google-auth-oauthlib google-api-python-client")
        return 0

    # 認証トークンの取得または更新
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), CALENDAR_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as exc:
                print(f"  [エラー] トークン更新失敗: {exc}")
                return 0
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), CALENDAR_SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(str(TOKEN_PATH), "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    from modules.db import DatabaseManager

    db = DatabaseManager(db_path=str(project_root / "db.sqlite3"))
    service = build("calendar", "v3", credentials=creds)
    synced_count = 0

    for ev in events:
        try:
            google_event = {
                "summary": ev["title"],
                "description": ev.get("description", ""),
                "start": {
                    "dateTime": ev["start_datetime"],
                    "timeZone": "Asia/Tokyo",
                },
                "end": {
                    "dateTime": ev.get("end_datetime") or ev["start_datetime"],
                    "timeZone": "Asia/Tokyo",
                },
            }

            created = (
                service.events()
                .insert(calendarId="primary", body=google_event)
                .execute()
            )
            google_event_id = created.get("id", "")
            db.mark_calendar_event_synced(ev["id"], google_event_id)
            synced_count += 1
            print(f"  [OK] 登録: {ev['title']} => {created.get('htmlLink', '')}")

        except HttpError as exc:
            print(f"  [エラー] Google Calendar API エラー ({ev['title']}): {exc}")
        except Exception as exc:
            print(f"  [エラー] 予期しないエラー ({ev['title']}): {exc}")

    db.close_connections()
    return synced_count


# ─────────────────────────────────────────────────
# メイン処理
# ─────────────────────────────────────────────────

async def main_async(args):
    run_save = args.save
    run_list = args.list
    run_sync = args.sync

    # デフォルト: フラグなしの場合は --save --list を実行
    if not run_save and not run_list and not run_sync:
        run_save = True
        run_list = True

    print("\n" + "=" * 60)
    print("  Phase 4: Google Calendar 開発モード テスト")
    print(f"  実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ── SAVE ──────────────────────────────────────
    if run_save:
        print_section("AniList API からデータ取得 & DB 保存")
        print("  AniList GraphQL API に接続中...")
        anime_list = await fetch_anilist_anime()

        if not anime_list:
            print("  [警告] データを取得できませんでした。ネットワーク接続を確認してください。")
        else:
            print(f"  取得完了: {len(anime_list)} 件のアニメ（NGフィルタ済み）")
            saved = save_events_to_db(anime_list)
            print(f"  DB 保存完了: {len(saved)} 件のカレンダーイベントを保存しました")
            for ev in saved[:5]:
                print(f"    - [{ev['id']}] {ev['title']} ({ev['start_datetime'][:16]})")
            if len(saved) > 5:
                print(f"    ... 他 {len(saved) - 5} 件")

    # ── LIST ──────────────────────────────────────
    if run_list:
        print_section("保存済みカレンダーイベント一覧（未同期）")
        events = list_saved_events()
        print(f"  未同期イベント数: {len(events)} 件")
        print()
        print_events(events)

    # ── SYNC ──────────────────────────────────────
    if run_sync:
        print_section("Google Calendar への同期")
        if not CREDENTIALS_PATH.exists():
            print(f"  credentials.json が見つかりません: {CREDENTIALS_PATH}")
            print("  --sync フラグは credentials.json が存在する場合のみ有効です。")
        else:
            pending = list_saved_events()
            if not pending:
                print("  同期対象のイベントがありません。先に --save を実行してください。")
            else:
                print(f"  同期対象: {len(pending)} 件")
                synced = sync_to_google_calendar(pending)
                print(f"  同期完了: {synced} 件を Google Calendar に登録しました")

    print("\n" + "=" * 60)
    print("  テスト完了")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 4: Google Calendar 開発モード テスト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python -X utf8 scripts/test_phase4_calendar.py           # --save --list を実行
  python -X utf8 scripts/test_phase4_calendar.py --save    # AniListから取得してDBに保存
  python -X utf8 scripts/test_phase4_calendar.py --list    # 保存済みイベント一覧を表示
  python -X utf8 scripts/test_phase4_calendar.py --sync    # Google Calendarに同期
        """,
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="AniList API からアニメを取得して pending_calendar_events に保存",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="pending_calendar_events の未同期イベントを一覧表示",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="credentials.json が存在する場合、Google Calendar API に同期する",
    )
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
