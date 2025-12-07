#!/usr/bin/env python3
"""
Database Migration Manager
マイグレーション実行・ロールバック・状態確認ツール
"""

import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "db.sqlite3"
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"
ROLLBACK_DIR = MIGRATIONS_DIR / "rollback"


class MigrationManager:
    """マイグレーション管理クラス"""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """データベース接続"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()

    def close(self):
        """データベース切断"""
        if self.conn:
            self.conn.close()

    def get_current_version(self):
        """現在のマイグレーションバージョン取得"""
        try:
            self.cursor.execute(
                "SELECT MAX(version) FROM schema_migrations"
            )
            result = self.cursor.fetchone()
            return result[0] if result[0] else 0
        except sqlite3.OperationalError:
            # schema_migrationsテーブルが存在しない
            return 0

    def get_migration_history(self):
        """マイグレーション履歴取得"""
        try:
            self.cursor.execute(
                """
                SELECT version, description, script_name, applied_at
                FROM schema_migrations
                ORDER BY version ASC
                """
            )
            return self.cursor.fetchall()
        except sqlite3.OperationalError:
            return []

    def execute_migration(self, version, script_path):
        """マイグレーション実行"""
        print(f"\n[INFO] Executing migration {version}: {script_path.name}")

        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                sql = f.read()

            # トランザクション内で実行（スクリプト内でBEGIN/COMMITしている場合は無視される）
            self.conn.executescript(sql)
            self.conn.commit()

            print(f"[SUCCESS] Migration {version} applied successfully")
            return True

        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] Migration {version} failed: {e}")
            return False

    def execute_rollback(self, version, script_path):
        """ロールバック実行"""
        print(f"\n[INFO] Rolling back migration {version}: {script_path.name}")

        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                sql = f.read()

            self.conn.executescript(sql)
            self.conn.commit()

            print(f"[SUCCESS] Rollback {version} completed successfully")
            return True

        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] Rollback {version} failed: {e}")
            return False

    def migrate_up(self, target_version=None):
        """マイグレーション実行（アップグレード）"""
        current_version = self.get_current_version()
        print(f"\n[INFO] Current database version: {current_version}")

        # マイグレーションファイル一覧取得
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        migration_files = [
            f for f in migration_files
            if f.name.startswith(tuple(str(i).zfill(3) for i in range(10)))
        ]

        if not migration_files:
            print("[WARNING] No migration files found")
            return

        # 実行するマイグレーション特定
        for migration_file in migration_files:
            # ファイル名から バージョン番号抽出（例: 001_initial_schema.sql → 1）
            version_str = migration_file.name.split('_')[0]
            version = int(version_str)

            # すでに適用済みならスキップ
            if version <= int(current_version):
                continue

            # ターゲットバージョン指定時はそれを超えたら終了
            if target_version and version > target_version:
                break

            # マイグレーション実行
            if not self.execute_migration(version, migration_file):
                print(f"\n[ERROR] Migration stopped at version {version}")
                return

        final_version = self.get_current_version()
        print(f"\n[SUCCESS] Database migrated to version {final_version}")

    def migrate_down(self, target_version=None):
        """マイグレーション ロールバック（ダウングレード）"""
        current_version = self.get_current_version()
        print(f"\n[INFO] Current database version: {current_version}")

        if current_version == 0:
            print("[WARNING] Database is already at version 0")
            return

        # ターゲットバージョン決定
        if target_version is None:
            target_version = current_version - 1

        if target_version >= current_version:
            print(f"[ERROR] Target version {target_version} must be less than current version {current_version}")
            return

        # ロールバックファイル一覧取得
        rollback_files = sorted(ROLLBACK_DIR.glob("*.sql"), reverse=True)

        # 実行するロールバック特定
        for rollback_file in rollback_files:
            version_str = rollback_file.name.split('_')[0]
            version = int(version_str)

            # current_version から target_version まで戻す
            if version > current_version or version <= target_version:
                continue

            # ロールバック実行
            if not self.execute_rollback(version, rollback_file):
                print(f"\n[ERROR] Rollback stopped at version {version}")
                return

        final_version = self.get_current_version()
        print(f"\n[SUCCESS] Database rolled back to version {final_version}")

    def show_status(self):
        """マイグレーション状態表示"""
        current_version = self.get_current_version()
        print("\n" + "=" * 60)
        print("DATABASE MIGRATION STATUS")
        print("=" * 60)
        print(f"Database Path: {self.db_path}")
        print(f"Current Version: {current_version}")
        print("\nMigration History:")
        print("-" * 60)

        history = self.get_migration_history()
        if history:
            for version, description, script_name, applied_at in history:
                print(f"  [{version}] {description}")
                print(f"      Script: {script_name}")
                print(f"      Applied: {applied_at}")
        else:
            print("  No migrations applied yet")

        print("=" * 60)

    def create_backup(self):
        """データベースバックアップ作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.db_path.parent / f"db_backup_{timestamp}.sqlite3"

        print(f"\n[INFO] Creating backup: {backup_path}")

        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            print(f"[SUCCESS] Backup created successfully")
            return backup_path
        except Exception as e:
            print(f"[ERROR] Backup failed: {e}")
            return None


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python migrate.py status           # マイグレーション状態確認")
        print("  python migrate.py up [version]     # マイグレーション実行")
        print("  python migrate.py down [version]   # ロールバック実行")
        print("  python migrate.py backup           # バックアップ作成")
        sys.exit(1)

    command = sys.argv[1]
    target_version = int(sys.argv[2]) if len(sys.argv) > 2 else None

    manager = MigrationManager()

    try:
        manager.connect()

        if command == "status":
            manager.show_status()

        elif command == "up":
            # バックアップ作成
            manager.create_backup()
            manager.migrate_up(target_version)
            manager.show_status()

        elif command == "down":
            # バックアップ作成
            manager.create_backup()
            manager.migrate_down(target_version)
            manager.show_status()

        elif command == "backup":
            manager.create_backup()

        else:
            print(f"[ERROR] Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        manager.close()


if __name__ == "__main__":
    main()
