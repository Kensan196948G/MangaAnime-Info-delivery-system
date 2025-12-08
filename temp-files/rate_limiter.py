"""
レート制限機能モジュール
Flask-Limiterを使用したAPIエンドポイントのレート制限実装
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import jsonify, redirect, url_for, request, flash

def get_user_identifier():
    """
    ユーザー識別子を取得
    ログイン済みの場合はユーザーID、未ログインはIPアドレス
    """
    from flask_login import current_user

    if current_user and current_user.is_authenticated:
        return f"user:{current_user.id}"
    return f"ip:{get_remote_address()}"


def init_limiter(app):
    """
    Flask-Limiterの初期化

    Args:
        app: Flaskアプリケーションインスタンス

    Returns:
        Limiter: 設定済みのLimiterインスタンス
    """
    # 環境変数から設定を取得
    storage_uri = app.config.get('RATELIMIT_STORAGE_URI', 'memory://')
    default_limits = app.config.get('RATELIMIT_DEFAULT', ["200 per day", "50 per hour"])

    limiter = Limiter(
        app=app,
        key_func=get_user_identifier,
        default_limits=default_limits,
        storage_uri=storage_uri,
        strategy="fixed-window",
        headers_enabled=True,
        swallow_errors=True,  # エラーが発生してもアプリを停止しない
    )

    # カスタムエラーハンドラ
    @app.errorhandler(429)
    def ratelimit_handler(e):
        """レート制限超過時のエラーハンドラ"""
        logger.warning(f"Rate limit exceeded: {request.remote_addr} - {request.endpoint}")

        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': 'リクエスト制限を超えました。しばらくしてから再試行してください。',
                'retry_after': e.description
            }), 429

        flash('リクエスト回数が多すぎます。しばらくしてからお試しください。', 'warning')
        return redirect(request.referent or url_for('index'))

    logger.info(f"Rate limiter initialized with storage: {storage_uri}")
    return limiter


# レート制限設定の定義
RATE_LIMITS = {
    # 認証関連
    'auth_login': "5 per minute",
    'auth_logout': "10 per minute",
    'auth_password_reset': "3 per hour",
    'auth_session_refresh': "10 per hour",

    # API全般
    'api_general': "100 per hour",
    'api_read': "200 per hour",
    'api_write': "50 per hour",

    # データ収集系
    'api_collection': "10 per hour",
    'api_scraping': "5 per hour",

    # 設定変更系
    'api_settings': "30 per hour",
    'api_config_update': "20 per hour",

    # 通知・メール系
    'api_notification': "20 per hour",
    'api_email': "10 per hour",

    # カレンダー同期
    'api_calendar_sync': "15 per hour",

    # RSS/フィード
    'api_rss': "30 per hour",

    # 管理者系（緩めの制限）
    'admin_general': "500 per hour",
    'admin_write': "100 per hour",
}


def get_rate_limit(limit_type):
    """
    レート制限設定を取得

    Args:
        limit_type: RATE_LIMITSのキー

    Returns:
        str: レート制限文字列
    """
    return RATE_LIMITS.get(limit_type, "100 per hour")


# デコレータのヘルパー関数
def limit_auth_login(limiter):
    """ログインエンドポイント用のレート制限デコレータ"""
    return limiter.limit(get_rate_limit('auth_login'))


def limit_auth_password_reset(limiter):
    """パスワードリセット用のレート制限デコレータ"""
    return limiter.limit(get_rate_limit('auth_password_reset'))


def limit_api_collection(limiter):
    """データ収集API用のレート制限デコレータ"""
    return limiter.limit(get_rate_limit('api_collection'))


def limit_api_settings(limiter):
    """設定変更API用のレート制限デコレータ"""
    return limiter.limit(get_rate_limit('api_settings'))


def limit_api_general(limiter):
    """一般API用のレート制限デコレータ"""
    return limiter.limit(get_rate_limit('api_general'))
