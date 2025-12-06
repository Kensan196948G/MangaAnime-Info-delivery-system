"""
監査ログシステムの簡易テスト
"""
import pytest
from datetime import datetime
from modules.audit_log import (
    AuditLogger,
    AuditEventType,
    AuditLog,
    audit_logger
)


class TestAuditLogger:
    """AuditLoggerの基本テスト"""

    def test_logger_initialization(self):
        """ロガーの初期化"""
        logger = AuditLogger()
        assert logger is not None
        assert hasattr(logger, '_logs')

    def test_log_event_basic(self):
        """基本的なイベント記録"""
        logger = AuditLogger()

        logger.log_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            user_id="user123",
            username="testuser",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            details={"method": "password"},
            success=True
        )

        logs = logger.get_logs(limit=1)
        assert len(logs) >= 1
        assert logs[0].event_type == AuditEventType.AUTH_LOGIN_SUCCESS

    def test_get_statistics(self):
        """統計情報取得"""
        logger = AuditLogger()

        logger.log_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            user_id="user1",
            username="user1",
            ip_address="192.168.1.1",
            user_agent="Test",
            success=True
        )

        logger.log_event(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            username="user2",
            ip_address="192.168.1.2",
            user_agent="Test",
            success=False
        )

        stats = audit_logger.get_statistics()
        assert 'total_logs' in stats
        assert 'success_count' in stats
        assert 'failure_count' in stats
        assert stats['success_rate'] >= 0

    def test_filter_by_event_type(self):
        """イベントタイプでフィルタ"""
        logger = AuditLogger()

        logger.log_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            username="user1",
            ip_address="192.168.1.1",
            user_agent="Test"
        )

        logger.log_event(
            event_type=AuditEventType.USER_CREATE,
            username="admin",
            ip_address="192.168.1.2",
            user_agent="Test"
        )

        login_logs = logger.get_logs(event_type=AuditEventType.AUTH_LOGIN_SUCCESS)
        assert all(log.event_type == AuditEventType.AUTH_LOGIN_SUCCESS for log in login_logs)

    def test_filter_by_user(self):
        """ユーザーでフィルタ"""
        logger = AuditLogger()

        logger.log_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            user_id="user1",
            username="user1",
            ip_address="192.168.1.1",
            user_agent="Test"
        )

        logger.log_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            user_id="user2",
            username="user2",
            ip_address="192.168.1.2",
            user_agent="Test"
        )

        user1_logs = logger.get_logs(user_id="user1")
        assert all(log.user_id == "user1" for log in user1_logs)
