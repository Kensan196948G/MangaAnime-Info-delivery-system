"""
認証モジュール - Flask-Login ベースの認証機構

このモジュールは以下の機能を提供します:
- ユーザー認証（ログイン/ログアウト）
- セッション管理
- 保護されたエンドポイント用デコレータ
"""

import os
import logging
from functools import wraps
from datetime import datetime
from typing import Optional, Dict
from dataclasses import dataclass, field

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)

# 認証用Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@dataclass
class User(UserMixin):
    """Flask-Login用ユーザーモデル"""
    id: str
    username: str
    password_hash: str
    is_admin: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None

    def check_password(self, password: str) -> bool:
        """パスワード検証"""
        return check_password_hash(self.password_hash, password)

    def get_id(self) -> str:
        """Flask-Login用のID取得"""
        return self.id

    def update_last_login(self):
        """最終ログイン時刻を更新"""
        self.last_login = datetime.now()


class UserStore:
    """インメモリユーザーストア（本番環境ではDBに置き換え）"""

    def __init__(self):
        self._users: Dict[str, User] = {}
        self._init_default_user()

    def _init_default_user(self):
        """デフォルト管理者ユーザーを作成"""
        default_username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
        default_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'changeme123')

        admin_user = User(
            id='1',
            username=default_username,
            password_hash=generate_password_hash(default_password),
            is_admin=True
        )
        self._users[admin_user.id] = admin_user
        logger.info(f"デフォルト管理者ユーザー '{default_username}' を作成しました")

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """IDでユーザーを取得"""
        return self._users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """ユーザー名でユーザーを取得"""
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    def add_user(self, username: str, password: str, is_admin: bool = False) -> User:
        """新規ユーザーを追加"""
        user_id = str(len(self._users) + 1)
        user = User(
            id=user_id,
            username=username,
            password_hash=generate_password_hash(password),
            is_admin=is_admin
        )
        self._users[user_id] = user
        logger.info(f"新規ユーザー '{username}' を作成しました")
        return user


# グローバルユーザーストア
user_store = UserStore()


def init_login_manager(app) -> LoginManager:
    """Flask-Loginの初期化"""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'このページにアクセスするにはログインが必要です。'
    login_manager.login_message_category = 'warning'
    login_manager.session_protection = 'strong'

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional[User]:
        """ユーザーローダーコールバック"""
        return user_store.get_user_by_id(user_id)

    logger.info("Flask-Login を初期化しました")
    return login_manager


def admin_required(f):
    """管理者権限が必要なエンドポイント用デコレータ"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            logger.warning(f"管理者権限のないユーザー '{current_user.username}' がアクセスを試みました")
            flash('このページにアクセスする権限がありません。', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# ============ ルート定義 ============

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """ログインページ"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        if not username or not password:
            flash('ユーザー名とパスワードを入力してください。', 'warning')
            return render_template('auth/login.html')

        user = user_store.get_user_by_username(username)

        if user and user.check_password(password):
            user.update_last_login()
            login_user(user, remember=bool(remember))
            logger.info(f"ユーザー '{username}' がログインしました")

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            logger.warning(f"ログイン失敗: ユーザー名 '{username}'")
            flash('ユーザー名またはパスワードが正しくありません。', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """ログアウト"""
    username = current_user.username
    logout_user()
    logger.info(f"ユーザー '{username}' がログアウトしました")
    flash('ログアウトしました。', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/status')
def status():
    """認証状態を返すAPIエンドポイント"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'username': current_user.username,
            'is_admin': current_user.is_admin,
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        })
    return jsonify({'authenticated': False})


@auth_bp.route('/refresh', methods=['GET', 'POST'])
@login_required
def refresh():
    """セッション更新ページ"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if current_user.check_password(password):
            # セッションを更新
            login_user(current_user, fresh=True)
            logger.info(f"ユーザー '{current_user.username}' のセッションを更新しました")
            flash('セッションを更新しました。', 'success')

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('パスワードが正しくありません。', 'danger')

    return render_template('auth/refresh.html')
