"""
セッションセキュリティテスト
Tests for Flask session security configuration
"""

import pytest
import os
import sys
from pathlib import Path
from datetime import timedelta

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestSessionSecurityConfig:
    """セキュリティ設定のテスト"""

    def test_security_config_import(self):
        """SecurityConfigがインポートできるか"""
        from app.utils.security import SecurityConfig
        assert SecurityConfig is not None

    def test_development_security_config_import(self):
        """DevelopmentSecurityConfigがインポートできるか"""
        from app.utils.security import DevelopmentSecurityConfig
        assert DevelopmentSecurityConfig is not None

    def test_session_cookie_secure_default(self):
        """SESSION_COOKIE_SECUREのデフォルト値"""
        from app.utils.security import SecurityConfig
        assert SecurityConfig.SESSION_COOKIE_SECURE is True

    def test_session_cookie_httponly_default(self):
        """SESSION_COOKIE_HTTPONLYのデフォルト値"""
        from app.utils.security import SecurityConfig
        assert SecurityConfig.SESSION_COOKIE_HTTPONLY is True

    def test_session_cookie_samesite_default(self):
        """SESSION_COOKIE_SAMESITEのデフォルト値"""
        from app.utils.security import SecurityConfig
        assert SecurityConfig.SESSION_COOKIE_SAMESITE == 'Lax'

    def test_permanent_session_lifetime_default(self):
        """PERMANENT_SESSION_LIFETIMEのデフォルト値"""
        from app.utils.security import SecurityConfig
        assert SecurityConfig.PERMANENT_SESSION_LIFETIME == timedelta(hours=2)

    def test_session_type_filesystem(self):
        """SESSION_TYPEがfilesystemか"""
        from app.utils.security import SecurityConfig
        assert SecurityConfig.SESSION_TYPE == 'filesystem'

    def test_session_use_signer(self):
        """SESSION_USE_SIGNERが有効か"""
        from app.utils.security import SecurityConfig
        assert SecurityConfig.SESSION_USE_SIGNER is True

    def test_development_config_http_allowed(self):
        """開発環境設定ではHTTPが許可されているか"""
        from app.utils.security import DevelopmentSecurityConfig
        assert DevelopmentSecurityConfig.SESSION_COOKIE_SECURE is False


class TestSecurityHeaders:
    """セキュリティヘッダーのテスト"""

    def test_security_headers_exist(self):
        """セキュリティヘッダーが定義されているか"""
        from app.utils.security import SecurityConfig
        assert hasattr(SecurityConfig, 'SECURITY_HEADERS')
        assert isinstance(SecurityConfig.SECURITY_HEADERS, dict)

    def test_x_content_type_options_header(self):
        """X-Content-Type-Optionsヘッダーが設定されているか"""
        from app.utils.security import SecurityConfig
        assert 'X-Content-Type-Options' in SecurityConfig.SECURITY_HEADERS
        assert SecurityConfig.SECURITY_HEADERS['X-Content-Type-Options'] == 'nosniff'

    def test_x_frame_options_header(self):
        """X-Frame-Optionsヘッダーが設定されているか"""
        from app.utils.security import SecurityConfig
        assert 'X-Frame-Options' in SecurityConfig.SECURITY_HEADERS
        assert SecurityConfig.SECURITY_HEADERS['X-Frame-Options'] == 'SAMEORIGIN'

    def test_x_xss_protection_header(self):
        """X-XSS-Protectionヘッダーが設定されているか"""
        from app.utils.security import SecurityConfig
        assert 'X-XSS-Protection' in SecurityConfig.SECURITY_HEADERS
        assert SecurityConfig.SECURITY_HEADERS['X-XSS-Protection'] == '1; mode=block'

    def test_strict_transport_security_header(self):
        """Strict-Transport-Securityヘッダーが設定されているか"""
        from app.utils.security import SecurityConfig
        assert 'Strict-Transport-Security' in SecurityConfig.SECURITY_HEADERS


class TestProductionConfig:
    """本番環境設定のテスト"""

    def test_production_session_config_method_exists(self):
        """get_production_session_configメソッドが存在するか"""
        from app.utils.security import SecurityConfig
        assert hasattr(SecurityConfig, 'get_production_session_config')
        assert callable(SecurityConfig.get_production_session_config)

    def test_production_config_session_type_redis(self):
        """本番環境設定でSESSION_TYPEがredisか"""
        from app.utils.security import SecurityConfig

        # Redis未インストール環境でもテスト可能にする
        try:
            config = SecurityConfig.get_production_session_config()
            assert config['SESSION_TYPE'] == 'redis'
            assert config['SESSION_COOKIE_SECURE'] is True
            assert config['SESSION_COOKIE_SAMESITE'] == 'Strict'
        except ImportError:
            pytest.skip("Redis not installed")


class TestFlaskAppIntegration:
    """Flaskアプリケーション統合テスト"""

    @pytest.fixture
    def app(self):
        """テスト用Flaskアプリケーション"""
        from flask import Flask
        from app.utils.security import DevelopmentSecurityConfig

        test_app = Flask(__name__)
        test_app.config['SECRET_KEY'] = 'test-secret-key'
        test_app.config['TESTING'] = True
        test_app.config['ENV'] = 'development'

        DevelopmentSecurityConfig.init_app(test_app)
        return test_app

    def test_app_session_config_applied(self, app):
        """Flaskアプリにセッション設定が適用されているか"""
        assert app.config['SESSION_COOKIE_HTTPONLY'] is True
        assert app.config['SESSION_TYPE'] == 'filesystem'
        assert app.config['SESSION_USE_SIGNER'] is True

    def test_app_session_lifetime_configured(self, app):
        """セッション有効期限が設定されているか"""
        assert 'PERMANENT_SESSION_LIFETIME' in app.config
        assert isinstance(app.config['PERMANENT_SESSION_LIFETIME'], timedelta)

    def test_app_security_headers_after_request(self, app):
        """after_requestフックでセキュリティヘッダーが追加されるか"""
        with app.test_client() as client:
            # テストエンドポイント追加
            @app.route('/test')
            def test_endpoint():
                return 'OK'

            response = client.get('/test')

            # セキュリティヘッダーの確認
            assert 'X-Content-Type-Options' in response.headers
            assert response.headers['X-Content-Type-Options'] == 'nosniff'


class TestSessionFileDirectory:
    """セッションファイルディレクトリのテスト"""

    def test_session_file_dir_path(self):
        """SESSION_FILE_DIRのパスが正しいか"""
        from app.utils.security import SecurityConfig
        assert SecurityConfig.SESSION_FILE_DIR is not None
        assert 'flask_session' in SecurityConfig.SESSION_FILE_DIR

    def test_session_directory_creation(self):
        """init_app実行時にセッションディレクトリが作成されるか"""
        from flask import Flask
        from app.utils.security import DevelopmentSecurityConfig
        import tempfile
        import shutil

        # 一時ディレクトリでテスト
        temp_dir = tempfile.mkdtemp()

        try:
            test_app = Flask(__name__)
            test_app.config['SECRET_KEY'] = 'test'

            # SESSION_FILE_DIRを一時ディレクトリに変更
            original_dir = DevelopmentSecurityConfig.SESSION_FILE_DIR
            test_session_dir = os.path.join(temp_dir, 'flask_session')
            DevelopmentSecurityConfig.SESSION_FILE_DIR = test_session_dir

            DevelopmentSecurityConfig.init_app(test_app)

            # ディレクトリが作成されたか確認
            assert os.path.exists(test_session_dir)
            assert os.path.isdir(test_session_dir)

            # 元に戻す
            DevelopmentSecurityConfig.SESSION_FILE_DIR = original_dir

        finally:
            # クリーンアップ
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
