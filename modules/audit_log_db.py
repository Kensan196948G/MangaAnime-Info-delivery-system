"""
監査ログDB永続化版 - SQLiteベース
"""

import json
import logging
import os

logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from modules.audit_log import AuditEventType, AuditLog


class AuditLoggerDB:
    """SQLiteベースの監査ログ管理クラス"""

    def __init__(self, db_path: str = "db.sqlite3"):
        self.db_path = db_path
        logger.info(f"AuditLoggerDB初期化: {db_path}")

    @contextmanager
    def get_connection(self):
        """データベース接続のコンテキストマネージャ"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"監査ログDBエラー: {e}")
            raise
        finally:
            conn.close()

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
        """監査イベントをDBに記録"""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs 
                (event_type, user_id, username, ip_address, user_agent, details, success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_type.value,
                    user_id,
                    username,
                    ip_address,
                    user_agent,
                    json.dumps(details) if details else "{}",
                    1 if success else 0,
                ),
            )

        log_level = logging.INFO if success else logging.WARNING
        logger.log(
            log_level,
            f"監査ログ記録: {event_type.value} - ユーザー={username or 'anonymous'} - "
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
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if success is not None:
            query += " AND success = ?"
            params.append(1 if success else 0)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            logs = []
            for row in rows:
                # event_typeを文字列からEnumに変換
                try:
                    event_enum = AuditEventType(row["event_type"])
                except ValueError:
                    # 未知のイベントタイプの場合はスキップ
                    continue

                logs.append(
                    AuditLog(
                        id=row["id"],
                        event_type=event_enum,
                        user_id=row["user_id"],
                        username=row["username"],
                        ip_address=row["ip_address"],
                        user_agent=row["user_agent"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        details=json.loads(row["details"]) if row["details"] else {},
                        success=bool(row["success"]),
                    )
                )

            return logs

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        with self.get_connection() as conn:
            # 総数・成功数・失敗数
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_logs,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failure_count
                FROM audit_logs
                """)
            row = cursor.fetchone()

            total_logs = row["total_logs"]
            success_count = row["success_count"] or 0
            failure_count = row["failure_count"] or 0
            success_rate = (success_count / total_logs * 100) if total_logs > 0 else 0

            # イベントタイプ別集計
            cursor = conn.execute("""
                SELECT event_type, COUNT(*) as count
                FROM audit_logs
                GROUP BY event_type
                ORDER BY count DESC
                """)
            event_counts = {row["event_type"]: row["count"] for row in cursor.fetchall()}

            return {
                "total_logs": total_logs,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": success_rate,
                "event_type_counts": event_counts,
            }

    def get_recent_failures(
        self, username: Optional[str] = None, limit: int = 10
    ) -> List[AuditLog]:
        """最近の失敗ログを取得"""
        query = "SELECT * FROM audit_logs WHERE success = 0"
        params = []

        if username:
            query += " AND username = ?"
            params.append(username)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            logs = []
            for row in rows:
                try:
                    event_enum = AuditEventType(row["event_type"])
                    logs.append(
                        AuditLog(
                            id=row["id"],
                            event_type=event_enum,
                            user_id=row["user_id"],
                            username=row["username"],
                            ip_address=row["ip_address"],
                            user_agent=row["user_agent"],
                            timestamp=datetime.fromisoformat(row["timestamp"]),
                            details=(json.loads(row["details"]) if row["details"] else {}),
                            success=False,
                        )
                    )
                except ValueError:
                    continue

            return logs


# グローバルインスタンス（DB版優先）
USE_DB_AUDIT_LOG = os.getenv("USE_DB_AUDIT_LOG", "true").lower() == "true"

if USE_DB_AUDIT_LOG:
    try:
        audit_logger = AuditLoggerDB()
        logger.info("AuditLoggerDB（DB版）を使用します")
    except Exception as e:
        logger.warning(f"AuditLoggerDB初期化失敗: {e}。メモリ版を使用します")
        from modules.audit_log import AuditLogger

        audit_logger = AuditLogger()
else:
    from modules.audit_log import AuditLogger

    audit_logger = AuditLogger()
    logger.info("AuditLogger（メモリ版）を使用します")
