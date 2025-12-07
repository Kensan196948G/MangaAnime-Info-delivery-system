"""
UserDBStoreのテスト - 完全版
SQLiteベースのユーザーデータベース管理機能の包括的テスト
"""
import pytest
import tempfile
import os
from datetime import datetime
from app.models.user_db import UserDBStore
from werkzeug.security import check_password_hash


@pytest.fixture
def temp_db():
    """テスト用一時データベース"""
    fd, path = tempfile.mkstemp(suffix='.db')
    yield path
    os.close(fd)
    os.unlink(path)


@pytest.fixture
def memory_store():
    """メモリ内データベースストア"""
    return UserDBStore(db_path=":memory:")


@pytest.fixture
def populated_store(memory_store):
    """テストデータが投入されたストア"""
    memory_store.add_user('alice', 'alice123', is_admin=True)
    memory_store.add_user('bob', 'bob123', is_admin=False)
    memory_store.add_user('charlie', 'charlie123', is_admin=False)
    return memory_store


class TestUserDBStoreInitialization:
    """UserDBStore初期化テスト"""

    def test_init_with_memory_db(self):
        """メモリDBで初期化"""
        store = UserDBStore(db_path=":memory:")
        assert store.db_path == ":memory:"

    def test_init_with_file_db(self, temp_db):
        """ファイルDBで初期化"""
        store = UserDBStore(db_path=temp_db)
        assert store.db_path == temp_db
        assert os.path.exists(temp_db)

    def test_connection_context_manager(self, memory_store):
        """接続コンテキストマネージャのテスト"""
        with memory_store.get_connection() as conn:
            assert conn is not None
            cursor = conn.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1


class TestUserDBStoreUserCreation:
    """ユーザー作成テスト"""

    def test_add_user_basic(self, memory_store):
        """基本的なユーザー追加"""
        user = memory_store.add_user('testuser', 'password123', is_admin=False)

        assert user is not None
        assert user.username == 'testuser'
        assert user.is_admin is False
        assert user.is_active is True
        assert user.id.startswith('user-')
        assert len(user.id) > 10
        assert user.created_at is not None
        assert user.last_login is None

    def test_add_admin_user(self, memory_store):
        """管理者ユーザーの追加"""
        user = memory_store.add_user('admin', 'admin123', is_admin=True)

        assert user.username == 'admin'
        assert user.is_admin is True
        assert user.is_active is True

    def test_password_is_hashed(self, memory_store):
        """パスワードがハッシュ化されることを確認"""
        user = memory_store.add_user('testuser', 'plaintext123')

        # パスワードハッシュはプレーンテキストと異なる
        assert user.password_hash != 'plaintext123'
        assert len(user.password_hash) > 20
        assert user.password_hash.startswith('pbkdf2:')

    def test_password_verification(self, memory_store):
        """パスワード検証機能のテスト"""
        user = memory_store.add_user('testuser', 'correct_password')

        # 正しいパスワードで検証
        assert check_password_hash(user.password_hash, 'correct_password')
        # 間違ったパスワードで検証
        assert not check_password_hash(user.password_hash, 'wrong_password')

    def test_unique_user_ids(self, memory_store):
        """各ユーザーがユニークなIDを持つことを確認"""
        user1 = memory_store.add_user('user1', 'pass1')
        user2 = memory_store.add_user('user2', 'pass2')
        user3 = memory_store.add_user('user3', 'pass3')

        assert user1.id != user2.id
        assert user2.id != user3.id
        assert user1.id != user3.id


class TestUserDBStoreUserRetrieval:
    """ユーザー取得テスト"""

    def test_get_user_by_username(self, populated_store):
        """ユーザー名でユーザー取得"""
        user = populated_store.get_user_by_username('alice')

        assert user is not None
        assert user.username == 'alice'
        assert user.is_admin is True

    def test_get_user_by_username_not_found(self, populated_store):
        """存在しないユーザー名での取得"""
        user = populated_store.get_user_by_username('nonexistent')
        assert user is None

    def test_get_user_by_id(self, populated_store):
        """IDでユーザー取得"""
        alice = populated_store.get_user_by_username('alice')
        user = populated_store.get_user_by_id(alice.id)

        assert user is not None
        assert user.id == alice.id
        assert user.username == 'alice'

    def test_get_user_by_id_not_found(self, populated_store):
        """存在しないIDでの取得"""
        user = populated_store.get_user_by_id('invalid-id-12345')
        assert user is None

    def test_get_all_users(self, populated_store):
        """全ユーザー取得"""
        users = populated_store.get_all_users()

        assert len(users) == 3
        usernames = [u.username for u in users]
        assert 'alice' in usernames
        assert 'bob' in usernames
        assert 'charlie' in usernames

    def test_get_all_users_empty_db(self, memory_store):
        """空のDBで全ユーザー取得"""
        users = memory_store.get_all_users()
        assert users == []

    def test_get_user_count(self, populated_store):
        """ユーザー数取得"""
        count = populated_store.get_user_count()
        assert count == 3

    def test_get_user_count_empty_db(self, memory_store):
        """空のDBでユーザー数取得"""
        count = memory_store.get_user_count()
        assert count == 0


class TestUserDBStoreUserUpdate:
    """ユーザー更新テスト"""

    def test_update_password_success(self, populated_store):
        """パスワード更新成功"""
        alice = populated_store.get_user_by_username('alice')

        success = populated_store.update_password(alice.id, 'new_password_456')
        assert success is True

        # パスワードが更新されたことを確認
        updated_user = populated_store.get_user_by_id(alice.id)
        assert check_password_hash(updated_user.password_hash, 'new_password_456')
        assert not check_password_hash(updated_user.password_hash, 'alice123')

    def test_update_password_nonexistent_user(self, populated_store):
        """存在しないユーザーのパスワード更新"""
        success = populated_store.update_password('invalid-id', 'newpass')
        assert success is False

    def test_update_last_login(self, populated_store):
        """最終ログイン時刻更新"""
        alice = populated_store.get_user_by_username('alice')

        # 初期状態ではNone
        assert alice.last_login is None

        # 更新
        success = populated_store.update_last_login(alice.id)
        assert success is True

        # 更新されたことを確認
        updated_user = populated_store.get_user_by_id(alice.id)
        assert updated_user.last_login is not None
        assert isinstance(updated_user.last_login, datetime)

    def test_update_last_login_nonexistent_user(self, populated_store):
        """存在しないユーザーの最終ログイン更新"""
        success = populated_store.update_last_login('invalid-id')
        assert success is False

    def test_toggle_admin_normal_to_admin(self, populated_store):
        """一般ユーザーを管理者に昇格"""
        bob = populated_store.get_user_by_username('bob')
        assert bob.is_admin is False

        success = populated_store.toggle_admin(bob.id)
        assert success is True

        updated_bob = populated_store.get_user_by_id(bob.id)
        assert updated_bob.is_admin is True

    def test_toggle_admin_admin_to_normal(self, populated_store):
        """管理者を一般ユーザーに降格"""
        alice = populated_store.get_user_by_username('alice')
        assert alice.is_admin is True

        success = populated_store.toggle_admin(alice.id)
        assert success is True

        updated_alice = populated_store.get_user_by_id(alice.id)
        assert updated_alice.is_admin is False

    def test_toggle_admin_twice(self, populated_store):
        """管理者権限を2回トグル"""
        bob = populated_store.get_user_by_username('bob')
        original_status = bob.is_admin

        # 1回目
        populated_store.toggle_admin(bob.id)
        user1 = populated_store.get_user_by_id(bob.id)
        assert user1.is_admin != original_status

        # 2回目（元に戻る）
        populated_store.toggle_admin(bob.id)
        user2 = populated_store.get_user_by_id(bob.id)
        assert user2.is_admin == original_status


class TestUserDBStoreUserDeletion:
    """ユーザー削除テスト"""

    def test_delete_user_success(self, populated_store):
        """ユーザー削除成功（論理削除）"""
        bob = populated_store.get_user_by_username('bob')

        success = populated_store.delete_user(bob.id)
        assert success is True

        # 削除後は取得できない（論理削除なので is_active=0）
        all_users = populated_store.get_all_users()
        assert bob.id not in [u.id for u in all_users]

        # ユーザー数も減少
        assert populated_store.get_user_count() == 2

    def test_delete_user_nonexistent(self, populated_store):
        """存在しないユーザーの削除"""
        success = populated_store.delete_user('invalid-id-123')
        assert success is False

    def test_delete_user_already_deleted(self, populated_store):
        """既に削除されたユーザーの再削除"""
        bob = populated_store.get_user_by_username('bob')

        # 1回目の削除
        success1 = populated_store.delete_user(bob.id)
        assert success1 is True

        # 2回目の削除（既に is_active=0 なので失敗）
        success2 = populated_store.delete_user(bob.id)
        assert success2 is False


class TestUserDBStoreEdgeCases:
    """エッジケースと例外処理テスト"""

    def test_add_user_with_special_characters(self, memory_store):
        """特殊文字を含むユーザー名とパスワード"""
        user = memory_store.add_user(
            'user@example.com',
            'P@ssw0rd!#$%',
            is_admin=False
        )

        assert user.username == 'user@example.com'
        assert check_password_hash(user.password_hash, 'P@ssw0rd!#$%')

    def test_add_user_with_unicode(self, memory_store):
        """Unicode文字を含むユーザー名"""
        user = memory_store.add_user('ユーザー太郎', 'パスワード123')

        assert user.username == 'ユーザー太郎'
        retrieved = memory_store.get_user_by_username('ユーザー太郎')
        assert retrieved is not None
        assert retrieved.username == 'ユーザー太郎'

    def test_add_user_with_empty_password(self, memory_store):
        """空のパスワードでユーザー作成"""
        user = memory_store.add_user('testuser', '')

        # 空のパスワードでもハッシュ化される
        assert user.password_hash != ''
        assert check_password_hash(user.password_hash, '')

    def test_get_all_users_excludes_inactive(self, populated_store):
        """非アクティブユーザーは一覧から除外される"""
        bob = populated_store.get_user_by_username('bob')

        # Bobを削除（is_active=0）
        populated_store.delete_user(bob.id)

        # 全ユーザー取得（is_active=1のみ）
        users = populated_store.get_all_users()
        assert len(users) == 2
        assert bob.id not in [u.id for u in users]


class TestUserDBStoreTransaction:
    """トランザクション処理テスト"""

    def test_context_manager_commit_on_success(self, memory_store):
        """成功時はコミットされる"""
        with memory_store.get_connection() as conn:
            conn.execute(
                "INSERT INTO users (id, username, password_hash, is_admin, is_active, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ('test-id', 'testuser', 'hash', 0, 1, datetime.now().isoformat())
            )

        # コミットされているので取得できる
        user = memory_store.get_user_by_username('testuser')
        assert user is not None

    def test_context_manager_rollback_on_error(self, memory_store):
        """エラー時はロールバックされる"""
        try:
            with memory_store.get_connection() as conn:
                conn.execute(
                    "INSERT INTO users (id, username, password_hash, is_admin, is_active, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    ('test-id', 'testuser', 'hash', 0, 1, datetime.now().isoformat())
                )
                # エラーを発生させる
                raise ValueError("Test error")
        except ValueError:
            pass

        # ロールバックされているので取得できない
        user = memory_store.get_user_by_username('testuser')
        assert user is None


class TestUserDBStoreConcurrency:
    """並行処理テスト"""

    def test_multiple_stores_same_db(self, temp_db):
        """同じDBに対する複数のストアインスタンス"""
        store1 = UserDBStore(db_path=temp_db)
        store2 = UserDBStore(db_path=temp_db)

        # store1でユーザー作成
        user1 = store1.add_user('user1', 'pass1')

        # store2から取得できる
        user2 = store2.get_user_by_username('user1')
        assert user2 is not None
        assert user2.id == user1.id
