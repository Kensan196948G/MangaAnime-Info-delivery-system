"""
APIキーデータベース管理のテスト - 完全版
SQLiteベースのAPIキー管理機能の包括的テスト
"""
import pytest
import tempfile
import os
import time
from datetime import datetime, timedelta
from app.models.api_key_db import APIKeyDBStore, APIKey


@pytest.fixture
def temp_db():
    """テスト用一時データベース"""
    fd, path = tempfile.mkstemp(suffix='.db')
    # usersテーブルを作成
    import sqlite3
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    """)
    conn.commit()
    conn.close()

    yield path
    os.close(fd)
    os.unlink(path)


@pytest.fixture
def memory_store():
    """メモリ内データベースストア"""
    # usersテーブルを作成
    import sqlite3
    conn = sqlite3.connect(':memory:')
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    """)
    conn.commit()
    conn.close()

    return APIKeyDBStore(db_path=":memory:")


@pytest.fixture
def populated_store(memory_store):
    """テストデータが投入されたストア"""
    # 3つのAPIキーを生成
    memory_store.generate_key('user-1', 'Production Key', ['read', 'write'])
    memory_store.generate_key('user-1', 'Testing Key', ['read'])
    memory_store.generate_key('user-2', 'Admin Key', ['admin'])
    return memory_store


class TestAPIKeyDBStoreInitialization:
    """APIKeyDBStore初期化テスト"""

    def test_init_with_memory_db(self, memory_store):
        """メモリDBで初期化"""
        assert memory_store.db_path == ":memory:"

    def test_init_with_file_db(self, temp_db):
        """ファイルDBで初期化"""
        store = APIKeyDBStore(db_path=temp_db)
        assert store.db_path == temp_db
        assert os.path.exists(temp_db)

    def test_connection_context_manager(self, memory_store):
        """接続コンテキストマネージャのテスト"""
        with memory_store.get_connection() as conn:
            assert conn is not None
            cursor = conn.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1

    def test_table_creation(self, memory_store):
        """テーブルが正しく作成されているか"""
        with memory_store.get_connection() as conn:
            # api_keysテーブルの存在確認
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='api_keys'"
            )
            assert cursor.fetchone() is not None

            # インデックスの存在確認
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_api_keys%'"
            )
            indexes = cursor.fetchall()
            assert len(indexes) >= 2  # user_id と is_active のインデックス


class TestAPIKeyDBStoreKeyGeneration:
    """APIキー生成テスト"""

    def test_generate_key_basic(self, memory_store):
        """基本的なキー生成"""
        api_key = memory_store.generate_key('user-123', 'Test Key')

        assert api_key is not None
        assert api_key.key.startswith('sk_')
        assert len(api_key.key) > 40
        assert api_key.user_id == 'user-123'
        assert api_key.name == 'Test Key'
        assert api_key.is_active is True
        assert api_key.permissions == 'read'
        assert isinstance(api_key.created_at, datetime)

    def test_generate_key_with_permissions(self, memory_store):
        """パーミッション指定でキー生成"""
        api_key = memory_store.generate_key(
            'user-456',
            'Full Access Key',
            permissions=['read', 'write', 'admin']
        )

        assert api_key.permissions == 'read,write,admin'

    def test_generate_key_uniqueness(self, memory_store):
        """各キーがユニークであることを確認"""
        key1 = memory_store.generate_key('user-1', 'Key 1')
        key2 = memory_store.generate_key('user-1', 'Key 2')
        key3 = memory_store.generate_key('user-1', 'Key 3')

        assert key1.key != key2.key
        assert key2.key != key3.key
        assert key1.key != key3.key

    def test_generate_multiple_keys_same_user(self, memory_store):
        """同一ユーザーが複数のキーを持つ"""
        for i in range(5):
            memory_store.generate_key('user-multi', f'Key {i}')

        keys = memory_store.get_keys_by_user('user-multi')
        assert len(keys) == 5

    def test_generate_key_long_name(self, memory_store):
        """長い名前でキー生成"""
        long_name = 'A' * 255
        api_key = memory_store.generate_key('user-1', long_name)
        assert api_key.name == long_name

    def test_generate_key_unicode_name(self, memory_store):
        """Unicode文字を含む名前"""
        api_key = memory_store.generate_key('user-1', 'テストキー')
        assert api_key.name == 'テストキー'


class TestAPIKeyDBStoreKeyVerification:
    """APIキー検証テスト"""

    def test_verify_valid_key(self, populated_store):
        """有効なキーの検証"""
        # 新しいキーを生成
        generated_key = populated_store.generate_key('user-test', 'Verify Key')

        # キーを検証
        verified_key = populated_store.verify_key(generated_key.key)

        assert verified_key is not None
        assert verified_key.key == generated_key.key
        assert verified_key.user_id == 'user-test'
        assert verified_key.is_active is True

    def test_verify_updates_last_used(self, memory_store):
        """検証時にlast_usedが更新される"""
        api_key = memory_store.generate_key('user-1', 'Test Key')

        # 初期状態ではNone
        assert api_key.last_used is None

        # 検証
        verified = memory_store.verify_key(api_key.key)

        # last_usedが更新されている
        assert verified.last_used is not None
        assert isinstance(verified.last_used, datetime)

    def test_verify_invalid_key(self, memory_store):
        """無効なキーの検証"""
        verified = memory_store.verify_key('sk_invalid_key_123456789')
        assert verified is None

    def test_verify_revoked_key(self, memory_store):
        """無効化されたキーの検証"""
        api_key = memory_store.generate_key('user-1', 'Revoke Test')

        # キーを無効化
        memory_store.revoke_key(api_key.key)

        # 検証失敗
        verified = memory_store.verify_key(api_key.key)
        assert verified is None

    def test_verify_empty_key(self, memory_store):
        """空のキーで検証"""
        verified = memory_store.verify_key('')
        assert verified is None

    def test_verify_none_key(self, memory_store):
        """Noneで検証"""
        verified = memory_store.verify_key(None)
        assert verified is None


class TestAPIKeyDBStoreKeyRetrieval:
    """APIキー取得テスト"""

    def test_get_keys_by_user(self, populated_store):
        """ユーザーのキー一覧取得"""
        keys = populated_store.get_keys_by_user('user-1')

        assert len(keys) == 2
        assert all(k.user_id == 'user-1' for k in keys)

    def test_get_keys_by_user_empty(self, memory_store):
        """キーを持たないユーザー"""
        keys = memory_store.get_keys_by_user('nonexistent-user')
        assert keys == []

    def test_get_keys_ordered_by_creation(self, memory_store):
        """キーが作成日時の降順で取得される"""
        for i in range(3):
            memory_store.generate_key('user-1', f'Key {i}')
            time.sleep(0.01)

        keys = memory_store.get_keys_by_user('user-1')

        # 最新が先頭
        assert keys[0].name == 'Key 2'
        assert keys[1].name == 'Key 1'
        assert keys[2].name == 'Key 0'

    def test_get_keys_includes_revoked(self, memory_store):
        """無効化されたキーも含めて取得"""
        key1 = memory_store.generate_key('user-1', 'Active Key')
        key2 = memory_store.generate_key('user-1', 'Revoked Key')

        # key2を無効化
        memory_store.revoke_key(key2.key)

        keys = memory_store.get_keys_by_user('user-1')

        # 両方取得される
        assert len(keys) == 2


class TestAPIKeyDBStoreKeyRevocation:
    """APIキー無効化テスト"""

    def test_revoke_key_success(self, memory_store):
        """キー無効化成功"""
        api_key = memory_store.generate_key('user-1', 'Test Key')

        success = memory_store.revoke_key(api_key.key)
        assert success is True

        # 無効化を確認
        keys = memory_store.get_keys_by_user('user-1')
        assert keys[0].is_active is False

    def test_revoke_nonexistent_key(self, memory_store):
        """存在しないキーの無効化"""
        success = memory_store.revoke_key('sk_nonexistent_12345')
        assert success is False

    def test_revoke_already_revoked_key(self, memory_store):
        """既に無効化されたキーの再無効化"""
        api_key = memory_store.generate_key('user-1', 'Test Key')

        # 1回目の無効化
        success1 = memory_store.revoke_key(api_key.key)
        assert success1 is True

        # 2回目の無効化（既に is_active=0 なので更新なし）
        success2 = memory_store.revoke_key(api_key.key)
        assert success2 is False

    def test_revoke_does_not_delete(self, memory_store):
        """無効化は物理削除しない"""
        api_key = memory_store.generate_key('user-1', 'Test Key')

        memory_store.revoke_key(api_key.key)

        # まだ取得できる（is_active=0だが存在する）
        keys = memory_store.get_keys_by_user('user-1')
        assert len(keys) == 1
        assert keys[0].key == api_key.key


class TestAPIKeyDBStoreKeyDeletion:
    """APIキー削除テスト"""

    def test_delete_key_success(self, memory_store):
        """キー削除成功"""
        api_key = memory_store.generate_key('user-1', 'Test Key')

        success = memory_store.delete_key(api_key.key)
        assert success is True

        # 削除を確認
        keys = memory_store.get_keys_by_user('user-1')
        assert len(keys) == 0

    def test_delete_nonexistent_key(self, memory_store):
        """存在しないキーの削除"""
        success = memory_store.delete_key('sk_nonexistent_12345')
        assert success is False

    def test_delete_is_permanent(self, memory_store):
        """削除は永続的（物理削除）"""
        api_key = memory_store.generate_key('user-1', 'Test Key')

        memory_store.delete_key(api_key.key)

        # 検証できない
        verified = memory_store.verify_key(api_key.key)
        assert verified is None

        # 一覧にも含まれない
        keys = memory_store.get_keys_by_user('user-1')
        assert len(keys) == 0


class TestAPIKeyDBStorePermissions:
    """パーミッション管理テスト"""

    def test_default_permissions(self, memory_store):
        """デフォルトパーミッション"""
        api_key = memory_store.generate_key('user-1', 'Default Key')
        assert api_key.permissions == 'read'

    def test_single_permission(self, memory_store):
        """単一パーミッション"""
        api_key = memory_store.generate_key('user-1', 'Write Key', ['write'])
        assert api_key.permissions == 'write'

    def test_multiple_permissions(self, memory_store):
        """複数パーミッション"""
        api_key = memory_store.generate_key(
            'user-1',
            'Full Key',
            ['read', 'write', 'admin']
        )
        assert api_key.permissions == 'read,write,admin'

    def test_permissions_preserved_after_verification(self, memory_store):
        """検証後もパーミッションが保持される"""
        api_key = memory_store.generate_key(
            'user-1',
            'Test Key',
            ['read', 'write']
        )

        verified = memory_store.verify_key(api_key.key)
        assert verified.permissions == 'read,write'


class TestAPIKeyDBStoreEdgeCases:
    """エッジケースと例外処理テスト"""

    def test_special_characters_in_name(self, memory_store):
        """特殊文字を含む名前"""
        api_key = memory_store.generate_key(
            'user-1',
            'Key @#$%^&*()'
        )
        assert api_key.name == 'Key @#$%^&*()'

    def test_empty_name(self, memory_store):
        """空の名前"""
        api_key = memory_store.generate_key('user-1', '')
        assert api_key.name == ''

    def test_very_long_user_id(self, memory_store):
        """非常に長いユーザーID"""
        long_user_id = 'user-' + 'x' * 1000
        api_key = memory_store.generate_key(long_user_id, 'Test Key')
        assert api_key.user_id == long_user_id

    def test_empty_permissions_list(self, memory_store):
        """空のパーミッションリスト"""
        api_key = memory_store.generate_key('user-1', 'Key', [])
        # 空リストはデフォルトの'read'になる
        assert api_key.permissions == 'read'

    def test_none_permissions(self, memory_store):
        """Noneパーミッション"""
        api_key = memory_store.generate_key('user-1', 'Key', None)
        assert api_key.permissions == 'read'


class TestAPIKeyDBStoreTransaction:
    """トランザクション処理テスト"""

    def test_context_manager_commit(self, memory_store):
        """成功時のコミット"""
        with memory_store.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO api_keys (key, user_id, name, permissions)
                VALUES (?, ?, ?, ?)
                """,
                ('sk_test_12345', 'user-1', 'Manual Key', 'read')
            )

        # コミットされているので検証できる
        verified = memory_store.verify_key('sk_test_12345')
        assert verified is not None

    def test_context_manager_rollback(self, memory_store):
        """エラー時のロールバック"""
        try:
            with memory_store.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO api_keys (key, user_id, name, permissions)
                    VALUES (?, ?, ?, ?)
                    """,
                    ('sk_test_rollback', 'user-1', 'Rollback Key', 'read')
                )
                # エラーを発生させる
                raise ValueError("Test error")
        except ValueError:
            pass

        # ロールバックされているので検証できない
        verified = memory_store.verify_key('sk_test_rollback')
        assert verified is None


class TestAPIKeyDBStoreConcurrency:
    """並行処理テスト"""

    def test_multiple_stores_same_db(self, temp_db):
        """同じDBに対する複数のストアインスタンス"""
        store1 = APIKeyDBStore(db_path=temp_db)
        store2 = APIKeyDBStore(db_path=temp_db)

        # store1でキー生成
        key1 = store1.generate_key('user-1', 'Key 1')

        # store2から検証できる
        verified = store2.verify_key(key1.key)
        assert verified is not None
        assert verified.key == key1.key


class TestAPIKeyDBStoreIntegration:
    """統合テスト"""

    def test_full_lifecycle(self, memory_store):
        """APIキーの完全なライフサイクル"""
        # 1. キー生成
        api_key = memory_store.generate_key(
            'user-lifecycle',
            'Lifecycle Key',
            ['read', 'write']
        )
        assert api_key.is_active is True

        # 2. キー検証（使用）
        verified = memory_store.verify_key(api_key.key)
        assert verified.last_used is not None

        # 3. ユーザーのキー一覧取得
        keys = memory_store.get_keys_by_user('user-lifecycle')
        assert len(keys) == 1

        # 4. キー無効化
        memory_store.revoke_key(api_key.key)

        # 5. 無効化されたキーは検証失敗
        verified = memory_store.verify_key(api_key.key)
        assert verified is None

        # 6. キー削除
        memory_store.delete_key(api_key.key)

        # 7. 削除されたキーは一覧から消える
        keys = memory_store.get_keys_by_user('user-lifecycle')
        assert len(keys) == 0

    def test_multiple_users_scenario(self, memory_store):
        """複数ユーザーのシナリオ"""
        # Alice: 2つのキー
        alice_key1 = memory_store.generate_key('alice', 'Alice Key 1')
        alice_key2 = memory_store.generate_key('alice', 'Alice Key 2')

        # Bob: 1つのキー
        bob_key1 = memory_store.generate_key('bob', 'Bob Key 1')

        # Charlie: キーなし

        # Aliceのキー確認
        alice_keys = memory_store.get_keys_by_user('alice')
        assert len(alice_keys) == 2

        # Bobのキー確認
        bob_keys = memory_store.get_keys_by_user('bob')
        assert len(bob_keys) == 1

        # Charlieのキー確認
        charlie_keys = memory_store.get_keys_by_user('charlie')
        assert len(charlie_keys) == 0

        # 各キーが正しいユーザーに紐づいている
        assert memory_store.verify_key(alice_key1.key).user_id == 'alice'
        assert memory_store.verify_key(bob_key1.key).user_id == 'bob'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
