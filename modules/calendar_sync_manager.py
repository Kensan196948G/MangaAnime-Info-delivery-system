#!/usr/bin/env python3
"""
Googleカレンダー同期マネージャー
Phase 17: カレンダー統合実装

機能:
- 未同期リリースの取得
- Googleカレンダーへのバッチ同期
- 同期ステータス管理
- エラーハンドリングとリトライ
- 同期ログ記録
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

import logging
import sqlite3

logger = logging.getLogger(__name__)
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from modules.calendar_api import GoogleCalendarAPI, GoogleCalendarAPIError


class CalendarSyncManager:
    """
    カレンダー同期マネージャー

    主要機能:
    - 未同期リリースの一括同期
    - 失敗した同期のリトライ
    - 同期整合性検証
    - 統計情報取得

    Example:
        >>> manager = CalendarSyncManager()
        >>> result = manager.sync_unsynced_releases(limit=100)
        >>> print(f"成功: {result['success']}件")
    """

    def __init__(self, db_path: str = "db.sqlite3", calendar_id: str = "primary"):
        """
        初期化

        Args:
            db_path: データベースファイルパス
            calendar_id: カレンダーID
        """
        self.db_path = db_path
        self.calendar_id = calendar_id
        self.calendar_api = None
        self.stats = {
            "total_processed": 0,
            "success_count": 0,
            "failure_count": 0,
            "skipped_count": 0,
        }

    def _get_calendar_api(self) -> GoogleCalendarAPI:
        """カレンダーAPI取得（遅延初期化）"""
        if self.calendar_api is None:
            self.calendar_api = GoogleCalendarAPI(calendar_id=self.calendar_id)
        return self.calendar_api

    def _get_connection(self):
        """データベース接続取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_unsynced_releases(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        未同期リリース取得

        Args:
            limit: 取得件数制限

        Returns:
            未同期リリースのリスト
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                r.id,
                r.work_id,
                w.title,
                w.title_kana,
                r.release_type,
                r.number,
                r.platform,
                r.release_date,
                r.source_url
            FROM releases r
            JOIN works w ON r.work_id = w.id
            WHERE r.calendar_synced = 0
            ORDER BY r.release_date ASC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        releases = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return releases

    def sync_unsynced_releases(
        self, limit: Optional[int] = None, batch_size: int = 20
    ) -> Dict[str, Any]:
        """
        未同期リリースを同期

        Args:
            limit: 同期件数制限
            batch_size: バッチサイズ

        Returns:
            同期結果の辞書
        """
        logger.info("未同期リリースの同期を開始...")

        # 未同期リリース取得
        releases = self.get_unsynced_releases(limit)

        if not releases:
            logger.info("同期すべきリリースはありません")
            return {"success": 0, "failed": 0, "skipped": 0, "total": 0, "results": []}

        logger.info(f"{len(releases)}件のリリースを同期します")

        # バッチ処理
        results = []
        success_count = 0
        failed_count = 0
        skipped_count = 0

        for i in range(0, len(releases), batch_size):
            batch = releases[i : i + batch_size]
            logger.info(f"バッチ {i//batch_size + 1}: {len(batch)}件処理中...")

            for release in batch:
                try:
                    result = self._sync_single_release(release)
                    results.append(result)

                    if result["status"] == "success":
                        success_count += 1
                    elif result["status"] == "failed":
                        failed_count += 1
                    elif result["status"] == "skipped":
                        skipped_count += 1

                    # レート制限対策
                    time.sleep(1.0)

                except Exception as e:
                    logger.error(f"リリース{release['id']}の同期に失敗: {e}")
                    failed_count += 1
                    results.append(
                        {
                            "release_id": release["id"],
                            "status": "failed",
                            "error": str(e),
                        }
                    )

            # バッチ間待機
            if i + batch_size < len(releases):
                logger.info("次のバッチまで5秒待機...")
                time.sleep(5)

        # 統計更新
        self.stats["total_processed"] = len(releases)
        self.stats["success_count"] = success_count
        self.stats["failure_count"] = failed_count
        self.stats["skipped_count"] = skipped_count

        logger.info(
            f"同期完了: 成功{success_count}件、失敗{failed_count}件、スキップ{skipped_count}件"
        )

        return {
            "success": success_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "total": len(releases),
            "results": results,
        }

    def _sync_single_release(self, release: Dict[str, Any]) -> Dict[str, Any]:
        """
        単一リリースを同期

        Args:
            release: リリース情報

        Returns:
            同期結果
        """
        release_id = release["id"]
        title = release["title_kana"] or release["title"]
        release_type = "話" if release["release_type"] == "episode" else "巻"
        number = release["number"] or "不明"

        # タイトル不明の場合はスキップ
        if title.startswith("タイトル不明"):
            logger.debug(f"スキップ: {title}")
            return {
                "release_id": release_id,
                "status": "skipped",
                "reason": "title_unknown",
            }

        try:
            # カレンダーAPI取得
            calendar = self._get_calendar_api()

            # イベント作成
            event_title = f"{title} 第{number}{release_type}"
            description = f"""
プラットフォーム: {release['platform']}
配信日: {release['release_date']}
URL: {release.get('source_url', 'N/A')}
            """.strip()

            event = calendar.create_event(
                summary=event_title,
                start_time=datetime.fromisoformat(release["release_date"]),
                duration_minutes=60,
                description=description,
            )

            # データベース更新
            self._update_sync_status(release_id=release_id, event_id=event["id"], success=True)

            logger.info(f"✅ 同期成功: {event_title}")

            return {
                "release_id": release_id,
                "event_id": event["id"],
                "status": "success",
                "event_title": event_title,
            }

        except GoogleCalendarAPIError as e:
            logger.error(f"❌ カレンダーAPI エラー: {e}")
            self._log_sync_error(release_id, str(e))

            return {"release_id": release_id, "status": "failed", "error": str(e)}

        except Exception as e:
            logger.error(f"❌ 予期しないエラー: {e}")
            self._log_sync_error(release_id, str(e))

            return {"release_id": release_id, "status": "failed", "error": str(e)}

    def _update_sync_status(self, release_id: int, event_id: str, success: bool = True):
        """同期ステータス更新"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if success:
            cursor.execute(
                """
                UPDATE releases
                SET calendar_synced = 1,
                    calendar_event_id = ?,
                    calendar_synced_at = ?
                WHERE id = ?
            """,
                (event_id, datetime.now(), release_id),
            )

            # calendar_events テーブルにも記録
            cursor.execute(
                """
                INSERT OR IGNORE INTO calendar_events
                (work_id, release_id, event_id, created_at)
                SELECT work_id, ?, ?, ?
                FROM releases
                WHERE id = ?
            """,
                (release_id, event_id, datetime.now(), release_id),
            )

        conn.commit()
        conn.close()

    def _log_sync_error(self, release_id: int, error_message: str):
        """同期エラーログ記録"""
        # 将来的に calendar_sync_log テーブルに記録
        logger.error(f"Release {release_id}: {error_message}")

    def get_sync_stats(self) -> Dict[str, Any]:
        """
        同期統計取得

        Returns:
            統計情報の辞書
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN calendar_synced = 1 THEN 1 ELSE 0 END) as synced,
                SUM(CASE WHEN calendar_synced = 0 THEN 1 ELSE 0 END) as unsynced,
                ROUND(SUM(CASE WHEN calendar_synced = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as sync_rate
            FROM releases
        """)

        stats = dict(cursor.fetchone())
        conn.close()

        return stats

    def retry_failed_syncs(self, max_retries: int = 3) -> Dict[str, Any]:
        """
        失敗した同期のリトライ

        Args:
            max_retries: 最大リトライ回数

        Returns:
            リトライ結果
        """
        # 将来的に calendar_sync_log から失敗レコードを取得してリトライ
        logger.info("失敗した同期のリトライ機能は未実装です")
        return {"message": "Not implemented yet"}

    def validate_sync_integrity(self) -> Dict[str, Any]:
        """
        同期整合性検証

        Returns:
            検証結果
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # calendar_synced = 1 だが calendar_event_id が NULL のレコード
        cursor.execute("""
            SELECT COUNT(*) as inconsistent
            FROM releases
            WHERE calendar_synced = 1 AND calendar_event_id IS NULL
        """)

        inconsistent = cursor.fetchone()["inconsistent"]
        conn.close()

        return {"inconsistent_records": inconsistent, "is_valid": inconsistent == 0}


# テスト実行用
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("🧪 CalendarSyncManager テスト")
    print("=" * 70)

    manager = CalendarSyncManager()

    # 統計取得
    print("\n【同期統計】")
    stats = manager.get_sync_stats()
    print(f"  総リリース数: {stats['total']}")
    print(f"  同期済み: {stats['synced']}件（{stats['sync_rate']}%）")
    print(f"  未同期: {stats['unsynced']}件")

    # 未同期リリース確認
    print("\n【未同期リリース】")
    unsynced = manager.get_unsynced_releases(limit=5)
    print(f"  件数: {len(unsynced)}件（最初の5件表示）")

    for i, release in enumerate(unsynced, 1):
        title = release["title_kana"] or release["title"]
        print(f"  {i}. {title} - {release['release_date']}")

    print("\n" + "=" * 70)
    print("✅ テスト完了")
    print("=" * 70)
