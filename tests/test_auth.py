"""
認証モジュールのテスト
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# テスト環境設定
os.environ.setdefault("DEFAULT_ADMIN_PASSWORD", "test_password_123")
os.environ.setdefault("USE_DB_STORE", "false")


class TestUserClass:
    """Userクラスのテスト"""

    def test_user_creation(self):
        """ユーザー作成テスト"""
        from app.routes.auth import User
        from werkzeug.security import generate_password_hash

        user = User(
            id="test-1",
            username="testuser",
            password_hash=generate_password_hash("password123"),
            is_admin=False,
            is_active=True,
        )

        assert user.id == "test-1"
        assert user.username == "testuser"
        assert user.is_admin is False
        assert user.is_active is True

    def test_user_check_password_valid(self):
        """正しいパスワードの検証"""
        from app.routes.auth import User
        from werkzeug.security import generate_password_hash

        password = "secure_password_123"
        user = User(
            id="test-2",
            username="testuser",
            password_hash=generate_password_hash(password),
        )

        assert user.check_password(password) is True

    def test_user_check_password_invalid(self):
        """間違ったパスワードの検証"""
        from app.routes.auth import User
        from werkzeug.security import generate_password_hash

        user = User(
            id="test-3",
            username="testuser",
            password_hash=generate_password_hash("correct_password"),
        )

        assert user.check_password("wrong_password") is False

    def test_user_get_id(self):
        """Flask-Login用ID取得テスト"""
        from app.routes.auth import User
        from werkzeug.security import generate_password_hash

        user = User(
            id="user-abc-123",
            username="testuser",
            password_hash=generate_password_hash("password"),
        )

        assert user.get_id() == "user-abc-123"

    def test_user_update_last_login(self):
        """最終ログイン更新テスト"""
        from app.routes.auth import User
        from werkzeug.security import generate_password_hash

        user = User(
            id="test-4",
            username="testuser",
            password_hash=generate_password_hash("password"),
        )

        assert user.last_login is None
        user.update_last_login()
        assert user.last_login is not None
        assert isinstance(user.last_login, datetime)


class TestUserStore:
    """UserStoreクラスのテスト"""

    def test_user_store_init(self):
        """UserStore初期化テスト"""
        from app.routes.auth import UserStore

        with patch.dict(os.environ, {"DEFAULT_ADMIN_PASSWORD": "admin123"}):
            store = UserStore()
            assert store.get_user_count() >= 1

    def test_add_user(self):
        """ユーザー追加テスト"""
        from app.routes.auth import UserStore

        with patch.dict(os.environ, {"DEFAULT_ADMIN_PASSWORD": "admin123"}):
            store = UserStore()
            initial_count = store.get_user_count()

            user = store.add_user("newuser", "password123", is_admin=False)
            assert user.username == "newuser"
            assert store.get_user_count() == initial_count + 1

    def test_get_user_by_username(self):
        """ユーザー名でユーザー取得テスト"""
        from app.routes.auth import UserStore

        with patch.dict(os.environ, {"DEFAULT_ADMIN_PASSWORD": "admin123"}):
            store = UserStore()
            store.add_user("findme", "password123")

            user = store.get_user_by_username("findme")
            assert user is not None
            assert user.username == "findme"

    def test_get_user_by_username_not_found(self):
        """存在しないユーザー取得テスト"""
        from app.routes.auth import UserStore

        with patch.dict(os.environ, {"DEFAULT_ADMIN_PASSWORD": "admin123"}):
            store = UserStore()
            user = store.get_user_by_username("nonexistent")
            assert user is None

    def test_delete_user(self):
        """ユーザー削除テスト"""
        from app.routes.auth import UserStore

        with patch.dict(os.environ, {"DEFAULT_ADMIN_PASSWORD": "admin123"}):
            store = UserStore()
            user = store.add_user("deleteme", "password123")
            user_id = user.id

            assert store.delete_user(user_id) is True
            assert store.get_user_by_id(user_id) is None

    def test_update_password(self):
        """パスワード更新テスト"""
        from app.routes.auth import UserStore

        with patch.dict(os.environ, {"DEFAULT_ADMIN_PASSWORD": "admin123"}):
            store = UserStore()
            user = store.add_user("pwduser", "old_password")

            assert store.update_password(user.id, "new_password") is True
            updated_user = store.get_user_by_id(user.id)
            assert updated_user.check_password("new_password") is True
            assert updated_user.check_password("old_password") is False


class TestAdminRequired:
    """admin_requiredデコレータのテスト"""

    def test_admin_required_decorator_exists(self):
        """admin_requiredデコレータの存在確認"""
        from app.routes.auth import admin_required
        assert callable(admin_required)


class TestAuthHelpers:
    """認証ヘルパー関数のテスト"""

    def test_get_user_store_function(self):
        """get_user_store関数のテスト"""
        from app.routes.auth import get_user_store

        store = get_user_store()
        assert store is not None
        assert hasattr(store, "get_user_by_id")
        assert hasattr(store, "get_user_by_username")


class TestUserStoreProxy:
    """_UserStoreProxyクラスのテスト"""

    def test_proxy_getattr(self):
        """プロキシのgetattr動作テスト"""
        from app.routes.auth import user_store

        # プロキシ経由でメソッドアクセス
        assert hasattr(user_store, "get_user_by_id")
        assert hasattr(user_store, "get_user_by_username")
        assert hasattr(user_store, "add_user")
