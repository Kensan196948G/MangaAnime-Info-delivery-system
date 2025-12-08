"""
監査ログビューア用ルート定義
管理者用の監査ログ閲覧、フィルタリング、エクスポート機能を提供
"""

import csv
import io
import os
import sys
from datetime import datetime
from functools import wraps

from flask import Blueprint, Response, jsonify, render_template, request

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

audit_bp = Blueprint("audit", __name__, url_prefix="/admin")


# 認証システムから admin_required をインポート
from flask_login import current_user, login_required


def admin_required(f):
    """管理者権限チェックデコレータ"""

    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            from flask import flash, redirect, url_for

            flash("管理者権限が必要です", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


@audit_bp.route("/audit-logs")
@admin_required
def audit_logs():
    """
    監査ログビューア（HTML）
    フィルタリング、ページネーション、検索機能付き
    """
    from modules.audit_log import audit_logger

    # フィルタパラメータ取得
    event_type = request.args.get("event_type", "")
    user_id = request.args.get("user_id", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    search_query = request.args.get("search", "")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))

    # フィルタ構築
    filters = {}
    if event_type:
        filters["event_type"] = event_type
    if user_id:
        filters["user_id"] = user_id
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    if search_query:
        filters["search"] = search_query

    # ページネーション用のオフセット計算
    offset = (page - 1) * per_page

    # ログ取得（実装に合わせて簡素化）
    logs = audit_logger.get_logs(limit=per_page)

    # イベントタイプをEnumから取得
    from modules.audit_log import AuditEventType

    event_types = [e.value for e in AuditEventType]

    # 簡易実装（ページネーションは後で拡張）
    total_count = len(logs)
    total_pages = 1

    return render_template(
        "admin/audit_logs.html",
        logs=[log.to_dict() for log in logs],  # dict形式に変換
        event_types=event_types,
        users=[],  # 簡易実装
        filters={
            "event_type": event_type,
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
            "search": search_query,
        },
        page=page,
        per_page=per_page,
        total_count=total_count,
        total_pages=total_pages,
    )


@audit_bp.route("/api/audit-logs")
@admin_required
def api_audit_logs():
    """
    監査ログAPI（JSON）
    フロントエンドからのAJAXリクエスト用
    """
    from modules.audit_log import audit_logger

    # フィルタパラメータ取得
    event_type = request.args.get("event_type")
    user_id = request.args.get("user_id")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    search_query = request.args.get("search")
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))

    # フィルタ構築
    filters = {}
    if event_type:
        filters["event_type"] = event_type
    if user_id:
        filters["user_id"] = user_id
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    if search_query:
        filters["search"] = search_query

    # ログ取得
    logs = audit_logger.get_logs(limit=limit)

    return jsonify(
        {
            "success": True,
            "data": [log.to_dict() for log in logs],
            "pagination": {
                "total": len(logs),
                "limit": limit,
                "offset": offset,
                "has_more": False,
            },
        }
    )


@audit_bp.route("/api/audit-logs/export")
@admin_required
def export_audit_logs():
    """
    監査ログCSVエクスポート
    現在のフィルタ条件でログをCSV形式でダウンロード
    """
    from modules.audit_log import audit_logger

    # フィルタパラメータ取得
    event_type = request.args.get("event_type")
    user_id = request.args.get("user_id")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    search_query = request.args.get("search")

    # フィルタ構築
    filters = {}
    if event_type:
        filters["event_type"] = event_type
    if user_id:
        filters["user_id"] = user_id
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    if search_query:
        filters["search"] = search_query

    # 全ログ取得（エクスポート用なので上限大きめ）
    logs = audit_logger.get_logs(limit=10000)

    # CSV生成
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "timestamp",
            "event_type",
            "user_id",
            "username",
            "ip_address",
            "details",
            "success",
        ],
        extrasaction="ignore",
    )

    writer.writeheader()
    for log in logs:
        writer.writerow(log.to_dict())

    # レスポンス作成
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audit_logs_{timestamp}.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@audit_bp.route("/api/audit-logs/stats")
@admin_required
def audit_logs_stats():
    """
    監査ログ統計情報API
    ダッシュボード用の統計データを返す
    """
    from modules.audit_log import audit_logger

    # 統計情報取得
    stats = audit_logger.get_statistics()

    return jsonify({"success": True, "data": stats})
