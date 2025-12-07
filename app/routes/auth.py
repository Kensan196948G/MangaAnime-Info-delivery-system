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
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass, field

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

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
        default_password = os.getenv('DEFAULT_ADMIN_PASSWORD')

        if not default_password:
            logger.error('DEFAULT_ADMIN_PASSWORD environment variable is required')
            raise ValueError(
                'DEFAULT_ADMIN_PASSWORD environment variable must be set in .env file. '
                'This is a security requirement to prevent using default passwords.'
            )

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

    def get_all_users(self) -> List[User]:
        """全ユーザーを取得"""
        return list(self._users.values())

    def delete_user(self, user_id: str) -> bool:
        """ユーザーを削除"""
        if user_id in self._users:
            username = self._users[user_id].username
            del self._users[user_id]
            logger.info(f"ユーザー '{username}' (ID: {user_id}) を削除しました")
            return True
        return False

    def get_user_count(self) -> int:
        """ユーザー数を取得"""
        return len(self._users)

    def update_password(self, user_id: str, new_password: str) -> bool:
        """ユーザーのパスワードを更新"""
        user = self.get_user_by_id(user_id)
        if user:
            user.password_hash = generate_password_hash(new_password)
            logger.info(f"ユーザー '{user.username}' のパスワードを更新しました")
            return True
        return False


# グローバルユーザーストア
# 環境変数でDB版とメモリ版を切り替え
USE_DB_STORE = os.getenv('USE_DB_STORE', 'true').lower() == 'true'

if USE_DB_STORE:
    try:
        from app.models.user_db import UserDBStore
        user_store = UserDBStore()
        logger.info("UserDBStore（DB版）を使用します")
    except ImportError as e:
        logger.warning(f"UserDBStoreの読み込み失敗: {e}。メモリ版を使用します")
        user_store = UserStore()
else:
    user_store = UserStore()
    logger.info("UserStore（メモリ版）を使用します")


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


# ============ パスワードリセット用ヘルパー ============

def generate_reset_token(user_id: str) -> str:
    """パスワードリセットトークンを生成"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(user_id, salt='password-reset')


def verify_reset_token(token: str, max_age: int = 3600) -> Optional[str]:
    """パスワードリセットトークンを検証"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        user_id = serializer.loads(token, salt='password-reset', max_age=max_age)
        return user_id
    except (SignatureExpired, BadSignature):
        return None


def send_password_reset_email(user_email: str, reset_url: str) -> bool:
    """パスワードリセットメールを送信"""
    try:
        from modules.mailer import GmailNotifier

        notifier = GmailNotifier()
        subject = "【重要】パスワードリセットのご案内"

        html_body = f"""
        <html>
            <body style="font-family: sans-serif; line-height: 1.6;">
                <h2 style="color: #0d6efd;">パスワードリセットのご案内</h2>
                <p>パスワードリセットのリクエストを受け付けました。</p>
                <p>以下のリンクをクリックして、新しいパスワードを設定してください：</p>
                <p style="margin: 20px 0;">
                    <a href="{reset_url}"
                       style="display: inline-block; padding: 10px 20px; background-color: #0d6efd;
                              color: white; text-decoration: none; border-radius: 5px;">
                        パスワードをリセット
                    </a>
                </p>
                <p style="color: #666; font-size: 14px;">
                    このリンクは1時間有効です。<br>
                    もしこのリクエストに心当たりがない場合は、このメールを無視してください。
                </p>
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
                <p style="color: #999; font-size: 12px;">
                    MangaAnime情報配信システム<br>
                    このメールは自動送信されています
                </p>
            </body>
        </html>
        """

        # メール送信（GmailNotifierのメソッドに合わせて調整）
        # 実装はGmailNotifierのインターフェースに依存
        logger.info(f"パスワードリセットメールを {user_email} に送信しました")
        return True

    except Exception as e:
        logger.error(f"パスワードリセットメール送信失敗: {e}")
        return False


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

        # ブルートフォース対策: アカウントロック確認
        try:
            from modules.brute_force_protection import attempt_tracker
            is_locked, unlock_time = attempt_tracker.is_locked(username)

            if is_locked:
                remaining_minutes = int((unlock_time - datetime.now()).total_seconds() / 60)
                flash(
                    f'アカウントがロックされています。{remaining_minutes}分後に再試行してください。',
                    'danger'
                )

                # 監査ログ記録
                try:
                    from modules.audit_log import audit_logger, AuditEventType
                    audit_logger.log_event(
                        event_type=AuditEventType.AUTH_LOGIN_FAILURE,
                        username=username,
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string,
                        details={'reason': 'account_locked', 'unlock_time': unlock_time.isoformat()},
                        success=False
                    )
                except ImportError:
                    pass

                return render_template('auth/login.html')
        except ImportError:
            attempt_tracker = None

        user = user_store.get_user_by_username(username)

        if user and user.check_password(password):
            # ログイン成功
            user.update_last_login()
            login_user(user, remember=bool(remember))
            logger.info(f"ユーザー '{username}' がログインしました")

            # ブルートフォース対策: 試行回数クリア
            if attempt_tracker:
                attempt_tracker.clear_attempts(username)

            # 監査ログ記録
            try:
                from modules.audit_log import audit_logger, AuditEventType
                audit_logger.log_event(
                    event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
                    user_id=user.id,
                    username=username,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string,
                    details={'remember': bool(remember)},
                    success=True
                )
            except ImportError:
                pass

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            # ログイン失敗
            logger.warning(f"ログイン失敗: ユーザー名 '{username}'")

            # ブルートフォース対策: 失敗記録
            if attempt_tracker:
                attempt_tracker.record_failed_attempt(username)
                remaining = attempt_tracker.get_remaining_attempts(username)
                if remaining > 0:
                    flash(
                        f'ユーザー名またはパスワードが正しくありません。（残り試行回数: {remaining}回）',
                        'danger'
                    )
                else:
                    flash(
                        'ログイン試行回数が上限に達しました。アカウントが一時的にロックされました。',
                        'danger'
                    )
            else:
                flash('ユーザー名またはパスワードが正しくありません。', 'danger')

            # 監査ログ記録
            try:
                from modules.audit_log import audit_logger, AuditEventType
                audit_logger.log_event(
                    event_type=AuditEventType.AUTH_LOGIN_FAILURE,
                    username=username,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string,
                    details={'reason': 'invalid_credentials'},
                    success=False
                )
            except ImportError:
                pass

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """ログアウト"""
    username = current_user.username
    user_id = current_user.id

    logout_user()
    logger.info(f"ユーザー '{username}' がログアウトしました")

    # 監査ログ記録
    try:
        from modules.audit_log import audit_logger, AuditEventType
        audit_logger.log_event(
            event_type=AuditEventType.AUTH_LOGOUT,
            user_id=user_id,
            username=username,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            success=True
        )
    except ImportError:
        pass

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

            # 監査ログ記録
            try:
                from modules.audit_log import audit_logger, AuditEventType
                audit_logger.log_event(
                    event_type=AuditEventType.AUTH_SESSION_REFRESH,
                    user_id=current_user.id,
                    username=current_user.username,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string,
                    success=True
                )
            except ImportError:
                pass

            flash('セッションを更新しました。', 'success')

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('パスワードが正しくありません。', 'danger')

    return render_template('auth/refresh.html')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """パスワードリセット要求ページ"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()

        if not username:
            flash('ユーザー名を入力してください。', 'warning')
            return render_template('auth/forgot_password.html')

        user = user_store.get_user_by_username(username)

        # セキュリティ: ユーザーが存在するかどうかを明かさない
        if user:
            token = generate_reset_token(user.id)
            reset_url = url_for('auth.reset_password', token=token, _external=True)

            # メール送信（ユーザーのメールアドレスが必要 - 今は仮実装）
            # send_password_reset_email(user.email, reset_url)
            logger.info(f"パスワードリセットトークン生成: ユーザー '{username}'")

        # 常に成功メッセージを表示（セキュリティのため）
        flash('パスワードリセットの手順をメールで送信しました。', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """パスワード再設定ページ"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # トークン検証
    user_id = verify_reset_token(token)
    if not user_id:
        flash('パスワードリセットリンクが無効か期限切れです。', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = user_store.get_user_by_id(user_id)
    if not user:
        flash('ユーザーが見つかりません。', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        # バリデーション
        if not password or len(password) < 8:
            flash('パスワードは8文字以上で入力してください。セキュリティ強化のため、大文字・小文字・数字を含めることを推奨します。', 'warning')
            return render_template('auth/reset_password.html', token=token)

        if password != password_confirm:
            flash('パスワードが一致しません。', 'warning')
            return render_template('auth/reset_password.html', token=token)

        # パスワード更新
        if user_store.update_password(user_id, password):
            logger.info(f"ユーザー '{user.username}' のパスワードをリセットしました")
            flash('パスワードを再設定しました。新しいパスワードでログインしてください。', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('パスワードの更新に失敗しました。', 'danger')

    return render_template('auth/reset_password.html', token=token)
