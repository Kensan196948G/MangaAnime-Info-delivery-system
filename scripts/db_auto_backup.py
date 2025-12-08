#!/usr/bin/env python3
"""
データベース自動バックアップスクリプト
- WALモードのチェックポイント実行
- 定期バックアップ作成
- 古いバックアップの自動削除
- 整合性チェック
"""

import os
import sys
import sqlite3
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'db_backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 設定
DB_PATH = project_root / 'data' / 'db.sqlite3'
BACKUP_DIR = project_root / 'backups'
MAX_BACKUPS = 30  # 保持するバックアップ数
BACKUP_INTERVAL_HOURS = 6  # バックアップ間隔（時間）


def ensure_directories() -> None:
    """必要なディレクトリを作成"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    (project_root / 'logs').mkdir(parents=True, exist_ok=True)


def check_database_integrity(db_path: Path) -> Tuple[bool, str]:
    """データベースの整合性をチェック"""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()[0]
        conn.close()

        if result == "ok":
            return True, "整合性チェック: OK"
        else:
            return False, f"整合性チェック失敗: {result}"
    except Exception as e:
        return False, f"整合性チェックエラー: {str(e)}"


def execute_wal_checkpoint(db_path: Path) -> Tuple[bool, str]:
    """WALモードのチェックポイントを実行"""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # WALモードか確認
        cursor.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]

        if journal_mode.lower() == 'wal':
            # チェックポイント実行（TRUNCATE: WALファイルを空にする）
            cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            result = cursor.fetchone()
            logger.info(f"WALチェックポイント完了: busy={result[0]}, log={result[1]}, checkpointed={result[2]}")
            conn.close()
            return True, f"WALチェックポイント完了"
        else:
            conn.close()
            return True, f"WALモードではありません（現在: {journal_mode}）"
    except Exception as e:
        return False, f"WALチェックポイントエラー: {str(e)}"


def create_backup(db_path: Path, backup_dir: Path) -> Tuple[bool, str, Optional[Path]]:
    """データベースのバックアップを作成"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"db_backup_{timestamp}.sqlite3"
        backup_path = backup_dir / backup_filename

        # 整合性チェック
        is_valid, msg = check_database_integrity(db_path)
        if not is_valid:
            logger.warning(f"元DBの整合性に問題: {msg}")

        # WALチェックポイント実行
        execute_wal_checkpoint(db_path)

        # バックアップ作成（SQLite Online Backup API使用）
        source_conn = sqlite3.connect(str(db_path))
        dest_conn = sqlite3.connect(str(backup_path))

        source_conn.backup(dest_conn)

        source_conn.close()
        dest_conn.close()

        # バックアップの整合性確認
        is_valid, msg = check_database_integrity(backup_path)
        if is_valid:
            logger.info(f"バックアップ作成成功: {backup_path}")
            return True, f"バックアップ作成成功: {backup_filename}", backup_path
        else:
            logger.error(f"バックアップの整合性に問題: {msg}")
            backup_path.unlink()  # 不正なバックアップを削除
            return False, f"バックアップの整合性に問題: {msg}", None

    except Exception as e:
        logger.error(f"バックアップ作成エラー: {str(e)}")
        return False, f"バックアップ作成エラー: {str(e)}", None


def cleanup_old_backups(backup_dir: Path, max_backups: int = MAX_BACKUPS) -> int:
    """古いバックアップを削除"""
    try:
        backups = sorted(
            backup_dir.glob("db_backup_*.sqlite3"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        deleted_count = 0
        for backup in backups[max_backups:]:
            backup.unlink()
            logger.info(f"古いバックアップを削除: {backup.name}")
            deleted_count += 1

        return deleted_count
    except Exception as e:
        logger.error(f"バックアップクリーンアップエラー: {str(e)}")
        return 0


def should_backup(backup_dir: Path, interval_hours: int = BACKUP_INTERVAL_HOURS) -> bool:
    """バックアップが必要かどうか判断"""
    try:
        backups = sorted(
            backup_dir.glob("db_backup_*.sqlite3"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if not backups:
            return True

        latest_backup = backups[0]
        latest_time = datetime.fromtimestamp(latest_backup.stat().st_mtime)
        time_since_backup = datetime.now() - latest_time

        return time_since_backup > timedelta(hours=interval_hours)
    except Exception:
        return True


def get_backup_stats(backup_dir: Path) -> dict:
    """バックアップの統計情報を取得"""
    backups = list(backup_dir.glob("db_backup_*.sqlite3"))

    if not backups:
        return {"count": 0, "total_size_mb": 0, "oldest": None, "newest": None}

    total_size = sum(b.stat().st_size for b in backups)
    sorted_backups = sorted(backups, key=lambda x: x.stat().st_mtime)

    return {
        "count": len(backups),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "oldest": sorted_backups[0].name,
        "newest": sorted_backups[-1].name
    }


def restore_from_backup(backup_path: Path, db_path: Path) -> Tuple[bool, str]:
    """バックアップからデータベースを復元"""
    try:
        # バックアップの整合性確認
        is_valid, msg = check_database_integrity(backup_path)
        if not is_valid:
            return False, f"バックアップの整合性に問題: {msg}"

        # 現在のDBをバックアップ（破損していても保存）
        corrupted_backup = db_path.parent / f"{db_path.name}.corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if db_path.exists():
            shutil.copy2(db_path, corrupted_backup)
            logger.info(f"破損DBを保存: {corrupted_backup}")

        # WALファイルを削除
        wal_file = Path(str(db_path) + "-wal")
        shm_file = Path(str(db_path) + "-shm")
        if wal_file.exists():
            wal_file.unlink()
        if shm_file.exists():
            shm_file.unlink()

        # バックアップから復元
        shutil.copy2(backup_path, db_path)

        # 復元後の整合性確認
        is_valid, msg = check_database_integrity(db_path)
        if is_valid:
            logger.info(f"データベース復元成功: {backup_path.name}")
            return True, f"データベース復元成功"
        else:
            return False, f"復元後の整合性に問題: {msg}"

    except Exception as e:
        return False, f"復元エラー: {str(e)}"


def main():
    """メイン処理"""
    ensure_directories()

    logger.info("=" * 50)
    logger.info("データベース自動バックアップ開始")
    logger.info("=" * 50)

    # データベース存在確認
    if not DB_PATH.exists():
        logger.error(f"データベースが見つかりません: {DB_PATH}")
        sys.exit(1)

    # 整合性チェック
    is_valid, msg = check_database_integrity(DB_PATH)
    logger.info(msg)

    if not is_valid:
        logger.warning("データベースに問題があります。最新のバックアップから復元を試みます。")
        backups = sorted(
            BACKUP_DIR.glob("db_backup_*.sqlite3"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        if backups:
            success, restore_msg = restore_from_backup(backups[0], DB_PATH)
            logger.info(restore_msg)
            if not success:
                sys.exit(1)
        else:
            logger.error("復元可能なバックアップがありません")
            sys.exit(1)

    # WALチェックポイント実行
    success, msg = execute_wal_checkpoint(DB_PATH)
    logger.info(msg)

    # バックアップ作成
    if should_backup(BACKUP_DIR):
        success, msg, backup_path = create_backup(DB_PATH, BACKUP_DIR)
        logger.info(msg)
    else:
        logger.info("前回のバックアップから十分な時間が経過していません。スキップします。")

    # 古いバックアップの削除
    deleted = cleanup_old_backups(BACKUP_DIR)
    if deleted > 0:
        logger.info(f"{deleted}個の古いバックアップを削除しました")

    # 統計情報
    stats = get_backup_stats(BACKUP_DIR)
    logger.info(f"バックアップ統計: {stats['count']}個, {stats['total_size_mb']}MB")

    logger.info("=" * 50)
    logger.info("データベース自動バックアップ完了")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
