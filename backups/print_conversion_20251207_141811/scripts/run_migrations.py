#!/usr/bin/env python3
"""
データベースマイグレーション実行スクリプト
migrations/ ディレクトリ内のSQLファイルを順次実行
"""
import sqlite3
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DB_PATH = "db.sqlite3"
MIGRATIONS_DIR = "migrations"


def get_migration_files():
    """マイグレーションファイル一覧を取得（番号順）"""
    migration_path = Path(MIGRATIONS_DIR)
    if not migration_path.exists():
        logger.info(f"❌ マイグレーションディレクトリが見つかりません: {MIGRATIONS_DIR}")
        return []
    
    sql_files = sorted(migration_path.glob("*.sql"))
    return sql_files


def run_migration(sql_file: Path, conn: sqlite3.Connection):
    """個別マイグレーションを実行"""
    logger.info(f"\n実行中: {sql_file.name}")
    
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # SQLスクリプト実行
        conn.executescript(sql)
        logger.info(f"✅ {sql_file.name} 実行完了")
        return True
    
    except sqlite3.Error as e:
        logger.info(f"❌ {sql_file.name} 実行失敗: {e}")
        return False
    except Exception as e:
        logger.info(f"❌ {sql_file.name} エラー: {e}")
        return False


def run_specific_migrations(migration_numbers: list):
    """特定のマイグレーションのみ実行"""
    migration_files = get_migration_files()
    
    logger.info(f"データベース: {DB_PATH}")
    logger.info(f"マイグレーション数: {len(migration_files)}")
    logger.info("=" * 60)
    
    with sqlite3.connect(DB_PATH) as conn:
        success_count = 0
        
        for sql_file in migration_files:
            # ファイル名から番号を抽出（例: 006_audit_logs.sql → 6）
            filename = sql_file.stem
            if '_' in filename:
                try:
                    file_number = int(filename.split('_')[0])
                except ValueError:
                    continue
                
                if file_number in migration_numbers:
                    if run_migration(sql_file, conn):
                        success_count += 1
        
        logger.info("\n" + "=" * 60)
        logger.info(f"実行完了: {success_count}/{len(migration_numbers)}件成功")
        
        return success_count == len(migration_numbers)


def run_all_migrations():
    """すべてのマイグレーションを実行"""
    migration_files = get_migration_files()

logger = logging.getLogger(__name__)

    
    if not migration_files:
        logger.info("実行するマイグレーションがありません")
        return False
    
    logger.info(f"データベース: {DB_PATH}")
    logger.info(f"マイグレーション数: {len(migration_files)}")
    logger.info("=" * 60)
    
    with sqlite3.connect(DB_PATH) as conn:
        success_count = 0
        
        for sql_file in migration_files:
            if run_migration(sql_file, conn):
                success_count += 1
        
        logger.info("\n" + "=" * 60)
        logger.info(f"実行完了: {success_count}/{len(migration_files)}件成功")
        
        return success_count == len(migration_files)


def verify_tables():
    """テーブル作成確認"""
    logger.info("\n" + "=" * 60)
    logger.info("テーブル確認:")
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = cursor.fetchall()
        
        for table in tables:
            logger.info(f"  ✅ {table[0]}")
        
        logger.info(f"\n総テーブル数: {len(tables)}")


if __name__ == '__main__':
    import argparse
import logging
    
    parser = argparse.ArgumentParser(description='データベースマイグレーション実行')
    parser.add_argument(
        '--migrations',
        nargs='+',
        type=int,
        help='実行するマイグレーション番号（例: 6 7）'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='テーブル確認のみ'
    )
    
    args = parser.parse_args()
    
    if args.verify:
        verify_tables()
    elif args.migrations:
        logger.info(f"マイグレーション実行: {args.migrations}")
        success = run_specific_migrations(args.migrations)
        verify_tables()
        sys.exit(0 if success else 1)
    else:
        logger.info("全マイグレーション実行")
        success = run_all_migrations()
        verify_tables()
        sys.exit(0 if success else 1)
