from datetime import datetime

"""
Flask Web UI for Manga/Anime Information Delivery System
アニメ・マンガ情報配信システム Web UI
"""

import json
import logging
import os
import sqlite3

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect

from modules.dashboard import dashboard_bp, dashboard_service
from modules.db import DatabaseManager
from modules.monitoring import SystemMonitor

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# セキュリティ: secret_keyを環境変数から取得
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    # 開発環境用フォールバック（本番では必ず環境変数を設定すること）
    import warnings

    warnings.warn("SECRET_KEY not set! Using fallback for development only.", RuntimeWarning)
    app.secret_key = "dev-fallback-key-not-for-production-use"

# CSRF保護を有効化
csrf = CSRFProtect(app)

# Jinja2グローバル関数の追加
app.jinja_env.globals["min"] = min
app.jinja_env.globals["max"] = max


# APIエンドポイントはCSRF除外（JSONリクエスト用）
@app.before_request
def csrf_protect_exclude_api():
    if request.path.startswith("/api/") and request.method in ["POST", "PUT", "DELETE"]:
        # API呼び出しはCSRFトークン不要（代わりにAPI認証で保護）
        pass


# セキュリティヘッダーを追加
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ダッシュボード Blueprint を登録
app.register_blueprint(dashboard_bp)

# グローバル変数
db_manager = DatabaseManager()

# 設定ファイル読み込み
_config = {}
_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
if os.path.exists(_config_path):
    with open(_config_path, "r", encoding="utf-8") as f:
        _config = json.load(f)

performance_monitor = SystemMonitor(_config)


# カスタムテンプレートフィルター
@app.template_filter("work_type_label")
def work_type_label_filter(work_type):
    """作品タイプのラベルを返す"""
    labels = {"anime": "アニメ", "manga": "マンガ", "novel": "小説", "other": "その他"}
    return labels.get(work_type, work_type or "不明")


@app.template_filter("release_type_label")
def release_type_label_filter(release_type):
    """リリースタイプのラベルを返す"""
    labels = {
        "episode": "話",
        "volume": "巻",
        "chapter": "章",
        "movie": "映画",
        "ova": "OVA",
        "special": "特別編",
    }
    return labels.get(release_type, release_type or "不明")


@app.template_filter("datetime_format")
def datetime_format_filter(value, format="%Y-%m-%d"):
    """日付/日時を指定フォーマットで文字列化するフィルター"""
    if value is None:
        return "-"
    try:
        if isinstance(value, str):
            # 文字列の場合、まずパースを試みる
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"]:
                try:
                    value = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
            else:
                return value  # パース失敗時は元の文字列を返す
        if isinstance(value, datetime):
            return value.strftime(format)
        return str(value)
    except (ValueError, TypeError):
        return str(value) if value else "-"


@app.route("/")
def index():
    """メインページ"""
    try:
        # 最新のリリース情報を取得
        with sqlite3.connect("db.sqlite3") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT w.title, r.release_type, r.number, r.platform,
                       r.release_date, r.notified, w.type
                FROM releases r
                JOIN works w ON r.work_id = w.id
                ORDER BY r.release_date DESC, r.created_at DESC
                LIMIT 50
            """)
            releases = [dict(row) for row in cursor.fetchall()]

            # 統計情報を取得
            cursor = conn.execute("SELECT COUNT(*) as count FROM works")
            total_works = cursor.fetchone()["count"]

            cursor = conn.execute("SELECT COUNT(*) as count FROM releases WHERE notified = 1")
            notified_releases = cursor.fetchone()["count"]

            cursor = conn.execute("""
                SELECT COUNT(*) as count FROM releases
                WHERE release_date >= date('now') AND release_date <= date('now', '+7 days')
            """)
            upcoming_releases = cursor.fetchone()["count"]

    except Exception as e:
        logger.error(f"Error loading index page: {e}")
        releases = []
        total_works = 0
        notified_releases = 0
        upcoming_releases = 0

    stats = {
        "total_works": total_works,
        "notified_releases": notified_releases,
        "upcoming_releases": upcoming_releases,
    }

    return render_template("index.html", releases=releases, stats=stats, now=datetime.now())


@app.route("/works")
def works():
    """作品一覧ページ"""
    try:
        search_query = request.args.get("search", "").strip()
        work_type = request.args.get("type", "").strip()
        page = request.args.get("page", 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page

        with sqlite3.connect("db.sqlite3") as conn:
            conn.row_factory = sqlite3.Row

            # カウントクエリ
            count_query = "SELECT COUNT(*) as total FROM works w WHERE 1=1"
            count_params = []

            if search_query:
                count_query += " AND (w.title LIKE ? OR w.title_kana LIKE ? OR w.title_en LIKE ?)"
                search_param = f"%{search_query}%"
                count_params.extend([search_param, search_param, search_param])

            if work_type:
                count_query += " AND w.type = ?"
                count_params.append(work_type)

            count_cursor = conn.execute(count_query, count_params)
            total = count_cursor.fetchone()["total"]

            # 基本クエリ
            query = """
                SELECT w.*,
                       COUNT(r.id) as release_count,
                       MAX(r.release_date) as latest_release
                FROM works w
                LEFT JOIN releases r ON w.id = r.work_id
                WHERE 1=1
            """
            params = []

            # 検索条件を追加
            if search_query:
                query += " AND (w.title LIKE ? OR w.title_kana LIKE ? OR w.title_en LIKE ?)"
                search_param = f"%{search_query}%"
                params.extend([search_param, search_param, search_param])

            if work_type:
                query += " AND w.type = ?"
                params.append(work_type)

            query += " GROUP BY w.id ORDER BY w.created_at DESC LIMIT ? OFFSET ?"
            params.extend([per_page, offset])

            cursor = conn.execute(query, params)
            works_data = [dict(row) for row in cursor.fetchall()]

        # ページネーション情報
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        pagination = {
            "total_pages": total_pages,
            "current_page": page,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "prev_page": page - 1 if page > 1 else None,
            "next_page": page + 1 if page < total_pages else None,
            "total": total,
        }

    except Exception as e:
        logger.error(f"Error loading works page: {e}")
        works_data = []
        pagination = {
            "total_pages": 1,
            "current_page": 1,
            "has_prev": False,
            "has_next": False,
            "total": 0,
        }
        search_query = ""
        work_type = ""

    return render_template(
        "works.html",
        works=works_data,
        search_query=search_query,
        current_type=work_type,
        pagination=pagination,
        now=datetime.now(),
        total_count=pagination["total"],
    )


@app.route("/work/<int:work_id>")
def work_detail(work_id):
    """作品詳細ページ"""
    try:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.row_factory = sqlite3.Row

            # 作品情報を取得
            cursor = conn.execute("SELECT * FROM works WHERE id = ?", (work_id,))
            work = cursor.fetchone()

            if not work:
                flash("指定された作品が見つかりません。", "error")
                return redirect(url_for("works"))

            # リリース情報を取得
            cursor = conn.execute(
                """
                SELECT * FROM releases
                WHERE work_id = ?
                ORDER BY release_date DESC, created_at DESC
            """,
                (work_id,),
            )
            releases = [dict(row) for row in cursor.fetchall()]

    except Exception as e:
        logger.error(f"Error loading work detail for ID {work_id}: {e}")
        flash("作品詳細の読み込みでエラーが発生しました。", "error")
        return redirect(url_for("works"))

    return render_template("work_detail.html", work=dict(work), releases=releases)


@app.route("/settings")
def settings():
    """設定ページ"""
    try:
        # 設定ファイルが存在するかチェック
        config_exists = os.path.exists("config.json")
        config_data = {}

        if config_exists:
            with open("config.json", "r", encoding="utf-8") as f:
                config_data = json.load(f)

    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        config_exists = False
        config_data = {}

    return render_template("settings.html", config_exists=config_exists, config=config_data)


@app.route("/api/trigger-collection", methods=["POST"])
def api_trigger_collection():
    """手動データ収集トリガー API"""
    try:
        # パフォーマンス監視開始
        with performance_monitor.measure_time("manual_collection"):
            # ここで実際のデータ収集処理を呼び出す
            # release_notifier.py の main() 関数を呼び出すか、
            # 必要な収集処理を実行

            # ダッシュボード統計を更新
            dashboard_service.record_metric(
                "manual_collection",
                1,
                "counter",
                source="web_ui",
                metadata={"timestamp": datetime.now().isoformat()},
            )

            # システムヘルス状態を更新
            dashboard_service.update_system_health(
                "manual_collection", "healthy", performance_score=1.0
            )

        return jsonify(
            {
                "success": True,
                "message": "データ収集を開始しました",
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error triggering collection: {e}")

        # エラー時のダッシュボード更新
        dashboard_service.update_system_health("manual_collection", "error", error_message=str(e))

        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            500,
        )


@app.route("/api/system-stats")
def api_system_stats():
    """システム統計情報 API"""
    try:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.row_factory = sqlite3.Row

            # 基本統計
            cursor = conn.execute("SELECT COUNT(*) as count FROM works")
            total_works = cursor.fetchone()["count"]

            cursor = conn.execute("SELECT COUNT(*) as count FROM works WHERE type = 'anime'")
            anime_count = cursor.fetchone()["count"]

            cursor = conn.execute("SELECT COUNT(*) as count FROM works WHERE type = 'manga'")
            manga_count = cursor.fetchone()["count"]

            cursor = conn.execute("SELECT COUNT(*) as count FROM releases WHERE notified = 1")
            total_notifications = cursor.fetchone()["count"]

            cursor = conn.execute("""
                SELECT COUNT(*) as count FROM releases
                WHERE notified = 1 AND created_at > datetime('now', '-24 hours')
            """)
            recent_notifications = cursor.fetchone()["count"]

            return jsonify(
                {
                    "total_works": total_works,
                    "anime_count": anime_count,
                    "manga_count": manga_count,
                    "total_notifications": total_notifications,
                    "recent_notifications": recent_notifications,
                    "timestamp": datetime.now().isoformat(),
                }
            )

    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500


@app.route("/releases")
def releases():
    """リリース履歴ページ"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page

        with sqlite3.connect("db.sqlite3") as conn:
            conn.row_factory = sqlite3.Row

            # 総件数を取得
            count_cursor = conn.execute("SELECT COUNT(*) as total FROM releases")
            total = count_cursor.fetchone()["total"]

            cursor = conn.execute(
                """
                SELECT w.title, r.release_type, r.number, r.platform,
                       r.release_date, r.notified, w.type, r.source_url, r.created_at
                FROM releases r
                JOIN works w ON r.work_id = w.id
                ORDER BY r.release_date DESC, r.created_at DESC
                LIMIT ? OFFSET ?
            """,
                (per_page, offset),
            )
            releases_list = [dict(row) for row in cursor.fetchall()]

        # ページネーション情報
        total_pages = (total + per_page - 1) // per_page
        pagination = {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "prev_num": page - 1 if page > 1 else None,
            "next_num": page + 1 if page < total_pages else None,
        }
    except Exception as e:
        logger.error(f"Error loading releases: {e}")
        releases_list = []
        pagination = {
            "page": 1,
            "per_page": 20,
            "total": 0,
            "pages": 0,
            "has_prev": False,
            "has_next": False,
        }
    return render_template(
        "releases.html",
        releases=releases_list,
        pagination=pagination,
        now=datetime.now(),
        current_page=pagination["page"],
        total_pages=pagination["pages"],
        work_type=request.args.get("type", ""),
        platform=request.args.get("platform", ""),
        search=request.args.get("search", ""),
    )


@app.route("/calendar")
def calendar():
    """カレンダーページ"""
    return render_template("calendar.html")


@app.route("/config")
def config():
    """設定ページ（configエンドポイント）"""
    try:
        config_exists = os.path.exists("config.json")
        config_data = {}
        if config_exists:
            with open("config.json", "r", encoding="utf-8") as f:
                config_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        config_exists = False
        config_data = {}
    return render_template("config.html", config_exists=config_exists, config=config_data)


@app.route("/logs")
def logs():
    """ログ表示ページ"""
    return render_template("logs.html")


@app.route("/collection-dashboard")
def collection_dashboard():
    """収集ダッシュボードページ"""
    return render_template("collection_dashboard.html")


@app.route("/data-browser")
def data_browser():
    """データブラウザページ"""
    return render_template("data_browser.html")


@app.route("/collection-settings")
def collection_settings():
    """収集設定ページ"""
    return render_template("collection_settings.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    # データベースの初期化
    db_manager.initialize_database()

    # 開発モードでの実行
    app.run(debug=True, host="0.0.0.0", port=5000)
