"""
Security Headers Module
=======================

OWASP準拠のセキュリティヘッダー設定モジュール

Features:
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy
"""

import os
from functools import wraps
from typing import Callable, Dict, Optional


class SecurityHeaders:
    """セキュリティヘッダー管理クラス"""

    # デフォルトCSPディレクティブ
    DEFAULT_CSP = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'"],  # 本番では'unsafe-inline'を削除
        "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        "font-src": ["'self'", "https://fonts.gstatic.com"],
        "img-src": ["'self'", "data:", "https:"],
        "connect-src": ["'self'", "https://graphql.anilist.co"],
        "frame-ancestors": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
        "object-src": ["'none'"],
        "upgrade-insecure-requests": [],
    }

    # 環境別CSP設定
    ENV_CSP_OVERRIDES = {
        "development": {
            "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
            "connect-src": ["'self'", "http://localhost:*", "https://graphql.anilist.co"],
        },
        "production": {
            "script-src": ["'self'"],
            "upgrade-insecure-requests": [],
        },
    }

    def __init__(self, env: str = "production"):
        """
        初期化

        Args:
            env: 環境名 ('development', 'production')
        """
        self.env = env
        self.csp_directives = self._build_csp()
        self.headers = self._build_headers()

    def _build_csp(self) -> Dict[str, list]:
        """CSPディレクティブを構築"""
        csp = self.DEFAULT_CSP.copy()

        # 環境別オーバーライドを適用
        if self.env in self.ENV_CSP_OVERRIDES:
            for directive, values in self.ENV_CSP_OVERRIDES[self.env].items():
                csp[directive] = values

        return csp

    def _csp_to_string(self) -> str:
        """CSPディレクティブを文字列に変換"""
        parts = []
        for directive, values in self.csp_directives.items():
            if values:
                parts.append(f"{directive} {' '.join(values)}")
            else:
                parts.append(directive)
        return "; ".join(parts)

    def _build_headers(self) -> Dict[str, str]:
        """セキュリティヘッダーを構築"""
        headers = {
            # Content Security Policy
            "Content-Security-Policy": self._csp_to_string(),
            # HTTP Strict Transport Security
            # max-age=31536000 (1年), includeSubDomains, preload
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            # X-Frame-Options (CSPのframe-ancestorsと併用)
            "X-Frame-Options": "DENY",
            # X-Content-Type-Options
            "X-Content-Type-Options": "nosniff",
            # X-XSS-Protection (レガシーブラウザ向け)
            "X-XSS-Protection": "1; mode=block",
            # Referrer-Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # Permissions-Policy (旧Feature-Policy)
            "Permissions-Policy": (
                "accelerometer=(), "
                "camera=(), "
                "geolocation=(), "
                "gyroscope=(), "
                "magnetometer=(), "
                "microphone=(), "
                "payment=(), "
                "usb=()"
            ),
            # Cross-Origin-Opener-Policy
            "Cross-Origin-Opener-Policy": "same-origin",
            # Cross-Origin-Embedder-Policy
            "Cross-Origin-Embedder-Policy": "require-corp",
            # Cross-Origin-Resource-Policy
            "Cross-Origin-Resource-Policy": "same-origin",
            # Cache-Control for sensitive pages
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }

        # 開発環境ではHSTSを無効化
        if self.env == "development":
            del headers["Strict-Transport-Security"]
            # COEP/COOPも開発時は緩和
            headers["Cross-Origin-Opener-Policy"] = "unsafe-none"
            headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"

        return headers

    def get_headers(self) -> Dict[str, str]:
        """セキュリティヘッダーを取得"""
        return self.headers.copy()

    def add_csp_directive(self, directive: str, values: list) -> None:
        """CSPディレクティブを追加"""
        self.csp_directives[directive] = values
        self.headers["Content-Security-Policy"] = self._csp_to_string()

    def add_csp_source(self, directive: str, source: str) -> None:
        """既存のCSPディレクティブにソースを追加"""
        if directive in self.csp_directives:
            if source not in self.csp_directives[directive]:
                self.csp_directives[directive].append(source)
        else:
            self.csp_directives[directive] = [source]
        self.headers["Content-Security-Policy"] = self._csp_to_string()


def init_security_headers(app, env: Optional[str] = None):
    """
    Flaskアプリケーションにセキュリティヘッダーを設定

    Args:
        app: Flaskアプリケーション
        env: 環境名 (Noneの場合はFLASK_ENVから取得)
    """
    if env is None:
        env = os.environ.get("FLASK_ENV", "production")

    security = SecurityHeaders(env=env)

    @app.after_request
    def add_security_headers(response):
        """レスポンスにセキュリティヘッダーを追加"""
        for header, value in security.get_headers().items():
            response.headers[header] = value
        return response

    return security


def security_headers_required(func: Callable) -> Callable:
    """
    特定のルートにセキュリティヘッダーを強制するデコレータ

    Usage:
        @app.route('/sensitive')
        @security_headers_required
        def sensitive_route():
            return 'Sensitive data'
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        # 追加のセキュリティヘッダー
        if hasattr(response, "headers"):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
        return response

    return wrapper


class CORSConfig:
    """CORS設定クラス"""

    def __init__(
        self,
        allowed_origins: Optional[list] = None,
        allowed_methods: Optional[list] = None,
        allowed_headers: Optional[list] = None,
        expose_headers: Optional[list] = None,
        max_age: int = 86400,
        supports_credentials: bool = False,
    ):
        """
        CORS設定の初期化

        Args:
            allowed_origins: 許可するオリジンのリスト
            allowed_methods: 許可するHTTPメソッドのリスト
            allowed_headers: 許可するヘッダーのリスト
            expose_headers: 公開するヘッダーのリスト
            max_age: プリフライトキャッシュ時間（秒）
            supports_credentials: 認証情報を含むリクエストを許可するか
        """
        self.allowed_origins = allowed_origins or ["http://localhost:3000"]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = allowed_headers or [
            "Content-Type",
            "Authorization",
            "X-Requested-With",
        ]
        self.expose_headers = expose_headers or ["X-Total-Count", "X-Page-Count"]
        self.max_age = max_age
        self.supports_credentials = supports_credentials

    def get_cors_headers(self, origin: Optional[str] = None) -> Dict[str, str]:
        """CORS関連ヘッダーを取得"""
        headers = {}

        # オリジンチェック
        if origin and self._is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
        elif "*" in self.allowed_origins:
            headers["Access-Control-Allow-Origin"] = "*"

        headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
        headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
        headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
        headers["Access-Control-Max-Age"] = str(self.max_age)

        if self.supports_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"

        return headers

    def _is_origin_allowed(self, origin: str) -> bool:
        """オリジンが許可されているかチェック"""
        if "*" in self.allowed_origins:
            return True
        return origin in self.allowed_origins


def init_cors(app, config: Optional[CORSConfig] = None):
    """
    FlaskアプリケーションにCORSを設定

    Args:
        app: Flaskアプリケーション
        config: CORS設定
    """
    if config is None:
        # 環境変数から設定を読み込み
        origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
        config = CORSConfig(allowed_origins=origins)

    @app.after_request
    def add_cors_headers(response):
        """CORSヘッダーを追加"""
        from flask import request

        origin = request.headers.get("Origin")
        cors_headers = config.get_cors_headers(origin)

        for header, value in cors_headers.items():
            response.headers[header] = value

        return response

    return config


# セキュリティヘッダー検証関数
def validate_security_headers(headers: Dict[str, str]) -> Dict[str, bool]:
    """
    セキュリティヘッダーの存在を検証

    Args:
        headers: HTTPヘッダー辞書

    Returns:
        各ヘッダーの存在状況を示す辞書
    """
    required_headers = [
        "Content-Security-Policy",
        "X-Frame-Options",
        "X-Content-Type-Options",
        "X-XSS-Protection",
        "Referrer-Policy",
    ]

    return {header: header in headers for header in required_headers}


if __name__ == "__main__":
    # テスト
    security = SecurityHeaders(env="production")
    print("Production Security Headers:")
    for header, value in security.get_headers().items():
        print(f"  {header}: {value[:50]}..." if len(value) > 50 else f"  {header}: {value}")

    print("\nDevelopment Security Headers:")
    security_dev = SecurityHeaders(env="development")
    for header, value in security_dev.get_headers().items():
        print(f"  {header}: {value[:50]}..." if len(value) > 50 else f"  {header}: {value}")
