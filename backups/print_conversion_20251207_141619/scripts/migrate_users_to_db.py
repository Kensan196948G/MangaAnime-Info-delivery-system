#!/usr/bin/env python3
"""
ユーザーデータのDB移行スクリプト

インメモリのユーザーストアからSQLiteデータベースへ移行します。
マイグレーション実行、データ検証、ロールバック機能を提供します。

使用方法:
    python scripts/migrate_users_to_db.py migrate    # 移行実行
    python scripts/migrate_users_to_db.py verify     # 検証のみ
    python scripts/migrate_users_to_db.py rollback   # ロールバック
"""

import sys
import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.user_db import UserDBStore, User
from werkzeug.security import generate_password_hash


class UserMigration:
    """ユーザーマイグレーション管理クラス"""

    def __init__(self, db_path: str = "db.sqlite3"):
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.migration_log = []

    def log(self, message: str, level: str = "INFO"):
        """ログメッセージを記録"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        self.migration_log.append(log_entry)

    def backup_database(self) -> bool:
        """データベースをバックアップ"""
        try:
            if os.path.exists(self.db_path):
                import shutil
                shutil.copy2(self.db_path, self.backup_path)
                self.log(f"Database backed up to: {self.backup_path}")
                return True
            else:
                self.log("No existing database to backup", "WARNING")
                return True
        except Exception as e:
            self.log(f"Backup failed: {e}", "ERROR")
            return False

    def execute_migration(self) -> bool:
        """マイグレーションを実行"""
        try:
            self.log("Starting user table migration...")

            # マイグレーションSQLファイルを読み込む
            migration_file = project_root / "migrations" / "007_users_table.sql"

            if not migration_file.exists():
                self.log(f"Migration file not found: {migration_file}", "ERROR")
                return False

            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()

            # SQLを実行
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executescript(migration_sql)
            conn.commit()
            conn.close()

            self.log("Migration executed successfully")
            return True

        except Exception as e:
            self.log(f"Migration failed: {e}", "ERROR")
            return False

    def migrate_inmemory_users(self) -> bool:
        """インメモリユーザーをDBに移行"""
        try:
            self.log("Migrating in-memory users to database...")

            # インメモリのデフォルトユーザーを定義
            default_users = [
                {
                    "username": "admin",
                    "password": "changeme123",
                    "email": "admin@example.com",
                    "is_admin": True
                },
                {
                    "username": "user1",
                    "password": "password123",
                    "email": "user1@example.com",
                    "is_admin": False
                }
            ]

            store = UserDBStore(self.db_path)

            for user_data in default_users:
                try:
                    # 既に存在するか確認
                    existing = store.get_user_by_username(user_data["username"])
                    if existing:
                        self.log(f"User already exists: {user_data['username']}", "INFO")
                        continue

                    # ユーザーを追加
                    store.add_user(
                        username=user_data["username"],
                        password=user_data["password"],
                        email=user_data["email"],
                        is_admin=user_data["is_admin"]
                    )
                    self.log(f"Migrated user: {user_data['username']}")

                except Exception as e:
                    self.log(f"Failed to migrate user {user_data['username']}: {e}", "WARNING")

            self.log("In-memory user migration completed")
            return True

        except Exception as e:
            self.log(f"In-memory migration failed: {e}", "ERROR")
            return False

    def verify_migration(self) -> bool:
        """マイグレーション結果を検証"""
        try:
            self.log("Verifying migration...")

            store = UserDBStore(self.db_path)

            # ユーザー統計を取得
            stats = store.get_user_stats()
            self.log(f"Total users: {stats.get('total_users', 0)}")
            self.log(f"Admin users: {stats.get('admin_count', 0)}")
            self.log(f"Active users: {stats.get('active_count', 0)}")

            # 全ユーザーを取得
            users = store.get_all_users()
            self.log(f"Retrieved {len(users)} users from database")

            for user in users:
                self.log(f"  - {user.username} (admin: {user.is_admin}, active: {user.is_active})")

            # デフォルト管理者が存在するか確認
            admin = store.get_user_by_username("admin")
            if admin:
                self.log("Default admin user verified")
                # パスワード検証
                if admin.check_password("changeme123"):
                    self.log("Admin password verification successful", "WARNING")
                    self.log("IMPORTANT: Change default admin password!", "WARNING")
            else:
                self.log("Default admin user not found", "ERROR")
                return False

            self.log("Migration verification completed successfully")
            return True

        except Exception as e:
            self.log(f"Verification failed: {e}", "ERROR")
            return False

    def rollback(self) -> bool:
        """最新のバックアップからロールバック"""
        try:
            # 最新のバックアップを検索
            backup_files = sorted(
                [f for f in os.listdir('.') if f.startswith(f"{self.db_path}.backup_")],
                reverse=True
            )

            if not backup_files:
                self.log("No backup files found", "ERROR")
                return False

            latest_backup = backup_files[0]
            self.log(f"Rolling back from: {latest_backup}")

            import shutil
            shutil.copy2(latest_backup, self.db_path)

            self.log("Rollback completed successfully")
            return True

        except Exception as e:
            self.log(f"Rollback failed: {e}", "ERROR")
            return False

    def save_migration_log(self):
        """マイグレーションログを保存"""
        log_file = f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.migration_log))
            self.log(f"Migration log saved to: {log_file}")
        except Exception as e:
            self.log(f"Failed to save migration log: {e}", "ERROR")

    def run_full_migration(self) -> bool:
        """完全なマイグレーションプロセスを実行"""
        self.log("=" * 60)
        self.log("User Database Migration - Starting")
        self.log("=" * 60)

        # 1. バックアップ
        if not self.backup_database():
            self.log("Aborting migration due to backup failure", "ERROR")
            return False

        # 2. マイグレーション実行
        if not self.execute_migration():
            self.log("Aborting migration due to execution failure", "ERROR")
            return False

        # 3. インメモリユーザー移行
        if not self.migrate_inmemory_users():
            self.log("Warning: In-memory user migration had issues", "WARNING")

        # 4. 検証
        if not self.verify_migration():
            self.log("Migration verification failed", "ERROR")
            self.log("Consider running rollback if issues persist", "WARNING")
            return False

        # 5. ログ保存
        self.save_migration_log()

        self.log("=" * 60)
        self.log("User Database Migration - Completed Successfully")
        self.log("=" * 60)
        return True


def main():
    """メイン実行関数"""
    if len(sys.argv) < 2:
        print("Usage: python migrate_users_to_db.py [migrate|verify|rollback]")
        print("\nCommands:")
        print("  migrate  - Execute full migration process")
        print("  verify   - Verify existing migration")
        print("  rollback - Rollback to latest backup")
        sys.exit(1)

    command = sys.argv[1].lower()
    migration = UserMigration()

    if command == "migrate":
        success = migration.run_full_migration()
        sys.exit(0 if success else 1)

    elif command == "verify":
        success = migration.verify_migration()
        migration.save_migration_log()
        sys.exit(0 if success else 1)

    elif command == "rollback":
        success = migration.rollback()
        migration.save_migration_log()
        sys.exit(0 if success else 1)

    else:
        print(f"Unknown command: {command}")
        print("Valid commands: migrate, verify, rollback")
        sys.exit(1)


if __name__ == "__main__":
    main()
