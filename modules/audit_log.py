"""
監査ログモジュール - セキュリティイベントの記録と管理
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AuditEventType(Enum):
    """監査イベントタイプ"""

    # 認証イベント
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_SESSION_REFRESH = "auth.session.refresh"
    AUTH_PASSWORD_RESET = "auth.password.reset"
    AUTH_PASSWORD_CHANGE = "auth.password.change"

    # ユーザー管理イベント
    USER_CREATE = "user.create"
    USER_DELETE = "user.delete"
    USER_UPDATE = "user.update"
    USER_PERMISSION_CHANGE = "user.permission.change"

    # 設定変更イベント
    CONFIG_UPDATE = "config.update"
    SOURCE_TOGGLE = "source.toggle"
    RSS_FEED_TOGGLE = "rss.feed.toggle"

    # データ操作イベント
    DATA_DELETE = "data.delete"
    DATA_COLLECTION = "data.collection"

    # APIイベント
    API_CALL = "api.call"
    API_KEY_GENERATE = "api.key.generate"
    API_KEY_REVOKE = "api.key.revoke"


@dataclass
class AuditLog:
    """監査ログエントリ"""

    id: int
    event_type: AuditEventType
    user_id: Optional[str]
    username: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data


class AuditLogger:
    """監査ログ管理クラス"""

    def __init__(self, max_logs: int = 10000):
        self._logs: List[AuditLog] = []
        self._log_id = 0
        self._max_logs = max_logs

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
    ):
        """監査イベントを記録"""
        self._log_id += 1

        log_entry = AuditLog(
            id=self._log_id,
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(),
            details=details or {},
            success=success,
        )

        self._logs.append(log_entry)

        # ログ数制限（メモリ使用量管理）
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs :]

        # ロギング
        log_level = logging.INFO if success else logging.WARNING
        logger.log(
            log_level,
            f"監査ログ: {event_type.value} - ユーザー={username or 'anonymous'} - "
            f"IP={ip_address} - 成功={success}",
        )

    def get_logs(
        self,
        limit: int = 100,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        success: Optional[bool] = None,
    ) -> List[AuditLog]:
        """ログを取得（フィルタ可能）"""
        filtered_logs = self._logs

        # フィルタ適用
        if event_type:
            filtered_logs = [log for log in filtered_logs if log.event_type == event_type]

        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]

        if success is not None:
            filtered_logs = [log for log in filtered_logs if log.success == success]

        # 最新順でlimit件を返す
        return sorted(filtered_logs, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_recent_failures(
        self, username: Optional[str] = None, limit: int = 10
    ) -> List[AuditLog]:
        """最近の失敗ログを取得"""
        failure_logs = [log for log in self._logs if not log.success]

        if username:
            failure_logs = [log for log in failure_logs if log.username == username]

        return sorted(failure_logs, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        total_logs = len(self._logs)
        success_logs = sum(1 for log in self._logs if log.success)
        failure_logs = total_logs - success_logs

        # イベントタイプ別集計
        event_counts = defaultdict(int)
        for log in self._logs:
            event_counts[log.event_type.value] += 1

        return {
            "total_logs": total_logs,
            "success_count": success_logs,
            "failure_count": failure_logs,
            "success_rate": (success_logs / total_logs * 100) if total_logs > 0 else 0,
            "event_type_counts": dict(event_counts),
        }


# グローバル監査ログインスタンス
audit_logger = AuditLogger()
