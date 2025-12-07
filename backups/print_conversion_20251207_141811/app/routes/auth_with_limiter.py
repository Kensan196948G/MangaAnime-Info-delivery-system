"""
認証関連のルート（レート制限付き）
Flask-Limiterを使用したレート制限実装
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Blueprintの作成
auth_bp = Bluelogger.info('auth', __name__, url_prefix='/auth')

# Limiterは後からweb_app.pyで注入される
limiter = None


def init_auth_routes(app, limiter_instance):
    """
    認証ルートの初期化

    Args:
        app: Flaskアプリケーションインスタンス
        limiter_instance: Limiterインスタンス
    """
    global limiter
    limiter = limiter_instance
    app.register_bluelogger.info(auth_bp)
    logger.info("Auth routes initialized with rate limiting")


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """
    ログインエンドポイント
    レート制限: 5回/分
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'ユーザー名とパスワードを入力してください'
            }), 400

        # 実際の認証ロジック（既存のコードに置き換える）
        # ここではダミー実装
        from app.models import User  # 適切なモデルをインポート

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            logger.info(f"User logged in: {username}")
            return jsonify({
                'success': True,
                'message': 'ログインに成功しました',
                'redirect': url_for('index')
            }), 200
        else:
            logger.warning(f"Failed login attempt: {username}")
            return jsonify({
                'success': False,
                'message': 'ユーザー名またはパスワードが正しくありません'
            }), 401

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'ログイン処理中にエラーが発生しました'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def logout():
    """
    ログアウトエンドポイント
    レート制限: 10回/分
    """
    try:
        username = current_user.username if current_user.is_authenticated else "Unknown"
        logout_user()
        logger.info(f"User logged out: {username}")

        return jsonify({
            'success': True,
            'message': 'ログアウトしました',
            'redirect': url_for('index')
        }), 200

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'ログアウト処理中にエラーが発生しました'
        }), 500


@auth_bp.route('/password-reset', methods=['POST'])
@limiter.limit("3 per hour")
def password_reset():
    """
    パスワードリセットエンドポイント
    レート制限: 3回/時間
    """
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({
                'success': False,
                'message': 'メールアドレスを入力してください'
            }), 400

        # パスワードリセットロジック
        # メール送信などの処理を実装
        logger.info(f"Password reset requested for: {email}")

        return jsonify({
            'success': True,
            'message': 'パスワードリセットメールを送信しました'
        }), 200

    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'パスワードリセット処理中にエラーが発生しました'
        }), 500


@auth_bp.route('/session-refresh', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def session_refresh():
    """
    セッション更新エンドポイント
    レート制限: 10回/時間
    """
    try:
        # セッション更新ロジック
        session.modified = True
        logger.info(f"Session refreshed for user: {current_user.username}")

        return jsonify({
            'success': True,
            'message': 'セッションを更新しました'
        }), 200

    except Exception as e:
        logger.error(f"Session refresh error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'セッション更新中にエラーが発生しました'
        }), 500


@auth_bp.route('/status', methods=['GET'])
@limiter.limit("60 per minute")
def auth_status():
    """
    認証状態確認エンドポイント
    レート制限: 60回/分
    """
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'username': current_user.username if current_user.is_authenticated else None
    }), 200
