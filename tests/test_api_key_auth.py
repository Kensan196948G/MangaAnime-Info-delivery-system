"""
APIキー認証システムのテスト
"""
import pytest
from datetime import datetime

try:
    from app.models.api_key_db import APIKeyDBStore, APIKey
except (ImportError, ValueError) as e:
    pytest.skip(f"app.models.api_key_db module not available: {e}", allow_module_level=True)


class TestAPIKeyGeneration:
    """APIキー生成のテスト"""
    
    def test_generate_key_format(self):
        """キー形式の検証"""
        store = APIKeyDBStore(db_path=":memory:")
        key = store.generate_key('user1', 'Test Key', ['read'])
        
        assert key.key.startswith('sk_')
        assert len(key.key) > 40
        assert key.user_id == 'user1'
        assert key.name == 'Test Key'
        assert key.is_active is True
        assert 'read' in key.permissions
    
    def test_generate_multiple_keys(self):
        """複数キー生成"""
        store = APIKeyDBStore(db_path=":memory:")
        
        key1 = store.generate_key('user1', 'Key 1', ['read'])
        key2 = store.generate_key('user1', 'Key 2', ['read', 'write'])
        
        assert key1.key != key2.key
        assert key1.user_id == key2.user_id


class TestAPIKeyVerification:
    """APIキー検証のテスト"""
    
    def test_verify_valid_key(self):
        """有効なキーの検証"""
        store = APIKeyDBStore(db_path=":memory:")
        key = store.generate_key('user1', 'Test Key', ['read'])
        
        verified = store.verify_key(key.key)
        assert verified is not None
        assert verified.user_id == 'user1'
        assert verified.last_used is not None
    
    def test_verify_invalid_key(self):
        """無効なキーの検証"""
        store = APIKeyDBStore(db_path=":memory:")
        
        verified = store.verify_key('sk_invalid_key')
        assert verified is None
    
    def test_verify_revoked_key(self):
        """無効化されたキーの検証"""
        store = APIKeyDBStore(db_path=":memory:")
        key = store.generate_key('user1', 'Test Key', ['read'])
        
        store.revoke_key(key.key)
        verified = store.verify_key(key.key)
        assert verified is None


class TestAPIKeyManagement:
    """APIキー管理のテスト"""
    
    def test_get_keys_by_user(self):
        """ユーザー別キー取得"""
        store = APIKeyDBStore(db_path=":memory:")
        
        store.generate_key('user1', 'Key 1', ['read'])
        store.generate_key('user1', 'Key 2', ['write'])
        store.generate_key('user2', 'Key 3', ['read'])
        
        user1_keys = store.get_keys_by_user('user1')
        assert len(user1_keys) == 2
        assert all(k.user_id == 'user1' for k in user1_keys)
    
    def test_revoke_key(self):
        """キー無効化"""
        store = APIKeyDBStore(db_path=":memory:")
        key = store.generate_key('user1', 'Test Key', ['read'])
        
        success = store.revoke_key(key.key)
        assert success is True
        
        verified = store.verify_key(key.key)
        assert verified is None
    
    def test_delete_key(self):
        """キー物理削除"""
        store = APIKeyDBStore(db_path=":memory:")
        key = store.generate_key('user1', 'Test Key', ['read'])
        
        success = store.delete_key(key.key)
        assert success is True
        
        keys = store.get_keys_by_user('user1')
        assert len(keys) == 0
