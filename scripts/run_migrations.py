#!/usr/bin/env python3
"""
データベースマイグレーション実行スクリプト

使用方法:
    # 全マイグレーションを実行
    python3 scripts/run_migrations.py

    # 特定のマイグレーションを実行
    python3 scripts/run_migrations.py --version 001

    # ドライラン（実行内容を確認のみ）
    python3 scripts/run_migrations.py --dry-run

    # バックアップを作成してから実行
    python3 scripts/run_migrations.py --backup
"""

import sqlite3
import os
import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime


class MigrationRunner:
    def __init__(self, db_path, migrations_dir):
        self.db_path = db_path
        self.migrations_dir = Path(migrations_dir)
        self.conn = None

    def connect(self):
        """データベースに接続"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """マイグレーション履歴テーブルを作成"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                checksum TEXT
            )
        ''')
        self.conn.commit()

    def get_applied_migrations(self):
        """適用済みマイグレーション一覧を取得"""
        cursor = self.conn.execute(
            'SELECT version FROM schema_migrations ORDER BY version'
        )
        return {row['version'] for row in cursor.fetchall()}

    def get_pending_migrations(self):
        """未適用マイグレーション一覧を取得"""
        applied = self.get_applied_migrations()
        all_migrations = self._get_all_migrations()

        pending = []
        for migration_file in all_migrations:
            version = self._extract_version(migration_file)
            if version not in applied:
                pending.append(migration_file)

        return sorted(pending)

    def _get_all_migrations(self):
        """全マイグレーションファイルを取得"""
        if not self.migrations_dir.exists():
            print(f"エラー: マイグレーションディレクトリが見つかりません: {self.migrations_dir}")
            return []

        migrations = list(self.migrations_dir.glob('*.sql'))
        return sorted(migrations)

    def _extract_version(self, migration_file):
        """ファイル名からバージョン番号を抽出"""
        # 例: 001_add_recommended_indexes.sql → 001
        return migration_file.stem.split('_')[0]

    def _extract_description(self, migration_file):
        """ファイル名から説明を抽出"""
        # 例: 001_add_recommended_indexes.sql → add_recommended_indexes
        parts = migration_file.stem.split('_', 1)
        return parts[1] if len(parts) > 1 else ''

    def _calculate_checksum(self, content):
        """SQLファイルのチェックサムを計算"""
        import hashlib
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def apply_migration(self, migration_file, dry_run=False):
        """マイグレーションを適用"""
        version = self._extract_version(migration_file)
        description = self._extract_description(migration_file)

        print(f"\n{'[DRY-RUN] ' if dry_run else ''}マイグレーション適用中: {migration_file.name}")
        print(f"  バージョン: {version}")
        print(f"  説明: {description}")

        # SQLファイルを読み込み
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        if dry_run:
            print(f"  SQL内容:\n{sql_content[:200]}...")
            return True

        try:
            # マイグレーションを実行
            self.conn.executescript(sql_content)

            # マイグレーション履歴に記録
            checksum = self._calculate_checksum(sql_content)
            self.conn.execute('''
                INSERT INTO schema_migrations (version, description, checksum)
                VALUES (?, ?, ?)
            ''', (version, description, checksum))

            self.conn.commit()
            print(f"  ✓ 適用完了")
            return True

        except Exception as e:
            self.conn.rollback()
            print(f"  ✗ エラー: {e}")
            return False

    def run_all_pending(self, dry_run=False, backup=False):
        """全ての未適用マイグレーションを実行"""
        if backup and not dry_run:
            self._create_backup()

        pending = self.get_pending_migrations()

        if not pending:
            print("適用すべきマイグレーションはありません")
            return True

        print(f"\n{'[DRY-RUN] ' if dry_run else ''}{len(pending)}件のマイグレーションを実行します")

        success = True
        for migration_file in pending:
            if not self.apply_migration(migration_file, dry_run):
                success = False
                break

        if success:
            print(f"\n{'[DRY-RUN] ' if dry_run else ''}全てのマイグレーションが正常に適用されました")
        else:
            print("\nエラーが発生しました。マイグレーションを中断しました")

        return success

    def run_specific(self, version, dry_run=False, backup=False):
        """特定のマイグレーションを実行"""
        if backup and not dry_run:
            self._create_backup()

        all_migrations = self._get_all_migrations()
        target = None

        for migration_file in all_migrations:
            if self._extract_version(migration_file) == version:
                target = migration_file
                break

        if not target:
            print(f"エラー: バージョン {version} のマイグレーションが見つかりません")
            return False

        # 既に適用済みかチェック
        applied = self.get_applied_migrations()
        if version in applied:
            print(f"警告: バージョン {version} は既に適用済みです")
            if not dry_run:
                response = input("再実行しますか？ (y/N): ")
                if response.lower() != 'y':
                    return False

        return self.apply_migration(target, dry_run)

    def _create_backup(self):
        """データベースのバックアップを作成"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.db_path}.backup_{timestamp}"

        print(f"\nバックアップを作成しています: {backup_path}")
        shutil.copy2(self.db_path, backup_path)
        print(f"✓ バックアップ完了")

    def show_status(self):
        """マイグレーション状態を表示"""
        applied = self.get_applied_migrations()
        all_migrations = self._get_all_migrations()

        print("\n=== マイグレーション状態 ===")
        print(f"データベース: {self.db_path}")
        print(f"マイグレーションディレクトリ: {self.migrations_dir}")
        print()

        if not all_migrations:
            print("マイグレーションファイルがありません")
            return

        for migration_file in all_migrations:
            version = self._extract_version(migration_file)
            description = self._extract_description(migration_file)
            status = "✓ 適用済み" if version in applied else "  未適用"

            print(f"{status}  {version} - {description}")

        pending_count = len([m for m in all_migrations
                            if self._extract_version(m) not in applied])
        print(f"\n未適用: {pending_count}件")

    def close(self):
        """データベース接続を閉じる"""
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='データベースマイグレーション実行スクリプト')
    parser.add_argument('--version', '-v', help='実行する特定のマイグレーションバージョン')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='実際には実行せず、内容のみ確認')
    parser.add_argument('--backup', '-b', action='store_true',
                       help='実行前にデータベースのバックアップを作成')
    parser.add_argument('--status', '-s', action='store_true',
                       help='マイグレーション状態のみ表示')
    parser.add_argument('--db-path', default=None,
                       help='データベースファイルのパス（デフォルト: ../db.sqlite3）')

    args = parser.parse_args()

    # プロジェクトルートからの相対パス
    project_root = Path(__file__).parent.parent

    db_path = args.db_path or (project_root / 'db.sqlite3')
    migrations_dir = project_root / 'migrations'

    # データベースファイルの存在チェック
    if not os.path.exists(db_path):
        print(f"エラー: データベースファイルが見つかりません: {db_path}")
        sys.exit(1)

    runner = MigrationRunner(db_path, migrations_dir)

    try:
        runner.connect()

        if args.status:
            # ステータス表示のみ
            runner.show_status()
        elif args.version:
            # 特定のマイグレーションを実行
            success = runner.run_specific(args.version, args.dry_run, args.backup)
            sys.exit(0 if success else 1)
        else:
            # 全ての未適用マイグレーションを実行
            success = runner.run_all_pending(args.dry_run, args.backup)
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        runner.close()


if __name__ == '__main__':
    main()
