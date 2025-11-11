#!/usr/bin/env python3
"""
Demo Database Initializer for Web UI Testing
This script creates sample data for testing the web interface.
"""

import sqlite3
import json
from datetime import datetime, timedelta
import secrets


def create_database():
    """Create the SQLite database with sample data"""

    # Connect to database
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    # Create tables
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            title_kana TEXT,
            title_en TEXT,
            type TEXT CHECK(type IN ('anime','manga')),
            official_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.execute(
        """
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(work_id, release_type, number, platform, release_date),
            FOREIGN KEY (work_id) REFERENCES works (id)
        )
    """
    )

    # Sample works data
    sample_works = [
        # Anime
        ("鬼滅の刃", "きめつのやいば", "Demon Slayer", "anime", "https://kimetsu.com"),
        (
            "進撃の巨人",
            "しんげきのきょじん",
            "Attack on Titan",
            "anime",
            "https://shingeki.tv",
        ),
        (
            "呪術廻戦",
            "じゅじゅつかいせん",
            "Jujutsu Kaisen",
            "anime",
            "https://jujutsukaisen.jp",
        ),
        (
            "ワンピース",
            "わんぴーす",
            "One Piece",
            "anime",
            "https://www.toei-anim.co.jp/tv/onep/",
        ),
        (
            "僕のヒーローアカデミア",
            "ぼくのひーろーあかでみあ",
            "My Hero Academia",
            "anime",
            "https://heroaca.com",
        ),
        # Manga
        ("ワンピース", "わんぴーす", "One Piece", "manga", "https://one-piece.com"),
        ("鬼滅の刃", "きめつのやいば", "Demon Slayer", "manga", "https://kimetsu.com"),
        (
            "呪術廻戦",
            "じゅじゅつかいせん",
            "Jujutsu Kaisen",
            "manga",
            "https://jujutsukaisen.jp",
        ),
        (
            "チェンソーマン",
            "ちぇんそーまん",
            "Chainsaw Man",
            "manga",
            "https://chainsawman.dog",
        ),
        (
            "スパイファミリー",
            "すぱいふぁみりー",
            "SPY×FAMILY",
            "manga",
            "https://spy-family.net",
        ),
    ]

    # Insert sample works
    cursor.executemany(
        """
        INSERT OR IGNORE INTO works (title, title_kana, title_en, type, official_url)
        VALUES (?, ?, ?, ?, ?)
    """,
        sample_works,
    )

    # Get work IDs
    cursor.execute("SELECT id, title, type FROM works")
    works = cursor.fetchall()

    # Sample platforms
    anime_platforms = [
        "Netflix",
        "Amazon Prime Video",
        "Crunchyroll",
        "Funimation",
        "dアニメストア",
        "ABEMA",
    ]
    manga_platforms = [
        "BookWalker",
        "Kindle",
        "楽天Kobo",
        "ComicWalker",
        "マガポケ",
        "ジャンプ+",
    ]

    # Generate sample releases
    releases = []
    today = datetime.now()

    for work_id, title, work_type in works:
        platform_list = anime_platforms if work_type == "anime" else manga_platforms

        # Generate releases for the past month and next month
        for days_offset in range(-30, 31, secrets.randbelow(1, 7)):
            release_date = today + timedelta(days=days_offset)

            # Random chance of having a release on this day
            if secrets.SystemRandom().random() < 0.3:  # 30% chance
                platform = secrets.choice(platform_list)
                release_type = "episode" if work_type == "anime" else "volume"

                # Generate episode/volume number
                if release_type == "episode":
                    number = str(secrets.randbelow(1, 24))
                else:
                    number = str(secrets.randbelow(1, 30))

                # Notification status (70% notified for past releases)
                notified = (
                    1
                    if (days_offset < 0 and secrets.SystemRandom().random() < 0.7)
                    else 0
                )

                releases.append(
                    (
                        work_id,
                        release_type,
                        number,
                        platform,
                        release_date.strftime("%Y-%m-%d"),
                        "demo_source",
                        f"https://example.com/{work_type}/{work_id}/{number}",
                        notified,
                    )
                )

    # Insert releases
    cursor.executemany(
        """
        INSERT OR IGNORE INTO releases
        (work_id, release_type, number, platform, release_date, source, source_url, notified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        releases,
    )

    # Commit and close
    conn.commit()
    conn.close()

    print(f"✅ データベース作成完了: {len(sample_works)}作品、{len(releases)}リリースを追加しました")


def create_sample_config():
    """Create a sample configuration file"""

    config = {
        "ng_keywords": ["エロ", "R18", "成人向け", "BL", "百合", "ボーイズラブ"],
        "notification_email": "example@gmail.com",
        "check_interval_hours": 24,
        "enabled_sources": {
            "anilist": True,
            "shobo_calendar": True,
            "bookwalker_rss": True,
            "mangapocket_rss": True,
        },
    }

    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print("✅ サンプル設定ファイル作成完了: config.json")


def create_sample_log():
    """Create a sample log file"""
    import os

    os.makedirs("logs", exist_ok=True)

    sample_logs = [
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - システム開始",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - データベース接続成功",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - 設定ファイル読み込み完了",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - AniList APIからデータ取得開始",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - 15件の新しいリリースを発見",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - WARNING - 一部のRSSフィードが取得できませんでした",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - 通知メール送信: 3件",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - Googleカレンダー更新完了",
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - 実行完了",
    ]

    with open("logs/system.log", "w", encoding="utf-8") as f:
        for log_entry in sample_logs:
            f.write(log_entry + "\n")

    print("✅ サンプルログファイル作成完了: logs/system.log")


def main():
    """Main function"""
    print("=" * 60)
    print("デモデータベース初期化スクリプト")
    print("=" * 60)
    print()

    try:
        create_database()
        create_sample_config()
        create_sample_log()

        print()
        print("🎉 初期化完了！")
        print()
        print("Web UIを起動してください：")
        print("  python3 start_web_ui.py")
        print()
        print("ブラウザで以下にアクセス：")
        print("  http://localhost:5000")
        print()

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
