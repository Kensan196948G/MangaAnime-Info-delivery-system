"""
APIキー認証統合テスト

このテストスイートは、FlaskアプリケーションとAPIキー認証機能の統合をテストします。

実行方法:
    pytest tests/test_api_integration.py -v
"""

import pytest
import sys
import os
import json

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.routes.api_auth import user_store, api_key_store


@pytest.fixture
def setup_test_data():
    """テストデータのセットアップ"""
    # ユーザーを作成
    try:
        user_store.create_user("test_user", "test_password")
    except ValueError:
        pass  # 既に存在する場合は無視

    # APIキーを生成
    api_key = api_key_store.generate_key("test_user", "Test API Key")

    yield {
        'username': 'test_user',
        'password': 'test_password',
        'api_key': api_key.key
    }

    # クリーンアップは不要（インメモリストア）


class TestAPIKeyAuthentication:
    """APIキー認証の統合テスト"""

    def test_api_key_generation_flow(self, setup_test_data):
        """APIキー生成フローのテスト"""
        data = setup_test_data

        # 1. ユーザーが存在することを確認
        user = user_store.get_user(data['username'])
        assert user is not None

        # 2. 新しいAPIキーを生成
        new_key = api_key_store.generate_key(
            data['username'],
            "Another Test Key",
            rate_limit=100
        )

        # 3. キーが生成されたことを確認
        assert new_key.key.startswith("sk_")
        assert new_key.user_id == data['username']
        assert new_key.rate_limit == 100

        # 4. ユーザーのキー一覧を確認
        keys = api_key_store.get_keys_by_user(data['username'])
        assert len(keys) >= 2  # 元のキー + 新しいキー

    def test_api_key_verification_flow(self, setup_test_data):
        """APIキー検証フローのテスト"""
        data = setup_test_data

        # 1. 有効なキーで検証
        verified = api_key_store.verify_key(data['api_key'])
        assert verified is not None
        assert verified.user_id == data['username']

        # 2. 無効なキーで検証
        verified = api_key_store.verify_key("sk_invalid_key")
        assert verified is None

    def test_api_key_revocation_flow(self, setup_test_data):
        """APIキー無効化フローのテスト"""
        data = setup_test_data

        # 1. 新しいキーを生成
        key = api_key_store.generate_key(data['username'], "Revoke Test Key")

        # 2. キーが有効であることを確認
        verified = api_key_store.verify_key(key.key)
        assert verified is not None

        # 3. キーを無効化
        success = api_key_store.revoke_key(key.key, data['username'])
        assert success is True

        # 4. 無効化されたキーは検証に失敗する
        verified = api_key_store.verify_key(key.key)
        assert verified is None

    def test_api_key_deletion_flow(self, setup_test_data):
        """APIキー削除フローのテスト"""
        data = setup_test_data

        # 1. 新しいキーを生成
        key = api_key_store.generate_key(data['username'], "Delete Test Key")

        # 2. ユーザーのキー数を確認
        keys_before = api_key_store.get_keys_by_user(data['username'])
        count_before = len(keys_before)

        # 3. キーを削除
        success = api_key_store.delete_key(key.key, data['username'])
        assert success is True

        # 4. キー数が減っていることを確認
        keys_after = api_key_store.get_keys_by_user(data['username'])
        assert len(keys_after) == count_before - 1

    def test_unauthorized_key_operations(self, setup_test_data):
        """権限のない操作のテスト"""
        data = setup_test_data

        # 1. 他のユーザーを作成
        try:
            user_store.create_user("other_user", "other_password")
        except ValueError:
            pass

        # 2. test_userのキーを生成
        key = api_key_store.generate_key(data['username'], "Protected Key")

        # 3. other_userがキーを無効化しようとする
        success = api_key_store.revoke_key(key.key, "other_user")
        assert success is False

        # 4. キーが依然として有効であることを確認
        verified = api_key_store.verify_key(key.key)
        assert verified is not None

        # 5. other_userがキーを削除しようとする
        success = api_key_store.delete_key(key.key, "other_user")
        assert success is False

        # 6. キーが依然として存在することを確認
        keys = api_key_store.get_keys_by_user(data['username'])
        assert any(k.key == key.key for k in keys)


class TestAPIKeyUsageScenarios:
    """実際の使用シナリオをシミュレート"""

    def test_mobile_app_scenario(self, setup_test_data):
        """モバイルアプリでの使用シナリオ"""
        data = setup_test_data

        # 1. モバイルアプリ用のキーを生成
        mobile_key = api_key_store.generate_key(
            data['username'],
            "Mobile App - iOS",
            rate_limit=120
        )

        # 2. アプリが起動時にキーを検証
        verified = api_key_store.verify_key(mobile_key.key)
        assert verified is not None
        assert verified.name == "Mobile App - iOS"

        # 3. 複数回のAPI呼び出しをシミュレート
        for _ in range(5):
            verified = api_key_store.verify_key(mobile_key.key)
            assert verified is not None

        # 4. 最終利用時刻が更新されていることを確認
        assert mobile_key.last_used is not None

    def test_multiple_devices_scenario(self, setup_test_data):
        """複数デバイスでの使用シナリオ"""
        data = setup_test_data

        # 1. 異なるデバイス用のキーを生成
        ios_key = api_key_store.generate_key(data['username'], "iPhone")
        android_key = api_key_store.generate_key(data['username'], "Android")
        web_key = api_key_store.generate_key(data['username'], "Web Browser")

        # 2. すべてのキーが有効であることを確認
        for key in [ios_key, android_key, web_key]:
            verified = api_key_store.verify_key(key.key)
            assert verified is not None

        # 3. 1つのデバイスのキーを無効化
        api_key_store.revoke_key(android_key.key)

        # 4. 他のキーは依然として有効
        assert api_key_store.verify_key(ios_key.key) is not None
        assert api_key_store.verify_key(web_key.key) is not None
        assert api_key_store.verify_key(android_key.key) is None

    def test_key_rotation_scenario(self, setup_test_data):
        """キーローテーションシナリオ"""
        data = setup_test_data

        # 1. 古いキーを生成
        old_key = api_key_store.generate_key(data['username'], "Production Key V1")

        # 2. 新しいキーを生成
        new_key = api_key_store.generate_key(data['username'], "Production Key V2")

        # 3. 両方のキーが有効であることを確認（移行期間）
        assert api_key_store.verify_key(old_key.key) is not None
        assert api_key_store.verify_key(new_key.key) is not None

        # 4. 古いキーを無効化（移行完了）
        api_key_store.revoke_key(old_key.key)

        # 5. 新しいキーのみが有効
        assert api_key_store.verify_key(old_key.key) is None
        assert api_key_store.verify_key(new_key.key) is not None


class TestAPIKeyEdgeCases:
    """エッジケースのテスト"""

    def test_empty_key_name(self, setup_test_data):
        """空のキー名でのテスト"""
        data = setup_test_data

        # 空の名前でキーを生成
        key = api_key_store.generate_key(data['username'], "")
        assert key is not None
        assert key.name == ""

    def test_very_long_key_name(self, setup_test_data):
        """非常に長いキー名でのテスト"""
        data = setup_test_data

        long_name = "A" * 1000
        key = api_key_store.generate_key(data['username'], long_name)
        assert key.name == long_name

    def test_special_characters_in_key_name(self, setup_test_data):
        """特殊文字を含むキー名でのテスト"""
        data = setup_test_data

        special_name = "Test Key 🔑 #1 (2025)"
        key = api_key_store.generate_key(data['username'], special_name)
        assert key.name == special_name

    def test_zero_rate_limit(self, setup_test_data):
        """レート制限0でのテスト"""
        data = setup_test_data

        key = api_key_store.generate_key(data['username'], "Zero Limit", rate_limit=0)
        assert key.rate_limit == 0

    def test_negative_rate_limit(self, setup_test_data):
        """負のレート制限でのテスト"""
        data = setup_test_data

        # 負の値も受け入れる（バリデーションは別レイヤーで行う）
        key = api_key_store.generate_key(data['username'], "Negative Limit", rate_limit=-1)
        assert key.rate_limit == -1

    def test_delete_nonexistent_key(self, setup_test_data):
        """存在しないキーの削除テスト"""
        data = setup_test_data

        success = api_key_store.delete_key("sk_nonexistent_key", data['username'])
        assert success is False

    def test_revoke_already_revoked_key(self, setup_test_data):
        """既に無効化されたキーの再無効化テスト"""
        data = setup_test_data

        # キーを生成して無効化
        key = api_key_store.generate_key(data['username'], "Test Key")
        api_key_store.revoke_key(key.key)

        # 再度無効化
        success = api_key_store.revoke_key(key.key)
        assert success is True  # 既に無効でも成功を返す


def test_api_key_format():
    """APIキーのフォーマットテスト"""
    key = api_key_store.generate_key("test_user", "Format Test")

    # キーが正しいプレフィックスで始まる
    assert key.key.startswith("sk_")

    # キーが十分な長さを持つ
    assert len(key.key) > 40

    # キーがURL-safeな文字のみを含む
    import string
    allowed_chars = string.ascii_letters + string.digits + '-_'
    key_without_prefix = key.key[3:]  # "sk_"を除去
    assert all(c in allowed_chars for c in key_without_prefix)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
