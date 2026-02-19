"""
通知履歴管理モジュール

通知の実行履歴を記録・管理し、ダッシュボードやAPIで参照可能にする
"""

import json
import logging
import sqlite3

logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class NotificationHistoryManager:
    """通知履歴管理クラス"""

    def __init__(self, db_path: str = "db.sqlite3"):
        """
        初期化

        Args:
            db_path: データベースファイルパス
        """
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self):
        """notification_historyテーブルを作成（既存スキーマに対応）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 既存テーブルの構造を確認
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='notification_history'"
            )
            table_exists = cursor.fetchone() is not None

            if table_exists:
                # 既存テーブルのカラムを確認
                cursor.execute("PRAGMA table_info(notification_history)")
                columns = {col[1] for col in cursor.fetchall()}

                # 必要なカラムを追加（存在しない場合）
                if "details" not in columns:
                    cursor.execute("ALTER TABLE notification_history ADD COLUMN details TEXT")
                    logger.info("details カラムを追加しました")

                if "metadata" not in columns:
                    cursor.execute("ALTER TABLE notification_history ADD COLUMN metadata TEXT")
                    logger.info("metadata カラムを追加しました")

                logger.info("notification_history テーブルを確認しました（既存）")
            else:
                # 新規テーブルを作成（既存スキーマ互換）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notification_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        notification_type TEXT NOT NULL,
                        executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        success INTEGER DEFAULT 1,
                        error_message TEXT,
                        releases_count INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        details TEXT,
                        metadata TEXT
                    )
                """)
                logger.info("notification_history テーブルを作成しました")

            # インデックスを作成
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON notification_history(created_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_type_success
                ON notification_history(notification_type, success)
            """)

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"テーブル作成エラー: {e}")
            raise

    def record_notification(
        self,
        notification_type: str,
        status: str = "success",
        details: str = "",
        count: int = 0,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        通知履歴を記録（既存スキーマ互換）

        Args:
            notification_type: 通知タイプ (email, calendar, etc.)
            status: ステータス (success, failed, partial) - 既存スキーマではsuccess (1/0)
            details: 詳細情報
            count: 通知件数 - 既存スキーマではreleases_count
            error_message: エラーメッセージ（失敗時）
            metadata: 追加メタデータ

        Returns:
            レコードID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # status文字列をsuccess整数値に変換
            success_value = 1 if status in ["success", "partial"] else 0

            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute(
                """
                INSERT INTO notification_history
                (notification_type, success, details, releases_count, error_message, metadata, executed_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (
                    notification_type,
                    success_value,
                    details,
                    count,
                    error_message,
                    metadata_json,
                ),
            )

            record_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(
                f"通知履歴記録: type={notification_type}, " f"status={status}, count={count}"
            )

            return record_id

        except Exception as e:
            logger.error(f"履歴記録エラー: {e}")
            raise

    def get_recent_history(
        self,
        limit: int = 100,
        notification_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        最近の通知履歴を取得（既存スキーマ互換）

        Args:
            limit: 取得件数
            notification_type: 通知タイプでフィルタ (optional)
            status: ステータスでフィルタ (optional) - success/failed

        Returns:
            履歴レコードのリスト
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM notification_history WHERE 1=1"
            params = []

            if notification_type:
                query += " AND notification_type = ?"
                params.append(notification_type)

            if status:
                # status文字列をsuccess整数値に変換
                success_value = 1 if status == "success" else 0
                query += " AND success = ?"
                params.append(success_value)

            query += " ORDER BY executed_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            history = []
            for row in rows:
                record = dict(row)
                # success整数値をstatus文字列に変換
                record["status"] = "success" if record.get("success", 0) == 1 else "failed"
                record["count"] = record.get("releases_count", 0)
                record["timestamp"] = record.get("executed_at") or record.get("created_at")

                # メタデータをJSONから復元
                if record.get("metadata"):
                    try:
                        record["metadata"] = json.loads(record["metadata"])
                    except:
                        pass
                history.append(record)

            conn.close()
            return history

        except Exception as e:
            logger.error(f"履歴取得エラー: {e}")
            return []

    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        統計情報を取得（既存スキーマ互換）

        Args:
            days: 集計期間（日数）

        Returns:
            統計情報
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

            # 総通知数（releases_count）
            cursor.execute(
                """
                SELECT SUM(releases_count) FROM notification_history
                WHERE executed_at >= ?
            """,
                (cutoff_date,),
            )
            total_notifications = cursor.fetchone()[0] or 0

            # 成功率
            cursor.execute(
                """
                SELECT
                    SUM(CASE WHEN success = 1 THEN releases_count ELSE 0 END) as success_count,
                    SUM(releases_count) as total_count
                FROM notification_history
                WHERE executed_at >= ?
            """,
                (cutoff_date,),
            )
            row = cursor.fetchone()
            success_count = row[0] or 0
            total_count = row[1] or 1  # ゼロ除算回避
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0

            # タイプ別集計
            cursor.execute(
                """
                SELECT notification_type, COUNT(*), SUM(releases_count)
                FROM notification_history
                WHERE executed_at >= ?
                GROUP BY notification_type
            """,
                (cutoff_date,),
            )
            type_stats = {}
            for row in cursor.fetchall():
                type_stats[row[0]] = {
                    "executions": row[1],
                    "total_notifications": row[2] or 0,
                }

            # 最終実行時刻
            cursor.execute("""
                SELECT executed_at FROM notification_history
                ORDER BY executed_at DESC LIMIT 1
            """)
            last_execution = cursor.fetchone()
            last_execution = last_execution[0] if last_execution else None

            conn.close()

            return {
                "total_notifications": total_notifications,
                "success_rate": round(success_rate, 2),
                "type_statistics": type_stats,
                "last_execution": last_execution,
                "period_days": days,
            }

        except Exception as e:
            logger.error(f"統計取得エラー: {e}")
            return {
                "total_notifications": 0,
                "success_rate": 0.0,
                "type_statistics": {},
                "last_execution": None,
                "period_days": days,
            }

    def calculate_next_execution(self, schedule_hour: int = 8, schedule_minute: int = 0) -> str:
        """
        次回実行時刻を計算

        Args:
            schedule_hour: 実行時刻（時）
            schedule_minute: 実行時刻（分）

        Returns:
            次回実行時刻（ISO形式）
        """
        now = datetime.now()
        next_run = now.replace(hour=schedule_hour, minute=schedule_minute, second=0, microsecond=0)

        # 今日の実行時刻を過ぎていたら翌日に設定
        if next_run <= now:
            next_run += timedelta(days=1)

        return next_run.strftime("%Y-%m-%d %H:%M:%S")

    def get_error_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        エラー履歴を取得

        Args:
            limit: 取得件数

        Returns:
            エラー履歴のリスト
        """
        return self.get_recent_history(limit=limit, status="failed")

    def cleanup_old_records(self, days: int = 90) -> int:
        """
        古い履歴レコードを削除

        Args:
            days: 保持期間（日数）

        Returns:
            削除件数
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                """
                DELETE FROM notification_history
                WHERE executed_at < ?
            """,
                (cutoff_date,),
            )

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"{deleted_count}件の古い履歴を削除しました")
            return deleted_count

        except Exception as e:
            logger.error(f"履歴削除エラー: {e}")
            return 0

    def export_history(self, output_path: str, days: int = 30) -> bool:
        """
        履歴をJSONファイルにエクスポート

        Args:
            output_path: 出力ファイルパス
            days: エクスポート期間（日数）

        Returns:
            成功したかどうか
        """
        try:
            history = self.get_recent_history(limit=10000)
            cutoff_date = datetime.now() - timedelta(days=days)

            filtered_history = []
            for record in history:
                # executed_atまたはcreated_atを使用
                timestamp_str = (
                    record.get("timestamp") or record.get("executed_at") or record.get("created_at")
                )
                if timestamp_str:
                    try:
                        record_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if record_date >= cutoff_date:
                            filtered_history.append(record)
                    except:
                        # パース失敗時もレコードを含める
                        filtered_history.append(record)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(filtered_history, f, ensure_ascii=False, indent=2)

            logger.info(f"履歴を {output_path} にエクスポートしました")
            return True

        except Exception as e:
            logger.error(f"履歴エクスポートエラー: {e}")
            return False


# グローバルインスタンス
_history_manager = None


def get_history_manager(db_path: str = "db.sqlite3") -> NotificationHistoryManager:
    """
    履歴マネージャーのシングルトンインスタンスを取得

    Args:
        db_path: データベースパス

    Returns:
        NotificationHistoryManager インスタンス
    """
    global _history_manager
    if _history_manager is None:
        _history_manager = NotificationHistoryManager(db_path)
    return _history_manager


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)

    manager = NotificationHistoryManager("test_history.db")

    # テストデータ挿入
    manager.record_notification(
        notification_type="email", status="success", details="5件のメール送信", count=5
    )

    manager.record_notification(
        notification_type="calendar",
        status="success",
        details="3件のイベント登録",
        count=3,
        metadata={"platform": "Google Calendar"},
    )

    manager.record_notification(
        notification_type="email",
        status="failed",
        details="送信失敗",
        count=0,
        error_message="SMTP authentication error",
    )

    # 履歴取得
    history = manager.get_recent_history(limit=10)
    logger.info(f"\n最近の履歴 ({len(history)}件):")
    for record in history:
        logger.info(
            f"  - {record['created_at']}: {record['notification_type']} / {record['status']}"
        )

    # 統計情報
    stats = manager.get_statistics(days=7)
    logger.info(f"\n統計情報:")
    logger.info(f"  総通知数: {stats['total_notifications']}")
    logger.info(f"  成功率: {stats['success_rate']}%")
    logger.info(f"  最終実行: {stats['last_execution']}")

    # 次回実行時刻
    next_run = manager.calculate_next_execution()
    logger.info(f"  次回実行: {next_run}")
