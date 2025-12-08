"""
ウォッチリスト機能のルート定義
作成日: 2025-12-07
"""

import logging
import sqlite3

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

logger = logging.getLogger(__name__)

watchlist_bp = Blueprint("watchlist", __name__, url_prefix="/watchlist")

DB_PATH = "db.sqlite3"


def get_db_connection():
    """データベース接続を取得"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@watchlist_bp.route("/")
@login_required
def watchlist_page():
    """ウォッチリストページを表示"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # ユーザーのウォッチリストを取得
        query = """
        SELECT
            w.id,
            w.work_id,
            w.notify_new_episodes,
            w.notify_new_volumes,
            w.created_at,
            works.title,
            works.title_kana,
            works.title_en,
            works.type,
            works.official_url,
            COUNT(DISTINCT CASE WHEN r.release_type = 'episode' THEN r.id END) as episode_count,
            COUNT(DISTINCT CASE WHEN r.release_type = 'volume' THEN r.id END) as volume_count,
            MAX(r.release_date) as latest_release
        FROM watchlist w
        JOIN works ON w.work_id = works.id
        LEFT JOIN releases r ON works.id = r.work_id
        WHERE w.user_id = ?
        GROUP BY w.id, w.work_id, works.title
        ORDER BY w.created_at DESC
        """

        cursor.execute(query, (current_user.id,))
        watchlist_items = cursor.fetchall()

        conn.close()

        return render_template(
            "watchlist.html", watchlist=watchlist_items, user=current_user
        )

    except Exception as e:
        logger.error(f"ウォッチリスト取得エラー: {str(e)}")
        return render_template(
            "watchlist.html",
            watchlist=[],
            error="ウォッチリストの取得に失敗しました",
            user=current_user,
        )


@watchlist_bp.route("/api/list", methods=["GET"])
@login_required
def get_watchlist_api():
    """ウォッチリストをJSON形式で取得（API）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            w.id,
            w.work_id,
            w.notify_new_episodes,
            w.notify_new_volumes,
            w.created_at,
            works.title,
            works.title_kana,
            works.title_en,
            works.type,
            works.official_url
        FROM watchlist w
        JOIN works ON w.work_id = works.id
        WHERE w.user_id = ?
        ORDER BY w.created_at DESC
        """

        cursor.execute(query, (current_user.id,))
        rows = cursor.fetchall()

        watchlist = []
        for row in rows:
            watchlist.append(
                {
                    "id": row["id"],
                    "work_id": row["work_id"],
                    "notify_new_episodes": bool(row["notify_new_episodes"]),
                    "notify_new_volumes": bool(row["notify_new_volumes"]),
                    "created_at": row["created_at"],
                    "work": {
                        "title": row["title"],
                        "title_kana": row["title_kana"],
                        "title_en": row["title_en"],
                        "type": row["type"],
                        "official_url": row["official_url"],
                    },
                }
            )

        conn.close()

        return jsonify(
            {"success": True, "watchlist": watchlist, "count": len(watchlist)}
        )

    except Exception as e:
        logger.error(f"ウォッチリスト取得エラー（API）: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@watchlist_bp.route("/api/add", methods=["POST"])
@login_required
def add_to_watchlist():
    """作品をウォッチリストに追加"""
    try:
        data = request.get_json()
        work_id = data.get("work_id")

        if not work_id:
            return (
                jsonify({"success": False, "error": "work_idが指定されていません"}),
                400,
            )

        conn = get_db_connection()
        cursor = conn.cursor()

        # 作品が存在するか確認
        cursor.execute("SELECT id, title FROM works WHERE id = ?", (work_id,))
        work = cursor.fetchone()

        if not work:
            conn.close()
            return (
                jsonify({"success": False, "error": "指定された作品が見つかりません"}),
                404,
            )

        # ウォッチリストに追加（既に存在する場合は無視）
        try:
            cursor.execute(
                """
                INSERT INTO watchlist (user_id, work_id, notify_new_episodes, notify_new_volumes)
                VALUES (?, ?, 1, 1)
            """,
                (current_user.id, work_id),
            )

            conn.commit()
            watchlist_id = cursor.lastrowid

            logger.info(f"ウォッチリスト追加: user={current_user.id}, work={work_id}")

            conn.close()

            return jsonify(
                {
                    "success": True,
                    "message": f'「{work["title"]}」をウォッチリストに追加しました',
                    "watchlist_id": watchlist_id,
                    "work": {"id": work["id"], "title": work["title"]},
                }
            )

        except sqlite3.IntegrityError:
            conn.close()
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "この作品は既にウォッチリストに登録されています",
                    }
                ),
                409,
            )

    except Exception as e:
        logger.error(f"ウォッチリスト追加エラー: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@watchlist_bp.route("/api/remove/<int:work_id>", methods=["DELETE"])
@login_required
def remove_from_watchlist(work_id):
    """作品をウォッチリストから削除"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 作品情報を取得
        cursor.execute(
            """
            SELECT w.id, works.title
            FROM watchlist w
            JOIN works ON w.work_id = works.id
            WHERE w.user_id = ? AND w.work_id = ?
        """,
            (current_user.id, work_id),
        )

        item = cursor.fetchone()

        if not item:
            conn.close()
            return (
                jsonify(
                    {"success": False, "error": "ウォッチリストに登録されていません"}
                ),
                404,
            )

        # 削除実行
        cursor.execute(
            """
            DELETE FROM watchlist
            WHERE user_id = ? AND work_id = ?
        """,
            (current_user.id, work_id),
        )

        conn.commit()

        logger.info(f"ウォッチリスト削除: user={current_user.id}, work={work_id}")

        conn.close()

        return jsonify(
            {
                "success": True,
                "message": f'「{item["title"]}」をウォッチリストから削除しました',
            }
        )

    except Exception as e:
        logger.error(f"ウォッチリスト削除エラー: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@watchlist_bp.route("/api/update/<int:work_id>", methods=["PUT"])
@login_required
def update_watchlist_settings(work_id):
    """ウォッチリストの通知設定を更新"""
    try:
        data = request.get_json()
        notify_episodes = data.get("notify_new_episodes", True)
        notify_volumes = data.get("notify_new_volumes", True)

        conn = get_db_connection()
        cursor = conn.cursor()

        # 更新実行
        cursor.execute(
            """
            UPDATE watchlist
            SET notify_new_episodes = ?,
                notify_new_volumes = ?
            WHERE user_id = ? AND work_id = ?
        """,
            (int(notify_episodes), int(notify_volumes), current_user.id, work_id),
        )

        if cursor.rowcount == 0:
            conn.close()
            return (
                jsonify(
                    {"success": False, "error": "ウォッチリストに登録されていません"}
                ),
                404,
            )

        conn.commit()
        conn.close()

        logger.info(f"ウォッチリスト設定更新: user={current_user.id}, work={work_id}")

        return jsonify(
            {
                "success": True,
                "message": "通知設定を更新しました",
                "settings": {
                    "notify_new_episodes": notify_episodes,
                    "notify_new_volumes": notify_volumes,
                },
            }
        )

    except Exception as e:
        logger.error(f"ウォッチリスト設定更新エラー: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@watchlist_bp.route("/api/check/<int:work_id>", methods=["GET"])
@login_required
def check_watchlist_status(work_id):
    """作品がウォッチリストに登録されているか確認"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, notify_new_episodes, notify_new_volumes
            FROM watchlist
            WHERE user_id = ? AND work_id = ?
        """,
            (current_user.id, work_id),
        )

        item = cursor.fetchone()
        conn.close()

        if item:
            return jsonify(
                {
                    "success": True,
                    "in_watchlist": True,
                    "notify_new_episodes": bool(item["notify_new_episodes"]),
                    "notify_new_volumes": bool(item["notify_new_volumes"]),
                }
            )
        else:
            return jsonify({"success": True, "in_watchlist": False})

    except Exception as e:
        logger.error(f"ウォッチリスト状態確認エラー: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@watchlist_bp.route("/api/stats", methods=["GET"])
@login_required
def get_watchlist_stats():
    """ウォッチリストの統計情報を取得"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 統計情報取得
        cursor.execute(
            """
            SELECT
                COUNT(*) as total_count,
                SUM(CASE WHEN works.type = 'anime' THEN 1 ELSE 0 END) as anime_count,
                SUM(CASE WHEN works.type = 'manga' THEN 1 ELSE 0 END) as manga_count,
                SUM(notify_new_episodes) as notify_episodes_count,
                SUM(notify_new_volumes) as notify_volumes_count
            FROM watchlist w
            JOIN works ON w.work_id = works.id
            WHERE w.user_id = ?
        """,
            (current_user.id,),
        )

        stats = cursor.fetchone()
        conn.close()

        return jsonify(
            {
                "success": True,
                "stats": {
                    "total": stats["total_count"] or 0,
                    "anime": stats["anime_count"] or 0,
                    "manga": stats["manga_count"] or 0,
                    "notify_episodes": stats["notify_episodes_count"] or 0,
                    "notify_volumes": stats["notify_volumes_count"] or 0,
                },
            }
        )

    except Exception as e:
        logger.error(f"ウォッチリスト統計取得エラー: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
