"""
レート制限ユーティリティモジュール
Flask-Limiterのラッパーとカスタム設定
"""

import logging

logger = logging.getLogger(__name__)

# デフォルトのレート制限設定
RATE_LIMITS = {
    "default": "100 per minute",
    "api": "60 per minute",
    "auth": "10 per minute",
    "strict": "5 per minute",
    "loose": "200 per minute",
    # 複合キー（category_action形式）
    "auth_login": "5 per minute",
    "auth_logout": "10 per minute",
    "auth_register": "3 per hour",
    "auth_password_reset": "3 per hour",
    "api_general": "100 per hour",
    "api_read": "200 per hour",
    "api_write": "50 per hour",
    "api_collection": "10 per hour",
    "api_scraping": "5 per hour",
    "admin_general": "500 per hour",
    "admin_read": "1000 per hour",
    "admin_write": "100 per hour",
    "admin_delete": "50 per hour",
}


def get_rate_limit(limit_type: str = "default") -> str:
    """
    指定されたタイプのレート制限を取得

    Args:
        limit_type: レート制限タイプ（default, api, auth, strict, loose）

    Returns:
        レート制限文字列
    """
    return RATE_LIMITS.get(limit_type, "100 per hour")


def init_limiter(app, storage_uri: str = "memory://"):
    """
    Flask-Limiterを初期化

    Args:
        app: Flaskアプリケーション
        storage_uri: ストレージURI（デフォルト: memory://）

    Returns:
        Limiterインスタンス
    """
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address

        # app.configのRATELIMIT_DEFAULTを優先、なければRATE_LIMITSのデフォルト値を使用
        default_limits = app.config.get("RATELIMIT_DEFAULT", [RATE_LIMITS["default"]])
        if isinstance(default_limits, str):
            default_limits = [default_limits]
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            storage_uri=storage_uri,
            default_limits=default_limits,
        )

        logger.info(f"Rate limiter initialized with storage: {storage_uri}")
        return limiter

    except ImportError:
        logger.warning("flask-limiter not installed. Rate limiting disabled.")
        # ダミーリミッター（デコレータとして機能するが制限なし）
        return DummyLimiter()


class DummyLimiter:
    """
    Flask-Limiterがインストールされていない場合のダミーリミッター
    """

    def limit(self, limit_string: str):
        """何もしないデコレータ"""

        def decorator(f):
            return f

        return decorator

    def exempt(self, f):
        """何もしないデコレータ"""
        return f


class RateLimitExceeded(Exception):
    """レート制限超過例外"""
