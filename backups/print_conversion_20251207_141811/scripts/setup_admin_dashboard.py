#!/usr/bin/env python3
"""
管理者ダッシュボードセットアップスクリプト

データベーステーブルの作成、初期データ投入、動作確認を行います。
"""

import sqlite3
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DB_PATH = project_root / 'db.sqlite3'


def create_database_tables():
    """必要なデータベーステーブルを作成"""
    logger.info("データベーステーブルを作成中...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ユーザーテーブルにロック機能追加
    try:
        cursor.execute('''
            ALTER TABLE users ADD COLUMN locked_until DATETIME
        ''')
        logger.info("  ✓ users.locked_until カラム追加")
    except sqlite3.OperationalError:
        logger.info("  - users.locked_until カラムは既に存在します")

    try:
        cursor.execute('''
            ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0
        ''')
        logger.info("  ✓ users.failed_attempts カラム追加")
    except sqlite3.OperationalError:
        logger.info("  - users.failed_attempts カラムは既に存在します")

    try:
        cursor.execute('''
            ALTER TABLE users ADD COLUMN last_login DATETIME
        ''')
        logger.info("  ✓ users.last_login カラム追加")
    except sqlite3.OperationalError:
        logger.info("  - users.last_login カラムは既に存在します")

    # 監査ログテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            action TEXT NOT NULL,
            username TEXT,
            ip_address TEXT,
            details TEXT
        )
    ''')
    logger.info("  ✓ audit_logs テーブル作成/確認")

    # APIキーテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT NOT NULL,
            key_prefix TEXT NOT NULL,
            key_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    logger.info("  ✓ api_keys テーブル作成/確認")

    # インデックス作成
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp
        ON audit_logs(timestamp)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_audit_action
        ON audit_logs(action)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_users_locked
        ON users(locked_until)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_users_last_login
        ON users(last_login)
    ''')

    logger.info("  ✓ インデックス作成完了")

    conn.commit()
    conn.close()
    logger.info("データベース準備完了!\n")


def insert_sample_data():
    """サンプルデータを投入（デモ用）"""
    logger.info("サンプルデータを投入中...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # サンプル監査ログ
    sample_logs = [
        ('login_success', 'admin', '127.0.0.1', 'Successful login'),
        ('login_failed', 'testuser', '192.168.1.100', 'Invalid password'),
        ('login_failed', 'testuser', '192.168.1.100', 'Invalid password'),
        ('api_request', 'api_user', '10.0.0.5', 'API key: ak_test123'),
        ('password_reset', 'user1', '127.0.0.1', 'Password reset requested'),
        ('logout', 'admin', '127.0.0.1', 'User logged out'),
    ]

    for action, username, ip, details in sample_logs:
        cursor.execute('''
            INSERT INTO audit_logs (action, username, ip_address, details)
            VALUES (?, ?, ?, ?)
        ''', (action, username, ip, details))

    logger.info(f"  ✓ {len(sample_logs)} 件の監査ログを追加")

    # サンプルAPIキー
    sample_keys = [
        ('Production API', 'ak_prod', 'hashed_key_prod_12345'),
        ('Development API', 'ak_dev', 'hashed_key_dev_67890'),
        ('Testing API', 'ak_test', 'hashed_key_test_abcde'),
    ]

    for key_name, prefix, key_hash in sample_keys:
        cursor.execute('''
            INSERT OR IGNORE INTO api_keys (key_name, key_prefix, key_hash)
            VALUES (?, ?, ?)
        ''', (key_name, prefix, key_hash))

    logger.info(f"  ✓ {len(sample_keys)} 件のAPIキーを追加")

    conn.commit()
    conn.close()
    logger.info("サンプルデータ投入完了!\n")


def verify_installation():
    """インストールを検証"""
    logger.info("インストールを検証中...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # テーブルの存在確認
    cursor.execute('''
        SELECT name FROM sqlite_master
        WHERE type='table' AND name IN ('users', 'audit_logs', 'api_keys')
    ''')

    tables = [row[0] for row in cursor.fetchall()]

    if 'users' in tables:
        logger.info("  ✓ users テーブル存在")
    else:
        logger.info("  ✗ users テーブル不足")

    if 'audit_logs' in tables:
        cursor.execute('SELECT COUNT(*) FROM audit_logs')
        count = cursor.fetchone()[0]
        logger.info(f"  ✓ audit_logs テーブル存在 ({count} 件)")
    else:
        logger.info("  ✗ audit_logs テーブル不足")

    if 'api_keys' in tables:
        cursor.execute('SELECT COUNT(*) FROM api_keys')
        count = cursor.fetchone()[0]
        logger.info(f"  ✓ api_keys テーブル存在 ({count} 件)")
    else:
        logger.info("  ✗ api_keys テーブル不足")

    # カラムの存在確認
    cursor.execute('PRAGMA table_info(users)')
    columns = [row[1] for row in cursor.fetchall()]

    required_columns = ['locked_until', 'failed_attempts', 'last_login']
    for col in required_columns:
        if col in columns:
            logger.info(f"  ✓ users.{col} カラム存在")
        else:
            logger.info(f"  ✗ users.{col} カラム不足")

    conn.close()
    logger.info("\n検証完了!\n")


def print_next_steps():
    """次のステップを表示"""
    logger.info("=" * 60)

logger = logging.getLogger(__name__)

    logger.info("管理者ダッシュボードセットアップ完了!")
    logger.info("=" * 60)
    logger.info()
    logger.info("次のステップ:")
    logger.info()
    logger.info("1. ブループリントを登録:")
    logger.info("   app/__init__.py または app/web_app.py に以下を追加")
    logger.info()
    logger.info("   from app.routes.admin_dashboard import admin_dash_bp")
import logging
    logger.info("   app.register_bluelogger.info(admin_dash_bp)")
    logger.info()
    logger.info("2. ナビゲーションメニューを追加:")
    logger.info("   templates/base.html の管理者メニューに")
    logger.info("   ダッシュボードリンクを追加")
    logger.info()
    logger.info("3. アプリケーションを起動:")
    logger.info("   python app/web_app.py")
    logger.info()
    logger.info("4. ダッシュボードにアクセス:")
    logger.info("   http://localhost:5000/admin/dashboard")
    logger.info()
    logger.info("詳細は docs/ADMIN_DASHBOARD_IMPLEMENTATION.md を参照")
    logger.info("=" * 60)


def main():
    """メイン処理"""
    logger.info("\n" + "=" * 60)
    logger.info("管理者ダッシュボード セットアップ")
    logger.info("=" * 60 + "\n")

    try:
        # データベーステーブル作成
        create_database_tables()

        # サンプルデータ投入（オプション）
        response = input("サンプルデータを投入しますか? (y/n): ").strip().lower()
        if response == 'y':
            insert_sample_data()

        # インストール検証
        verify_installation()

        # 次のステップ表示
        print_next_steps()

        return 0

    except Exception as e:
        logger.info(f"\n✗ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
