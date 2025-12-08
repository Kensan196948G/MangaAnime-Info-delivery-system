"""
拡張認証モジュール - パスワードリセット機能付き

このモジュールは以下の機能を提供します:
- パスワードリセットトークン生成
- パスワードリセットトークン検証
- パスワードリセットフロー
"""

import logging
import os
import sqlite3
from datetime import datetime
from typing import Dict, Optional

from flask import Blueprint, flash, redirect, render_template, request, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

# 認証用Blueprint
auth_bp = Blueprint("auth_enhanced", __name__, url_prefix="/auth")

# データベースパス
DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/db.sqlite3")


def get_db():
    """データベース接続を取得"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def generate_reset_token(email: str, secret_key: str = None) -> str:
    """
    パスワードリセットトークンを生成

    Args:
        email: ユーザーのメールアドレス
        secret_key: シークレットキー（デフォルトは環境変数から）

    Returns:
        リセットトークン文字列
    """
    if secret_key is None:
        secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(email, salt="password-reset-salt")


def verify_reset_token(token: str, secret_key: str = None, max_age: int = 3600) -> Optional[str]:
    """
    パスワードリセットトークンを検証

    Args:
        token: リセットトークン
        secret_key: シークレットキー
        max_age: トークンの有効期限（秒）

    Returns:
        有効な場合はメールアドレス、無効な場合はNone
    """
    if secret_key is None:
        secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

    serializer = URLSafeTimedSerializer(secret_key)

    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=max_age)
        return email
    except (SignatureExpired, BadSignature):
        return None


class UserStore:
    """ユーザーストアクラス"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DATABASE_PATH

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """メールでユーザーを検索"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"User lookup error: {e}")
            return None

    def update_password(self, email: str, new_password: str) -> bool:
        """パスワードを更新"""
        try:
            conn = sqlite3.connect(self.db_path)
            password_hash = generate_password_hash(new_password)
            conn.execute(
                "UPDATE users SET password_hash = ?, updated_at = ? WHERE email = ?",
                (password_hash, datetime.now(), email),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Password update error: {e}")
            return False


# ルートハンドラ
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """パスワードリセットリクエスト"""
    if request.method == "POST":
        email = request.form.get("email")

        if email:
            # トークン生成
            token = generate_reset_token(email)
            # 実際にはメール送信処理が必要
            logger.info(f"Password reset token generated for {email}")

            flash("パスワードリセットメールを送信しました", "success")
            return redirect(url_for("auth_enhanced.login"))

        flash("メールアドレスを入力してください", "error")

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    """パスワードリセット実行"""
    email = verify_reset_token(token)

    if not email:
        flash("リセットリンクが無効または期限切れです", "error")
        return redirect(url_for("auth_enhanced.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password and password == confirm_password:
            store = UserStore()
            if store.update_password(email, password):
                flash("パスワードを更新しました", "success")
                return redirect(url_for("auth_enhanced.login"))

        flash("パスワードが一致しません", "error")

    return render_template("auth/reset_password.html", token=token)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """ログインページ"""
    return render_template("auth/login.html")
