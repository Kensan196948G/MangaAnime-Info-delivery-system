"""
レート制限設定ファイル

環境別のレート制限設定を管理
"""

import os


class RateLimitConfig:
    """レート制限設定クラス"""

    # ストレージ設定
    STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')

    # 開発環境
    DEV_STORAGE = 'memory://'

    # 本番環境（Redis推奨）
    PROD_STORAGE = os.environ.get('REDIS_URL', 'redis://localhost:6379')

    # デフォルトのレート制限
    DEFAULT_LIMITS = ["200 per day", "50 per hour"]

    # 認証関連のレート制限
    AUTH_LIMITS = {
        'login': "5 per minute",
        'logout': "10 per minute",
        'password_reset': "3 per hour",
        'password_change': "5 per hour",
        'session_refresh': "10 per hour",
        'register': "3 per hour",
    }

    # API関連のレート制限
    API_LIMITS = {
        'general': "100 per hour",
        'read': "200 per hour",
        'write': "50 per hour",
        'collection': "10 per hour",
        'scraping': "5 per hour",
    }

    # 設定変更系のレート制限
    SETTINGS_LIMITS = {
        'settings_read': "50 per hour",
        'settings_write': "30 per hour",
        'config_update': "20 per hour",
    }

    # 通知・メール系のレート制限
    NOTIFICATION_LIMITS = {
        'notification_send': "20 per hour",
        'email_send': "10 per hour",
        'sms_send': "5 per hour",
    }

    # カレンダー系のレート制限
    CALENDAR_LIMITS = {
        'calendar_sync': "15 per hour",
        'calendar_read': "50 per hour",
        'calendar_write': "20 per hour",
    }

    # RSS/フィード系のレート制限
    RSS_LIMITS = {
        'rss_read': "30 per hour",
        'rss_subscribe': "10 per hour",
        'rss_unsubscribe': "10 per hour",
    }

    # 管理者系のレート制限（緩めの制限）
    ADMIN_LIMITS = {
        'admin_general': "500 per hour",
        'admin_read': "1000 per hour",
        'admin_write': "100 per hour",
        'admin_delete': "50 per hour",
    }

    @classmethod
    def get_storage_uri(cls, environment='development'):
        """
        環境に応じたストレージURIを取得

        Args:
            environment: 'development' または 'production'

        Returns:
            str: ストレージURI
        """
        if environment == 'production':
            return cls.PROD_STORAGE
        return cls.DEV_STORAGE

    @classmethod
    def get_all_limits(cls):
        """
        全てのレート制限設定を取得

        Returns:
            dict: 全レート制限設定
        """
        return {
            'auth': cls.AUTH_LIMITS,
            'api': cls.API_LIMITS,
            'settings': cls.SETTINGS_LIMITS,
            'notification': cls.NOTIFICATION_LIMITS,
            'calendar': cls.CALENDAR_LIMITS,
            'rss': cls.RSS_LIMITS,
            'admin': cls.ADMIN_LIMITS,
        }

    @classmethod
    def get_limit(cls, category, key):
        """
        特定のレート制限値を取得

        Args:
            category: カテゴリ名 ('auth', 'api', など)
            key: 設定キー

        Returns:
            str: レート制限文字列
        """
        limits_map = {
            'auth': cls.AUTH_LIMITS,
            'api': cls.API_LIMITS,
            'settings': cls.SETTINGS_LIMITS,
            'notification': cls.NOTIFICATION_LIMITS,
            'calendar': cls.CALENDAR_LIMITS,
            'rss': cls.RSS_LIMITS,
            'admin': cls.ADMIN_LIMITS,
        }

        category_limits = limits_map.get(category, {})
        return category_limits.get(key, "100 per hour")


# 環境変数ベースの設定
ENV = os.environ.get('FLASK_ENV', 'development')
IS_PRODUCTION = ENV == 'production'

# アクティブな設定
ACTIVE_STORAGE_URI = RateLimitConfig.get_storage_uri(
    'production' if IS_PRODUCTION else 'development'
)

# Flask-Limiter用の設定辞書
FLASK_LIMITER_CONFIG = {
    'RATELIMIT_STORAGE_URI': ACTIVE_STORAGE_URI,
    'RATELIMIT_DEFAULT': RateLimitConfig.DEFAULT_LIMITS,
    'RATELIMIT_STRATEGY': 'fixed-window',
    'RATELIMIT_HEADERS_ENABLED': True,
    'RATELIMIT_SWALLOW_ERRORS': True,
}
