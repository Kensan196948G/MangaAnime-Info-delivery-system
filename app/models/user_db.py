"""
ユーザーデータベースストア - SQLite永続化版
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List
from contextlib import contextmanager
from werkzeug.security import generate_password_hash, check_password_hash

# User dataclass をインポート
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.routes.auth import User

logger = logging.getLogger(__name__)


class UserDBStore:
    """SQLiteベースのユーザーストア"""
    
    def __init__(self, db_path: str = "db.sqlite3"):
        self.db_path = db_path
        logger.info(f"UserDBStore初期化: {db_path}")
    
    @contextmanager
    def get_connection(self):
        """データベース接続のコンテキストマネージャ"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 辞書ライクなアクセス
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"データベースエラー: {e}")
            raise
        finally:
            conn.close()
    
    def _row_to_user(self, row: sqlite3.Row) -> User:
        """SQLiteのRowをUserオブジェクトに変換"""
        return User(
            id=row['id'],
            username=row['username'],
            password_hash=row['password_hash'],
            is_admin=bool(row['is_admin']),
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None
        )
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """IDでユーザーを取得"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_user(row)
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """ユーザー名でユーザーを取得"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_user(row)
            return None
    
    def add_user(self, username: str, password: str, is_admin: bool = False) -> User:
        """新規ユーザーを追加"""
        import secrets
        
        user_id = f"user-{secrets.token_urlsafe(12)}"
        password_hash = generate_password_hash(password)
        
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (id, username, password_hash, is_admin, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, username, password_hash, int(is_admin), 1, datetime.now().isoformat())
            )
        
        logger.info(f"新規ユーザー作成: '{username}' (ID: {user_id}, 管理者: {is_admin})")
        
        return User(
            id=user_id,
            username=username,
            password_hash=password_hash,
            is_admin=is_admin,
            is_active=True,
            created_at=datetime.now()
        )
    
    def get_all_users(self) -> List[User]:
        """全ユーザーを取得"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
            
            return [self._row_to_user(row) for row in rows]
    
    def delete_user(self, user_id: str) -> bool:
        """ユーザーを削除（論理削除）"""
        with self.get_connection() as conn:
            # 物理削除ではなく論理削除
            cursor = conn.execute(
                "UPDATE users SET is_active = 0 WHERE id = ?",
                (user_id,)
            )
            
            if cursor.rowcount > 0:
                logger.info(f"ユーザー削除（論理削除）: ID={user_id}")
                return True
            return False
    
    def update_password(self, user_id: str, new_password: str) -> bool:
        """パスワードを更新"""
        password_hash = generate_password_hash(new_password)
        
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
                (password_hash, datetime.now().isoformat(), user_id)
            )
            
            if cursor.rowcount > 0:
                logger.info(f"パスワード更新: user_id={user_id}")
                return True
            return False
    
    def update_last_login(self, user_id: str) -> bool:
        """最終ログイン時刻を更新"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), user_id)
            )
            
            return cursor.rowcount > 0
    
    def get_user_count(self) -> int:
        """ユーザー数を取得"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM users WHERE is_active = 1"
            )
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    def toggle_admin(self, user_id: str) -> bool:
        """管理者権限を切り替え"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE users SET is_admin = NOT is_admin WHERE id = ?",
                (user_id,)
            )
            
            if cursor.rowcount > 0:
                logger.info(f"管理者権限切り替え: user_id={user_id}")
                return True
            return False
