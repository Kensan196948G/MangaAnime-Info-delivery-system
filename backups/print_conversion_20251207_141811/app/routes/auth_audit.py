"""
認証ルート - 監査ログ統合版

すべての認証イベントに監査ログを記録します。

Features:
- ログイン成功/失敗の追跡
- ログアウトイベント記録
- セッション管理の監査
- IPアドレス・User-Agent記録
- 不審なアクティビティ検出
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
from typing import Optional, Dict, Any
import logging

from modules.audit_log import (
    audit_logger,
    AuditEventType,
    log_auth_event,
    log_security_event
)

logger = logging.getLogger(__name__)

auth_bp = Bluelogger.info('auth', __name__, url_prefix='/api/auth')


def get_client_info() -> Dict[str, str]:
    """クライアント情報を取得"""
    return {
        'ip_address': request.remote_addr or 'unknown',
        'user_agent': request.headers.get('User-Agent', 'unknown')
    }


def get_user_info() -> Dict[str, Optional[str]]:
    """セッションからユーザー情報を取得"""
    return {
        'user_id': session.get('user_id'),
        'username': session.get('username')
    }


def require_auth(f):
    """認証が必要なエンドポイント用デコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            client_info = get_client_info()
            log_security_event(
                event_type=AuditEventType.SECURITY_PERMISSION_DENIED,
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent'],
                details={
                    'endpoint': request.endpoint,
                    'method': request.method,
                    'reason': 'not_authenticated'
                }
            )
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    ログイン

    Request Body:
        {
            "username": "admin",
            "password": "password123"
        }

    Returns:
        200: ログイン成功
        401: 認証失敗
    """
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    client_info = get_client_info()

    # バリデーション
    if not username or not password:
        log_auth_event(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            username=username,
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            success=False,
            details={
                'reason': 'missing_credentials',
                'username_provided': bool(username),
                'password_provided': bool(password)
            }
        )
        return jsonify({'error': 'Username and password required'}), 400

    # 簡易認証（実際はデータベースと照合）
    # TODO: 本番環境では適切な認証システムを実装
    if username == "admin" and password == "admin":
        # ログイン成功
        session['user_id'] = username
        session['username'] = username
        session.permanent = True

        log_auth_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            user_id=username,
            username=username,
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            success=True,
            details={
                'method': 'password',
                'session_id': session.get('_id', 'unknown')
            }
        )

        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': username,
                'username': username
            }
        }), 200
    else:
        # ログイン失敗
        log_auth_event(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            username=username,
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            success=False,
            details={
                'reason': 'invalid_credentials',
                'username': username
            }
        )

        # ブルートフォース攻撃検出
        recent_failures = audit_logger.get_logs(
            limit=10,
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            ip_address=client_info['ip_address']
        )

        if len(recent_failures) >= 5:
            log_security_event(
                event_type=AuditEventType.SECURITY_SUSPICIOUS_ACTIVITY,
                username=username,
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent'],
                details={
                    'type': 'brute_force_attempt',
                    'failed_attempts': len(recent_failures),
                    'username': username
                }
            )
            logger.warning(
                f"Possible brute force attack from {client_info['ip_address']} "
                f"({len(recent_failures)} failed login attempts)"
            )

        return jsonify({'error': 'Invalid credentials'}), 401


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """
    ログアウト

    Returns:
        200: ログアウト成功
    """
    user_info = get_user_info()
    client_info = get_client_info()

    log_auth_event(
        event_type=AuditEventType.AUTH_LOGOUT,
        user_id=user_info['user_id'],
        username=user_info['username'],
        ip_address=client_info['ip_address'],
        user_agent=client_info['user_agent'],
        success=True,
        details={
            'session_id': session.get('_id', 'unknown')
        }
    )

    session.clear()

    return jsonify({'message': 'Logout successful'}), 200


@auth_bp.route('/session', methods=['GET'])
@require_auth
def get_session():
    """
    セッション情報取得

    Returns:
        200: セッション情報
    """
    user_info = get_user_info()
    client_info = get_client_info()

    log_auth_event(
        event_type=AuditEventType.AUTH_SESSION_REFRESH,
        user_id=user_info['user_id'],
        username=user_info['username'],
        ip_address=client_info['ip_address'],
        user_agent=client_info['user_agent'],
        success=True,
        details={
            'action': 'session_check'
        }
    )

    return jsonify({
        'user': {
            'id': user_info['user_id'],
            'username': user_info['username']
        },
        'authenticated': True
    }), 200


@auth_bp.route('/password/reset', methods=['POST'])
def reset_password():
    """
    パスワードリセット要求

    Request Body:
        {
            "email": "user@example.com"
        }

    Returns:
        200: リセットメール送信成功
    """
    data = request.get_json() or {}
    email = data.get('email', '').strip()

    client_info = get_client_info()

    if not email:
        return jsonify({'error': 'Email required'}), 400

    # TODO: 実際のパスワードリセットロジックを実装
    # メール送信、トークン生成など

    log_auth_event(
        event_type=AuditEventType.AUTH_PASSWORD_RESET,
        username=email,
        ip_address=client_info['ip_address'],
        user_agent=client_info['user_agent'],
        success=True,
        details={
            'email': email,
            'action': 'reset_requested'
        }
    )

    return jsonify({
        'message': 'Password reset email sent',
        'email': email
    }), 200


@auth_bp.route('/password/change', methods=['POST'])
@require_auth
def change_password():
    """
    パスワード変更

    Request Body:
        {
            "old_password": "old123",
            "new_password": "new456"
        }

    Returns:
        200: パスワード変更成功
        400: バリデーションエラー
        401: 現在のパスワードが不正
    """
    data = request.get_json() or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    user_info = get_user_info()
    client_info = get_client_info()

    if not old_password or not new_password:
        return jsonify({'error': 'Old and new passwords required'}), 400

    # パスワード強度チェック
    if len(new_password) < 8:
        log_auth_event(
            event_type=AuditEventType.AUTH_PASSWORD_CHANGE,
            user_id=user_info['user_id'],
            username=user_info['username'],
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            success=False,
            details={
                'reason': 'password_too_weak',
                'min_length': 8
            }
        )
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    # TODO: 実際のパスワード検証と変更ロジック

    log_auth_event(
        event_type=AuditEventType.AUTH_PASSWORD_CHANGE,
        user_id=user_info['user_id'],
        username=user_info['username'],
        ip_address=client_info['ip_address'],
        user_agent=client_info['user_agent'],
        success=True,
        details={
            'action': 'password_changed'
        }
    )

    return jsonify({'message': 'Password changed successfully'}), 200


@auth_bp.route('/audit/logs', methods=['GET'])
@require_auth
def get_audit_logs():
    """
    監査ログ取得（管理者専用）

    Query Parameters:
        limit: 取得件数（デフォルト: 50）
        offset: オフセット（デフォルト: 0）
        event_type: イベントタイプフィルタ
        user_id: ユーザーIDフィルタ
        severity: 深刻度フィルタ

    Returns:
        200: 監査ログリスト
    """
    user_info = get_user_info()
    client_info = get_client_info()

    # 管理者チェック（TODO: 実際のロール管理を実装）
    if user_info['user_id'] != 'admin':
        log_security_event(
            event_type=AuditEventType.SECURITY_PERMISSION_DENIED,
            user_id=user_info['user_id'],
            username=user_info['username'],
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            details={
                'endpoint': '/api/auth/audit/logs',
                'reason': 'insufficient_permissions'
            }
        )
        return jsonify({'error': 'Admin access required'}), 403

    # クエリパラメータ取得
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    event_type_str = request.args.get('event_type')
    user_id_filter = request.args.get('user_id')
    severity = request.args.get('severity')

    # イベントタイプ変換
    event_type = None
    if event_type_str:
        try:
            event_type = AuditEventType(event_type_str)
        except ValueError:
            pass

    # ログ取得
    logs = audit_logger.get_logs(
        limit=min(limit, 1000),  # 最大1000件
        offset=offset,
        event_type=event_type,
        user_id=user_id_filter,
        severity=severity
    )

    total_count = audit_logger.get_log_count(
        event_type=event_type,
        user_id=user_id_filter,
        severity=severity
    )

    # アクセスをログに記録
    log_auth_event(
        event_type=AuditEventType.DATA_READ,
        user_id=user_info['user_id'],
        username=user_info['username'],
        ip_address=client_info['ip_address'],
        user_agent=client_info['user_agent'],
        success=True,
        details={
            'resource': 'audit_logs',
            'count': len(logs),
            'filters': {
                'event_type': event_type_str,
                'user_id': user_id_filter,
                'severity': severity
            }
        }
    )

    return jsonify({
        'logs': [log.to_dict() for log in logs],
        'total': total_count,
        'limit': limit,
        'offset': offset
    }), 200


@auth_bp.route('/audit/statistics', methods=['GET'])
@require_auth
def get_audit_statistics():
    """
    監査ログ統計情報取得（管理者専用）

    Returns:
        200: 統計情報
    """
    user_info = get_user_info()
    client_info = get_client_info()

    # 管理者チェック
    if user_info['user_id'] != 'admin':
        log_security_event(
            event_type=AuditEventType.SECURITY_PERMISSION_DENIED,
            user_id=user_info['user_id'],
            username=user_info['username'],
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent'],
            details={
                'endpoint': '/api/auth/audit/statistics',
                'reason': 'insufficient_permissions'
            }
        )
        return jsonify({'error': 'Admin access required'}), 403

    stats = audit_logger.get_statistics()

    log_auth_event(
        event_type=AuditEventType.DATA_READ,
        user_id=user_info['user_id'],
        username=user_info['username'],
        ip_address=client_info['ip_address'],
        user_agent=client_info['user_agent'],
        success=True,
        details={
            'resource': 'audit_statistics'
        }
    )

    return jsonify(stats), 200
