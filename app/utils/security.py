"""
セキュリティ関連設定モジュール
Session Management & Security Configuration
"""

import os
from datetime import timedelta
from pathlib import Path


class SecurityConfig:
    """セキュリティ設定クラス"""

    # プロジェクトルート
    PROJECT_ROOT = Path(__file__).parent.parent.parent

    # セッションセキュリティ設定
    SESSION_COOKIE_SECURE = True  # HTTPS only (本番環境必須)
    SESSION_COOKIE_HTTPONLY = True  # XSS防止
    SESSION_COOKIE_SAMESITE = "Lax"  # CSRF補完
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # セッション有効期限

    # Flask-Session サーバーサイドセッション設定（開発環境）
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = os.path.join(PROJECT_ROOT, "flask_session")
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True  # Cookie改ざん防止

    # 本番環境用Redis設定テンプレート
    @staticmethod
    def get_production_session_config():
        """
        本番環境用セッション設定を返す

        Returns:
            dict: 本番環境用設定辞書

        Usage:
            if app.config['ENV'] == 'production':
                app.config.update(SecurityConfig.get_production_session_config())
        """
        import redis

        return {
            "SESSION_TYPE": "redis",
            "SESSION_REDIS": redis.from_url(
                os.environ.get("REDIS_URL", "redis://localhost:6379")
            ),
            "SESSION_COOKIE_SECURE": True,
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SAMESITE": "Strict",  # 本番はStrictを推奨
            "PERMANENT_SESSION_LIFETIME": timedelta(hours=1),  # より短く設定
        }

    # CSRFトークン設定
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # トークン有効期限（Noneで無期限）

    # セキュリティヘッダー
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "SAMEORIGIN",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' cdn.jsdelivr.net code.jquery.com; "
            "style-src 'self' cdn.jsdelivr.net fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' fonts.googleapis.com fonts.gstatic.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        ),
    }

    @staticmethod
    def apply_security_headers(response):
        """
        レスポンスにセキュリティヘッダーを適用

        Args:
            response: Flaskレスポンスオブジェクト

        Returns:
            response: ヘッダー適用済みレスポンス

        Usage:
            @app.after_request
            def add_security_headers(response):
                return SecurityConfig.apply_security_headers(response)
        """
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response

    @staticmethod
    def init_app(app):
        """
        Flaskアプリケーションにセキュリティ設定を適用

        Args:
            app: Flaskアプリケーションインスタンス

        Usage:
            from app.utils.security import SecurityConfig
            SecurityConfig.init_app(app)
        """
        # セッション設定適用
        app.config["SESSION_COOKIE_SECURE"] = SecurityConfig.SESSION_COOKIE_SECURE
        app.config["SESSION_COOKIE_HTTPONLY"] = SecurityConfig.SESSION_COOKIE_HTTPONLY
        app.config["SESSION_COOKIE_SAMESITE"] = SecurityConfig.SESSION_COOKIE_SAMESITE
        app.config["PERMANENT_SESSION_LIFETIME"] = (
            SecurityConfig.PERMANENT_SESSION_LIFETIME
        )

        # Flask-Session設定
        app.config["SESSION_TYPE"] = SecurityConfig.SESSION_TYPE
        app.config["SESSION_FILE_DIR"] = SecurityConfig.SESSION_FILE_DIR
        app.config["SESSION_PERMANENT"] = SecurityConfig.SESSION_PERMANENT
        app.config["SESSION_USE_SIGNER"] = SecurityConfig.SESSION_USE_SIGNER

        # セッションディレクトリ作成
        os.makedirs(SecurityConfig.SESSION_FILE_DIR, exist_ok=True)

        # 本番環境の場合はRedis設定を適用
        if app.config.get("ENV") == "production":
            app.config.update(SecurityConfig.get_production_session_config())

        # セキュリティヘッダーを全レスポンスに適用
        @app.after_request
        def add_security_headers(response):
            return SecurityConfig.apply_security_headers(response)

        # Flask-Sessionの初期化
        try:
            from flask_session import Session

            Session(app)
        except ImportError:
            app.logger.warning(
                "Flask-Session not installed. Using default session management."
            )

        return app


# 開発環境用の簡易設定（HTTPS無効）
class DevelopmentSecurityConfig(SecurityConfig):
    """開発環境用セキュリティ設定（HTTPSなし）"""

    SESSION_COOKIE_SECURE = False  # 開発環境ではHTTPを許可
    SESSION_COOKIE_SAMESITE = "Lax"
