"""
認証フロー統合テスト - 完全版
ユーザー管理、ブルートフォース対策、監査ログの統合テスト
"""
import pytest
import tempfile
import os
import time
from datetime import datetime, timedelta
from app.models.user_db import UserDBStore
from app.models.api_key_db import APIKeyDBStore
from modules.brute_force_protection import LoginAttemptTracker
from modules.audit_log_db import AuditLoggerDB
from modules.audit_log import AuditEventType


@pytest.fixture
def temp_db():
    """テスト用一時データベース"""
    fd, path = tempfile.mkstemp(suffix='.db')

    # 必要なテーブルを作成
    import sqlite3
    conn = sqlite3.connect(path)

    # usersテーブル
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            updated_at DATETIME
        )
    """)

    # api_keysテーブル
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_used DATETIME,
            is_active INTEGER DEFAULT 1,
            permissions TEXT DEFAULT 'read',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # audit_logsテーブル
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_id TEXT,
            username TEXT,
            ip_address TEXT DEFAULT 'unknown',
            user_agent TEXT DEFAULT 'unknown',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            details TEXT DEFAULT '{}',
            success INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()

    yield path
    os.close(fd)
    os.unlink(path)


@pytest.fixture
def auth_system(temp_db):
    """統合認証システム"""
    return {
        'user_db': UserDBStore(db_path=temp_db),
        'api_key_db': APIKeyDBStore(db_path=temp_db),
        'brute_force': LoginAttemptTracker(),
        'audit_log': AuditLoggerDB(db_path=temp_db)
    }


class TestUserRegistrationFlow:
    """ユーザー登録フローのテスト"""

    def test_complete_registration_flow(self, auth_system):
        """完全な登録フロー"""
        user_db = auth_system['user_db']
        audit_log = auth_system['audit_log']

        # 1. ユーザー登録
        user = user_db.add_user('newuser', 'SecurePass123!', is_admin=False)

        assert user is not None
        assert user.username == 'newuser'
        assert user.is_active is True

        # 2. 監査ログ記録
        audit_log.log_event(
            AuditEventType.USER_CREATE,
            user_id=user.id,
            username='admin',
            details={'new_user': 'newuser'}
        )

        # 3. 監査ログ確認
        logs = audit_log.get_logs(limit=1)
        assert len(logs) == 1
        assert logs[0].event_type == AuditEventType.USER_CREATE

    def test_registration_with_duplicate_username(self, auth_system):
        """重複ユーザー名での登録失敗"""
        user_db = auth_system['user_db']

        # 最初のユーザー
        user_db.add_user('duplicate', 'pass123')

        # 同じユーザー名で再登録
        with user_db.get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO users (id, username, password_hash, is_admin, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    ('user-dup', 'duplicate', 'hash', 0, 1, datetime.now().isoformat())
                )
                assert False, "Should raise UNIQUE constraint error"
            except Exception as e:
                # UNIQUE constraint violation expected
                assert 'UNIQUE' in str(e) or 'duplicate' in str(e).lower()


class TestLoginFlow:
    """ログインフローのテスト"""

    def test_successful_login_flow(self, auth_system):
        """成功ログインフロー"""
        user_db = auth_system['user_db']
        brute_force = auth_system['brute_force']
        audit_log = auth_system['audit_log']

        # 1. ユーザー作成
        user = user_db.add_user('testuser', 'correct_password')

        # 2. アカウントロックチェック
        is_locked, _ = brute_force.is_locked('testuser')
        assert is_locked is False

        # 3. パスワード検証（実際のアプリではここで検証）
        from werkzeug.security import check_password_hash
        assert check_password_hash(user.password_hash, 'correct_password')

        # 4. 最終ログイン時刻更新
        user_db.update_last_login(user.id)

        # 5. ブルートフォース試行クリア
        brute_force.clear_attempts('testuser')

        # 6. 監査ログ記録
        audit_log.log_event(
            AuditEventType.AUTH_LOGIN_SUCCESS,
            user_id=user.id,
            username='testuser',
            ip_address='192.168.1.100',
            success=True
        )

        # 検証
        updated_user = user_db.get_user_by_id(user.id)
        assert updated_user.last_login is not None

        logs = audit_log.get_logs(limit=1)
        assert logs[0].event_type == AuditEventType.AUTH_LOGIN_SUCCESS

    def test_failed_login_flow(self, auth_system):
        """失敗ログインフロー"""
        user_db = auth_system['user_db']
        brute_force = auth_system['brute_force']
        audit_log = auth_system['audit_log']

        # 1. ユーザー作成
        user_db.add_user('testuser', 'correct_password')

        # 2. ログイン失敗
        brute_force.record_failed_attempt('testuser')

        # 3. 監査ログ記録
        audit_log.log_event(
            AuditEventType.AUTH_LOGIN_FAILURE,
            username='testuser',
            ip_address='192.168.1.100',
            details={'reason': 'invalid_password'},
            success=False
        )

        # 検証
        remaining = brute_force.get_remaining_attempts('testuser')
        assert remaining == 4  # 5 - 1 = 4

        logs = audit_log.get_logs(success=False, limit=1)
        assert len(logs) == 1
        assert logs[0].success is False


class TestBruteForceProtectionFlow:
    """ブルートフォース攻撃対策フローのテスト"""

    def test_account_lockout_flow(self, auth_system):
        """アカウントロックフロー"""
        user_db = auth_system['user_db']
        brute_force = auth_system['brute_force']
        audit_log = auth_system['audit_log']

        # 1. ユーザー作成
        user = user_db.add_user('victim', 'password123')

        # 2. 5回ログイン失敗
        for i in range(5):
            brute_force.record_failed_attempt('victim')
            audit_log.log_event(
                AuditEventType.AUTH_LOGIN_FAILURE,
                user_id=user.id,
                username='victim',
                ip_address='10.0.0.1',
                details={'attempt': i + 1},
                success=False
            )

        # 3. アカウントロック確認
        is_locked, unlock_time = brute_force.is_locked('victim')
        assert is_locked is True
        assert unlock_time is not None

        # 4. ロック中は残り試行回数0
        remaining = brute_force.get_remaining_attempts('victim')
        assert remaining == 0

        # 5. 失敗ログが5件記録されている
        failure_logs = audit_log.get_recent_failures(username='victim', limit=10)
        assert len(failure_logs) == 5

    def test_admin_unlock_flow(self, auth_system):
        """管理者によるロック解除フロー"""
        brute_force = auth_system['brute_force']
        audit_log = auth_system['audit_log']

        # 1. アカウントをロック
        for i in range(5):
            brute_force.record_failed_attempt('locked_user')

        is_locked, _ = brute_force.is_locked('locked_user')
        assert is_locked is True

        # 2. 管理者によるロック解除
        success = brute_force.unlock_account('locked_user')
        assert success is True

        # 3. ロック解除ログ記録
        audit_log.log_event(
            AuditEventType.USER_UPDATE,
            user_id='admin-1',
            username='admin',
            details={'action': 'unlock_account', 'target_user': 'locked_user'}
        )

        # 4. ロック解除確認
        is_locked, _ = brute_force.is_locked('locked_user')
        assert is_locked is False


class TestAPIKeyAuthenticationFlow:
    """APIキー認証フローのテスト"""

    def test_api_key_generation_flow(self, auth_system):
        """APIキー生成フロー"""
        user_db = auth_system['user_db']
        api_key_db = auth_system['api_key_db']
        audit_log = auth_system['audit_log']

        # 1. ユーザー作成
        user = user_db.add_user('apiuser', 'password123')

        # 2. APIキー生成
        api_key = api_key_db.generate_key(
            user.id,
            'Production API Key',
            ['read', 'write']
        )

        # 3. 監査ログ記録
        audit_log.log_event(
            AuditEventType.API_KEY_GENERATE,
            user_id=user.id,
            username='apiuser',
            details={'key_name': 'Production API Key', 'permissions': 'read,write'}
        )

        # 検証
        assert api_key.key.startswith('sk_')
        assert api_key.user_id == user.id

        logs = audit_log.get_logs(event_type=AuditEventType.API_KEY_GENERATE, limit=1)
        assert len(logs) == 1

    def test_api_key_usage_flow(self, auth_system):
        """APIキー使用フロー"""
        user_db = auth_system['user_db']
        api_key_db = auth_system['api_key_db']
        audit_log = auth_system['audit_log']

        # 1. ユーザーとAPIキー作成
        user = user_db.add_user('apiuser', 'password123')
        api_key = api_key_db.generate_key(user.id, 'Test Key')

        # 2. APIキー検証
        verified_key = api_key_db.verify_key(api_key.key)
        assert verified_key is not None

        # 3. API呼び出しログ記録
        audit_log.log_event(
            AuditEventType.API_CALL,
            user_id=user.id,
            username='apiuser',
            details={'endpoint': '/api/data', 'method': 'GET'}
        )

        # 4. last_usedが更新されている
        assert verified_key.last_used is not None

    def test_api_key_revocation_flow(self, auth_system):
        """APIキー無効化フロー"""
        user_db = auth_system['user_db']
        api_key_db = auth_system['api_key_db']
        audit_log = auth_system['audit_log']

        # 1. ユーザーとAPIキー作成
        user = user_db.add_user('apiuser', 'password123')
        api_key = api_key_db.generate_key(user.id, 'Revoke Test')

        # 2. キー無効化
        success = api_key_db.revoke_key(api_key.key)
        assert success is True

        # 3. 監査ログ記録
        audit_log.log_event(
            AuditEventType.API_KEY_REVOKE,
            user_id=user.id,
            username='apiuser',
            details={'key_name': 'Revoke Test'}
        )

        # 4. 無効化されたキーは検証失敗
        verified = api_key_db.verify_key(api_key.key)
        assert verified is None


class TestPasswordChangeFlow:
    """パスワード変更フローのテスト"""

    def test_password_change_flow(self, auth_system):
        """パスワード変更フロー"""
        user_db = auth_system['user_db']
        audit_log = auth_system['audit_log']

        # 1. ユーザー作成
        user = user_db.add_user('testuser', 'old_password')

        # 2. パスワード変更
        success = user_db.update_password(user.id, 'new_password')
        assert success is True

        # 3. 監査ログ記録
        audit_log.log_event(
            AuditEventType.AUTH_PASSWORD_CHANGE,
            user_id=user.id,
            username='testuser',
            details={'method': 'user_initiated'}
        )

        # 4. 新しいパスワードで検証できる
        from werkzeug.security import check_password_hash
        updated_user = user_db.get_user_by_id(user.id)
        assert check_password_hash(updated_user.password_hash, 'new_password')
        assert not check_password_hash(updated_user.password_hash, 'old_password')


class TestUserDeletionFlow:
    """ユーザー削除フローのテスト"""

    def test_user_deletion_flow(self, auth_system):
        """ユーザー削除フロー"""
        user_db = auth_system['user_db']
        api_key_db = auth_system['api_key_db']
        audit_log = auth_system['audit_log']

        # 1. ユーザーとAPIキー作成
        user = user_db.add_user('deleteuser', 'password123')
        api_key = api_key_db.generate_key(user.id, 'User Key')

        # 2. ユーザー削除（論理削除）
        success = user_db.delete_user(user.id)
        assert success is True

        # 3. 監査ログ記録
        audit_log.log_event(
            AuditEventType.USER_DELETE,
            user_id='admin-1',
            username='admin',
            details={'deleted_user': 'deleteuser', 'user_id': user.id}
        )

        # 4. 削除されたユーザーは一覧に表示されない
        all_users = user_db.get_all_users()
        assert user.id not in [u.id for u in all_users]

        # 5. APIキーも無効化すべき（実装による）
        # この例ではキーは残っているが、ユーザーが無効なので使用不可


class TestCompleteAuthenticationScenario:
    """完全な認証シナリオテスト"""

    def test_typical_user_session(self, auth_system):
        """典型的なユーザーセッション"""
        user_db = auth_system['user_db']
        api_key_db = auth_system['api_key_db']
        brute_force = auth_system['brute_force']
        audit_log = auth_system['audit_log']

        # === 1. ユーザー登録 ===
        user = user_db.add_user('alice', 'AlicePass123!')
        audit_log.log_event(
            AuditEventType.USER_CREATE,
            user_id=user.id,
            username='alice',
            ip_address='192.168.1.100'
        )

        # === 2. 初回ログイン成功 ===
        is_locked, _ = brute_force.is_locked('alice')
        assert is_locked is False

        user_db.update_last_login(user.id)
        brute_force.clear_attempts('alice')
        audit_log.log_event(
            AuditEventType.AUTH_LOGIN_SUCCESS,
            user_id=user.id,
            username='alice',
            ip_address='192.168.1.100'
        )

        # === 3. APIキー生成 ===
        api_key = api_key_db.generate_key(user.id, 'Alice Main Key', ['read', 'write'])
        audit_log.log_event(
            AuditEventType.API_KEY_GENERATE,
            user_id=user.id,
            username='alice',
            details={'key_name': 'Alice Main Key'}
        )

        # === 4. API使用 ===
        verified = api_key_db.verify_key(api_key.key)
        assert verified is not None
        audit_log.log_event(
            AuditEventType.API_CALL,
            user_id=user.id,
            username='alice',
            details={'endpoint': '/api/data'}
        )

        # === 5. パスワード変更 ===
        user_db.update_password(user.id, 'NewAlicePass456!')
        audit_log.log_event(
            AuditEventType.AUTH_PASSWORD_CHANGE,
            user_id=user.id,
            username='alice'
        )

        # === 6. ログアウト ===
        audit_log.log_event(
            AuditEventType.AUTH_LOGOUT,
            user_id=user.id,
            username='alice',
            ip_address='192.168.1.100'
        )

        # === 検証 ===
        # ユーザー情報
        final_user = user_db.get_user_by_id(user.id)
        assert final_user.last_login is not None

        # APIキー
        keys = api_key_db.get_keys_by_user(user.id)
        assert len(keys) == 1

        # 監査ログ
        all_logs = audit_log.get_logs(user_id=user.id, limit=100)
        assert len(all_logs) >= 6

        # 統計
        stats = audit_log.get_statistics()
        assert stats['total_logs'] >= 6

    def test_security_incident_scenario(self, auth_system):
        """セキュリティインシデントシナリオ"""
        user_db = auth_system['user_db']
        brute_force = auth_system['brute_force']
        audit_log = auth_system['audit_log']

        # === 1. 正規ユーザー作成 ===
        user = user_db.add_user('target', 'SecurePassword123!')

        # === 2. 攻撃者による複数回ログイン試行 ===
        attacker_ip = '10.0.0.1'
        for i in range(10):
            brute_force.record_failed_attempt('target')
            audit_log.log_event(
                AuditEventType.AUTH_LOGIN_FAILURE,
                username='target',
                ip_address=attacker_ip,
                details={'attempt': i + 1, 'reason': 'invalid_password'},
                success=False
            )

        # === 3. アカウントロック確認 ===
        is_locked, unlock_time = brute_force.is_locked('target')
        assert is_locked is True

        # === 4. ロック中のアカウント一覧 ===
        locked_accounts = brute_force.get_locked_accounts()
        assert len(locked_accounts) > 0
        assert any(acc['username'] == 'target' for acc in locked_accounts)

        # === 5. 失敗ログ分析 ===
        failures = audit_log.get_recent_failures(username='target', limit=20)
        assert len(failures) >= 10

        # 全て同じIPからの攻撃
        assert all(f.ip_address == attacker_ip for f in failures)

        # === 6. 管理者による対応 ===
        # ロック解除
        brute_force.unlock_account('target')

        # 監査ログ記録
        audit_log.log_event(
            AuditEventType.USER_UPDATE,
            user_id='admin-1',
            username='admin',
            details={'action': 'unlock_account', 'target': 'target', 'reason': 'verified_user'}
        )

        # === 7. ロック解除確認 ===
        is_locked, _ = brute_force.is_locked('target')
        assert is_locked is False


class TestMultiUserScenario:
    """複数ユーザーシナリオテスト"""

    def test_multiple_users_independence(self, auth_system):
        """複数ユーザーの独立性"""
        user_db = auth_system['user_db']
        api_key_db = auth_system['api_key_db']
        brute_force = auth_system['brute_force']

        # === ユーザー作成 ===
        alice = user_db.add_user('alice', 'AlicePass123!')
        bob = user_db.add_user('bob', 'BobPass456!')
        charlie = user_db.add_user('charlie', 'CharliePass789!')

        # === 各ユーザーのAPIキー ===
        alice_key = api_key_db.generate_key(alice.id, 'Alice Key')
        bob_key1 = api_key_db.generate_key(bob.id, 'Bob Key 1')
        bob_key2 = api_key_db.generate_key(bob.id, 'Bob Key 2')

        # === Aliceはログイン失敗3回 ===
        for i in range(3):
            brute_force.record_failed_attempt('alice')

        # === Bobはログイン失敗5回（ロック） ===
        for i in range(5):
            brute_force.record_failed_attempt('bob')

        # === Charlieはログイン成功 ===
        user_db.update_last_login(charlie.id)

        # === 検証 ===
        # Alice: まだロックされていない
        assert not brute_force.is_locked('alice')[0]
        assert brute_force.get_remaining_attempts('alice') == 2

        # Bob: ロックされている
        assert brute_force.is_locked('bob')[0]
        assert brute_force.get_remaining_attempts('bob') == 0

        # Charlie: 影響なし
        assert not brute_force.is_locked('charlie')[0]
        assert brute_force.get_remaining_attempts('charlie') == 5

        # APIキー数
        assert len(api_key_db.get_keys_by_user(alice.id)) == 1
        assert len(api_key_db.get_keys_by_user(bob.id)) == 2
        assert len(api_key_db.get_keys_by_user(charlie.id)) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
