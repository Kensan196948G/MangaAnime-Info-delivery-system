"""
APIキー認証モジュール

REST API用のAPIキー認証機能を提供
"""

import logging
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Dict, List, Optional

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

logger = logging.getLogger(__name__)

# API認証用Blueprint
api_auth_bp = Blueprint("api_auth", __name__, url_prefix="/api/auth")


@dataclass
class APIKey:
    """APIキーモデル"""

    key: str
    user_id: str
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    is_active: bool = True
    permissions: List[str] = field(default_factory=lambda: ["read"])


@dataclass
class User:
    """ユーザーモデル"""

    id: str
    username: str
    password_hash: str
    is_active: bool = True


class UserStore:
    """インメモリユーザーストア"""

    def __init__(self):
        self._users: Dict[str, User] = {}
        self._by_username: Dict[str, str] = {}

    def create_user(self, username: str, password: str) -> User:
        """ユーザーを作成"""
        if username in self._by_username:
            raise ValueError(f"User {username} already exists")

        user_id = str(len(self._users) + 1)
        user = User(
            id=user_id,
            username=username,
            password_hash=generate_password_hash(password),
        )
        self._users[user_id] = user
        self._by_username[username] = user_id
        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        """ユーザー名でユーザーを取得"""
        user_id = self._by_username.get(username)
        if user_id:
            return self._users.get(user_id)
        return None

    def verify_password(self, username: str, password: str) -> bool:
        """パスワードを検証"""
        user = self.get_user_by_username(username)
        if user:
            return check_password_hash(user.password_hash, password)
        return False


class APIKeyStore:
    """インメモリAPIキーストア"""

    def __init__(self):
        self._keys: Dict[str, APIKey] = {}
        self._by_user: Dict[str, List[str]] = {}

    def generate_key(
        self,
        user_id: str,
        name: str,
        permissions: List[str] = None,
    ) -> APIKey:
        """APIキーを生成"""
        key = f"sk_{secrets.token_urlsafe(32)}"

        api_key = APIKey(
            key=key,
            user_id=user_id,
            name=name,
            permissions=permissions or ["read"],
        )

        self._keys[key] = api_key

        if user_id not in self._by_user:
            self._by_user[user_id] = []
        self._by_user[user_id].append(key)

        return api_key

    def verify_key(self, key: str) -> Optional[APIKey]:
        """APIキーを検証"""
        api_key = self._keys.get(key)
        if api_key and api_key.is_active:
            api_key.last_used = datetime.now()
            return api_key
        return None

    def revoke_key(self, key: str) -> bool:
        """APIキーを無効化"""
        api_key = self._keys.get(key)
        if api_key:
            api_key.is_active = False
            return True
        return False

    def get_keys_for_user(self, user_id: str) -> List[APIKey]:
        """ユーザーのAPIキー一覧を取得"""
        key_ids = self._by_user.get(user_id, [])
        return [self._keys[k] for k in key_ids if k in self._keys]


# グローバルインスタンス
user_store = UserStore()
api_key_store = APIKeyStore()


def require_api_key(f):
    """APIキー認証デコレータ"""

    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return jsonify({"error": "API key required"}), 401

        key_obj = api_key_store.verify_key(api_key)
        if not key_obj:
            return jsonify({"error": "Invalid API key"}), 401

        request.api_key = key_obj
        return f(*args, **kwargs)

    return decorated


# ルートハンドラ
@api_auth_bp.route("/keys", methods=["POST"])
def create_api_key():
    """APIキーを作成"""
    data = request.get_json() or {}

    user_id = data.get("user_id")
    name = data.get("name", "Default Key")
    permissions = data.get("permissions", ["read"])

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    try:
        api_key = api_key_store.generate_key(user_id, name, permissions)
        return jsonify({
            "key": api_key.key,
            "name": api_key.name,
            "permissions": api_key.permissions,
            "created_at": api_key.created_at.isoformat(),
        }), 201
    except Exception as e:
        logger.error(f"API key creation error: {e}")
        return jsonify({"error": str(e)}), 500


@api_auth_bp.route("/keys/verify", methods=["POST"])
def verify_api_key():
    """APIキーを検証"""
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        return jsonify({"valid": False, "error": "No API key provided"}), 400

    key_obj = api_key_store.verify_key(api_key)
    if key_obj:
        return jsonify({
            "valid": True,
            "user_id": key_obj.user_id,
            "permissions": key_obj.permissions,
        })

    return jsonify({"valid": False, "error": "Invalid API key"}), 401
