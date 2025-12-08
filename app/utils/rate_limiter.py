"""
レート制限ユーティリティモジュール
Flask-Limiterのラッパーとカスタム設定
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# デフォルトのレート制限設定
RATE_LIMITS = {
    "default": "100 per minute",
    "api": "60 per minute",
    "auth": "10 per minute",
    "strict": "5 per minute",
    "loose": "200 per minute",
}


def get_rate_limit(limit_type: str = "default") -> str:
    """
    指定されたタイプのレート制限を取得

    Args:
        limit_type: レート制限タイプ（default, api, auth, strict, loose）

    Returns:
        レート制限文字列
    """
    return RATE_LIMITS.get(limit_type, RATE_LIMITS["default"])


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

        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            storage_uri=storage_uri,
            default_limits=[RATE_LIMITS["default"]],
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
    pass
