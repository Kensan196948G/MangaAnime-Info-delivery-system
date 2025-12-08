from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import sqlite3
import os
from datetime import datetime
from typing import Optional

auth_bp = Bluelogger.info('auth', __name__, url_prefix='/auth')

# データベース接続
def get_db():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'db.sqlite3')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# ユーザーストア
class UserStore:
    @staticmethod
    def get_user_by_username(username):
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        return User(user) if user else None

    @staticmethod
    def get_user_by_email(email):
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        return User(user) if user else None

    @staticmethod
    def get_user_by_id(user_id):
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        return User(user) if user else None

    @staticmethod
    def create_user(username, email, password):
        conn = get_db()
        password_hash = generate_password_hash(password)
        try:
            conn.execute(
                'INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
                (username, email, password_hash, datetime.now())
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    @staticmethod
    def update_password(user_id, new_password):
        """ユーザーのパスワードを更新"""
        conn = get_db()
        password_hash = generate_password_hash(new_password)
        try:
            conn.execute(
                'UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?',
                (password_hash, datetime.now(), user_id)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error")
            return False
        finally:
            conn.close()

class User:
    def __init__(self, user_row):
        self.id = user_row['id']
        self.username = user_row['username']
        self.email = user_row['email']
        self.password_hash = user_row['password_hash']

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# トークン生成・検証機能
def generate_reset_token(user_id: str) -> str:
    """パスワードリセット用トークンを生成"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(user_id, salt='password-reset')

def verify_reset_token(token: str, max_age: int = 3600) -> Optional[str]:
    """パスワードリセット用トークンを検証（デフォルト有効期限: 1時間）"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        user_id = serializer.loads(token, salt='password-reset', max_age=max_age)
        return user_id
    except (SignatureExpired, BadSignature):
        return None

# メール送信機能
def send_password_reset_email(user_email: str, reset_url: str, username: str) -> bool:
    """パスワードリセットメールを送信"""
    try:
        from modules.mailer import GmailNotifier

        notifier = GmailNotifier()

        # HTML形式のメール本文
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #f9f9f9;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .content {{
                    background-color: white;
                    padding: 25px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 15px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 20px;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 パスワードリセット</h1>
                </div>
                <div class="content">
                    <p>こんにちは、<strong>{username}</strong> さん</p>
                    <p>アカウントのパスワードリセットリクエストを受け付けました。</p>
                    <p>以下のボタンをクリックして、新しいパスワードを設定してください：</p>
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">パスワードをリセット</a>
                    </div>
                    <div class="warning">
                        <strong>⚠️ セキュリティに関する重要な注意事項：</strong>
                        <ul>
                            <li>このリンクは <strong>1時間</strong> で期限切れになります</li>
                            <li>リクエストに心当たりがない場合は、このメールを無視してください</li>
                            <li>パスワードは誰にも教えないでください</li>
                        </ul>
                    </div>
                    <p style="font-size: 12px; color: #666; margin-top: 20px;">
                        ボタンが機能しない場合は、以下のURLをコピーしてブラウザに貼り付けてください：<br>
                        <code style="background-color: #f5f5f5; padding: 5px; display: block; margin-top: 5px; word-wrap: break-word;">
                            {reset_url}
                        </code>
                    </p>
                </div>
                <div class="footer">
                    <p>MangaAnime Info Delivery System</p>
                    <p>このメールは自動送信されています。返信しないでください。</p>
                </div>
            </div>
        </body>
        </html>
        """

        # メール送信
        success = notifier.send_email(
            to_email=user_email,
            subject='パスワードリセットのご案内',
            body=html_content
        )

        return success

    except Exception as e:
        logger.error(f"Error")
        return False

# ルート定義
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = UserStore.get_user_by_username(username)

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('ログインしました', 'success')
            return redirect(url_for('index'))
        else:
            flash('ユーザー名またはパスワードが間違っています', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        # バリデーション
        if not username or not email or not password:
            flash('すべての項目を入力してください', 'danger')
            return render_template('auth/register.html')

        if password != password_confirm:
            flash('パスワードが一致しません', 'danger')
            return render_template('auth/register.html')

        if len(password) < 8:
            flash('パスワードは8文字以上にしてください', 'danger')
            return render_template('auth/register.html')

        # ユーザー作成
        if UserStore.create_user(username, email, password):
            flash('アカウントを作成しました。ログインしてください。', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('ユーザー名またはメールアドレスが既に使用されています', 'danger')

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('ログアウトしました', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """パスワードリセット要求"""
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            flash('メールアドレスを入力してください', 'danger')
            return render_template('auth/forgot_password.html')

        # ユーザーを検索
        user = UserStore.get_user_by_email(email)

        if user:
            # トークン生成
            token = generate_reset_token(str(user.id))

            # リセットURL生成
            reset_url = url_for('auth.reset_password', token=token, _external=True)

            # メール送信
            if send_password_reset_email(user.email, reset_url, user.username):
                flash('パスワードリセットの案内をメールで送信しました。メールをご確認ください。', 'success')
            else:
                flash('メール送信に失敗しました。しばらくしてから再度お試しください。', 'danger')
        else:
            # セキュリティのため、ユーザーが存在しない場合も同じメッセージを表示
            flash('パスワードリセットの案内をメールで送信しました。メールをご確認ください。', 'success')

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """パスワード再設定"""
    # トークン検証
    user_id = verify_reset_token(token)


    if not user_id:
        flash('パスワードリセットリンクが無効または期限切れです。再度リセットをリクエストしてください。', 'danger')
        return redirect(url_for('auth.forgot_password'))

    # ユーザー取得
    user = UserStore.get_user_by_id(user_id)

    if not user:
        flash('ユーザーが見つかりません', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        # バリデーション
        if not password or not password_confirm:
            flash('すべての項目を入力してください', 'danger')
            return render_template('auth/reset_password.html', token=token)

        if password != password_confirm:
            flash('パスワードが一致しません', 'danger')
            return render_template('auth/reset_password.html', token=token)

        if len(password) < 8:
            flash('パスワードは8文字以上にしてください', 'danger')
            return render_template('auth/reset_password.html', token=token)

        # パスワード更新
        if UserStore.update_password(user.id, password):
            flash('パスワードをリセットしました。新しいパスワードでログインしてください。', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('パスワードの更新に失敗しました', 'danger')

    return render_template('auth/reset_password.html', token=token)
