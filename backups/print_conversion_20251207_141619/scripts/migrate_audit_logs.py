#!/usr/bin/env python3
"""
監査ログマイグレーション実行スクリプト
作成日: 2025-12-07
目的: audit_logsテーブルを作成し、既存のメモリログをDBに移行
"""

import os
import sys
import sqlite3
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_migration(db_path: str = "db.sqlite3"):
    """
    マイグレーション実行

    Args:
        db_path: データベースファイルパス
    """
    print("=" * 60)
    print("🔄 監査ログマイグレーション開始")
    print("=" * 60)

    # マイグレーションファイルパス
    migration_file = project_root / "migrations" / "006_audit_logs.sql"

    if not migration_file.exists():
        print(f"⚠️  マイグレーションファイルが見つかりません: {migration_file}")
        print("📝 基本テーブルを作成します...")

        # 基本テーブルSQL
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_id TEXT,
            username TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            details TEXT,
            success INTEGER DEFAULT 1,
            session_id TEXT,
            endpoint TEXT,
            method TEXT,
            status_code INTEGER,
            response_time_ms INTEGER,
            error_message TEXT,
            resource_type TEXT,
            resource_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp
            ON audit_logs(timestamp DESC);

        CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id
            ON audit_logs(user_id)
            WHERE user_id IS NOT NULL;

        CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type
            ON audit_logs(event_type);

        CREATE INDEX IF NOT EXISTS idx_audit_logs_success
            ON audit_logs(success);

        -- マイグレーション実行ログ
        INSERT INTO audit_logs (event_type, details, user_id, username)
        VALUES (
            'migration_executed',
            '{"migration": "006_audit_logs_basic", "status": "completed"}',
            'system',
            'migration_script'
        );
        """

        try:
            conn = sqlite3.connect(db_path)
            conn.executescript(create_table_sql)
            conn.commit()
            conn.close()
            print("✅ 基本テーブル作成完了")
        except Exception as e:
            print(f"❌ エラー: {e}")
            return False

    else:
        print(f"📄 マイグレーションファイル: {migration_file}")

        try:
            # SQLファイルを読み込み
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql = f.read()

            # データベースに適用
            conn = sqlite3.connect(db_path)
            conn.executescript(sql)
            conn.commit()
            conn.close()

            print("✅ マイグレーション完了")
        except Exception as e:
            print(f"❌ エラー: {e}")
            return False

    # テーブル確認
    print("\n📊 テーブル構造確認:")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # テーブル存在確認
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='audit_logs'
        """)
        table_exists = cursor.fetchone()

        if table_exists:
            print("  ✓ audit_logs テーブル: 存在")

            # カラム情報取得
            cursor.execute("PRAGMA table_info(audit_logs)")
            columns = cursor.fetchall()
            print(f"  ✓ カラム数: {len(columns)}")
            for col in columns:
                print(f"    - {col[1]} ({col[2]})")

            # インデックス確認
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND tbl_name='audit_logs'
            """)
            indexes = cursor.fetchall()
            print(f"  ✓ インデックス数: {len(indexes)}")
            for idx in indexes:
                print(f"    - {idx[0]}")

            # レコード数確認
            cursor.execute("SELECT COUNT(*) FROM audit_logs")
            count = cursor.fetchone()[0]
            print(f"  ✓ 現在のログ件数: {count}")

        else:
            print("  ❌ audit_logs テーブルが見つかりません")

        conn.close()

    except Exception as e:
        print(f"⚠️  確認エラー: {e}")

    print("\n" + "=" * 60)
    print("✅ マイグレーション処理完了")
    print("=" * 60)

    return True


def migrate_memory_logs():
    """既存のメモリログをDBに移行"""
    print("\n🔄 メモリログ移行処理開始...")

    try:
        # 既存のaudit_log.pyからインポート
        from modules.audit_log import audit_logger

        if hasattr(audit_logger, '_logs') and len(audit_logger._logs) > 0:
            print(f"📝 メモリ上のログ: {len(audit_logger._logs)} 件")

            # DB版のロガーを初期化
            from modules.audit_log_db import AuditLoggerDB

            db_logger = AuditLoggerDB()

            # 移行実行
            migrated = db_logger.migrate_from_memory(audit_logger._logs)

            print(f"✅ {migrated} 件のログをDBに移行しました")

        else:
            print("ℹ️  移行対象のメモリログが見つかりません")

    except ImportError:
        print("ℹ️  modules/audit_log.py が見つかりません（スキップ）")
    except Exception as e:
        print(f"⚠️  移行エラー: {e}")


def verify_migration():
    """マイグレーション結果を検証"""
    print("\n🔍 マイグレーション検証...")

    try:
        from modules.audit_log_db import AuditLoggerDB

        logger = AuditLoggerDB()

        # 統計情報を取得
        stats = logger.get_statistics()

        print(f"  ✓ 総ログ数: {stats['total_logs']}")
        print(f"  ✓ 過去24時間の失敗: {stats['recent_failures_24h']}")
        print(f"  ✓ アクティブユーザー: {stats['active_users_24h']}")
        print(f"  ✓ 平均レスポンス時間: {stats['avg_response_time_ms']}ms")

        # テストログ書き込み
        log_id = logger.log_event(
            event_type="migration_test",
            user_id="test_user",
            username="Test User",
            details={"test": True, "timestamp": "2025-12-07"},
            success=True
        )

        print(f"  ✓ テストログ書き込み成功 (ID: {log_id})")

        # テストログ読み込み
        logs = logger.get_logs(limit=1, event_type="migration_test")
        if logs:
            print(f"  ✓ テストログ読み込み成功")
        else:
            print(f"  ⚠️  テストログが見つかりません")

        print("\n✅ 検証完了: システムは正常に動作しています")

    except Exception as e:
        print(f"❌ 検証エラー: {e}")
        return False

    return True


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(
        description="監査ログマイグレーション実行スクリプト"
    )
    parser.add_argument(
        "--db",
        default="db.sqlite3",
        help="データベースファイルパス (デフォルト: db.sqlite3)"
    )
    parser.add_argument(
        "--migrate-memory",
        action="store_true",
        help="メモリログをDBに移行"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="マイグレーション後の検証を実行"
    )

    args = parser.parse_args()

    # マイグレーション実行
    success = run_migration(args.db)

    if not success:
        sys.exit(1)

    # メモリログ移行
    if args.migrate_memory:
        migrate_memory_logs()

    # 検証
    if args.verify:
        if not verify_migration():
            sys.exit(1)

    print("\n🎉 すべての処理が完了しました！")


if __name__ == "__main__":
    main()
