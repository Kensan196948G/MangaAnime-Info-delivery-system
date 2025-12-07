"""
管理者用セキュリティダッシュボード

統計情報、セキュリティアラート、ロック中アカウント、監査ログの可視化
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import sqlite3
from functools import wraps

# ブループリント定義
admin_dash_bp = Blueprint('admin_dashboard', __name__, url_prefix='/admin')

# 管理者権限チェックデコレーター
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


# データベース接続ヘルパー
def get_db_connection():
    """データベース接続を取得"""
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn


# 統計情報取得関数
def get_dashboard_statistics():
    """ダッシュボード用統計情報を取得"""
    conn = get_db_connection()
    cursor = conn.cursor()

    stats = {}

    # ユーザー数
    cursor.execute('SELECT COUNT(*) as count FROM users')
    stats['total_users'] = cursor.fetchone()['count']

    # アクティブユーザー（24時間以内にログイン）
    cursor.execute('''
        SELECT COUNT(*) as count FROM users
        WHERE last_login > datetime('now', '-1 day')
    ''')
    stats['active_users'] = cursor.fetchone()['count']

    # APIキー数
    cursor.execute('SELECT COUNT(*) as count FROM api_keys WHERE is_active = 1')
    stats['active_api_keys'] = cursor.fetchone()['count']

    # 監査ログ数（24時間）
    cursor.execute('''
        SELECT COUNT(*) as count FROM audit_logs
        WHERE timestamp > datetime('now', '-1 day')
    ''')
    stats['audit_logs_24h'] = cursor.fetchone()['count']

    # ロック中アカウント
    cursor.execute('''
        SELECT COUNT(*) as count FROM users
        WHERE locked_until > datetime('now')
    ''')
    stats['locked_accounts'] = cursor.fetchone()['count']

    # 失敗したログイン試行（24時間）
    cursor.execute('''
        SELECT COUNT(*) as count FROM audit_logs
        WHERE action = 'login_failed'
        AND timestamp > datetime('now', '-1 day')
    ''')
    stats['failed_logins_24h'] = cursor.fetchone()['count']

    conn.close()
    return stats


def get_locked_accounts():
    """ロック中アカウント一覧を取得"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, username, email, locked_until, failed_attempts
        FROM users
        WHERE locked_until > datetime('now')
        ORDER BY locked_until DESC
    ''')

    accounts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return accounts


def get_recent_failures(limit=10):
    """最近の失敗ログイン試行を取得"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            al.timestamp,
            al.username,
            al.ip_address,
            al.details,
            u.id as user_id
        FROM audit_logs al
        LEFT JOIN users u ON al.username = u.username
        WHERE al.action = 'login_failed'
        ORDER BY al.timestamp DESC
        LIMIT ?
    ''', (limit,))

    failures = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return failures


def get_security_alerts():
    """セキュリティアラートを生成"""
    alerts = []
    conn = get_db_connection()
    cursor = conn.cursor()

    # 複数回の失敗ログイン（1時間以内に5回以上）
    cursor.execute('''
        SELECT username, ip_address, COUNT(*) as attempts
        FROM audit_logs
        WHERE action = 'login_failed'
        AND timestamp > datetime('now', '-1 hour')
        GROUP BY username, ip_address
        HAVING attempts >= 5
    ''')

    for row in cursor.fetchall():
        alerts.append({
            'level': 'danger',
            'type': 'brute_force',
            'message': f"ブルートフォース攻撃の可能性: {row['username']} from {row['ip_address']} ({row['attempts']}回)",
            'timestamp': datetime.now().isoformat()
        })

    # 24時間以内のロック
    cursor.execute('''
        SELECT username, locked_until
        FROM users
        WHERE locked_until > datetime('now')
        AND locked_until < datetime('now', '+1 day')
    ''')

    for row in cursor.fetchall():
        alerts.append({
            'level': 'warning',
            'type': 'account_locked',
            'message': f"アカウントロック: {row['username']} (解除: {row['locked_until']})",
            'timestamp': datetime.now().isoformat()
        })

    # APIキー使用量異常（1時間に100回以上）
    cursor.execute('''
        SELECT al.details, COUNT(*) as count
        FROM audit_logs al
        WHERE al.action = 'api_request'
        AND al.timestamp > datetime('now', '-1 hour')
        GROUP BY al.details
        HAVING count > 100
    ''')

    for row in cursor.fetchall():
        alerts.append({
            'level': 'info',
            'type': 'high_api_usage',
            'message': f"APIキー使用量が高い: {row['details']} ({row['count']}回/時)",
            'timestamp': datetime.now().isoformat()
        })

    conn.close()
    return alerts


def get_audit_statistics():
    """監査ログ統計を取得"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # アクション別統計（24時間）
    cursor.execute('''
        SELECT action, COUNT(*) as count
        FROM audit_logs
        WHERE timestamp > datetime('now', '-1 day')
        GROUP BY action
        ORDER BY count DESC
    ''')

    action_stats = [dict(row) for row in cursor.fetchall()]

    # 時間別統計（過去24時間、1時間ごと）
    cursor.execute('''
        SELECT
            strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
            COUNT(*) as count
        FROM audit_logs
        WHERE timestamp > datetime('now', '-1 day')
        GROUP BY hour
        ORDER BY hour
    ''')

    hourly_stats = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        'action_stats': action_stats,
        'hourly_stats': hourly_stats
    }


def get_api_usage_stats():
    """API使用統計を取得"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # APIキー別使用回数（24時間）
    cursor.execute('''
        SELECT
            ak.key_name,
            ak.key_prefix,
            COUNT(al.id) as request_count
        FROM api_keys ak
        LEFT JOIN audit_logs al
            ON al.details LIKE '%' || ak.key_prefix || '%'
            AND al.action = 'api_request'
            AND al.timestamp > datetime('now', '-1 day')
        WHERE ak.is_active = 1
        GROUP BY ak.id
        ORDER BY request_count DESC
        LIMIT 10
    ''')

    api_usage = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return api_usage


# ===============================
# ルート定義
# ===============================

@admin_dash_bp.route('/dashboard')
@admin_required
def dashboard():
    """メインダッシュボード"""
    stats = get_dashboard_statistics()
    locked_accounts = get_locked_accounts()
    recent_failures = get_recent_failures(limit=10)
    security_alerts = get_security_alerts()

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        locked_accounts=locked_accounts,
        recent_failures=recent_failures,
        security_alerts=security_alerts
    )


@admin_dash_bp.route('/security')
@admin_required
def security():
    """セキュリティ専用ダッシュボード"""
    audit_stats = get_audit_statistics()
    api_usage = get_api_usage_stats()
    security_alerts = get_security_alerts()

    return render_template(
        'admin/security.html',
        audit_stats=audit_stats,
        api_usage=api_usage,
        security_alerts=security_alerts
    )


# ===============================
# API エンドポイント
# ===============================

@admin_dash_bp.route('/api/dashboard-stats')
@admin_required
def api_dashboard_stats():
    """ダッシュボード統計JSON"""
    stats = get_dashboard_statistics()
    return jsonify(stats)


@admin_dash_bp.route('/api/security-alerts')
@admin_required
def api_security_alerts():
    """セキュリティアラートJSON"""
    alerts = get_security_alerts()
    return jsonify({'alerts': alerts})


@admin_dash_bp.route('/api/audit-stats')
@admin_required
def api_audit_stats():
    """監査ログ統計JSON"""
    stats = get_audit_statistics()
    return jsonify(stats)


@admin_dash_bp.route('/api/api-usage')
@admin_required
def api_api_usage():
    """API使用統計JSON"""
    usage = get_api_usage_stats()
    return jsonify({'usage': usage})


@admin_dash_bp.route('/api/unlock-account/<int:user_id>', methods=['POST'])
@admin_required
def api_unlock_account(user_id):
    """アカウントロック解除"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE users
            SET locked_until = NULL, failed_attempts = 0
            WHERE id = ?
        ''', (user_id,))

        conn.commit()

        # 監査ログ記録
        cursor.execute('''
            INSERT INTO audit_logs (action, username, ip_address, details)
            VALUES (?, ?, ?, ?)
        ''', (
import logging

logger = logging.getLogger(__name__)

            'account_unlocked',

logger = logging.getLogger(__name__)

            current_user.username,
            request.remote_addr,
            f'Unlocked user_id: {user_id}'
        ))
        conn.commit()

        return jsonify({'success': True, 'message': 'アカウントのロックを解除しました'})

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        conn.close()
