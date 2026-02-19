"""
データベース操作モジュール（型ヒント付き）
"""

import hashlib
import logging
import sqlite3

logger = logging.getLogger(__name__)
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union


def get_connection(db_path: str = "data/db.sqlite3") -> sqlite3.Connection:
    """
    データベース接続を取得

    Args:
        db_path: データベースファイルのパス

    Returns:
        sqlite3.Connection: データベース接続オブジェクト
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = "data/db.sqlite3") -> None:
    """
    データベース初期化

    Args:
        db_path: データベースファイルのパス
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # worksテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            title_kana TEXT,
            title_en TEXT,
            type TEXT CHECK(type IN ('anime','manga')),
            official_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # releasesテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS releases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_id INTEGER NOT NULL,
            release_type TEXT CHECK(release_type IN ('episode','volume')),
            number TEXT,
            platform TEXT,
            release_date DATE,
            source TEXT,
            source_url TEXT,
            notified INTEGER DEFAULT 0,
            calendar_synced INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(work_id, release_type, number, platform, release_date),
            FOREIGN KEY(work_id) REFERENCES works(id)
        )
    """)

    # calendar_eventsテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            release_id INTEGER NOT NULL,
            event_id TEXT NOT NULL UNIQUE,
            calendar_id TEXT DEFAULT 'primary',
            synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(release_id) REFERENCES releases(id)
        )
    """)

    conn.commit()
    conn.close()
    logger.info("データベース初期化完了")


def generate_work_hash(title: str, work_type: str) -> str:
    """
    作品のハッシュIDを生成

    Args:
        title: 作品タイトル
        work_type: 作品タイプ（anime/manga）

    Returns:
        str: SHA256ハッシュ値（先頭16文字）
    """
    return hashlib.sha256(f"{title}:{work_type}".encode()).hexdigest()[:16]


def insert_work(
    title: str,
    work_type: str,
    title_kana: Optional[str] = None,
    title_en: Optional[str] = None,
    official_url: Optional[str] = None,
    db_path: str = "data/db.sqlite3",
) -> int:
    """
    作品を登録（既存の場合はIDを返す）

    Args:
        title: 作品タイトル
        work_type: 作品タイプ（anime/manga）
        title_kana: タイトル読み仮名
        title_en: 英語タイトル
        official_url: 公式URL
        db_path: データベースファイルのパス

    Returns:
        int: 作品ID
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 既存チェック
    cursor.execute("SELECT id FROM works WHERE title = ? AND type = ?", (title, work_type))
    row = cursor.fetchone()

    if row:
        work_id = int(row["id"])
    else:
        cursor.execute(
            """INSERT INTO works (title, title_kana, title_en, type, official_url)
               VALUES (?, ?, ?, ?, ?)""",
            (title, title_kana, title_en, work_type, official_url),
        )
        conn.commit()
        work_id = cursor.lastrowid
        logger.info(f"作品登録: {title} (ID: {work_id})")

    conn.close()
    return work_id


def insert_release(
    work_id: int,
    release_type: str,
    release_date: Union[str, date, datetime],
    number: Optional[str] = None,
    platform: Optional[str] = None,
    source: Optional[str] = None,
    source_url: Optional[str] = None,
    db_path: str = "data/db.sqlite3",
) -> Optional[int]:
    """
    リリース情報を登録

    Args:
        work_id: 作品ID
        release_type: リリースタイプ（episode/volume）
        release_date: リリース日
        number: 話数/巻数
        platform: プラットフォーム
        source: 情報ソース
        source_url: ソースURL
        db_path: データベースファイルのパス

    Returns:
        Optional[int]: リリースID（重複の場合はNone）
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 日付を文字列に変換
    if isinstance(release_date, (date, datetime)):
        release_date_str = release_date.strftime("%Y-%m-%d")
    else:
        release_date_str = release_date

    try:
        cursor.execute(
            """INSERT INTO releases
               (work_id, release_type, number, platform, release_date, source, source_url)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (work_id, release_type, number, platform, release_date_str, source, source_url),
        )
        conn.commit()
        release_id = cursor.lastrowid
        logger.info(f"リリース登録: work_id={work_id}, {release_type} {number}")
        conn.close()
        return release_id
    except sqlite3.IntegrityError:
        logger.debug(f"リリース重複: work_id={work_id}, {release_type} {number}")
        conn.close()
        return None


def get_unnotified_releases(db_path: str = "data/db.sqlite3") -> List[Dict[str, Any]]:
    """
    未通知のリリース情報を取得

    Args:
        db_path: データベースファイルのパス

    Returns:
        List[Dict[str, Any]]: 未通知リリース情報のリスト
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            r.id as release_id,
            r.work_id,
            w.title,
            w.type as work_type,
            r.release_type,
            r.number,
            r.platform,
            r.release_date,
            r.source,
            r.source_url
        FROM releases r
        JOIN works w ON r.work_id = w.id
        WHERE r.notified = 0
        ORDER BY r.release_date ASC
    """)

    releases: List[Dict[str, Any]] = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return releases


def mark_as_notified(release_id: int, db_path: str = "data/db.sqlite3") -> None:
    """
    通知済みとしてマーク

    Args:
        release_id: リリースID
        db_path: データベースファイルのパス
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("UPDATE releases SET notified = 1 WHERE id = ?", (release_id,))
    conn.commit()
    conn.close()
    logger.info(f"通知済みマーク: release_id={release_id}")


def get_unsynced_calendar_releases(db_path: str = "data/db.sqlite3") -> List[Dict[str, Any]]:
    """
    カレンダー未同期のリリース情報を取得

    Args:
        db_path: データベースファイルのパス

    Returns:
        List[Dict[str, Any]]: 未同期リリース情報のリスト
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            r.id as release_id,
            r.work_id,
            w.title,
            w.type as work_type,
            r.release_type,
            r.number,
            r.platform,
            r.release_date,
            r.source
        FROM releases r
        JOIN works w ON r.work_id = w.id
        WHERE r.calendar_synced = 0
        ORDER BY r.release_date ASC
    """)

    releases: List[Dict[str, Any]] = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return releases


def mark_calendar_synced(
    release_id: int, event_id: str, calendar_id: str = "primary", db_path: str = "data/db.sqlite3"
) -> None:
    """
    カレンダー同期済みとしてマーク

    Args:
        release_id: リリースID
        event_id: GoogleカレンダーのイベントID
        calendar_id: カレンダーID
        db_path: データベースファイルのパス
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # releasesテーブルを更新
    cursor.execute("UPDATE releases SET calendar_synced = 1 WHERE id = ?", (release_id,))

    # calendar_eventsテーブルに記録
    try:
        cursor.execute(
            """INSERT INTO calendar_events (release_id, event_id, calendar_id)
               VALUES (?, ?, ?)""",
            (release_id, event_id, calendar_id),
        )
    except sqlite3.IntegrityError:
        logger.warning(f"カレンダーイベント重複: event_id={event_id}")

    conn.commit()
    conn.close()
    logger.info(f"カレンダー同期済みマーク: release_id={release_id}, event_id={event_id}")


def get_all_works(db_path: str = "data/db.sqlite3") -> List[Dict[str, Any]]:
    """
    全作品を取得

    Args:
        db_path: データベースファイルのパス

    Returns:
        List[Dict[str, Any]]: 作品情報のリスト
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM works ORDER BY created_at DESC")
    works: List[Dict[str, Any]] = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return works


def get_work_by_id(work_id: int, db_path: str = "data/db.sqlite3") -> Optional[Dict[str, Any]]:
    """
    IDで作品を取得

    Args:
        work_id: 作品ID
        db_path: データベースファイルのパス

    Returns:
        Optional[Dict[str, Any]]: 作品情報（存在しない場合はNone）
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM works WHERE id = ?", (work_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_releases_by_work(work_id: int, db_path: str = "data/db.sqlite3") -> List[Dict[str, Any]]:
    """
    作品のリリース情報を取得

    Args:
        work_id: 作品ID
        db_path: データベースファイルのパス

    Returns:
        List[Dict[str, Any]]: リリース情報のリスト
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM releases WHERE work_id = ? ORDER BY release_date DESC", (work_id,)
    )
    releases: List[Dict[str, Any]] = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return releases


def get_statistics(db_path: str = "data/db.sqlite3") -> Dict[str, Any]:
    """
    統計情報を取得

    Args:
        db_path: データベースファイルのパス

    Returns:
        Dict[str, Any]: 統計情報
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    stats: Dict[str, Any] = {}

    # 作品数
    cursor.execute("SELECT COUNT(*) as count FROM works")
    stats["total_works"] = cursor.fetchone()["count"]

    # アニメ作品数
    cursor.execute("SELECT COUNT(*) as count FROM works WHERE type = 'anime'")
    stats["anime_works"] = cursor.fetchone()["count"]

    # マンガ作品数
    cursor.execute("SELECT COUNT(*) as count FROM works WHERE type = 'manga'")
    stats["manga_works"] = cursor.fetchone()["count"]

    # リリース総数
    cursor.execute("SELECT COUNT(*) as count FROM releases")
    stats["total_releases"] = cursor.fetchone()["count"]

    # 未通知リリース数
    cursor.execute("SELECT COUNT(*) as count FROM releases WHERE notified = 0")
    stats["unnotified_releases"] = cursor.fetchone()["count"]

    # カレンダー未同期リリース数
    cursor.execute("SELECT COUNT(*) as count FROM releases WHERE calendar_synced = 0")
    stats["unsynced_calendar_releases"] = cursor.fetchone()["count"]

    conn.close()

    return stats
