"""
ブルートフォース攻撃対策モジュールのテスト - 完全版
ログイン試行追跡とアカウントロック機能の包括的テスト
"""
import pytest
import time
from datetime import datetime, timedelta
from modules.brute_force_protection import LoginAttemptTracker


@pytest.fixture
def tracker():
    """新しいLoginAttemptTrackerインスタンス"""
    return LoginAttemptTracker()


@pytest.fixture
def tracker_with_attempts(tracker):
    """失敗試行が記録されたトラッカー"""
    tracker.record_failed_attempt('testuser')
    tracker.record_failed_attempt('testuser')
    tracker.record_failed_attempt('testuser')
    return tracker


class TestLoginAttemptTrackerBasics:
    """基本機能テスト"""

    def test_tracker_initialization(self, tracker):
        """トラッカーの初期化"""
        assert tracker.MAX_ATTEMPTS == 5
        assert tracker.ATTEMPT_WINDOW == timedelta(minutes=15)
        assert tracker.LOCKOUT_DURATION == timedelta(minutes=30)
        assert isinstance(tracker._attempts, dict)
        assert isinstance(tracker._locked_accounts, dict)

    def test_record_first_failed_attempt(self, tracker):
        """最初の失敗試行を記録"""
        tracker.record_failed_attempt('alice')

        assert 'alice' in tracker._attempts
        assert len(tracker._attempts['alice']) == 1
        assert isinstance(tracker._attempts['alice'][0], datetime)

    def test_record_multiple_failed_attempts(self, tracker):
        """複数の失敗試行を記録"""
        tracker.record_failed_attempt('bob')
        tracker.record_failed_attempt('bob')
        tracker.record_failed_attempt('bob')

        assert len(tracker._attempts['bob']) == 3

    def test_record_attempts_for_different_users(self, tracker):
        """異なるユーザーの試行を個別に記録"""
        tracker.record_failed_attempt('alice')
        tracker.record_failed_attempt('bob')
        tracker.record_failed_attempt('alice')

        assert len(tracker._attempts['alice']) == 2
        assert len(tracker._attempts['bob']) == 1


class TestLoginAttemptTrackerLocking:
    """アカウントロック機能テスト"""

    def test_is_locked_no_attempts(self, tracker):
        """試行がない場合はロックされていない"""
        is_locked, unlock_time = tracker.is_locked('newuser')

        assert is_locked is False
        assert unlock_time is None

    def test_is_locked_few_attempts(self, tracker_with_attempts):
        """試行回数が閾値未満の場合"""
        # 3回の失敗試行
        is_locked, unlock_time = tracker_with_attempts.is_locked('testuser')

        assert is_locked is False
        assert unlock_time is None

    def test_account_locked_after_max_attempts(self, tracker):
        """最大試行回数到達後にロック"""
        # 5回失敗試行
        for i in range(5):
            tracker.record_failed_attempt('alice')

        is_locked, unlock_time = tracker.is_locked('alice')

        assert is_locked is True
        assert unlock_time is not None
        assert unlock_time > datetime.now()
        assert 'alice' in tracker._locked_accounts

    def test_lockout_duration_correct(self, tracker):
        """ロック期間が正しいことを確認"""
        # 5回失敗してロック
        for i in range(5):
            tracker.record_failed_attempt('bob')

        is_locked, unlock_time = tracker.is_locked('bob')

        # ロック期間は約30分
        expected_unlock = datetime.now() + tracker.LOCKOUT_DURATION
        time_diff = abs((unlock_time - expected_unlock).total_seconds())
        assert time_diff < 2  # 2秒以内の誤差を許容

    def test_locked_account_stays_locked(self, tracker):
        """ロックされたアカウントはロック期間中ロックされ続ける"""
        # 5回失敗してロック
        for i in range(5):
            tracker.record_failed_attempt('charlie')

        # 1回目のチェック
        is_locked1, unlock_time1 = tracker.is_locked('charlie')
        assert is_locked1 is True

        # 少し待つ
        time.sleep(0.1)

        # 2回目のチェック（まだロック中）
        is_locked2, unlock_time2 = tracker.is_locked('charlie')
        assert is_locked2 is True


class TestLoginAttemptTrackerClearAttempts:
    """試行回数クリア機能テスト"""

    def test_clear_attempts_success(self, tracker_with_attempts):
        """成功ログイン時の試行回数クリア"""
        # 事前に3回の失敗がある
        assert len(tracker_with_attempts._attempts['testuser']) == 3

        # クリア
        tracker_with_attempts.clear_attempts('testuser')

        # 試行記録が削除される
        assert 'testuser' not in tracker_with_attempts._attempts

    def test_clear_nonexistent_user(self, tracker):
        """存在しないユーザーのクリア（エラーにならない）"""
        tracker.clear_attempts('nonexistent')
        # エラーが発生しないことを確認

    def test_clear_resets_lock_eligibility(self, tracker):
        """クリア後は再びロック対象になる"""
        # 4回失敗
        for i in range(4):
            tracker.record_failed_attempt('dave')

        # クリア
        tracker.clear_attempts('dave')

        # 再度5回失敗でロック
        for i in range(5):
            tracker.record_failed_attempt('dave')

        is_locked, _ = tracker.is_locked('dave')
        assert is_locked is True


class TestLoginAttemptTrackerRemainingAttempts:
    """残り試行回数取得テスト"""

    def test_remaining_attempts_no_failures(self, tracker):
        """失敗がない場合の残り試行回数"""
        remaining = tracker.get_remaining_attempts('newuser')
        assert remaining == 5

    def test_remaining_attempts_after_failures(self, tracker):
        """失敗後の残り試行回数"""
        tracker.record_failed_attempt('eve')
        tracker.record_failed_attempt('eve')

        remaining = tracker.get_remaining_attempts('eve')
        assert remaining == 3  # 5 - 2 = 3

    def test_remaining_attempts_at_limit(self, tracker):
        """限界到達時の残り試行回数"""
        for i in range(5):
            tracker.record_failed_attempt('frank')

        remaining = tracker.get_remaining_attempts('frank')
        assert remaining == 0

    def test_remaining_attempts_over_limit(self, tracker):
        """限界超過時の残り試行回数（負にならない）"""
        for i in range(10):
            tracker.record_failed_attempt('grace')

        remaining = tracker.get_remaining_attempts('grace')
        assert remaining == 0  # 負にならない


class TestLoginAttemptTrackerUnlock:
    """管理者による手動ロック解除テスト"""

    def test_unlock_locked_account(self, tracker):
        """ロックされたアカウントを解除"""
        # アカウントをロック
        for i in range(5):
            tracker.record_failed_attempt('hank')

        is_locked, _ = tracker.is_locked('hank')
        assert is_locked is True

        # 管理者による解除
        success = tracker.unlock_account('hank')
        assert success is True

        # ロック解除を確認
        is_locked, _ = tracker.is_locked('hank')
        assert is_locked is False

    def test_unlock_clears_attempts(self, tracker):
        """ロック解除は試行記録もクリア"""
        for i in range(5):
            tracker.record_failed_attempt('ivan')

        tracker.unlock_account('ivan')

        # 試行記録がクリアされる
        assert 'ivan' not in tracker._attempts or len(tracker._attempts['ivan']) == 0

    def test_unlock_non_locked_account(self, tracker):
        """ロックされていないアカウントの解除"""
        success = tracker.unlock_account('judy')
        assert success is False

    def test_unlock_allows_immediate_login(self, tracker):
        """解除後は即座にログイン可能"""
        # ロック
        for i in range(5):
            tracker.record_failed_attempt('kate')

        # 解除
        tracker.unlock_account('kate')

        # 再度試行可能
        remaining = tracker.get_remaining_attempts('kate')
        assert remaining == 5


class TestLoginAttemptTrackerLockedAccountsList:
    """ロック中アカウント一覧取得テスト"""

    def test_get_locked_accounts_empty(self, tracker):
        """ロックされたアカウントがない場合"""
        locked = tracker.get_locked_accounts()
        assert locked == []

    def test_get_locked_accounts_single(self, tracker):
        """1つのロックされたアカウント"""
        for i in range(5):
            tracker.record_failed_attempt('leo')

        tracker.is_locked('leo')  # ロックを確定

        locked = tracker.get_locked_accounts()
        assert len(locked) == 1
        assert locked[0]['username'] == 'leo'
        assert 'unlock_time' in locked[0]
        assert 'remaining_minutes' in locked[0]
        assert locked[0]['remaining_minutes'] > 0

    def test_get_locked_accounts_multiple(self, tracker):
        """複数のロックされたアカウント"""
        users = ['mike', 'nancy', 'oscar']
        for user in users:
            for i in range(5):
                tracker.record_failed_attempt(user)
            tracker.is_locked(user)

        locked = tracker.get_locked_accounts()
        assert len(locked) == 3

        locked_usernames = [account['username'] for account in locked]
        for user in users:
            assert user in locked_usernames


class TestLoginAttemptTrackerTimeWindow:
    """時間窓（タイムウィンドウ）テスト"""

    def test_old_attempts_are_ignored(self, tracker):
        """古い試行は無視される"""
        # テスト用に時間窓を短く設定
        original_window = tracker.ATTEMPT_WINDOW
        tracker.ATTEMPT_WINDOW = timedelta(seconds=1)

        # 失敗試行を記録
        tracker.record_failed_attempt('paul')
        assert len(tracker._attempts['paul']) == 1

        # 2秒待つ（時間窓外）
        time.sleep(2)

        # 新しい試行を記録（古い記録は削除される）
        tracker.record_failed_attempt('paul')

        # 時間窓内の記録のみ保持（1つだけ）
        assert len(tracker._attempts['paul']) == 1

        # 元に戻す
        tracker.ATTEMPT_WINDOW = original_window

    def test_recent_attempts_counted(self, tracker):
        """最近の試行はカウントされる"""
        # 短時間に5回失敗
        for i in range(5):
            tracker.record_failed_attempt('quinn')
            time.sleep(0.01)  # わずかな遅延

        is_locked, _ = tracker.is_locked('quinn')
        assert is_locked is True


class TestLoginAttemptTrackerAutoUnlock:
    """自動ロック解除テスト"""

    def test_auto_unlock_after_duration(self, tracker):
        """ロック期間経過後の自動解除"""
        # テスト用にロック期間を短く設定
        original_lockout = tracker.LOCKOUT_DURATION
        tracker.LOCKOUT_DURATION = timedelta(seconds=1)

        # アカウントをロック
        for i in range(5):
            tracker.record_failed_attempt('rachel')

        is_locked1, _ = tracker.is_locked('rachel')
        assert is_locked1 is True

        # ロック期間経過を待つ
        time.sleep(2)

        # 自動解除を確認
        is_locked2, _ = tracker.is_locked('rachel')
        assert is_locked2 is False

        # 元に戻す
        tracker.LOCKOUT_DURATION = original_lockout

    def test_auto_unlock_clears_lock_record(self, tracker):
        """自動解除時にロック記録がクリアされる"""
        original_lockout = tracker.LOCKOUT_DURATION
        tracker.LOCKOUT_DURATION = timedelta(seconds=1)

        for i in range(5):
            tracker.record_failed_attempt('sam')

        tracker.is_locked('sam')
        assert 'sam' in tracker._locked_accounts

        time.sleep(2)
        tracker.is_locked('sam')

        # ロック記録が削除される
        assert 'sam' not in tracker._locked_accounts

        tracker.LOCKOUT_DURATION = original_lockout


class TestLoginAttemptTrackerEdgeCases:
    """エッジケースと例外処理テスト"""

    def test_unicode_username(self, tracker):
        """Unicode文字を含むユーザー名"""
        tracker.record_failed_attempt('ユーザー太郎')
        tracker.record_failed_attempt('ユーザー太郎')

        assert len(tracker._attempts['ユーザー太郎']) == 2

    def test_special_characters_username(self, tracker):
        """特殊文字を含むユーザー名"""
        username = "user@example.com"
        tracker.record_failed_attempt(username)

        assert username in tracker._attempts

    def test_empty_username(self, tracker):
        """空のユーザー名（実運用ではありえないが）"""
        tracker.record_failed_attempt('')

        assert '' in tracker._attempts

    def test_very_long_username(self, tracker):
        """非常に長いユーザー名"""
        long_username = 'a' * 1000
        tracker.record_failed_attempt(long_username)

        assert long_username in tracker._attempts

    def test_concurrent_attempts_same_user(self, tracker):
        """同一ユーザーの同時試行"""
        # 実際の並行処理ではないが、短時間に複数記録
        for i in range(10):
            tracker.record_failed_attempt('tara')

        # 全て記録される
        assert len(tracker._attempts['tara']) == 10


class TestLoginAttemptTrackerIntegration:
    """統合テスト"""

    def test_full_workflow_lock_and_unlock(self, tracker):
        """完全なワークフロー：失敗 → ロック → 解除 → 成功"""
        username = 'workflow_user'

        # 1. 初期状態
        is_locked, _ = tracker.is_locked(username)
        assert is_locked is False
        assert tracker.get_remaining_attempts(username) == 5

        # 2. 3回失敗
        for i in range(3):
            tracker.record_failed_attempt(username)

        assert tracker.get_remaining_attempts(username) == 2

        # 3. さらに2回失敗してロック
        for i in range(2):
            tracker.record_failed_attempt(username)

        is_locked, unlock_time = tracker.is_locked(username)
        assert is_locked is True
        assert tracker.get_remaining_attempts(username) == 0

        # 4. 管理者による解除
        tracker.unlock_account(username)

        is_locked, _ = tracker.is_locked(username)
        assert is_locked is False
        assert tracker.get_remaining_attempts(username) == 5

        # 5. 成功ログイン（クリア）
        tracker.clear_attempts(username)
        assert username not in tracker._attempts

    def test_multiple_users_independent_tracking(self, tracker):
        """複数ユーザーの独立した追跡"""
        # Alice: 2回失敗
        tracker.record_failed_attempt('alice')
        tracker.record_failed_attempt('alice')

        # Bob: 5回失敗（ロック）
        for i in range(5):
            tracker.record_failed_attempt('bob')

        # Charlie: 成功（記録なし）

        # 各ユーザーの状態を確認
        assert tracker.get_remaining_attempts('alice') == 3
        assert not tracker.is_locked('alice')[0]

        assert tracker.get_remaining_attempts('bob') == 0
        assert tracker.is_locked('bob')[0]

        assert tracker.get_remaining_attempts('charlie') == 5
        assert not tracker.is_locked('charlie')[0]

    def test_security_scenario_brute_force_attack(self, tracker):
        """セキュリティシナリオ：ブルートフォース攻撃"""
        attacker = 'attacker'

        # 攻撃者が100回ログイン試行
        for i in range(100):
            tracker.record_failed_attempt(attacker)

        # 5回でロックされる
        is_locked, unlock_time = tracker.is_locked(attacker)
        assert is_locked is True

        # 残り試行回数は0
        assert tracker.get_remaining_attempts(attacker) == 0

        # ロック中のアカウント一覧に含まれる
        locked_accounts = tracker.get_locked_accounts()
        assert any(acc['username'] == attacker for acc in locked_accounts)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
