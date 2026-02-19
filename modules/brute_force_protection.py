"""
ブルートフォース攻撃対策モジュール
ログイン失敗回数の追跡とアカウントロック機能
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class LoginAttemptTracker:
    """ログイン試行追跡クラス"""

    # 設定
    MAX_ATTEMPTS = 5  # 最大試行回数
    ATTEMPT_WINDOW = timedelta(minutes=15)  # 試行回数カウント期間
    LOCKOUT_DURATION = timedelta(minutes=30)  # ロック期間

    def __init__(self):
        self._attempts: Dict[str, List[datetime]] = defaultdict(list)
        self._locked_accounts: Dict[str, datetime] = {}

    def record_failed_attempt(self, username: str):
        """失敗したログイン試行を記録"""
        self._attempts[username].append(datetime.now())

        # 古い記録を削除（ATTEMPT_WINDOW以内のみ保持）
        cutoff_time = datetime.now() - self.ATTEMPT_WINDOW
        self._attempts[username] = [
            attempt for attempt in self._attempts[username] if attempt > cutoff_time
        ]

        recent_attempts = len(self._attempts[username])
        logger.warning(f"ログイン失敗記録: '{username}' ({recent_attempts}/{self.MAX_ATTEMPTS})")

    def is_locked(self, username: str) -> Tuple[bool, Optional[datetime]]:
        """アカウントがロックされているか確認"""
        # ロック確認
        if username in self._locked_accounts:
            unlock_time = self._locked_accounts[username]
            if datetime.now() < unlock_time:
                remaining = (unlock_time - datetime.now()).total_seconds() / 60
                logger.info(f"ロック中のアカウント: '{username}' (残り {remaining:.1f}分)")
                return True, unlock_time
            else:
                # ロック期限切れ - クリア
                del self._locked_accounts[username]
                self._attempts[username] = []
                logger.info(f"ロック解除: '{username}'")

        # 失敗回数チェック
        cutoff_time = datetime.now() - self.ATTEMPT_WINDOW
        recent_attempts = [
            attempt for attempt in self._attempts.get(username, []) if attempt > cutoff_time
        ]

        if len(recent_attempts) >= self.MAX_ATTEMPTS:
            # ロック実施
            unlock_time = datetime.now() + self.LOCKOUT_DURATION
            self._locked_accounts[username] = unlock_time
            logger.warning(
                f"アカウントロック実施: '{username}' "
                f"(失敗回数: {len(recent_attempts)}, ロック期間: {self.LOCKOUT_DURATION.total_seconds()/60}分)"
            )
            return True, unlock_time

        return False, None

    def clear_attempts(self, username: str):
        """ログイン成功時に試行回数をクリア"""
        if username in self._attempts:
            del self._attempts[username]
        logger.info(f"ログイン試行記録クリア: '{username}'")

    def get_remaining_attempts(self, username: str) -> int:
        """残り試行回数を取得"""
        cutoff_time = datetime.now() - self.ATTEMPT_WINDOW
        recent_attempts = [
            attempt for attempt in self._attempts.get(username, []) if attempt > cutoff_time
        ]
        return max(0, self.MAX_ATTEMPTS - len(recent_attempts))

    def unlock_account(self, username: str) -> bool:
        """管理者によるアカウントロック解除"""
        if username in self._locked_accounts:
            del self._locked_accounts[username]
            self._attempts[username] = []
            logger.info(f"管理者によるロック解除: '{username}'")
            return True
        # 正式ロック前でも試行記録がある場合はクリアする
        if username in self._attempts and len(self._attempts[username]) > 0:
            self._attempts[username] = []
            logger.info(f"試行記録クリア（未ロック）: '{username}'")
            return True
        return False

    def get_locked_accounts(self) -> List[Dict[str, Any]]:
        """ロック中のアカウント一覧を取得"""
        locked = []
        for username, unlock_time in self._locked_accounts.items():
            if datetime.now() < unlock_time:
                locked.append(
                    {
                        "username": username,
                        "unlock_time": unlock_time,
                        "remaining_minutes": (unlock_time - datetime.now()).total_seconds() / 60,
                    }
                )
        return locked


# グローバルインスタンス
attempt_tracker = LoginAttemptTracker()
