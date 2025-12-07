"""
APIキー認証モジュール

このモジュールは、RESTful APIエンドポイント用のAPIキー認証機能を提供します。

主な機能:
- APIキーの生成・管理
- APIキー認証デコレータ
- ユーザーごとのAPIキー管理
- レート制限対応（将来実装）

使用例:
    from app.routes.api_auth import api_key_required, api_key_store

    @app.route('/api/data')
    @api_key_required
    def get_data():
        return jsonify({'user': g.api_user_id})
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, List
from functools import wraps
from flask import request, jsonify, g, Blueprint, session, flash, redirect, url_for
import secrets
import hashlib

# Blueprint定義
api_auth_bp = Blueprint('api_auth', __name__, url_prefix='/auth')


@dataclass
class User:
    """ユーザー情報を保持するデータクラス"""
    username: str
    password_hash: str
    created_at: datetime
    last_login: Optional[datetime] = None


@dataclass
class APIKey:
    """APIキー情報を保持するデータクラス"""
    key: str
    user_id: str
    name: str
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True
    rate_limit: Optional[int] = None  # リクエスト/分


class UserStore:
    """シンプルなインメモリユーザーストア（本番環境ではDBを使用）"""

    def __init__(self):
        self._users: Dict[str, User] = {}

    def create_user(self, username: str, password: str) -> User:
        """新規ユーザーを作成"""
        if username in self._users:
            raise ValueError("Username already exists")

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = User(
            username=username,
            password_hash=password_hash,
            created_at=datetime.now()
        )
        self._users[username] = user
        return user

    def verify_user(self, username: str, password: str) -> Optional[User]:
        """ユーザー認証"""
        user = self._users.get(username)
        if not user:
            return None

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user.password_hash == password_hash:
            user.last_login = datetime.now()
            return user
        return None

    def get_user(self, username: str) -> Optional[User]:
        """ユーザー情報を取得"""
        return self._users.get(username)


class APIKeyStore:
    """APIキー管理ストア"""

    def __init__(self):
        self._keys: Dict[str, APIKey] = {}
        self._user_keys: Dict[str, List[str]] = {}  # user_id -> [key_ids]

    def generate_key(self, user_id: str, name: str, rate_limit: Optional[int] = None) -> APIKey:
        """
        新しいAPIキーを生成

        Args:
            user_id: ユーザーID
            name: APIキーの名前
            rate_limit: レート制限（リクエスト/分）

        Returns:
            生成されたAPIKeyオブジェクト
        """
        key = f"sk_{secrets.token_urlsafe(32)}"
        api_key = APIKey(
            key=key,
            user_id=user_id,
            name=name,
            created_at=datetime.now(),
            rate_limit=rate_limit
        )
        self._keys[key] = api_key

        # ユーザーごとのキー管理
        if user_id not in self._user_keys:
            self._user_keys[user_id] = []
        self._user_keys[user_id].append(key)

        return api_key

    def verify_key(self, key: str) -> Optional[APIKey]:
        """
        APIキーを検証し、最終利用時刻を更新

        Args:
            key: 検証するAPIキー

        Returns:
            有効な場合はAPIKeyオブジェクト、無効な場合はNone
        """
        api_key = self._keys.get(key)
        if api_key and api_key.is_active:
            api_key.last_used = datetime.now()
            return api_key
        return None

    def get_keys_by_user(self, user_id: str) -> List[APIKey]:
        """
        ユーザーの全APIキーを取得

        Args:
            user_id: ユーザーID

        Returns:
            APIKeyオブジェクトのリスト
        """
        key_ids = self._user_keys.get(user_id, [])
        return [self._keys[k] for k in key_ids if k in self._keys]

    def revoke_key(self, key: str, user_id: Optional[str] = None) -> bool:
        """
        APIキーを無効化

        Args:
            key: 無効化するAPIキー
            user_id: ユーザーID（指定時は所有者確認）

        Returns:
            成功した場合True
        """
        if key in self._keys:
            api_key = self._keys[key]
            # ユーザー確認が必要な場合
            if user_id and api_key.user_id != user_id:
                return False
            api_key.is_active = False
            return True
        return False

    def delete_key(self, key: str, user_id: Optional[str] = None) -> bool:
        """
        APIキーを完全に削除

        Args:
            key: 削除するAPIキー
            user_id: ユーザーID（指定時は所有者確認）

        Returns:
            成功した場合True
        """
        if key in self._keys:
            api_key = self._keys[key]
            # ユーザー確認が必要な場合
            if user_id and api_key.user_id != user_id:
                return False

            # ユーザーのキーリストから削除
            if api_key.user_id in self._user_keys:
                self._user_keys[api_key.user_id].remove(key)

            # キー自体を削除
            del self._keys[key]
            return True
        return False


# グローバルインスタンス
user_store = UserStore()
api_key_store = APIKeyStore()


def login_required(f):
    """ログイン必須デコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('ログインが必要です', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def api_key_required(f):
    """
    APIキー認証デコレータ

    使用方法:
        @app.route('/api/data')
        @api_key_required
        def get_data():
            user_id = g.api_user_id
            return jsonify({'user': user_id})

    認証方法:
        1. HTTPヘッダー: X-API-Key: sk_xxxxx
        2. クエリパラメータ: ?api_key=sk_xxxxx
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # ヘッダーまたはクエリパラメータからAPIキーを取得
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'Please provide API key in X-API-Key header or api_key query parameter',
                'status': 401
            }), 401

        # キーを検証
        key_obj = api_key_store.verify_key(api_key)
        if not key_obj:
            return jsonify({
                'error': 'Invalid or inactive API key',
                'message': 'The provided API key is invalid or has been revoked',
                'status': 401
            }), 401

        # リクエストコンテキストにユーザー情報を追加
        g.api_user_id = key_obj.user_id
        g.api_key_name = key_obj.name
        g.api_key = key_obj.key

        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# APIキー管理エンドポイント
# ============================================================

@api_auth_bp.route('/api-keys/generate', methods=['POST'])
@login_required
def generate_api_key():
    """
    新しいAPIキーを生成

    Request Body:
        {
            "name": "My API Key",
            "rate_limit": 60  # optional
        }

    Response:
        {
            "success": true,
            "api_key": {
                "key": "sk_xxxxx",
                "name": "My API Key",
                "created_at": "2025-12-07T10:00:00",
                "rate_limit": 60
            },
            "message": "API key generated successfully..."
        }
    """
    try:
        data = request.get_json() or {}
        name = data.get('name', 'Default API Key')
        rate_limit = data.get('rate_limit')

        username = session.get('username')
        api_key = api_key_store.generate_key(username, name, rate_limit)

        return jsonify({
            'success': True,
            'api_key': {
                'key': api_key.key,
                'name': api_key.name,
                'created_at': api_key.created_at.isoformat(),
                'rate_limit': api_key.rate_limit
            },
            'message': 'API key generated successfully. Please save it securely - it will not be shown again.'
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 400
        }), 400


@api_auth_bp.route('/api-keys', methods=['GET'])
@login_required
def list_api_keys():
    """
    ユーザーの全APIキーを一覧表示（キー本体は非表示）

    Response:
        {
            "success": true,
            "api_keys": [
                {
                    "key_preview": "sk_abc123...xyz",
                    "name": "My API Key",
                    "created_at": "2025-12-07T10:00:00",
                    "last_used": "2025-12-07T12:30:00",
                    "is_active": true,
                    "rate_limit": 60
                }
            ]
        }
    """
    try:
        username = session.get('username')
        keys = api_key_store.get_keys_by_user(username)

        return jsonify({
            'success': True,
            'count': len(keys),
            'api_keys': [
                {
                    'key_preview': f"{k.key[:10]}...{k.key[-4:]}",
                    'full_key': k.key,  # 一覧表示時にも完全なキーを返す
                    'name': k.name,
                    'created_at': k.created_at.isoformat(),
                    'last_used': k.last_used.isoformat() if k.last_used else None,
                    'is_active': k.is_active,
                    'rate_limit': k.rate_limit
                }
                for k in keys
            ]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 400
        }), 400


@api_auth_bp.route('/api-keys/<key_id>', methods=['DELETE'])
@login_required
def revoke_api_key(key_id):
    """
    APIキーを無効化

    Response:
        {
            "success": true,
            "message": "API key revoked successfully"
        }
    """
    try:
        username = session.get('username')

        # キーを無効化（ユーザー確認付き）
        success = api_key_store.revoke_key(key_id, username)

        if success:
            return jsonify({
                'success': True,
                'message': 'API key revoked successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'API key not found or unauthorized',
                'status': 404
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 400
        }), 400


@api_auth_bp.route('/api-keys/<key_id>/delete', methods=['DELETE'])
@login_required
def delete_api_key(key_id):
    """
    APIキーを完全に削除

    Response:
        {
            "success": true,
            "message": "API key deleted successfully"
        }
    """
    try:
        username = session.get('username')

        # キーを削除（ユーザー確認付き）
        success = api_key_store.delete_key(key_id, username)

        if success:
            return jsonify({
                'success': True,
                'message': 'API key deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'API key not found or unauthorized',
                'status': 404
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 400
        }), 400


@api_auth_bp.route('/api-keys/verify', methods=['GET'])
@api_key_required
def verify_api_key_endpoint():
    """
    現在のAPIキーの情報を確認（デバッグ用）

    Response:
        {
            "success": true,
            "user_id": "username",
            "key_name": "My API Key",
            "message": "API key is valid and active"
        }
    """
    return jsonify({
        'success': True,
        'user_id': g.api_user_id,
        'key_name': g.api_key_name,
        'key_preview': f"{g.api_key[:10]}...{g.api_key[-4:]}",
        'message': 'API key is valid and active'
    }), 200
