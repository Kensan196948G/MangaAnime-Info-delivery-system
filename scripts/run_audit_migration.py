#!/usr/bin/env python3
"""
監査ログマイグレーション実行スクリプト

migrations/006_audit_logs.sql を実行して監査ログテーブルを作成します。
"""

import sqlite3
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_migration():
    """マイグレーションを実行"""
    db_path = PROJECT_ROOT / "db.sqlite3"
    migration_path = PROJECT_ROOT / "migrations" / "006_audit_logs.sql"

    logger.info("=" * 60)
    logger.info("監査ログマイグレーション実行")
    logger.info("=" * 60)
    logger.info(f"データベース: {db_path}")
    logger.info(f"マイグレーション: {migration_path}")
    logger.info()

    # マイグレーションファイルの存在確認
    if not migration_path.exists():
        logger.info(f"❌ エラー: マイグレーションファイルが見つかりません")
        logger.info(f"   {migration_path}")
        sys.exit(1)

    # SQLファイルを読み込み
    with open(migration_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    try:
        # データベース接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        logger.info("📊 マイグレーション実行中...")

        # スクリプトを実行
        cursor.executescript(sql_script)

        conn.commit()

        # 確認
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='audit_logs'
        """)

        if cursor.fetchone():
            logger.info("✅ audit_logs テーブルが作成されました")

            # レコード数確認
            cursor.execute("SELECT COUNT(*) FROM audit_logs")
            count = cursor.fetchone()[0]
            logger.info(f"   サンプルデータ: {count} 件")

            # インデックス確認
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND tbl_name='audit_logs'
            """)
            indexes = cursor.fetchall()
            logger.info(f"   インデックス: {len(indexes)} 個")
            for idx in indexes:
                logger.info(f"     - {idx[0]}")

            # ビュー確認
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='view' AND name LIKE 'audit_%'
            """)
            views = cursor.fetchall()
            logger.info(f"   ビュー: {len(views)} 個")
            for view in views:
                logger.info(f"     - {view[0]}")

        else:
            logger.info("❌ テーブル作成に失敗しました")
            sys.exit(1)

        conn.close()

        logger.info()
        logger.info("=" * 60)
        logger.info("✅ マイグレーション完了")
        logger.info("=" * 60)

    except sqlite3.Error as e:
        logger.info(f"❌ データベースエラー: {e}")
        sys.exit(1)
    except Exception as e:
        logger.info(f"❌ 予期しないエラー: {e}")
        sys.exit(1)


def verify_audit_log_system():
    """監査ログシステムの動作確認"""
    logger.info()
    logger.info("=" * 60)
    logger.info("監査ログシステム動作確認")
    logger.info("=" * 60)

    try:
        from modules.audit_log import audit_logger, AuditEventType

        # テストログ記録
        logger.info("📝 テストログを記録中...")
        log_id = audit_logger.log_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            user_id="test_user",
            username="Test User",
            ip_address="127.0.0.1",
            user_agent="Migration Script",
            details={"test": True, "script": "run_audit_migration.py"},
            success=True,
            severity="info"
        )

        if log_id:
            logger.info(f"✅ ログID {log_id} が記録されました")

            # ログ取得テスト
            logs = audit_logger.get_logs(limit=1)
            if logs:
                logger.info(f"✅ ログ取得成功: {logs[0].event_type.value}")

                # 統計情報テスト
                stats = audit_logger.get_statistics()
                logger.info(f"✅ 統計情報取得成功: 合計 {stats['total_events']} 件")
            else:
                logger.info("⚠️  ログ取得に失敗しました")
        else:
            logger.info("❌ ログ記録に失敗しました")

        logger.info()
        logger.info("=" * 60)
        logger.info("✅ 動作確認完了")
        logger.info("=" * 60)

    except ImportError as e:
        logger.info(f"❌ モジュールのインポートエラー: {e}")
        sys.exit(1)
    except Exception as e:
        logger.info(f"❌ 動作確認エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def show_usage_example():
    """使用例を表示"""
    logger.info()
    logger.info("=" * 60)
    logger.info("使用例")
    logger.info("=" * 60)
    logger.info()

    example_code = '''
# 基本的な使い方
from modules.audit_log import audit_logger, AuditEventType
import logging

# イベント記録
audit_logger.log_event(

logger = logging.getLogger(__name__)

    event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
    user_id="user123",
    username="testuser",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0",
    details={"method": "password"},
    success=True
)

# ログ取得
logs = audit_logger.get_logs(limit=10)
for log in logs:
    logger.info(f"{log.timestamp} - {log.event_type.value} - {log.username}")

# 統計情報
stats = audit_logger.get_statistics()
logger.info(f"Total events: {stats['total_events']}")
logger.info(f"Success'success_rate']:.1f}%")
'''

    logger.info(example_code)
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        run_migration()
        verify_audit_log_system()
        show_usage_example()

        logger.info()
        logger.info("🎉 すべての処理が正常に完了しました！")
        logger.info()
        logger.info("次のステップ:")
        logger.info("  1. Web アプリケーションで認証機能を試す")
        logger.info("  2. /api/auth/audit/logs で監査ログを確認")
        logger.info("  3. /api/auth/audit/statistics で統計情報を確認")
        logger.info()
        logger.info("詳細は docs/AUDIT_LOG_SYSTEM.md を参照してください。")

    except KeyboardInterrupt:
        logger.info("\n⚠️  処理が中断されました")
        sys.exit(1)
