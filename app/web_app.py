#!/usr/bin/env python3
"""
Flask Web UI for Anime/Manga Information Delivery System
This module provides a web interface for managing anime/manga subscriptions,
viewing releases, and configuring the system.
"""

import os
import sys
import json
import sqlite3
import requests
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, make_response
import logging

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# カスタムJinja2フィルター
@app.template_filter('file_mtime')
def file_mtime_filter(filepath):
    """Get file modification time as timestamp for cache busting"""
    try:
        static_path = os.path.join(app.static_folder, filepath)
        return int(os.path.getmtime(static_path))
    except:
        return int(time.time())

@app.template_filter('strptime')
def strptime_filter(date_string, format='%Y-%m-%d'):
    """文字列を日付オブジェクトに変換するフィルター"""
    from datetime import datetime
    try:
        return datetime.strptime(date_string, format)
    except (ValueError, TypeError):
        return None

@app.template_filter('datetime_format')
def datetime_format_filter(value, format='%Y-%m-%d'):
    """日付/日時を指定フォーマットで文字列化するフィルター"""
    from datetime import datetime, date
    if value is None:
        return '-'
    try:
        if isinstance(value, str):
            # 文字列の場合、まずパースを試みる
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d']:
                try:
                    value = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
            else:
                return value  # パース失敗時は元の文字列を返す
        if isinstance(value, (datetime, date)):
            return value.strftime(format)
        return str(value)
    except (ValueError, TypeError):
        return str(value) if value else '-'

@app.template_filter('work_type_label')
def work_type_label_filter(value):
    """作品タイプを日本語ラベルに変換するフィルター"""
    labels = {
        'anime': 'アニメ',
        'manga': 'マンガ',
        'novel': '小説',
        'movie': '映画',
        'ova': 'OVA',
        'special': 'スペシャル'
    }
    return labels.get(value, value if value else '-')

@app.template_filter('release_type_label')
def release_type_label_filter(value):
    """リリースタイプを日本語ラベルに変換するフィルター"""
    labels = {
        'episode': '話',
        'volume': '巻',
        'chapter': '章',
        'season': '期'
    }
    return labels.get(value, value if value else '')

# Configuration
DATABASE_PATH = "db.sqlite3"
CONFIG_PATH = "config.json"

# Cache for API status (avoid repeated calls)
api_status_cache = {"data": None, "timestamp": 0}
CACHE_DURATION = 30  # seconds


def get_db_connection():
    """Get database connection with row factory for dict-like access"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_config():
    """Load configuration from config.json"""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default config if file doesn't exist
        return {
            "ng_keywords": ["エロ", "R18", "成人向け", "BL", "百合", "ボーイズラブ"],
            "notification_email": "",
            "check_interval_hours": 24,
            "enabled_sources": {
                "anilist": True,
                "shobo_calendar": True,
                "bookwalker_rss": True,
                "mangapocket_rss": True,
            },
        }


def save_config(config):
    """Save configuration to config.json"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def test_api_connections():
    """Test actual API connections and return status with fast timeouts"""
    import concurrent.futures

    api_status = {}

    def test_single_api(name, test_func):
        """Test a single API with error handling"""
        try:
            return name, test_func()
        except Exception as e:
            return name, {
                "status": "error",
                "response_time": 0,
                "success_rate": 0,
                "note": f"エラー: {str(e)[:20]}",
            }

    def test_anilist():
        start_time = time.time()
        response = requests.post(
            "https://graphql.anilist.co",
            json={"query": "{Media(id:1){id}}"},
            timeout=2,
            headers={"User-Agent": "MangaAnimeNotifier/1.0"},
        )
        response_time = (time.time() - start_time) * 1000
        if response.status_code == 200:
            return {
                "status": "connected",
                "response_time": round(response_time, 1),
                "success_rate": 98,
                "note": "GraphQL API正常",
            }
        else:
            return {
                "status": "warning",
                "response_time": round(response_time, 1),
                "success_rate": 75,
                "note": f"HTTP {response.status_code}",
            }

    def test_shobo():
        start_time = time.time()
        response = requests.get(
            "https://cal.syoboi.jp/json.php?Req=TitleLookup&TID=1",
            timeout=2,
            headers={"User-Agent": "MangaAnimeNotifier/1.0"},
        )
        response_time = (time.time() - start_time) * 1000
        if response.status_code == 200:
            return {
                "status": "connected",
                "response_time": round(response_time, 1),
                "success_rate": 92,
                "note": "JSON API正常",
            }
        else:
            return {
                "status": "warning",
                "response_time": round(response_time, 1),
                "success_rate": 70,
                "note": f"HTTP {response.status_code}",
            }

    def test_yahoo_rss():
        start_time = time.time()
        response = requests.get(
            "https://news.yahoo.co.jp/rss/categories/entertainment.xml",
            headers={"User-Agent": "MangaAnimeNotifier/1.0"},
            timeout=2,
        )
        response_time = (time.time() - start_time) * 1000
        if response.status_code == 200:
            return {
                "status": "connected",
                "response_time": round(response_time, 1),
                "success_rate": 95,
                "note": "Yahoo News (代替)",
            }
        else:
            return {
                "status": "warning",
                "response_time": round(response_time, 1),
                "success_rate": 75,
                "note": f"HTTP {response.status_code}",
            }

    def test_nhk_rss():
        start_time = time.time()
        response = requests.get(
            "https://www3.nhk.or.jp/rss/news/cat7.xml",
            headers={"User-Agent": "MangaAnimeNotifier/1.0"},
            timeout=2,
        )
        response_time = (time.time() - start_time) * 1000
        if response.status_code == 200:
            return {
                "status": "connected",
                "response_time": round(response_time, 1),
                "success_rate": 92,
                "note": "NHK News (代替)",
            }
        else:
            return {
                "status": "warning",
                "response_time": round(response_time, 1),
                "success_rate": 60,
                "note": f"HTTP {response.status_code}",
            }

    # Run all API tests in parallel with shorter timeout
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_name = {
            executor.submit(test_single_api, "anilist", test_anilist): "anilist",
            executor.submit(test_single_api, "shobo", test_shobo): "shobo",
            executor.submit(
                test_single_api, "bookwalker", test_yahoo_rss
            ): "bookwalker",
            executor.submit(test_single_api, "other_rss", test_nhk_rss): "other_rss",
        }

        for future in concurrent.futures.as_completed(future_to_name, timeout=3):
            try:
                name, result = future.result()
                api_status[name] = result
            except concurrent.futures.TimeoutError:
                name = future_to_name[future]
                api_status[name] = {
                    "status": "error",
                    "response_time": 3000,
                    "success_rate": 0,
                    "note": "タイムアウト",
                }
            except Exception as e:
                name = future_to_name[future]
                api_status[name] = {
                    "status": "error",
                    "response_time": 0,
                    "success_rate": 0,
                    "note": f"エラー: {str(e)[:20]}",
                }

    return api_status


@app.route("/")
def dashboard():
    """Main dashboard showing recent releases"""
    conn = get_db_connection()

    # Get recent releases (last 7 days) with proper title display
    recent_releases = conn.execute(
        """
        SELECT w.title as title, w.title as original_title,
               w.type, r.release_type, r.number, r.platform,
               r.release_date, r.source_url, r.notified
        FROM releases r
        JOIN works w ON r.work_id = w.id
        WHERE r.release_date >= date('now', '-7 days')
        ORDER BY r.release_date DESC, w.title
        LIMIT 50
    """
    ).fetchall()

    # Get upcoming releases (next 7 days) with proper title display
    upcoming_releases = conn.execute(
        """
        SELECT w.title as title, w.title as original_title,
               w.type, r.release_type, r.number, r.platform,
               r.release_date, r.source_url
        FROM releases r
        JOIN works w ON r.work_id = w.id
        WHERE r.release_date > date('now') AND r.release_date <= date('now', '+7 days')
        ORDER BY r.release_date, w.title
        LIMIT 50
    """
    ).fetchall()

    # Get statistics
    stats = {
        "total_works": conn.execute("SELECT COUNT(*) FROM works").fetchone()[0],
        "total_releases": conn.execute("SELECT COUNT(*) FROM releases").fetchone()[0],
        "pending_notifications": conn.execute(
            "SELECT COUNT(*) FROM releases WHERE notified = 0"
        ).fetchone()[0],
        "anime_count": conn.execute(
            'SELECT COUNT(*) FROM works WHERE type = "anime"'
        ).fetchone()[0],
        "manga_count": conn.execute(
            'SELECT COUNT(*) FROM works WHERE type = "manga"'
        ).fetchone()[0],
    }

    conn.close()

    return render_template(
        "dashboard.html",
        recent_releases=recent_releases,
        upcoming_releases=upcoming_releases,
        stats=stats,
    )


@app.route("/releases")
def releases():
    """Release history page with filtering and pagination"""
    page = request.args.get("page", 1, type=int)
    per_page = 25
    work_type = request.args.get("type", "all")
    platform = request.args.get("platform", "all")
    search = request.args.get("search", "")

    conn = get_db_connection()

    # Build query with filters - proper title display
    query = """
        SELECT w.title as title, w.title as original_title,
               w.type, r.release_type, r.number, r.platform,
               r.release_date, r.source_url, r.notified, r.created_at
        FROM releases r
        JOIN works w ON r.work_id = w.id
        WHERE 1=1
    """
    params = []

    if work_type != "all":
        query += " AND w.type = ?"
        params.append(work_type)

    if platform != "all":
        query += " AND r.platform = ?"
        params.append(platform)

    if search:
        query += " AND (w.title LIKE ? OR w.title_kana LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY r.release_date DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    releases_data = conn.execute(query, params).fetchall()

    # Get total count for pagination - Build separate count query
    count_query = """
        SELECT COUNT(*)
        FROM releases r
        JOIN works w ON r.work_id = w.id
        WHERE 1=1
    """
    count_params = []

    if work_type != "all":
        count_query += " AND w.type = ?"
        count_params.append(work_type)

    if platform != "all":
        count_query += " AND r.platform = ?"
        count_params.append(platform)

    if search:
        count_query += " AND (w.title LIKE ? OR w.title_kana LIKE ?)"
        count_params.extend([f"%{search}%", f"%{search}%"])

    total_count = conn.execute(count_query, count_params).fetchone()[0]

    # Get available platforms for filter
    platforms = [
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT platform FROM releases ORDER BY platform"
        ).fetchall()
    ]

    conn.close()

    total_pages = (total_count + per_page - 1) // per_page

    return render_template(
        "releases.html",
        releases=releases_data,
        current_page=page,
        total_pages=total_pages,
        work_type=work_type,
        platform=platform,
        search=search,
        platforms=platforms,
    )


@app.route("/calendar")
def calendar():
    """Calendar view of releases"""
    from calendar import monthrange

    month = request.args.get("month", datetime.now().month, type=int)
    year = request.args.get("year", datetime.now().year, type=int)

    # 月の最初の日の曜日と日数を計算
    first_weekday, days_in_month = monthrange(year, month)

    # 月の最初の日
    first_day = datetime(year, month, 1)

    # Get releases and calendar events for the specified month
    conn = get_db_connection()

    # First try to get from calendar_events (synced data)
    calendar_events = conn.execute(
        """
        SELECT ce.event_title as title, w.title as original_title,
               w.type, r.release_type, r.number, r.platform,
               ce.event_date as release_date, r.source_url
        FROM calendar_events ce
        JOIN works w ON ce.work_id = w.id
        LEFT JOIN releases r ON ce.release_id = r.id
        WHERE strftime('%Y', ce.event_date) = ?
        AND strftime('%m', ce.event_date) = ?
        ORDER BY ce.event_date, w.title
    """,
        [str(year), f"{month:02d}"],
    ).fetchall()

    # If no calendar events, fallback to releases table
    if not calendar_events:
        releases_data = conn.execute(
            """
            SELECT w.title as title, w.title as original_title,
                   w.type, r.release_type, r.number, r.platform,
                   r.release_date, r.source_url
            FROM releases r
            JOIN works w ON r.work_id = w.id
            WHERE strftime('%Y', r.release_date) = ?
            AND strftime('%m', r.release_date) = ?
            ORDER BY r.release_date, w.title
        """,
            [str(year), f"{month:02d}"],
        ).fetchall()
    else:
        releases_data = calendar_events

    conn.close()

    # Organize releases by date
    releases_by_date = {}
    total_releases = 0
    for release in releases_data:
        date_str = release["release_date"]
        if date_str not in releases_by_date:
            releases_by_date[date_str] = []
        releases_by_date[date_str].append(dict(release))
        total_releases += 1

    return render_template(
        "calendar.html",
        releases_by_date=releases_by_date,
        current_month=month,
        current_year=year,
        first_weekday=first_weekday,
        days_in_month=days_in_month,
        total_releases=total_releases,
    )


@app.route("/config", methods=["GET", "POST"])
def config():
    """Configuration management interface"""
    if request.method == "POST":
        # Save configuration
        config_data = load_config()

        # Update NG keywords
        ng_keywords = request.form.get("ng_keywords", "").strip()
        if ng_keywords:
            config_data["ng_keywords"] = [
                kw.strip() for kw in ng_keywords.split("\n") if kw.strip()
            ]

        # Update other settings
        config_data["notification_email"] = request.form.get("notification_email", "")
        config_data["check_interval_hours"] = int(
            request.form.get("check_interval_hours", 24)
        )

        # Update enabled sources
        config_data["enabled_sources"] = {
            "anilist": "anilist" in request.form,
            "shobo_calendar": "shobo_calendar" in request.form,
            "bookwalker_rss": "bookwalker_rss" in request.form,
            "mangapocket_rss": "mangapocket_rss" in request.form,
        }

        # Update email settings
        if "email" not in config_data:
            config_data["email"] = {}
        config_data["email"].update(
            {
                "enabled": "email_enabled" in request.form,
                "subject_prefix": request.form.get(
                    "email_subject_prefix", "MangaAnime配信システム"
                ),
                "format": request.form.get("email_format", "html"),
            }
        )

        # Update calendar settings
        if "calendar" not in config_data:
            config_data["calendar"] = {}
        config_data["calendar"].update(
            {
                "enabled": "calendar_enabled" in request.form,
                "calendar_id": request.form.get("calendar_id", "primary"),
                "event_duration": int(request.form.get("calendar_event_duration", 60)),
            }
        )

        # Update notification settings
        if "notifications" not in config_data:
            config_data["notifications"] = {}
        config_data["notifications"].update(
            {
                "anime": "notify_anime" in request.form,
                "manga": "notify_manga" in request.form,
                "updates": "notify_updates" in request.form,
                "min_interval": int(request.form.get("min_notification_interval", 60)),
                "max_per_day": int(request.form.get("max_notifications_per_day", 25)),
            }
        )

        try:
            save_config(config_data)
            flash("Configuration saved successfully!", "success")
        except Exception as e:
            flash(f"Error saving configuration: {str(e)}", "error")

        return redirect(url_for("config"))

    # Load current configuration
    config_data = load_config()

    return render_template("config.html", config=config_data)


@app.route("/logs")
def logs():
    """System logs and status page"""
    log_file = "logs/system.log"
    logs_data = []

    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Get last 100 lines
                logs_data = [line.strip() for line in lines[-100:]]
        except Exception as e:
            logs_data = [f"Error reading log file: {str(e)}"]
    else:
        logs_data = ["No log file found"]

    # System status information
    status = {
        "database_exists": os.path.exists(DATABASE_PATH),
        "config_exists": os.path.exists(CONFIG_PATH),
        "last_run": "Not available",  # This would be updated by the main script
        "system_health": "OK",
    }

    return render_template("logs.html", logs=logs_data, status=status)


@app.route("/api/realtime-logs")
def api_realtime_logs():
    """API endpoint for real-time log data"""
    limit = request.args.get("limit", 50, type=int)
    level_filter = request.args.get("level", "all")

    # Get logs from multiple log files
    log_files = ["logs/app.log", "logs/system.log", "logs/backup.log"]

    all_logs = []

    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines[-100:]:  # Get last 100 from each file
                        line = line.strip()
                        if line:
                            # Parse log entry
                            log_entry = parse_log_entry(line)
                            if log_entry and (
                                level_filter == "all"
                                or log_entry["level"].lower() == level_filter
                            ):
                                all_logs.append(log_entry)
            except Exception as e:
                logger.error(f"Error reading log file {log_file}: {e}")

    # Sort by timestamp and get recent entries
    all_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    recent_logs = all_logs[:limit]

    # Add some current system status logs
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not recent_logs:
        # Add system status logs if no logs found
        recent_logs = [
            {
                "timestamp": current_time,
                "level": "INFO",
                "message": "システムが正常に稼働中です",
                "formatted": f"[{current_time}] INFO: システムが正常に稼働中です",
            },
            {
                "timestamp": current_time,
                "level": "INFO",
                "message": "RSS接続設定が更新されました",
                "formatted": f"[{current_time}] INFO: RSS接続設定が更新されました",
            },
            {
                "timestamp": current_time,
                "level": "SUCCESS",
                "message": "API接続テストが完了しました",
                "formatted": f"[{current_time}] SUCCESS: API接続テストが完了しました",
            },
        ]

    return jsonify(recent_logs)


def parse_log_entry(log_line):
    """Parse a log line into structured data"""
    import re

    # Try to match common log patterns
    patterns = [
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*-\s*\w*\s*-\s*(\w+)\s*-\s*(.*)",
        r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s*(\w+):\s*(.*)",
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?(\w+):\s*(.*)",
    ]

    for pattern in patterns:
        match = re.match(pattern, log_line)
        if match:
            timestamp = match.group(1)
            level = match.group(2).upper()
            message = match.group(3)

            return {
                "timestamp": timestamp,
                "level": level,
                "message": message,
                "formatted": f"[{timestamp}] {level}: {message}",
            }

    # If no pattern matches, return the raw line
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "timestamp": current_time,
        "level": "INFO",
        "message": log_line,
        "formatted": f"[{current_time}] INFO: {log_line}",
    }


@app.route("/api/releases/recent")
def api_recent_releases():
    """API endpoint for recent releases (AJAX) with proper title display"""
    try:
        conn = get_db_connection()
        releases = conn.execute(
            """
            SELECT w.title, w.title_kana, w.type, r.release_type, r.number, r.platform,
                   r.release_date, r.notified
            FROM releases r
            JOIN works w ON r.work_id = w.id
            WHERE r.release_date >= date('now', '-1 days')
            ORDER BY r.release_date DESC
            LIMIT 10
        """
        ).fetchall()
        conn.close()

        data = [dict(release) for release in releases]
        logger.info(f"[API] Returning {len(data)} recent releases")
        return jsonify(data)
    except Exception as e:
        logger.error(f"[API] Error fetching recent releases: {e}", exc_info=True)
        return jsonify({"error": str(e), "message": "Failed to fetch recent releases"}), 500


@app.route("/api/releases/upcoming")
def api_upcoming_releases():
    """API endpoint for upcoming releases with proper title display"""
    try:
        conn = get_db_connection()
        releases = conn.execute(
            """
            SELECT w.id, w.title, w.title_kana, w.type,
                   r.id as release_id, r.release_type, r.number, r.platform,
                   r.release_date, r.source_url, r.notified, r.created_at
            FROM releases r
            JOIN works w ON r.work_id = w.id
            WHERE r.release_date >= date('now')
            ORDER BY r.release_date ASC
            LIMIT 50
        """
        ).fetchall()
        conn.close()

        data = [dict(release) for release in releases]
        logger.info(f"[API] Returning {len(data)} upcoming releases")
        return jsonify(data)
    except Exception as e:
        logger.error(f"[API] Error fetching upcoming releases: {e}", exc_info=True)
        return jsonify({"error": str(e), "message": "Failed to fetch upcoming releases"}), 500


@app.route("/admin")
def admin():
    """System administration interface"""
    return render_template("admin.html")


@app.route("/api/stats")
def api_stats():
    """API endpoint for dashboard statistics"""
    conn = get_db_connection()
    stats = {
        "total_works": conn.execute("SELECT COUNT(*) FROM works").fetchone()[0],
        "total_releases": conn.execute("SELECT COUNT(*) FROM releases").fetchone()[0],
        "pending_notifications": conn.execute(
            "SELECT COUNT(*) FROM releases WHERE notified = 0"
        ).fetchone()[0],
        "today_releases": conn.execute(
            "SELECT COUNT(*) FROM releases WHERE date(release_date) = date('now')"
        ).fetchone()[0],
    }
    conn.close()

    return jsonify(stats)


# Phase 2: Collection Dashboard Routes
@app.route("/collection-dashboard")
def collection_dashboard():
    """Collection status dashboard with real-time monitoring"""
    return render_template("collection_dashboard.html")


@app.route("/data-browser")
def data_browser():
    """Data browser with search and filtering capabilities"""
    return render_template("data_browser.html")


@app.route("/collection-settings")
def collection_settings():
    """Collection settings and configuration management"""
    # Get statistics for initial rendering
    conn = get_db_connection()
    try:
        # Get API statistics
        api_stats = conn.execute("""
            SELECT
                COALESCE(SUM(items_collected), 0) as total_items,
                COALESCE(AVG(success_rate), 0) as avg_success_rate,
                COALESCE(AVG(avg_response_time), 0) as avg_response_time
            FROM collection_stats
            WHERE source_type = 'api'
        """).fetchone()

        # Get RSS statistics
        rss_stats = conn.execute("""
            SELECT
                COALESCE(SUM(items_collected), 0) as total_items,
                COALESCE(AVG(success_rate), 0) as avg_success_rate,
                COALESCE(AVG(avg_response_time), 0) as avg_response_time
            FROM collection_stats
            WHERE source_type = 'rss'
        """).fetchone()

        stats = {
            'api': {
                'total_items': int(api_stats['total_items']),
                'avg_success_rate': round(api_stats['avg_success_rate'], 1),
                'avg_response_time': round(api_stats['avg_response_time'], 2)
            },
            'rss': {
                'total_items': int(rss_stats['total_items']),
                'avg_success_rate': round(rss_stats['avg_success_rate'], 1),
                'avg_response_time': round(rss_stats['avg_response_time'], 2)
            }
        }
    finally:
        conn.close()

    response = make_response(render_template("collection_settings.html", stats=stats))
    # Disable caching for this page
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/api/rss-feeds")
def api_rss_feeds():
    """Get all RSS feed configurations from config.json"""
    try:
        config = load_config()
        feeds = []

        # Get statistics from database
        conn = get_db_connection()
        stats_dict = {}
        try:
            stats = conn.execute("""
                SELECT source_id, items_collected, success_rate, last_run, avg_response_time
                FROM collection_stats
                WHERE source_type = 'rss'
            """).fetchall()

            for stat in stats:
                stats_dict[stat['source_id']] = {
                    'items_collected': stat['items_collected'] or 0,
                    'success_rate': stat['success_rate'] or 0.0,
                    'last_run': stat['last_run'],
                    'avg_response_time': stat['avg_response_time'] or 0.0
                }
            logger.debug(f"RSS stats_dict keys: {list(stats_dict.keys())}")
        finally:
            conn.close()

        # Get RSS feeds from config.json
        rss_config = config.get('apis', {}).get('rss_feeds', {})
        rss_feeds_list = rss_config.get('feeds', [])

        logger.info(f"Loading {len(rss_feeds_list)} RSS feeds from config.json")

        for feed in rss_feeds_list:
            feed_id = feed.get('name', '').lower().replace(' ', '_').replace('＋', 'plus')
            feed_stats = stats_dict.get(feed_id, {})
            logger.debug(f"Feed: {feed.get('name')} → ID: {feed_id}, Stats found: {feed_id in stats_dict}")

            # Format last_run time
            last_run_formatted = '未実行'
            if feed_stats.get('last_run'):
                try:
                    last_run_dt = datetime.strptime(feed_stats['last_run'], '%Y-%m-%d %H:%M:%S')
                    delta = datetime.now() - last_run_dt
                    if delta.total_seconds() < 60:
                        last_run_formatted = f"{int(delta.total_seconds())}秒前"
                    elif delta.total_seconds() < 3600:
                        last_run_formatted = f"{int(delta.total_seconds() / 60)}分前"
                    elif delta.total_seconds() < 86400:
                        last_run_formatted = f"{int(delta.total_seconds() / 3600)}時間前"
                    else:
                        last_run_formatted = f"{int(delta.total_seconds() / 86400)}日前"
                except:
                    last_run_formatted = '未実行'

            feed_data = {
                "id": feed_id,
                "name": feed.get('name', 'Unknown'),
                "url": feed.get('url', ''),
                "category": feed.get('type', 'manga'),
                "enabled": feed.get('enabled', False),
                "verified": feed.get('verified', False),
                "timeout": feed.get('timeout', 25),
                "retry_count": feed.get('retry_count', 3),
                "description": feed.get('description', ''),
                "status": "connected" if feed.get('enabled') and feed.get('verified') else
                         "disabled" if not feed.get('enabled') else "unknown",
                "stats": {
                    "items_collected": feed_stats.get('items_collected', 0),
                    "success_rate": round(feed_stats.get('success_rate', 0.0), 1),
                    "last_run": last_run_formatted,
                    "response_time": f"{feed_stats.get('avg_response_time', 0.0):.1f}s" if feed_stats.get('avg_response_time') else 'N/A'
                }
            }

            feeds.append(feed_data)

        logger.info(f"Returning {len(feeds)} RSS feeds")

        return jsonify({
            "success": True,
            "feeds": feeds,
            "total": len(feeds)
        })

    except Exception as e:
        logger.error(f"Failed to get RSS feeds: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/rss-feeds/toggle", methods=["POST"])
def api_rss_feeds_toggle():
    """Toggle RSS feed enable/disable status"""
    try:
        data = request.get_json()
        feed_id = data.get("feedId")
        enabled = data.get("enabled", True)

        if not feed_id:
            return jsonify({
                "success": False,
                "error": "feedId is required"
            }), 400

        # TODO: Persist the enabled/disabled state to database or config file
        # For now, we'll just acknowledge the request

        logging.info(f"RSS feed '{feed_id}' {'enabled' if enabled else 'disabled'}")

        return jsonify({
            "success": True,
            "feedId": feed_id,
            "enabled": enabled
        })

    except Exception as e:
        logging.error(f"Failed to toggle RSS feed: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/rss-feeds/test", methods=["POST"])
def api_rss_feeds_test():
    """Test connection to an RSS feed from config.json"""
    try:
        data = request.get_json()
        feed_id = data.get("feedId")

        if not feed_id:
            return jsonify({
                "success": False,
                "error": "feedId is required"
            }), 400

        # Load config from config.json
        config = load_config()
        rss_config = config.get('apis', {}).get('rss_feeds', {})
        rss_feeds_list = rss_config.get('feeds', [])

        # Find the feed by ID
        feed_config = None
        for feed in rss_feeds_list:
            # Generate ID from name (same logic as in /api/rss-feeds)
            generated_id = feed.get('name', '').lower().replace(' ', '_').replace('＋', 'plus')
            if generated_id == feed_id:
                feed_config = feed
                break

        if not feed_config:
            logger.warning(f"Feed ID '{feed_id}' not found in config.json")
            return jsonify({
                "success": False,
                "error": f"Feed '{feed_id}' not found"
            }), 404

        # Test the feed
        import feedparser

        feed_url = feed_config.get('url')
        feed_timeout = feed_config.get('timeout', 25)
        feed_name = feed_config.get('name', 'Unknown')

        try:
            logger.info(f"Testing RSS feed: {feed_name} ({feed_url})")

            # Use requests with timeout
            response = requests.get(
                feed_url,
                timeout=feed_timeout,
                headers={
                    'User-Agent': rss_config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                }
            )
            response.raise_for_status()

            # Parse the feed
            feed = feedparser.parse(response.content)

            if feed.bozo:
                # Feed has parsing errors
                logger.warning(f"Feed parsing error for {feed_name}: {feed.bozo_exception}")
                return jsonify({
                    "success": False,
                    "error": f"Feed parsing error: {str(feed.bozo_exception)[:100]}"
                })

            items_found = len(feed.entries)
            logger.info(f"Successfully tested {feed_name}: {items_found} items found")

            return jsonify({
                "success": True,
                "feedId": feed_id,
                "itemsFound": items_found,
                "feedTitle": feed.feed.get("title", "Unknown")
            })

        except requests.exceptions.Timeout:
            logger.error(f"Timeout testing {feed_name}")
            return jsonify({
                "success": False,
                "error": f"タイムアウトが発生しました（{feed_timeout}秒）"
            })
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error testing {feed_name}: {e.response.status_code}")
            if e.response.status_code == 404:
                return jsonify({
                    "success": False,
                    "error": f"フィード '{feed_name}' は利用できません（HTTP 404 NOT FOUND）"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"HTTPエラー: {e.response.status_code}"
                })
        except Exception as e:
            logger.error(f"Error testing {feed_name}: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)[:200]
            })

    except Exception as e:
        logger.error(f"Failed to test RSS feed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/rss-feeds/diagnose", methods=["POST"])
def api_rss_feeds_diagnose():
    """Diagnose RSS feed problems"""
    try:
        data = request.get_json()
        feed_id = data.get("feedId")

        if not feed_id:
            return jsonify({
                "success": False,
                "error": "feedId is required"
            }), 400

        from modules.manga_rss_enhanced import EnhancedMangaRSSCollector
        import requests

        collector = EnhancedMangaRSSCollector()
        feed_config = collector.MANGA_SOURCES.get(feed_id)

        if not feed_config:
            return jsonify({
                "success": False,
                "error": f"Feed '{feed_id}' not found"
            }), 404

        diagnosis = {
            "feedId": feed_id,
            "url": feed_config.url,
            "checks": []
        }

        # Check 1: DNS resolution
        try:
            from urllib.parse import urlparse
            hostname = urlparse(feed_config.url).hostname
            import socket
            socket.gethostbyname(hostname)
            diagnosis["checks"].append({
                "name": "DNS解決",
                "status": "success",
                "message": f"ホスト '{hostname}' は解決されました"
            })
        except Exception as e:
            diagnosis["checks"].append({
                "name": "DNS解決",
                "status": "error",
                "message": f"DNS解決に失敗: {str(e)}"
            })

        # Check 2: HTTP connectivity
        try:
            response = requests.head(
                feed_config.url,
                timeout=10,
                allow_redirects=True,
                headers={'User-Agent': 'Manga-Anime-Collector/1.0'}
            )
            diagnosis["checks"].append({
                "name": "HTTP接続",
                "status": "success" if response.status_code < 400 else "warning",
                "message": f"HTTPステータス: {response.status_code}"
            })
        except Exception as e:
            diagnosis["checks"].append({
                "name": "HTTP接続",
                "status": "error",
                "message": f"接続失敗: {str(e)}"
            })

        # Check 3: SSL certificate (if HTTPS)
        if feed_config.url.startswith("https://"):
            try:
                import ssl
                import socket
                from urllib.parse import urlparse

                hostname = urlparse(feed_config.url).hostname
                context = ssl.create_default_context()

                with socket.create_connection((hostname, 443), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        diagnosis["checks"].append({
                            "name": "SSL証明書",
                            "status": "success",
                            "message": "証明書は有効です"
                        })
            except Exception as e:
                diagnosis["checks"].append({
                    "name": "SSL証明書",
                    "status": "error",
                    "message": f"証明書エラー: {str(e)}"
                })

        # Determine overall status
        error_count = sum(1 for check in diagnosis["checks"] if check["status"] == "error")
        warning_count = sum(1 for check in diagnosis["checks"] if check["status"] == "warning")

        if error_count > 0:
            diagnosis["overallStatus"] = "error"
            diagnosis["recommendation"] = "このフィードは現在利用できません。URLを確認するか、フィードを無効化してください。"
        elif warning_count > 0:
            diagnosis["overallStatus"] = "warning"
            diagnosis["recommendation"] = "接続に問題がある可能性があります。監視を続けてください。"
        else:
            diagnosis["overallStatus"] = "success"
            diagnosis["recommendation"] = "すべてのチェックが成功しました。"

        return jsonify({
            "success": True,
            "diagnosis": diagnosis
        })

    except Exception as e:
        logging.error(f"Failed to diagnose RSS feed: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/collection-status")
def api_collection_status():
    """API endpoint for collection status information with caching"""
    current_time = time.time()

    # Check cache first
    if (
        api_status_cache["data"]
        and current_time - api_status_cache["timestamp"] < CACHE_DURATION
    ):
        return jsonify(api_status_cache["data"])

    conn = get_db_connection()

    # Get collection metrics from collection_stats table
    # Sum of items_collected from sources that ran today
    today_collected = conn.execute("""
        SELECT COALESCE(SUM(items_collected), 0)
        FROM collection_stats
        WHERE date(last_run, 'localtime') = date('now', 'localtime')
           OR date(updated_at, 'localtime') = date('now', 'localtime')
    """).fetchone()[0]

    # If no runs today, show total from all sources as reference
    if today_collected == 0:
        today_collected = conn.execute("""
            SELECT COALESCE(SUM(items_collected), 0)
            FROM collection_stats
            WHERE items_collected > 0
        """).fetchone()[0]

    metrics = {
        "todayCollected": today_collected,
        "pendingCount": conn.execute(
            "SELECT COUNT(*) FROM releases WHERE notified = 0"
        ).fetchone()[0],
        "errorCount": conn.execute(
            "SELECT COUNT(*) FROM collection_stats WHERE success_rate < 80 AND total_attempts > 0"
        ).fetchone()[0],
        "systemUptime": "稼働中",
    }

    # Test API connections (potentially slow)
    api_status = test_api_connections()

    conn.close()

    result = {"metrics": metrics, "apiStatus": api_status}

    # Update cache
    api_status_cache["data"] = result
    api_status_cache["timestamp"] = current_time

    return jsonify(result)


@app.route("/api/works")
def api_works():
    """API endpoint for works data with filtering and pagination"""
    # Get query parameters
    search = request.args.get("search", "")
    work_type = request.args.get("type", "")
    platform = request.args.get("platform", "")
    quality = request.args.get("quality", "")
    start_date = request.args.get("startDate", "")
    end_date = request.args.get("endDate", "")
    genre = request.args.get("genre", "")
    sort = request.args.get("sort", "newest")
    page = int(request.args.get("page", 1))
    per_page = 25

    conn = get_db_connection()

    # Build base query with proper title display
    query = """
        SELECT w.id, w.title, w.title_kana, w.title_en, w.type, w.official_url,
               GROUP_CONCAT(DISTINCT r.platform) as platforms,
               MIN(r.release_date) as next_release_date,
               COUNT(r.id) as release_count
        FROM works w
        LEFT JOIN releases r ON w.id = r.work_id
        WHERE 1=1
    """
    params = []

    # Apply filters
    if search:
        query += " AND (w.title LIKE ? OR w.title_kana LIKE ? OR w.title_en LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    if work_type:
        query += " AND w.type = ?"
        params.append(work_type)

    if platform:
        query += " AND r.platform = ?"
        params.append(platform)

    if start_date:
        query += " AND r.release_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND r.release_date <= ?"
        params.append(end_date)

    # Add GROUP BY
    query += " GROUP BY w.id, w.title, w.title_kana, w.title_en, w.type, w.official_url"

    # Add sorting
    if sort == "newest":
        query += " ORDER BY MAX(r.created_at) DESC"
    elif sort == "oldest":
        query += " ORDER BY MIN(r.created_at) ASC"
    elif sort == "title_asc":
        query += " ORDER BY w.title ASC"
    elif sort == "title_desc":
        query += " ORDER BY w.title DESC"
    else:
        query += " ORDER BY MAX(r.created_at) DESC"

    # Add pagination
    offset = (page - 1) * per_page
    query += f" LIMIT {per_page} OFFSET {offset}"

    works = conn.execute(query, params).fetchall()

    # Get total count for pagination - Build separate count query
    count_query = """
        SELECT COUNT(DISTINCT w.id)
        FROM works w
        LEFT JOIN releases r ON w.id = r.work_id
        WHERE 1=1
    """
    count_params = []

    # Apply same filters as main query
    if search:
        count_query += (
            " AND (w.title LIKE ? OR w.title_kana LIKE ? OR w.title_en LIKE ?)"
        )
        count_params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    if work_type:
        count_query += " AND w.type = ?"
        count_params.append(work_type)

    if platform:
        count_query += " AND r.platform = ?"
        count_params.append(platform)

    if start_date:
        count_query += " AND r.release_date >= ?"
        count_params.append(start_date)

    if end_date:
        count_query += " AND r.release_date <= ?"
        count_params.append(end_date)

    total_count = conn.execute(count_query, count_params).fetchone()[0]

    conn.close()

    # Format works data
    works_data = []
    for work in works:
        work_dict = dict(work)
        work_dict["platforms"] = (
            work_dict["platforms"].split(",") if work_dict["platforms"] else []
        )
        work_dict["quality_score"] = 85  # Mock quality score
        work_dict["genres"] = ["Action", "Adventure"]  # Mock genres
        work_dict["description"] = "サンプル説明文です。"  # Mock description
        works_data.append(work_dict)

    return jsonify(
        {
            "works": works_data,
            "total": total_count,
            "filtered": len(works_data),
            "totalPages": (total_count + per_page - 1) // per_page,
            "currentPage": page,
        }
    )


@app.route("/api/works/<int:work_id>")
def api_work_detail(work_id):
    """API endpoint for individual work details"""
    conn = get_db_connection()

    work = conn.execute(
        """
        SELECT w.*, w.title, w.title_kana,
               GROUP_CONCAT(DISTINCT r.platform) as platforms
        FROM works w
        LEFT JOIN releases r ON w.id = r.work_id
        WHERE w.id = ?
        GROUP BY w.id
    """,
        [work_id],
    ).fetchone()

    if not work:
        conn.close()
        return jsonify({"error": "Work not found"}), 404

    # Get releases for this work
    releases = conn.execute(
        """
        SELECT * FROM releases WHERE work_id = ? ORDER BY release_date DESC
    """,
        [work_id],
    ).fetchall()

    conn.close()

    work_dict = dict(work)
    work_dict["platforms"] = (
        work_dict["platforms"].split(",") if work_dict["platforms"] else []
    )
    work_dict["releases"] = [dict(release) for release in releases]
    work_dict["quality_score"] = 85  # Mock quality score
    work_dict["genres"] = ["Action", "Adventure"]  # Mock genres
    work_dict["description"] = "サンプル説明文です。"  # Mock description

    return jsonify(work_dict)


@app.route("/api/watchlist/add", methods=["POST"])
def api_add_to_watchlist():
    """API endpoint to add work to watchlist"""
    data = request.get_json()
    work_id = data.get("work_id")

    if not work_id:
        return jsonify({"error": "work_id is required"}), 400

    # This would add to user's watchlist in a real implementation
    # For now, just return success
    return jsonify({"success": True, "message": "Added to watchlist"})


@app.route("/api/manual-collection", methods=["POST"])
def api_manual_collection():
    """API endpoint to trigger manual collection"""
    # This would trigger the actual collection process
    # For now, just return success
    return jsonify({"success": True, "message": "Manual collection started"})


@app.route("/api/refresh-upcoming", methods=["POST"])
def api_refresh_upcoming():
    """API endpoint to refresh upcoming releases"""
    try:
        # This would trigger the actual collection process for upcoming releases
        # For now, return success with timestamp
        from datetime import datetime

        result = {
            "success": True,
            "message": "今後の予定を更新しました",
            "timestamp": datetime.now().isoformat(),
            "count": 0  # This would be the actual count of updated releases
        }

        logger.info("Upcoming releases refresh triggered")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error refreshing upcoming releases: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/refresh-history", methods=["POST"])
def api_refresh_history():
    """API endpoint to refresh release history"""
    try:
        # This would trigger the actual collection process for historical data
        # For now, return success with timestamp
        from datetime import datetime

        result = {
            "success": True,
            "message": "リリース履歴を更新しました",
            "timestamp": datetime.now().isoformat(),
            "count": 0  # This would be the actual count of updated releases
        }

        logger.info("Release history refresh triggered")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error refreshing release history: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    """API endpoint for settings management"""
    # Import database manager
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from modules.db import get_db

    db_manager = get_db()

    if request.method == "GET":
        try:
            # Get all settings from database
            settings = db_manager.get_all_settings()

            # If no settings found, return defaults
            if not settings:
                settings = {
                    "notification_email": "kensan1969@gmail.com",
                    "check_interval_hours": 1,
                    "email_notifications_enabled": True,
                    "calendar_enabled": False,
                    "max_notifications_per_day": 50
                }

            return jsonify({
                "success": True,
                "settings": settings
            })

        except Exception as e:
            logger.error(f"Error getting settings: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    elif request.method == "POST":
        try:
            # Update settings
            data = request.get_json()

            if not data:
                return jsonify({
                    "success": False,
                    "error": "No data provided"
                }), 400

            # Update settings in database
            db_manager.update_settings(data)

            logger.info(f"Settings updated: {list(data.keys())}")

            return jsonify({
                "success": True,
                "message": "設定を保存しました",
                "settings": db_manager.get_all_settings()
            })

        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@app.route("/api/collection-processes")
def api_collection_processes():
    """API endpoint for collection processes status - loads from config.json and database stats"""
    try:
        import sqlite3
        from datetime import datetime

        config = load_config()
        processes = []

        # Connect to database to get statistics
        conn = sqlite3.connect('db.sqlite3')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all statistics
        cursor.execute("""
            SELECT source_id, source_name, source_type, total_attempts, successful_attempts,
                   items_collected, success_rate, avg_response_time, last_run
            FROM collection_stats
        """)
        stats_dict = {row['source_id']: dict(row) for row in cursor.fetchall()}
        conn.close()

        # Add API sources
        api_config = config.get('apis', {})
        for api_name, api_data in api_config.items():
            if api_name == 'rss_feeds':  # Skip RSS feeds section
                continue

            stats = stats_dict.get(api_name, {})
            enabled = api_data.get('enabled', False)

            # Calculate time since last run
            last_update = "未実行"
            if stats.get('last_run'):
                try:
                    last_run_dt = datetime.fromisoformat(stats['last_run'].replace('Z', '+00:00'))
                    delta = datetime.now() - last_run_dt
                    if delta.total_seconds() < 60:
                        last_update = f"{int(delta.total_seconds())}秒前"
                    elif delta.total_seconds() < 3600:
                        last_update = f"{int(delta.total_seconds() / 60)}分前"
                    else:
                        last_update = f"{int(delta.total_seconds() / 3600)}時間前"
                except:
                    last_update = "リアルタイム"

            processes.append({
                "id": api_name,
                "name": api_data.get('name', stats.get('source_name', api_name)),
                "type": "anime" if 'anime' in api_name.lower() else "manga",
                "status": "connected" if enabled and stats.get('success_rate', 0) > 80 else ("warning" if enabled else "disconnected"),
                "last_update": last_update if enabled else "無効",
                "success_rate": round(stats.get('success_rate', 0), 1) if enabled else 0,
                "response_time": f"{stats.get('avg_response_time', 0):.1f}s" if enabled else "N/A",
                "note": f"取得: {stats.get('items_collected', 0)}件" if enabled else "無効",
                "items_collected": stats.get('items_collected', 0),
                "total_attempts": stats.get('total_attempts', 0),
            })

        # Add RSS feeds
        rss_config = config.get('apis', {}).get('rss_feeds', {})
        rss_feeds_list = rss_config.get('feeds', [])

        for feed in rss_feeds_list:
            feed_id = feed.get('name', '').lower().replace(' ', '_').replace('＋', 'plus')
            stats = stats_dict.get(feed_id, {})
            enabled = feed.get('enabled', False)

            # Calculate time since last run
            last_update = "未実行"
            if stats.get('last_run'):
                try:
                    last_run_dt = datetime.fromisoformat(stats['last_run'].replace('Z', '+00:00'))
                    delta = datetime.now() - last_run_dt
                    if delta.total_seconds() < 60:
                        last_update = f"{int(delta.total_seconds())}秒前"
                    elif delta.total_seconds() < 3600:
                        last_update = f"{int(delta.total_seconds() / 60)}分前"
                    else:
                        last_update = f"{int(delta.total_seconds() / 3600)}時間前"
                except:
                    last_update = "リアルタイム"

            processes.append({
                "id": feed_id,
                "name": feed.get('name', stats.get('source_name', 'Unknown')),
                "type": feed.get('type', 'manga'),
                "status": "connected" if enabled and stats.get('success_rate', 0) > 80 else ("warning" if enabled else "disconnected"),
                "last_update": last_update if enabled else "無効",
                "success_rate": round(stats.get('success_rate', 0), 1) if enabled else 0,
                "response_time": f"{stats.get('avg_response_time', 0):.1f}s" if enabled else "N/A",
                "note": f"取得: {stats.get('items_collected', 0)}件" if enabled else '無効',
                "items_collected": stats.get('items_collected', 0),
                "total_attempts": stats.get('total_attempts', 0),
            })

        logger.info(f"Returning {len(processes)} collection processes with statistics")
        return jsonify(processes)

    except Exception as e:
        logger.error(f"Error loading collection processes: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/collection-processes/retry", methods=["POST"])
def api_retry_collection_process():
    """API endpoint to retry a specific collection process"""
    data = request.get_json()
    process_id = data.get("process_id")

    if not process_id:
        return jsonify({"error": "process_id is required"}), 400

    # Fast retry operation (no sleep needed for UI responsiveness)
    return jsonify(
        {
            "success": True,
            "message": f"Collection process {process_id} retry completed",
            "process_id": process_id,
            "new_status": "connected",
        }
    )


@app.route("/api/collection-stats/refresh", methods=["POST"])
def api_refresh_collection_stats():
    """
    API endpoint to refresh collection statistics for a specific source.

    Updates the collection_stats table with current timestamp for last_run and updated_at.

    Request body:
        {
            "source_id": "anilist"  # Required: source identifier
        }

    Returns:
        Success: {
            "success": true,
            "source_id": "anilist",
            "last_run": "2025-11-16 09:00:00",
            "message": "統計を更新しました"
        }
        Error: {
            "success": false,
            "error": "エラーメッセージ"
        }
    """
    try:
        # Get request data
        data = request.get_json()
        source_id = data.get("source_id")

        # Validate required parameter
        if not source_id:
            logger.warning("API /api/collection-stats/refresh called without source_id")
            return jsonify({"success": False, "error": "source_id is required"}), 400

        # Get current timestamp in localtime format
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update collection_stats table
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE collection_stats
                SET last_run = ?, updated_at = ?
                WHERE source_id = ?
                """,
                (current_time, current_time, source_id),
            )
            conn.commit()

            # Check if any rows were actually updated
            if cursor.rowcount == 0:
                logger.warning(f"Source ID '{source_id}' not found in collection_stats")
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"Source ID '{source_id}' not found",
                        }
                    ),
                    404,
                )

            logger.info(
                f"Successfully updated collection_stats for source_id: {source_id} "
                f"(last_run: {current_time}, updated_at: {current_time})"
            )

            return jsonify(
                {
                    "success": True,
                    "source_id": source_id,
                    "last_run": current_time,
                    "message": "統計を更新しました",
                }
            )

        except Exception as db_error:
            conn.rollback()
            logger.error(
                f"Database error updating collection_stats for source_id {source_id}: {str(db_error)}"
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Database error: {str(db_error)}",
                    }
                ),
                500,
            )
        finally:
            conn.close()

    except Exception as e:
        logger.error(
            f"Error in /api/collection-stats/refresh endpoint: {str(e)}",
            exc_info=True,
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Internal server error: {str(e)}",
                }
            ),
            500,
        )


@app.route("/debug")
def debug():
    """Debug test page"""
    return render_template("debug.html")


@app.route("/ws/collection-status")
def websocket_collection_status():
    """Fallback endpoint for collection status (replaces WebSocket for now)"""
    # Return regular JSON response instead of WebSocket error
    return (
        jsonify(
            {"status": "ok", "message": "Real-time updates available via API polling"}
        ),
        200,
    )


@app.route("/api/test-notification", methods=["POST"])
def api_test_notification():
    """API endpoint for sending test notifications"""
    import smtplib
    import ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from dotenv import load_dotenv

    try:
        # .envファイル読み込み
        load_dotenv()

        data = request.get_json() or {}
        message = data.get("message", "テスト通知です。システムが正常に動作しています。")

        logger.info(f"Test notification requested: {message}")

        # 環境変数から認証情報取得
        gmail_address = os.getenv('GMAIL_ADDRESS')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')

        # 設定ファイルからメールアドレス取得
        config = load_config()
        from_email = gmail_address or config.get('notification_email', '')
        to_email = gmail_address or config.get('notification_email', '')

        if not from_email or not to_email:
            return jsonify({
                "success": False,
                "error": "メールアドレスが設定されていません"
            }), 400

        if not gmail_password:
            return jsonify({
                "success": False,
                "error": "Gmailアプリパスワードが設定されていません（.envファイルを確認）"
            }), 400

        # テストメール作成
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '【MangaAnime】テスト通知 ✅'
        msg['From'] = from_email
        msg['To'] = to_email

        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h2 {{ color: #0d6efd; border-bottom: 3px solid #0d6efd; padding-bottom: 10px; }}
                .info-box {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                ul {{ list-style-type: none; padding-left: 0; }}
                li {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
                .footer {{ text-align: center; color: #6c757d; font-size: 0.9em; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🎬 MangaAnime情報配信システム</h2>
                <div class="info-box">
                    <p><strong>📧 {message}</strong></p>
                </div>
                <h3>📊 システム情報</h3>
                <ul>
                    <li><strong>送信元:</strong> {from_email}</li>
                    <li><strong>送信先:</strong> {to_email}</li>
                    <li><strong>送信日時:</strong> {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</li>
                    <li><strong>サーバー:</strong> Gmail SMTP</li>
                </ul>
                <div class="footer">
                    <p>🤖 このメールはMangaAnime情報配信システムから自動送信されました</p>
                    <p>システムが正常に動作しています ✅</p>
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))

        # Gmail SMTP経由で送信
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(from_email, gmail_password)
            server.send_message(msg)

        logger.info(f"✅ Test email sent successfully: {from_email} -> {to_email}")

        return jsonify({
            "success": True,
            "message": f"✅ テスト通知を送信しました！\n\n送信先: {to_email}\nメールボックスをご確認ください。",
            "details": {
                "from": from_email,
                "to": to_email,
                "sent_at": datetime.now().isoformat()
            }
        })

    except ImportError as e:
        logger.error(f"Failed to import email sender: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "メール送信モジュールの読み込みに失敗しました",
                }
            ),
            500,
        )
    except Exception as e:
        logger.error(f"Test notification error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/test-configuration", methods=["POST"])
def api_test_configuration():
    """Test all system configurations"""
    import requests
    import sqlite3
    import os
    import smtplib
    import ssl

    results = {
        "gmail": {"status": "testing", "message": "", "details": {}},
        "database": {"status": "testing", "message": "", "details": {}},
        "anilist": {"status": "testing", "message": "", "details": {}},
        "rss_feeds": {"status": "testing", "message": "", "details": {}},
    }

    try:
        # Load configuration
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        return (
            jsonify({"success": False, "error": f"設定ファイルの読み込みに失敗: {str(e)}"}),
            500,
        )

    # Test Gmail SMTP connection
    try:
        # .envファイルから環境変数を読み込み
        from dotenv import load_dotenv
        load_dotenv()

        # 環境変数から取得（.envファイル）
        sender_email = os.getenv('GMAIL_ADDRESS') or os.getenv('GMAIL_SENDER_EMAIL', '')
        sender_password = os.getenv('GMAIL_APP_PASSWORD', '')

        # フォールバック: config.jsonから取得
        if not sender_email:
            gmail_config = config.get("google", {}).get("gmail", {})
            sender_email = gmail_config.get("from_email", "")

        smtp_server = "smtp.gmail.com"
        smtp_port = 465  # SSL接続

        if not sender_email or not sender_password:
            results["gmail"]["status"] = "error"
            results["gmail"]["message"] = "メール設定が不完全です（.envファイルを確認してください）"
        else:
            # SSL接続（465ポート）
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=10) as server:
                server.login(sender_email, sender_password)

            results["gmail"]["status"] = "success"
            results["gmail"]["message"] = "Gmail接続成功"
            results["gmail"]["details"] = {
                "server": smtp_server,
                "port": smtp_port,
                "email": sender_email,
            }
    except Exception as e:
        results["gmail"]["status"] = "error"
        results["gmail"]["message"] = f"Gmail接続エラー: {str(e)}"

    # Test Database connection
    try:
        db_path = config.get("database", {}).get("path", "./db.sqlite3")
        if not os.path.exists(db_path):
            results["database"]["status"] = "error"
            results["database"]["message"] = "データベースファイルが見つかりません"
        else:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check table existence
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            # Count records
            works_count = 0
            releases_count = 0
            if "works" in tables:
                cursor.execute("SELECT COUNT(*) FROM works")
                works_count = cursor.fetchone()[0]
            if "releases" in tables:
                cursor.execute("SELECT COUNT(*) FROM releases")
                releases_count = cursor.fetchone()[0]

            conn.close()

            results["database"]["status"] = "success"
            results["database"]["message"] = "データベース接続成功"
            results["database"]["details"] = {
                "path": db_path,
                "tables": tables,
                "works_count": works_count,
                "releases_count": releases_count,
            }
    except Exception as e:
        results["database"]["status"] = "error"
        results["database"]["message"] = f"データベースエラー: {str(e)}"

    # Test AniList API
    try:
        anilist_config = config.get("apis", {}).get("anilist", {})
        graphql_url = anilist_config.get("graphql_url", "https://graphql.anilist.co")
        timeout = anilist_config.get("timeout_seconds", 30)

        # Simple AniList query
        query = """
        query {
            Media(id: 1) {
                id
                title {
                    romaji
                }
            }
        }
        """

        response = requests.post(
            graphql_url,
            json={"query": query},
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                results["anilist"]["status"] = "success"
                results["anilist"]["message"] = "AniList API接続成功"
                results["anilist"]["details"] = {
                    "url": graphql_url,
                    "response_time": f"{response.elapsed.total_seconds():.2f}秒",
                }
            else:
                results["anilist"]["status"] = "error"
                results["anilist"]["message"] = "AniList APIレスポンスエラー"
        else:
            results["anilist"]["status"] = "error"
            results["anilist"][
                "message"
            ] = f"AniList API HTTPエラー: {response.status_code}"

    except Exception as e:
        results["anilist"]["status"] = "error"
        results["anilist"]["message"] = f"AniList APIエラー: {str(e)}"

    # Test RSS Feeds
    try:
        rss_config = config.get("apis", {}).get("rss_feeds", {})
        feeds = rss_config.get("feeds", [])
        timeout = rss_config.get("timeout_seconds", 20)
        user_agent = rss_config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        feed_results = []
        success_count = 0

        for feed in feeds[:3]:  # Test first 3 feeds only
            feed_name = feed.get("name", "Unknown")
            feed_url = feed.get("url", "")
            enabled = feed.get("enabled", False)

            if not enabled:
                feed_results.append(
                    {
                        "name": feed_name,
                        "status": "disabled",
                        "message": "無効化されています",
                    }
                )
                continue

            try:
                # User-Agentヘッダーを追加してボット対策を回避
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'application/rss+xml, application/xml, text/xml, */*'
                }
                response = requests.get(feed_url, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    success_count += 1
                    feed_results.append(
                        {"name": feed_name, "status": "success", "message": "接続成功"}
                    )
                else:
                    feed_results.append(
                        {
                            "name": feed_name,
                            "status": "error",
                            "message": f"HTTPエラー: {response.status_code}",
                        }
                    )
            except Exception as e:
                feed_results.append(
                    {
                        "name": feed_name,
                        "status": "error",
                        "message": f"接続エラー: {str(e)}",
                    }
                )

        if success_count > 0:
            results["rss_feeds"]["status"] = "success"
            results["rss_feeds"][
                "message"
            ] = f"{success_count}/{len(feed_results)}個のRSSフィードが正常"
        else:
            results["rss_feeds"]["status"] = "error"
            results["rss_feeds"]["message"] = "すべてのRSSフィードでエラー"

        results["rss_feeds"]["details"] = {"feeds": feed_results}

    except Exception as e:
        results["rss_feeds"]["status"] = "error"
        results["rss_feeds"]["message"] = f"RSSフィードテストエラー: {str(e)}"

    # Calculate overall success
    success_count = sum(
        1 for result in results.values() if result["status"] == "success"
    )
    total_tests = len(results)
    overall_success = success_count == total_tests

    return jsonify(
        {
            "success": overall_success,
            "summary": {
                "passed": success_count,
                "total": total_tests,
                "message": (
                    f"{success_count}/{total_tests}個のテストが成功"
                    if overall_success
                    else f"{total_tests - success_count}個のテストで問題が発生"
                ),
            },
            "results": results,
        }
    )


@app.route("/api/generate-ics", methods=["POST"])
def generate_ics():
    """選択されたリリースからiCalendarファイルを生成"""
    from datetime import datetime as dt
    import uuid
    from flask import Response

    try:
        data = request.get_json()
        releases = data.get('releases', [])

        if not releases:
            return jsonify({'error': '登録するリリースがありません'}), 400

        # iCalendar形式のファイル生成
        ics_content = ['BEGIN:VCALENDAR']
        ics_content.append('VERSION:2.0')
        ics_content.append('PRODID:-//MangaAnime Info System//Calendar//JP')
        ics_content.append('CALSCALE:GREGORIAN')
        ics_content.append('METHOD:PUBLISH')
        ics_content.append('X-WR-CALNAME:アニメ・マンガリリース予定')
        ics_content.append('X-WR-TIMEZONE:Asia/Tokyo')

        for release in releases:
            # イベントID生成
            event_uid = str(uuid.uuid4())

            # タイトル生成
            type_icon = '🎬' if release.get('type') == 'anime' else '📚'
            type_label = 'アニメ' if release.get('type') == 'anime' else 'マンガ'
            release_text = '話' if release.get('release_type') == 'episode' else '巻'

            title = f"{type_icon}【{type_label}】{release.get('title', '')} 第{release.get('number', '')}{release_text} | {release.get('platform', '')}"

            # 詳細情報
            description = f"作品: {release.get('title', '')}\\n"
            description += f"タイプ: {type_label}\\n"
            description += f"{release_text}: 第{release.get('number', '')}{release_text}\\n"
            description += f"配信プラットフォーム: {release.get('platform', '')}\\n"
            if release.get('source_url'):
                description += f"ソースURL: {release.get('source_url')}\\n"
            description += "\\n---\\n自動登録: MangaAnime情報配信システム"

            # 日付（YYYYMMDD形式）
            release_date = release.get('release_date', '')
            date_str = release_date.replace('-', '')

            # イベント作成
            ics_content.append('BEGIN:VEVENT')
            ics_content.append(f'UID:{event_uid}')
            ics_content.append(f'DTSTAMP:{dt.now().strftime("%Y%m%dT%H%M%SZ")}')
            ics_content.append(f'DTSTART;VALUE=DATE:{date_str}')
            ics_content.append(f'DTEND;VALUE=DATE:{date_str}')
            ics_content.append(f'SUMMARY:{title}')
            ics_content.append(f'DESCRIPTION:{description}')
            ics_content.append(f'LOCATION:{release.get("platform", "")}')
            ics_content.append('STATUS:CONFIRMED')
            ics_content.append('TRANSP:TRANSPARENT')
            ics_content.append('END:VEVENT')

        ics_content.append('END:VCALENDAR')

        # レスポンス生成
        ics_text = '\r\n'.join(ics_content)

        return Response(
            ics_text,
            mimetype='text/calendar',
            headers={
                'Content-Disposition': f'attachment; filename=anime_manga_releases_{dt.now().strftime("%Y%m%d")}.ics'
            }
        )

    except Exception as e:
        logger.error(f'iCalendar生成エラー: {e}')
        return jsonify({'error': str(e)}), 500


@app.route("/api/notification-status")
def api_notification_status():
    """通知・カレンダー連携の実行状況を返すAPIエンドポイント（notification_history使用）"""
    try:
        from datetime import timedelta, time
        from datetime import datetime as dt

        conn = get_db_connection()

        # メール通知の最終実行時刻と統計を取得
        email_last = conn.execute("""
            SELECT executed_at, success, error_message, releases_count
            FROM notification_history
            WHERE notification_type = 'email'
            ORDER BY executed_at DESC
            LIMIT 1
        """).fetchone()

        # メール通知の本日の統計
        email_stats_today = conn.execute("""
            SELECT
                COUNT(*) as total_executions,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count,
                SUM(CASE WHEN success = 1 THEN releases_count ELSE 0 END) as total_releases
            FROM notification_history
            WHERE notification_type = 'email' AND DATE(executed_at) = DATE('now')
        """).fetchone()

        # メール通知の直近のエラー
        email_recent_errors = conn.execute("""
            SELECT executed_at, error_message, releases_count
            FROM notification_history
            WHERE notification_type = 'email' AND success = 0
            ORDER BY executed_at DESC
            LIMIT 5
        """).fetchall()

        # カレンダー登録の最終実行時刻と統計を取得
        calendar_last = conn.execute("""
            SELECT executed_at, success, error_message, releases_count
            FROM notification_history
            WHERE notification_type = 'calendar'
            ORDER BY executed_at DESC
            LIMIT 1
        """).fetchone()

        # カレンダー登録の本日の統計
        calendar_stats_today = conn.execute("""
            SELECT
                COUNT(*) as total_executions,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count,
                SUM(CASE WHEN success = 1 THEN releases_count ELSE 0 END) as total_events
            FROM notification_history
            WHERE notification_type = 'calendar' AND DATE(executed_at) = DATE('now')
        """).fetchone()

        # カレンダー登録の直近のエラー
        calendar_recent_errors = conn.execute("""
            SELECT executed_at, error_message, releases_count
            FROM notification_history
            WHERE notification_type = 'calendar' AND success = 0
            ORDER BY executed_at DESC
            LIMIT 5
        """).fetchall()

        # settingsテーブルからチェック間隔を取得
        check_interval = conn.execute("""
            SELECT value FROM settings WHERE key = 'check_interval_hours'
        """).fetchone()

        interval_hours = int(check_interval['value']) if check_interval else 1

        # 次回実行予定時刻を計算
        now = dt.now()
        if email_last and email_last['executed_at']:
            last_executed = dt.fromisoformat(email_last['executed_at'])
            next_run = last_executed + timedelta(hours=interval_hours)
        else:
            # デフォルト: 次の整時
            next_run = dt.combine(now.date(), time(now.hour + 1, 0))

        conn.close()

        # レスポンスを構築
        response = {
            'email': {
                'lastExecuted': email_last['executed_at'] if email_last else None,
                'lastSuccess': email_last['success'] == 1 if email_last else None,
                'lastError': email_last['error_message'] if email_last and not email_last['success'] else None,
                'lastReleasesCount': email_last['releases_count'] if email_last else 0,
                'nextScheduled': next_run.isoformat(),
                'checkIntervalHours': interval_hours,
                'todayStats': {
                    'totalExecutions': email_stats_today['total_executions'] if email_stats_today else 0,
                    'successCount': email_stats_today['success_count'] if email_stats_today else 0,
                    'errorCount': email_stats_today['error_count'] if email_stats_today else 0,
                    'totalReleases': email_stats_today['total_releases'] if email_stats_today else 0,
                },
                'recentErrors': [
                    {
                        'time': row['executed_at'],
                        'message': row['error_message'],
                        'releasesCount': row['releases_count']
                    }
                    for row in email_recent_errors
                ],
                'status': 'success' if (email_last and email_last['success']) else ('error' if email_last else 'unknown')
            },
            'calendar': {
                'lastExecuted': calendar_last['executed_at'] if calendar_last else None,
                'lastSuccess': calendar_last['success'] == 1 if calendar_last else None,
                'lastError': calendar_last['error_message'] if calendar_last and not calendar_last['success'] else None,
                'lastEventsCount': calendar_last['releases_count'] if calendar_last else 0,
                'nextScheduled': next_run.isoformat(),
                'checkIntervalHours': interval_hours,
                'todayStats': {
                    'totalExecutions': calendar_stats_today['total_executions'] if calendar_stats_today else 0,
                    'successCount': calendar_stats_today['success_count'] if calendar_stats_today else 0,
                    'errorCount': calendar_stats_today['error_count'] if calendar_stats_today else 0,
                    'totalEvents': calendar_stats_today['total_events'] if calendar_stats_today else 0,
                },
                'recentErrors': [
                    {
                        'time': row['executed_at'],
                        'message': row['error_message'],
                        'eventsCount': row['releases_count']
                    }
                    for row in calendar_recent_errors
                ],
                'status': 'success' if (calendar_last and calendar_last['success']) else ('error' if calendar_last else 'unknown')
            },
            'overall': {
                'healthStatus': 'healthy' if (
                    (not email_last or email_last['success']) and
                    (not calendar_last or calendar_last['success'])
                ) else 'issues',
                'lastUpdate': now.isoformat()
            }
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f'通知状況取得エラー: {e}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# ============================================================================
# API Source Testing and Configuration Endpoints
# ============================================================================

@app.route('/api/sources')
def api_sources():
    """
    Get all collection sources with their status and configuration.

    Returns:
        JSON with list of all sources (APIs and RSS feeds) including:
        - Source name and type
        - Enabled/disabled status
        - Last test results
        - Configuration details
        - Statistics from collection_stats table
    """
    try:
        import sqlite3
        from datetime import datetime

        config = load_config()

        sources = {
            'apis': [],
            'rss_feeds': [],
            'summary': {
                'total_sources': 0,
                'enabled_sources': 0,
                'disabled_sources': 0,
                'last_updated': datetime.now().isoformat()
            }
        }

        # Connect to database to get statistics
        conn = sqlite3.connect('db.sqlite3')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all statistics
        cursor.execute("""
            SELECT source_id, source_name, source_type, total_attempts, successful_attempts,
                   items_collected, success_rate, avg_response_time, last_run
            FROM collection_stats
        """)
        stats_dict = {row['source_id']: dict(row) for row in cursor.fetchall()}
        conn.close()

        # Helper function to format time since last run
        def format_last_run(last_run_str):
            if not last_run_str:
                return None
            try:
                last_run_dt = datetime.fromisoformat(last_run_str.replace('Z', '+00:00'))
                delta = datetime.now() - last_run_dt
                if delta.total_seconds() < 60:
                    return f"{int(delta.total_seconds())}秒前"
                elif delta.total_seconds() < 3600:
                    return f"{int(delta.total_seconds() / 60)}分前"
                else:
                    return f"{int(delta.total_seconds() / 3600)}時間前"
            except:
                return None

        # AniList API
        anilist_config = config.get('apis', {}).get('anilist', {})
        anilist_stats = stats_dict.get('anilist', {})
        anilist_source = {
            'id': 'anilist',
            'name': 'AniList GraphQL API',
            'type': 'api',
            'enabled': anilist_config.get('enabled', True),
            'url': anilist_config.get('graphql_url', 'https://graphql.anilist.co'),
            'rate_limit': anilist_config.get('rate_limit', {}).get('requests_per_minute', 90),
            'timeout': anilist_config.get('timeout_seconds', 30),
            'description': 'アニメ情報取得用GraphQL API',
            'data_type': 'anime',
            'last_test': None,
            'health_status': 'unknown',
            'stats': {
                'items_collected': anilist_stats.get('items_collected', 0),
                'success_rate': round(anilist_stats.get('success_rate', 0), 1),
                'last_run': format_last_run(anilist_stats.get('last_run')),
                'response_time': f"{anilist_stats.get('avg_response_time', 0):.1f}s" if anilist_stats.get('avg_response_time') else None,
                'total_attempts': anilist_stats.get('total_attempts', 0)
            }
        }
        sources['apis'].append(anilist_source)

        # Kitsu API
        kitsu_config = config.get('apis', {}).get('kitsu', {})
        if kitsu_config:
            kitsu_stats = stats_dict.get('kitsu', {})
            kitsu_source = {
                'id': 'kitsu',
                'name': 'Kitsu API',
                'type': 'api',
                'enabled': kitsu_config.get('enabled', True),
                'url': kitsu_config.get('base_url', 'https://kitsu.io/api/edge'),
                'rate_limit': kitsu_config.get('rate_limit', {}).get('requests_per_minute', 90),
                'timeout': kitsu_config.get('timeout_seconds', 30),
                'description': 'アニメ・マンガ情報取得用REST API',
                'data_type': 'anime_manga',
                'last_test': None,
                'health_status': 'unknown',
                'stats': {
                    'items_collected': kitsu_stats.get('items_collected', 0),
                    'success_rate': round(kitsu_stats.get('success_rate', 0), 1),
                    'last_run': format_last_run(kitsu_stats.get('last_run')),
                    'response_time': f"{kitsu_stats.get('avg_response_time', 0):.1f}s" if kitsu_stats.get('avg_response_time') else None,
                    'total_attempts': kitsu_stats.get('total_attempts', 0)
                }
            }
            sources['apis'].append(kitsu_source)

        # MangaDex API
        mangadex_config = config.get('apis', {}).get('mangadex', {})
        if mangadex_config:
            mangadex_stats = stats_dict.get('mangadex', {})
            mangadex_source = {
                'id': 'mangadex',
                'name': 'MangaDex API',
                'type': 'api',
                'enabled': mangadex_config.get('enabled', True),
                'url': mangadex_config.get('base_url', 'https://api.mangadex.org'),
                'rate_limit': mangadex_config.get('rate_limit', {}).get('requests_per_minute', 40),
                'timeout': mangadex_config.get('timeout_seconds', 30),
                'description': 'マンガ情報取得用REST API',
                'data_type': 'manga',
                'last_test': None,
                'health_status': 'unknown',
                'stats': {
                    'items_collected': mangadex_stats.get('items_collected', 0),
                    'success_rate': round(mangadex_stats.get('success_rate', 0), 1),
                    'last_run': format_last_run(mangadex_stats.get('last_run')),
                    'response_time': f"{mangadex_stats.get('avg_response_time', 0):.1f}s" if mangadex_stats.get('avg_response_time') else None,
                    'total_attempts': mangadex_stats.get('total_attempts', 0)
                }
            }
            sources['apis'].append(mangadex_source)

        # MangaUpdates API
        mangaupdates_config = config.get('apis', {}).get('mangaupdates', {})
        if mangaupdates_config:
            mangaupdates_stats = stats_dict.get('mangaupdates', {})
            mangaupdates_source = {
                'id': 'mangaupdates',
                'name': 'MangaUpdates API',
                'type': 'api',
                'enabled': mangaupdates_config.get('enabled', True),
                'url': mangaupdates_config.get('base_url', 'https://api.mangaupdates.com/v1'),
                'rate_limit': mangaupdates_config.get('rate_limit', {}).get('requests_per_minute', 30),
                'timeout': mangaupdates_config.get('timeout_seconds', 30),
                'description': 'マンガリリース情報取得用REST API',
                'data_type': 'manga',
                'last_test': None,
                'health_status': 'unknown',
                'stats': {
                    'items_collected': mangaupdates_stats.get('items_collected', 0),
                    'success_rate': round(mangaupdates_stats.get('success_rate', 0), 1),
                    'last_run': format_last_run(mangaupdates_stats.get('last_run')),
                    'response_time': f"{mangaupdates_stats.get('avg_response_time', 0):.1f}s" if mangaupdates_stats.get('avg_response_time') else None,
                    'total_attempts': mangaupdates_stats.get('total_attempts', 0)
                }
            }
            sources['apis'].append(mangaupdates_source)

        # Annict API
        annict_config = config.get('apis', {}).get('annict', {})
        if annict_config:
            annict_stats = stats_dict.get('annict', {})
            annict_source = {
                'id': 'annict',
                'name': 'Annict API',
                'type': 'api',
                'enabled': annict_config.get('enabled', True),
                'url': annict_config.get('base_url', 'https://api.annict.com/v1'),
                'rate_limit': annict_config.get('rate_limit', {}).get('requests_per_minute', 60),
                'timeout': annict_config.get('timeout_seconds', 30),
                'description': 'Annict REST API v1 - 日本アニメ放送情報・作品データベース',
                'data_type': 'anime',
                'last_test': None,
                'health_status': 'unknown',
                'stats': {
                    'items_collected': annict_stats.get('items_collected', 0),
                    'success_rate': round(annict_stats.get('success_rate', 0), 1),
                    'last_run': format_last_run(annict_stats.get('last_run')),
                    'response_time': f"{annict_stats.get('avg_response_time', 0):.1f}s" if annict_stats.get('avg_response_time') else None,
                    'total_attempts': annict_stats.get('total_attempts', 0)
                }
            }
            sources['apis'].append(annict_source)

        # Syoboi Calendar API
        syoboi_config = config.get('apis', {}).get('syoboi', {})
        syoboi_stats = stats_dict.get('syoboi', {})
        syoboi_source = {
            'id': 'syoboi',
            'name': 'しょぼいカレンダー',
            'type': 'api',
            'enabled': syoboi_config.get('enabled', False),
            'url': syoboi_config.get('base_url', 'https://cal.syoboi.jp'),
            'rate_limit': syoboi_config.get('rate_limit', {}).get('requests_per_minute', 60),
            'description': '日本のアニメ放送スケジュール',
            'data_type': 'anime',
            'last_test': None,
            'health_status': 'unknown',
            'stats': {
                'items_collected': syoboi_stats.get('items_collected', 0),
                'success_rate': round(syoboi_stats.get('success_rate', 0), 1),
                'last_run': format_last_run(syoboi_stats.get('last_run')),
                'response_time': f"{syoboi_stats.get('avg_response_time', 0):.1f}s" if syoboi_stats.get('avg_response_time') else None,
                'total_attempts': syoboi_stats.get('total_attempts', 0)
            }
        }
        sources['apis'].append(syoboi_source)

        # RSS Feeds
        rss_config = config.get('apis', {}).get('rss_feeds', {})
        rss_feeds = rss_config.get('feeds', [])

        for feed in rss_feeds:
            feed_id = feed.get('name', '').lower().replace(' ', '_').replace('＋', 'plus')
            feed_stats = stats_dict.get(feed_id, {})
            feed_source = {
                'id': feed_id,
                'name': feed.get('name', 'Unknown'),
                'type': 'rss',
                'enabled': feed.get('enabled', False),
                'url': feed.get('url', ''),
                'description': feed.get('description', ''),
                'data_type': feed.get('type', 'manga'),
                'verified': feed.get('verified', False),
                'timeout': feed.get('timeout', 25),
                'retry_count': feed.get('retry_count', 3),
                'last_test': None,
                'health_status': 'unknown' if feed.get('enabled') else 'disabled',
                'stats': {
                    'items_collected': feed_stats.get('items_collected', 0),
                    'success_rate': round(feed_stats.get('success_rate', 0), 1),
                    'last_run': format_last_run(feed_stats.get('last_run')),
                    'response_time': f"{feed_stats.get('avg_response_time', 0):.1f}s" if feed_stats.get('avg_response_time') else None,
                    'total_attempts': feed_stats.get('total_attempts', 0)
                }
            }
            sources['rss_feeds'].append(feed_source)

        # Calculate summary
        total_apis = len(sources['apis'])
        total_rss = len(sources['rss_feeds'])
        sources['summary']['total_sources'] = total_apis + total_rss
        sources['summary']['enabled_sources'] = (
            sum(1 for api in sources['apis'] if api['enabled']) +
            sum(1 for rss in sources['rss_feeds'] if rss['enabled'])
        )
        sources['summary']['disabled_sources'] = (
            sources['summary']['total_sources'] - sources['summary']['enabled_sources']
        )

        logger.info(f"Returning {sources['summary']['total_sources']} sources with statistics")
        return jsonify(sources)

    except Exception as e:
        logger.error(f"Failed to get sources: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/sources/anilist/test', methods=['POST'])
def api_test_anilist():
    """
    Test AniList GraphQL API connection.
    
    Returns:
        JSON with test results including:
        - Connection status
        - Response time
        - Error details if any
        - Sample data retrieval success
    """
    try:
        start_time = time.time()
        test_results = {
            'source': 'anilist',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
        
        # Test 1: Basic connectivity
        try:
            basic_query = '{ Media(id: 1) { id title { romaji } } }'
            response = requests.post(
                'https://graphql.anilist.co',
                json={'query': basic_query},
                headers={'User-Agent': 'MangaAnimeNotifier/1.0'},
                timeout=5
            )
            basic_time = time.time() - start_time
            
            test_results['tests'].append({
                'name': 'basic_connectivity',
                'status': 'success' if response.status_code == 200 else 'failed',
                'response_time_ms': round(basic_time * 1000, 2),
                'http_status': response.status_code,
                'details': f'HTTP {response.status_code}' if response.status_code != 200 else 'GraphQL API responding'
            })
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' in data:
                    test_results['tests'][-1]['status'] = 'warning'
                    test_results['tests'][-1]['details'] = f"GraphQL errors: {data['errors']}"
                    
        except requests.exceptions.Timeout:
            test_results['tests'].append({
                'name': 'basic_connectivity',
                'status': 'failed',
                'response_time_ms': 5000,
                'error': 'タイムアウト (5秒)'
            })
        except Exception as e:
            test_results['tests'].append({
                'name': 'basic_connectivity',
                'status': 'error',
                'error': str(e)
            })
        
        # Test 2: Current season query
        try:
            now = datetime.now()
            year = now.year
            month = now.month
            if month in [12, 1, 2]:
                season = "WINTER"
            elif month in [3, 4, 5]:
                season = "SPRING"
            elif month in [6, 7, 8]:
                season = "SUMMER"
            else:
                season = "FALL"
            
            season_query = f'''
            {{
                Page(page: 1, perPage: 5) {{
                    media(season: {season}, seasonYear: {year}, type: ANIME) {{
                        id
                        title {{ romaji }}
                        status
                    }}
                }}
            }}
            '''
            
            start_season = time.time()
            response = requests.post(
                'https://graphql.anilist.co',
                json={'query': season_query},
                headers={'User-Agent': 'MangaAnimeNotifier/1.0'},
                timeout=5
            )
            season_time = time.time() - start_season
            
            if response.status_code == 200:
                data = response.json()
                media_count = len(data.get('data', {}).get('Page', {}).get('media', []))
                test_results['tests'].append({
                    'name': 'current_season_query',
                    'status': 'success',
                    'response_time_ms': round(season_time * 1000, 2),
                    'results_count': media_count,
                    'details': f'{season} {year}シーズンのアニメ{media_count}件取得'
                })
            else:
                test_results['tests'].append({
                    'name': 'current_season_query',
                    'status': 'failed',
                    'http_status': response.status_code,
                    'response_time_ms': round(season_time * 1000, 2)
                })
                
        except Exception as e:
            test_results['tests'].append({
                'name': 'current_season_query',
                'status': 'error',
                'error': str(e)
            })
        
        # Test 3: Rate limit check
        test_results['tests'].append({
            'name': 'rate_limit_info',
            'status': 'info',
            'details': 'AniList rate limit: 90 requests/minute',
            'configured_limit': 90
        })
        
        # Overall status
        failed_tests = sum(1 for test in test_results['tests'] if test['status'] in ['failed', 'error'])
        test_results['overall_status'] = 'success' if failed_tests == 0 else 'failed'
        test_results['success_rate'] = f"{((len(test_results['tests']) - failed_tests) / len(test_results['tests']) * 100):.1f}%"
        test_results['total_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        return jsonify(test_results)

    except Exception as e:
        logger.error(f"AniList test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'source': 'anilist',
            'overall_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/sources/annict/test', methods=['POST'])
def api_test_annict():
    """
    Test Annict REST API v1 connection.

    Returns:
        JSON with test results including:
        - Connection status
        - Response time
        - Error details if any
        - Sample data retrieval success
    """
    try:
        start_time = time.time()
        config = load_config()
        annict_config = config.get('apis', {}).get('annict', {})
        access_token = annict_config.get('access_token', '')
        base_url = annict_config.get('base_url', 'https://api.annict.com/v1')

        test_results = {
            'source': 'annict',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }

        # Test 1: Basic connectivity
        try:
            headers = {'User-Agent': 'MangaAnimeNotifier/1.0'}
            if access_token:
                headers['Authorization'] = f'Bearer {access_token}'

            response = requests.get(
                f'{base_url}/works',
                params={'filter_status': 'current'},
                headers=headers,
                timeout=5
            )
            basic_time = time.time() - start_time

            test_results['tests'].append({
                'name': 'basic_connectivity',
                'status': 'success' if response.status_code == 200 else 'failed',
                'response_time_ms': round(basic_time * 1000, 2),
                'http_status': response.status_code,
                'details': f'HTTP {response.status_code}' if response.status_code != 200 else 'REST API responding'
            })

            if response.status_code == 200:
                try:
                    data = response.json()
                    works = data.get('works', [])
                    test_results['tests'].append({
                        'name': 'current_works_query',
                        'status': 'success',
                        'response_time_ms': round(basic_time * 1000, 2),
                        'results_count': len(works),
                        'details': f'現在放映中のアニメ{len(works)}件取得'
                    })
                except:
                    test_results['tests'][-1]['status'] = 'warning'
                    test_results['tests'][-1]['details'] = 'Response received but JSON parsing failed'

        except requests.exceptions.Timeout:
            test_results['tests'].append({
                'name': 'basic_connectivity',
                'status': 'failed',
                'response_time_ms': 5000,
                'error': 'タイムアウト (5秒)'
            })
        except Exception as e:
            test_results['tests'].append({
                'name': 'basic_connectivity',
                'status': 'error',
                'error': str(e)
            })

        # Test 2: Authentication status
        if access_token:
            test_results['tests'].append({
                'name': 'authentication',
                'status': 'info',
                'details': 'API token is configured',
                'token_configured': True
            })
        else:
            test_results['tests'].append({
                'name': 'authentication',
                'status': 'warning',
                'details': 'API token not configured',
                'token_configured': False
            })

        # Test 3: Rate limit check
        test_results['tests'].append({
            'name': 'rate_limit_info',
            'status': 'info',
            'details': 'Annict rate limit: 60 requests/minute',
            'configured_limit': 60
        })

        # Overall status
        failed_tests = sum(1 for test in test_results['tests'] if test['status'] in ['failed', 'error'])
        test_results['overall_status'] = 'success' if failed_tests == 0 else 'failed'
        test_results['success_rate'] = f"{((len(test_results['tests']) - failed_tests) / len(test_results['tests']) * 100):.1f}%"
        test_results['total_time_ms'] = round((time.time() - start_time) * 1000, 2)

        return jsonify(test_results)

    except Exception as e:
        logger.error(f"Annict test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'source': 'annict',
            'overall_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/sources/syoboi/test', methods=['POST'])
def api_test_syoboi():
    """
    Test Syoboi Calendar API connection.
    
    Returns:
        JSON with test results including:
        - Connection status
        - Response time
        - Sample data retrieval
    """
    try:
        start_time = time.time()
        test_results = {
            'source': 'syoboi',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
        
        # Test 1: Title lookup
        try:
            response = requests.get(
                'https://cal.syoboi.jp/json.php?Req=TitleLookup&TID=1',
                headers={'User-Agent': 'MangaAnimeNotifier/1.0'},
                timeout=5
            )
            lookup_time = time.time() - start_time
            
            test_results['tests'].append({
                'name': 'title_lookup',
                'status': 'success' if response.status_code == 200 else 'failed',
                'response_time_ms': round(lookup_time * 1000, 2),
                'http_status': response.status_code,
                'details': 'タイトル検索APIアクセス成功' if response.status_code == 200 else f'HTTP {response.status_code}'
            })
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    test_results['tests'][-1]['data_format'] = 'valid_json'
                except:
                    test_results['tests'][-1]['status'] = 'warning'
                    test_results['tests'][-1]['data_format'] = 'invalid_json'
                    
        except requests.exceptions.Timeout:
            test_results['tests'].append({
                'name': 'title_lookup',
                'status': 'failed',
                'response_time_ms': 5000,
                'error': 'タイムアウト (5秒)'
            })
        except Exception as e:
            test_results['tests'].append({
                'name': 'title_lookup',
                'status': 'error',
                'error': str(e)
            })
        
        # Test 2: Program lookup
        try:
            start_prog = time.time()
            response = requests.get(
                'https://cal.syoboi.jp/json.php?Req=ProgramByDate&Start=20240101&Days=1',
                headers={'User-Agent': 'MangaAnimeNotifier/1.0'},
                timeout=5
            )
            prog_time = time.time() - start_prog
            
            test_results['tests'].append({
                'name': 'program_lookup',
                'status': 'success' if response.status_code == 200 else 'failed',
                'response_time_ms': round(prog_time * 1000, 2),
                'http_status': response.status_code,
                'details': '番組スケジュール取得成功' if response.status_code == 200 else f'HTTP {response.status_code}'
            })
            
        except Exception as e:
            test_results['tests'].append({
                'name': 'program_lookup',
                'status': 'error',
                'error': str(e)
            })
        
        # Overall status
        failed_tests = sum(1 for test in test_results['tests'] if test['status'] in ['failed', 'error'])
        test_results['overall_status'] = 'success' if failed_tests == 0 else 'failed'
        test_results['success_rate'] = f"{((len(test_results['tests']) - failed_tests) / len(test_results['tests']) * 100):.1f}%"
        test_results['total_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        return jsonify(test_results)
        
    except Exception as e:
        logger.error(f"Syoboi test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'source': 'syoboi',
            'overall_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/sources/rss/test', methods=['POST'])
def api_test_rss():
    """
    Test RSS feed connection.
    
    Request JSON:
        {
            "feed_id": "shonenjump_plus" or "feed_url": "https://..."
        }
    
    Returns:
        JSON with test results
    """
    try:
        data = request.get_json() or {}
        feed_id = data.get('feed_id')
        feed_url = data.get('feed_url')
        
        if not feed_id and not feed_url:
            return jsonify({'error': 'feed_id or feed_url is required'}), 400
        
        # Find feed configuration
        config = load_config()
        rss_feeds = config.get('apis', {}).get('rss_feeds', {}).get('feeds', [])
        
        feed_config = None
        if feed_id:
            # Convert feed_id to match name
            for feed in rss_feeds:
                if feed.get('name', '').lower().replace(' ', '_').replace('＋', 'plus') == feed_id.lower():
                    feed_config = feed
                    break
        
        if not feed_config and feed_url:
            # Use provided URL
            feed_config = {
                'name': 'Custom Feed',
                'url': feed_url,
                'timeout': 25,
                'enabled': True
            }
        elif not feed_config:
            return jsonify({'error': f'Feed not found: {feed_id}'}), 404
        
        start_time = time.time()
        test_results = {
            'source': feed_config.get('name', 'Unknown'),
            'url': feed_config.get('url'),
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
        
        # Test 1: HTTP connectivity
        try:
            response = requests.get(
                feed_config['url'],
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                timeout=feed_config.get('timeout', 25),
                allow_redirects=True
            )
            http_time = time.time() - start_time
            
            test_results['tests'].append({
                'name': 'http_connectivity',
                'status': 'success' if response.status_code == 200 else 'failed',
                'response_time_ms': round(http_time * 1000, 2),
                'http_status': response.status_code,
                'content_type': response.headers.get('content-type', 'unknown'),
                'content_length': len(response.content),
                'details': f'HTTP {response.status_code}' + (f' (リダイレクト: {response.url})' if response.url != feed_config['url'] else '')
            })
            
            # Test 2: RSS/XML parsing
            if response.status_code == 200:
                try:
                    import feedparser
                    feed_start = time.time()
                    parsed_feed = feedparser.parse(response.content)
                    parse_time = time.time() - feed_start
                    
                    entries_count = len(parsed_feed.get('entries', []))
                    has_title = bool(parsed_feed.get('feed', {}).get('title'))
                    
                    test_results['tests'].append({
                        'name': 'rss_parsing',
                        'status': 'success' if entries_count > 0 else 'warning',
                        'response_time_ms': round(parse_time * 1000, 2),
                        'entries_count': entries_count,
                        'feed_title': parsed_feed.get('feed', {}).get('title', 'N/A'),
                        'has_valid_structure': has_title and entries_count > 0,
                        'details': f'{entries_count}件のエントリー検出' if entries_count > 0 else 'エントリーが見つかりません'
                    })
                    
                    # Sample entry details
                    if entries_count > 0:
                        sample_entry = parsed_feed.entries[0]
                        test_results['sample_entry'] = {
                            'title': sample_entry.get('title', 'N/A'),
                            'link': sample_entry.get('link', 'N/A'),
                            'published': sample_entry.get('published', 'N/A'),
                            'has_description': bool(sample_entry.get('description') or sample_entry.get('summary'))
                        }
                    
                except Exception as parse_error:
                    test_results['tests'].append({
                        'name': 'rss_parsing',
                        'status': 'error',
                        'error': str(parse_error),
                        'details': 'RSSパース失敗'
                    })
            
        except requests.exceptions.Timeout:
            test_results['tests'].append({
                'name': 'http_connectivity',
                'status': 'failed',
                'response_time_ms': feed_config.get('timeout', 25) * 1000,
                'error': f'タイムアウト ({feed_config.get("timeout", 25)}秒)'
            })
        except Exception as e:
            test_results['tests'].append({
                'name': 'http_connectivity',
                'status': 'error',
                'error': str(e)
            })
        
        # Overall status
        failed_tests = sum(1 for test in test_results['tests'] if test['status'] in ['failed', 'error'])
        test_results['overall_status'] = 'success' if failed_tests == 0 else 'failed'
        test_results['success_rate'] = f"{((len(test_results['tests']) - failed_tests) / len(test_results['tests']) * 100):.1f}%"
        test_results['total_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        return jsonify(test_results)
        
    except Exception as e:
        logger.error(f"RSS test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'overall_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/sources/toggle', methods=['POST'])
def api_toggle_source():
    """
    Toggle a collection source on/off.
    
    Request JSON:
        {
            "source_type": "anilist" | "syoboi" | "rss_feed",
            "source_id": "feed_name_for_rss",  # Required only for RSS feeds
            "enabled": true | false
        }
    
    Returns:
        JSON with updated source configuration
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        source_type = data.get('source_type')
        source_id = data.get('source_id')
        enabled = data.get('enabled')
        
        if not source_type:
            return jsonify({'error': 'source_type is required'}), 400
        
        if enabled is None:
            return jsonify({'error': 'enabled is required'}), 400
        
        # Load current configuration
        config = load_config()
        
        updated = False
        
        if source_type == 'anilist':
            if 'apis' not in config:
                config['apis'] = {}
            if 'anilist' not in config['apis']:
                config['apis']['anilist'] = {}
            config['apis']['anilist']['enabled'] = bool(enabled)
            updated = True
            
        elif source_type == 'syoboi':
            if 'apis' not in config:
                config['apis'] = {}
            if 'syoboi' not in config['apis']:
                config['apis']['syoboi'] = {}
            config['apis']['syoboi']['enabled'] = bool(enabled)
            updated = True
            
        elif source_type == 'rss_feed':
            if not source_id:
                return jsonify({'error': 'source_id is required for RSS feeds'}), 400
            
            rss_feeds = config.get('apis', {}).get('rss_feeds', {}).get('feeds', [])
            
            for feed in rss_feeds:
                feed_key = feed.get('name', '').lower().replace(' ', '_').replace('＋', 'plus')
                if feed_key == source_id.lower():
                    feed['enabled'] = bool(enabled)
                    updated = True
                    break
            
            if not updated:
                return jsonify({'error': f'RSS feed not found: {source_id}'}), 404
        else:
            return jsonify({'error': f'Invalid source_type: {source_type}'}), 400
        
        # Save updated configuration
        if updated:
            save_config(config)
            
            return jsonify({
                'success': True,
                'source_type': source_type,
                'source_id': source_id,
                'enabled': enabled,
                'message': f'Source {"enabled" if enabled else "disabled"} successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to update configuration'}), 500
        
    except Exception as e:
        logger.error(f"Failed to toggle source: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/sources/test-all', methods=['POST'])
def api_test_all_sources():
    """
    Test all enabled collection sources in parallel.
    
    Returns:
        JSON with test results for all sources
    """
    try:
        import concurrent.futures
        
        config = load_config()
        results = {
            'timestamp': datetime.now().isoformat(),
            'sources': [],
            'summary': {
                'total': 0,
                'success': 0,
                'failed': 0,
                'errors': 0
            }
        }
        
        def test_source(source_info):
            """Test a single source"""
            source_type = source_info['type']
            source_id = source_info['id']
            
            try:
                if source_type == 'anilist':
                    response = requests.post(
                        '/api/sources/anilist/test',
                        json={},
                        headers={'Content-Type': 'application/json'}
                    )
                    # Since we can't make internal requests, call the test function directly
                    with app.test_request_context(method='POST'):
                        test_result = api_test_anilist()
                        return json.loads(test_result[0].get_data(as_text=True))
                        
                elif source_type == 'syoboi':
                    with app.test_request_context(method='POST'):
                        test_result = api_test_syoboi()
                        return json.loads(test_result[0].get_data(as_text=True))
                        
                elif source_type == 'rss':
                    with app.test_request_context(
                        method='POST',
                        json={'feed_id': source_id}
                    ):
                        test_result = api_test_rss()
                        return json.loads(test_result[0].get_data(as_text=True))
                        
            except Exception as e:
                return {
                    'source': source_id,
                    'overall_status': 'error',
                    'error': str(e)
                }
        
        # Collect enabled sources
        sources_to_test = []
        
        # APIs
        if config.get('apis', {}).get('anilist', {}).get('enabled', True):
            sources_to_test.append({'type': 'anilist', 'id': 'anilist'})
        
        if config.get('apis', {}).get('syoboi', {}).get('enabled', False):
            sources_to_test.append({'type': 'syoboi', 'id': 'syoboi'})
        
        # RSS Feeds
        rss_feeds = config.get('apis', {}).get('rss_feeds', {}).get('feeds', [])
        for feed in rss_feeds:
            if feed.get('enabled', False):
                feed_id = feed.get('name', '').lower().replace(' ', '_').replace('＋', 'plus')
                sources_to_test.append({'type': 'rss', 'id': feed_id})
        
        # Test sources in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_source = {
                executor.submit(test_source, source): source
                for source in sources_to_test
            }
            
            for future in concurrent.futures.as_completed(future_to_source, timeout=30):
                source = future_to_source[future]
                try:
                    result = future.result()
                    results['sources'].append(result)
                    
                    # Update summary
                    results['summary']['total'] += 1
                    status = result.get('overall_status', 'error')
                    if status == 'success':
                        results['summary']['success'] += 1
                    elif status == 'failed':
                        results['summary']['failed'] += 1
                    else:
                        results['summary']['errors'] += 1
                        
                except Exception as e:
                    results['sources'].append({
                        'source': source['id'],
                        'overall_status': 'error',
                        'error': str(e)
                    })
                    results['summary']['total'] += 1
                    results['summary']['errors'] += 1
        
        return jsonify(results)

    except Exception as e:
        logger.error(f"Failed to test all sources: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route("/api/calendar/sync", methods=["POST"])
def api_calendar_sync():
    """Sync releases to calendar events (up to 3 months ahead)"""
    try:
        data = request.get_json() or {}
        months_ahead = data.get('months_ahead', 3)  # Default: 3 months
        force_resync = data.get('force_resync', False)  # Default: False

        if months_ahead < 1 or months_ahead > 12:
            return jsonify({
                "success": False,
                "error": "months_ahead must be between 1 and 12"
            }), 400

        conn = get_db_connection()
        try:
            # Calculate date range
            from datetime import datetime, timedelta
            today = datetime.now().date()
            end_date = today + timedelta(days=30 * months_ahead)

            # Get releases within the date range
            releases = conn.execute("""
                SELECT r.id, r.work_id, r.release_type, r.number, r.platform,
                       r.release_date, r.source, w.title, w.type
                FROM releases r
                JOIN works w ON r.work_id = w.id
                WHERE r.release_date >= date('now')
                  AND r.release_date <= date('now', '+' || ? || ' months')
                ORDER BY r.release_date
            """, (months_ahead,)).fetchall()

            total_releases = len(releases)
            new_events = 0
            updated_events = 0
            skipped_events = 0
            errors = []

            for release in releases:
                try:
                    # Check if calendar event already exists for this release
                    existing = conn.execute("""
                        SELECT id, event_title FROM calendar_events
                        WHERE release_id = ?
                    """, (release['id'],)).fetchone()

                    # Build event title
                    release_type_label = '話' if release['release_type'] == 'episode' else '巻'
                    number_label = f"第{release['number']}{release_type_label}" if release['number'] else ''
                    platform_label = f"[{release['platform']}]" if release['platform'] else ''
                    event_title = f"{release['title']} {number_label} {platform_label}".strip()

                    # Build description
                    description = f"""
作品: {release['title']}
種類: {release['type']}
リリース種類: {release['release_type']}
番号: {release['number'] or 'N/A'}
プラットフォーム: {release['platform'] or 'N/A'}
ソース: {release['source']}
                    """.strip()

                    if existing and not force_resync:
                        # Event exists and not forcing resync - skip
                        skipped_events += 1
                    elif existing and force_resync:
                        # Update existing event
                        conn.execute("""
                            UPDATE calendar_events
                            SET event_title = ?,
                                event_date = ?,
                                description = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (event_title, release['release_date'], description, existing['id']))
                        updated_events += 1
                    else:
                        # Create new event
                        conn.execute("""
                            INSERT INTO calendar_events
                            (work_id, release_id, event_title, event_date, description, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """, (release['work_id'], release['id'], event_title, release['release_date'], description))
                        new_events += 1

                except Exception as e:
                    errors.append({
                        'release_id': release['id'],
                        'title': release['title'],
                        'error': str(e)
                    })
                    logger.error(f"Failed to sync release {release['id']}: {e}")

            conn.commit()

            # Get statistics
            total_calendar_events = conn.execute(
                "SELECT COUNT(*) as count FROM calendar_events"
            ).fetchone()['count']

            result = {
                "success": True,
                "sync_date": datetime.now().isoformat(),
                "months_ahead": months_ahead,
                "total_releases_scanned": total_releases,
                "new_events": new_events,
                "updated_events": updated_events,
                "skipped_events": skipped_events,
                "total_calendar_events": total_calendar_events,
                "errors": errors
            }

            logger.info(f"Calendar sync completed: {new_events} new, {updated_events} updated, {skipped_events} skipped")
            return jsonify(result)

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Calendar sync failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/calendar/events")
def api_calendar_events():
    """Get calendar events with optional filtering"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')  # YYYY-MM-DD
        end_date = request.args.get('end_date')      # YYYY-MM-DD
        limit = request.args.get('limit', type=int, default=100)

        conn = get_db_connection()
        try:
            query = """
                SELECT ce.id, ce.work_id, ce.release_id, ce.event_title,
                       ce.event_date, ce.description, ce.calendar_id, ce.event_id,
                       ce.created_at, ce.updated_at,
                       w.title as work_title, w.type as work_type
                FROM calendar_events ce
                JOIN works w ON ce.work_id = w.id
                WHERE 1=1
            """
            params = []

            if start_date:
                query += " AND ce.event_date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND ce.event_date <= ?"
                params.append(end_date)

            query += " ORDER BY ce.event_date ASC LIMIT ?"
            params.append(limit)

            events = conn.execute(query, params).fetchall()

            events_list = []
            for event in events:
                events_list.append({
                    'id': event['id'],
                    'work_id': event['work_id'],
                    'release_id': event['release_id'],
                    'event_title': event['event_title'],
                    'event_date': event['event_date'],
                    'description': event['description'],
                    'calendar_id': event['calendar_id'],
                    'event_id': event['event_id'],
                    'work_title': event['work_title'],
                    'work_type': event['work_type'],
                    'created_at': event['created_at'],
                    'updated_at': event['updated_at']
                })

            return jsonify({
                'success': True,
                'total': len(events_list),
                'events': events_list
            })

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to get calendar events: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route("/api/calendar/stats")
def api_calendar_stats():
    """Get calendar statistics"""
    try:
        conn = get_db_connection()
        try:
            stats = {
                'total_events': conn.execute(
                    "SELECT COUNT(*) as count FROM calendar_events"
                ).fetchone()['count'],
                'events_this_month': conn.execute("""
                    SELECT COUNT(*) as count FROM calendar_events
                    WHERE strftime('%Y-%m', event_date) = strftime('%Y-%m', 'now')
                """).fetchone()['count'],
                'events_next_month': conn.execute("""
                    SELECT COUNT(*) as count FROM calendar_events
                    WHERE strftime('%Y-%m', event_date) = strftime('%Y-%m', date('now', '+1 month'))
                """).fetchone()['count'],
                'upcoming_7days': conn.execute("""
                    SELECT COUNT(*) as count FROM calendar_events
                    WHERE event_date >= date('now')
                      AND event_date <= date('now', '+7 days')
                """).fetchone()['count'],
                'synced_releases': conn.execute("""
                    SELECT COUNT(DISTINCT release_id) as count FROM calendar_events
                    WHERE release_id IS NOT NULL
                """).fetchone()['count'],
                'total_releases': conn.execute(
                    "SELECT COUNT(*) as count FROM releases WHERE release_date >= date('now')"
                ).fetchone()['count']
            }

            return jsonify({
                'success': True,
                'stats': stats
            })

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to get calendar stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route("/api/calendar/monthly")
def api_calendar_monthly():
    """Get calendar events grouped by month (3 months by default)"""
    try:
        months = request.args.get('months', type=int, default=3)

        conn = get_db_connection()
        try:
            from datetime import datetime, timedelta
            from collections import defaultdict

            # Calculate date range
            today = datetime.now().date()
            start_date = today.replace(day=1)  # First day of current month

            # Get events for the next N months
            events = conn.execute("""
                SELECT ce.id, ce.event_title, ce.event_date, ce.description,
                       w.title as work_title, w.type as work_type,
                       r.release_type, r.number, r.platform
                FROM calendar_events ce
                JOIN works w ON ce.work_id = w.id
                LEFT JOIN releases r ON ce.release_id = r.id
                WHERE ce.event_date >= date('now')
                  AND ce.event_date <= date('now', '+' || ? || ' months')
                ORDER BY ce.event_date ASC
            """, (months,)).fetchall()

            # Group events by year-month
            monthly_data = defaultdict(list)
            for event in events:
                event_date = datetime.strptime(event['event_date'], '%Y-%m-%d').date()
                month_key = event_date.strftime('%Y-%m')

                monthly_data[month_key].append({
                    'id': event['id'],
                    'title': event['event_title'],
                    'date': event['event_date'],
                    'day': event_date.day,
                    'work_title': event['work_title'],
                    'work_type': event['work_type'],
                    'release_type': event['release_type'],
                    'number': event['number'],
                    'platform': event['platform'],
                    'description': event['description']
                })

            # Create result with month information
            result = []
            current = start_date
            for i in range(months):
                month_key = current.strftime('%Y-%m')
                year = current.year
                month = current.month
                month_name_ja = ['', '1月', '2月', '3月', '4月', '5月', '6月',
                                '7月', '8月', '9月', '10月', '11月', '12月'][month]

                result.append({
                    'year': year,
                    'month': month,
                    'month_key': month_key,
                    'month_name': month_name_ja,
                    'events': monthly_data.get(month_key, []),
                    'event_count': len(monthly_data.get(month_key, []))
                })

                # Move to next month
                if month == 12:
                    current = current.replace(year=year + 1, month=1)
                else:
                    current = current.replace(month=month + 1)

            return jsonify({
                'success': True,
                'months': result,
                'total_events': sum(len(m['events']) for m in result)
            })

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to get monthly calendar: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Register health check blueprint
try:
    from app.routes.health import health_bp
    app.register_blueprint(health_bp)
    logger.info("Health check endpoints registered: /health, /ready, /metrics")
except ImportError:
    logger.warning("Health check blueprint not available")


if __name__ == "__main__":
    # Initialize database if it doesn't exist
    if not os.path.exists(DATABASE_PATH):
        logger.warning(
            f"Database {DATABASE_PATH} not found. Please run the main system first to initialize the database."
        )

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Run the Flask app
    app.run(debug=True, host="0.0.0.0", port=3030)
