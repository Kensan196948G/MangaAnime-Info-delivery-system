"""
APIキーデータベースストア - SQLite永続化版
"""

import logging
import secrets
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class APIKey:
    """APIキーモデル"""

    key: str
    user_id: str
    name: str
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True
    permissions: str = "read"  # read, write, admin（カンマ区切り）


class APIKeyDBStore:
    """SQLiteベースのAPIキーストア"""

    def __init__(self, db_path: str = "db.sqlite3"):
        self.db_path = db_path
        self._init_db()
        logger.info(f"APIKeyDBStore初期化: {db_path}")

    @contextmanager
    def get_connection(self):
        """データベース接続のコンテキストマネージャ"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"APIキーDBエラー: {e}")
            raise
        finally:
            conn.close()

    def _init_db(self):
        """テーブル初期化"""
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    key TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_used DATETIME,
                    is_active INTEGER DEFAULT 1,
                    permissions TEXT DEFAULT 'read',
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active)
            """
            )

    def generate_key(
        self, user_id: str, name: str, permissions: List[str] = None
    ) -> APIKey:
        """APIキーを生成"""
        key = f"sk_{secrets.token_urlsafe(32)}"
        permissions_str = ",".join(permissions) if permissions else "read"

        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO api_keys (key, user_id, name, permissions, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (key, user_id, name, permissions_str, datetime.now().isoformat()),
            )

        logger.info(
            f"APIキー生成: user_id={user_id}, name={name}, permissions={permissions_str}"
        )

        return APIKey(
            key=key,
            user_id=user_id,
            name=name,
            created_at=datetime.now(),
            permissions=permissions_str,
        )

    def verify_key(self, key: str) -> Optional[APIKey]:
        """APIキーを検証"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM api_keys WHERE key = ? AND is_active = 1", (key,)
            )
            row = cursor.fetchone()

            if row:
                # 最終利用時刻を更新
                conn.execute(
                    "UPDATE api_keys SET last_used = ? WHERE key = ?",
                    (datetime.now().isoformat(), key),
                )

                return APIKey(
                    key=row["key"],
                    user_id=row["user_id"],
                    name=row["name"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_used=(
                        datetime.fromisoformat(row["last_used"])
                        if row["last_used"]
                        else None
                    ),
                    is_active=bool(row["is_active"]),
                    permissions=row["permissions"],
                )
            return None

    def get_keys_by_user(self, user_id: str) -> List[APIKey]:
        """ユーザーのAPIキー一覧を取得"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM api_keys WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            )
            rows = cursor.fetchall()

            keys = []
            for row in rows:
                keys.append(
                    APIKey(
                        key=row["key"],
                        user_id=row["user_id"],
                        name=row["name"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        last_used=(
                            datetime.fromisoformat(row["last_used"])
                            if row["last_used"]
                            else None
                        ),
                        is_active=bool(row["is_active"]),
                        permissions=row["permissions"],
                    )
                )

            return keys

    def revoke_key(self, key: str) -> bool:
        """APIキーを無効化"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE api_keys SET is_active = 0 WHERE key = ?", (key,)
            )

            if cursor.rowcount > 0:
                logger.info(f"APIキー無効化: key={key[:15]}...")
                return True
            return False

    def delete_key(self, key: str) -> bool:
        """APIキーを物理削除"""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM api_keys WHERE key = ?", (key,))

            if cursor.rowcount > 0:
                logger.info(f"APIキー削除: key={key[:15]}...")
                return True
            return False


# グローバルインスタンス
api_key_store = APIKeyDBStore()
