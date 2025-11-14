"""
セキュリティ実装例集
Security Implementation Examples

このファイルは、セキュリティ監査レポートで推奨された
セキュリティ対策の具体的な実装例を提供します。
"""

from flask import Flask, request, jsonify, session, redirect
from functools import wraps
import jwt
import secrets
import logging
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import validators
from marshmallow import Schema, fields, validate, ValidationError

# ========================================
# 1. アプリケーション初期化とセキュリティ設定
# ========================================

app = Flask(__name__)

# 秘密鍵の設定（環境変数から取得）
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# セッション設定
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # JavaScriptからアクセス不可
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF対策
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# JWT設定
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# ========================================
# 2. CORS設定
# ========================================

CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://yourdomain.com",
            "https://www.yourdomain.com"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Range", "X-Content-Range"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

# ========================================
# 3. レート制限
# ========================================

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# ========================================
# 4. ログ設定
# ========================================

# セキュリティログ専用のロガー
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

security_handler = logging.FileHandler('logs/security.log')
security_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - [%(request_ip)s] - %(message)s'
))
security_logger.addHandler(security_handler)

# アプリケーションログ
app_logger = logging.getLogger('app')
app_logger.setLevel(logging.INFO)

app_handler = logging.FileHandler('logs/app.log')
app_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
app_logger.addHandler(app_handler)

# ========================================
# 5. セキュリティヘッダー
# ========================================

@app.after_request
def add_security_headers(response):
    """すべてのレスポンスにセキュリティヘッダーを追加"""

    # XSS保護
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https://cdn.jsdelivr.net; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )

    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Permissions Policy
    response.headers['Permissions-Policy'] = (
        "geolocation=(), microphone=(), camera=()"
    )

    # HSTS (本番環境のみ)
    if app.config.get('ENV') == 'production':
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains; preload'
        )

    return response

# ========================================
# 6. HTTPS強制リダイレクト
# ========================================

@app.before_request
def force_https():
    """本番環境でHTTPSを強制"""
    if app.config.get('ENV') == 'production':
        if not request.is_secure:
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)

# ========================================
# 7. リクエストログ
# ========================================

@app.before_request
def log_request():
    """全リクエストをログに記録"""
    extra = {'request_ip': request.remote_addr}
    security_logger.info(
        f"Request: {request.method} {request.path}",
        extra=extra
    )

# ========================================
# 8. JWT認証
# ========================================

def generate_token(user_id: int, username: str) -> str:
    """JWTトークンを生成"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """JWTトークンを検証"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')


def require_auth(f):
    """認証デコレーター"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            security_logger.warning(
                f"Missing Authorization header from {request.remote_addr}",
                extra={'request_ip': request.remote_addr}
            )
            return jsonify({'error': 'No token provided'}), 401

        try:
            # "Bearer <token>" 形式から取得
            token = auth_header.replace('Bearer ', '')
            payload = verify_token(token)

            # リクエストコンテキストにユーザー情報を追加
            request.current_user = payload

        except ValueError as e:
            security_logger.warning(
                f"Invalid token from {request.remote_addr}: {str(e)}",
                extra={'request_ip': request.remote_addr}
            )
            return jsonify({'error': str(e)}), 401

        return f(*args, **kwargs)

    return decorated_function


def require_role(role: str):
    """ロールベース認証デコレーター"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401

            user_role = request.current_user.get('role', 'user')

            if user_role != role and user_role != 'admin':
                security_logger.warning(
                    f"Unauthorized access attempt: user={request.current_user.get('username')}, "
                    f"required_role={role}",
                    extra={'request_ip': request.remote_addr}
                )
                return jsonify({'error': 'Insufficient permissions'}), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator

# ========================================
# 9. ユーザー管理
# ========================================

def create_users_table():
    """ユーザーテーブルを作成"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            failed_login_attempts INTEGER DEFAULT 0,
            last_login DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # インデックス作成
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")

    conn.commit()
    conn.close()


def create_user(username: str, email: str, password: str, role: str = 'user') -> int:
    """ユーザーを作成"""
    # パスワードハッシュ化
    password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (username, email, password_hash, role))

        user_id = cursor.lastrowid
        conn.commit()

        security_logger.info(
            f"New user created: username={username}, email={email}",
            extra={'request_ip': request.remote_addr if request else 'system'}
        )

        return user_id

    except sqlite3.IntegrityError:
        raise ValueError('Username or email already exists')
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> dict:
    """ユーザー認証"""
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, email, password_hash, role, is_active, failed_login_attempts
        FROM users
        WHERE username = ? OR email = ?
    """, (username, username))

    user = cursor.fetchone()

    if not user:
        security_logger.warning(
            f"Failed login attempt: user not found, username={username}",
            extra={'request_ip': request.remote_addr}
        )
        raise ValueError('Invalid credentials')

    # アカウントがアクティブか確認
    if not user['is_active']:
        security_logger.warning(
            f"Login attempt for inactive account: username={username}",
            extra={'request_ip': request.remote_addr}
        )
        raise ValueError('Account is inactive')

    # 失敗回数チェック（5回以上でロック）
    if user['failed_login_attempts'] >= 5:
        security_logger.warning(
            f"Account locked due to too many failed attempts: username={username}",
            extra={'request_ip': request.remote_addr}
        )
        raise ValueError('Account is locked due to too many failed login attempts')

    # パスワード検証
    if not check_password_hash(user['password_hash'], password):
        # 失敗回数をインクリメント
        cursor.execute("""
            UPDATE users
            SET failed_login_attempts = failed_login_attempts + 1
            WHERE id = ?
        """, (user['id'],))
        conn.commit()
        conn.close()

        security_logger.warning(
            f"Failed login attempt: invalid password, username={username}",
            extra={'request_ip': request.remote_addr}
        )
        raise ValueError('Invalid credentials')

    # ログイン成功
    cursor.execute("""
        UPDATE users
        SET last_login = CURRENT_TIMESTAMP,
            failed_login_attempts = 0
        WHERE id = ?
    """, (user['id'],))
    conn.commit()
    conn.close()

    security_logger.info(
        f"Successful login: username={username}",
        extra={'request_ip': request.remote_addr}
    )

    return {
        'user_id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'role': user['role']
    }

# ========================================
# 10. 入力検証スキーマ
# ========================================

class UserRegistrationSchema(Schema):
    """ユーザー登録スキーマ"""
    username = fields.Str(
        required=True,
        validate=validate.And(
            validate.Length(min=3, max=50),
            validate.Regexp(r'^[a-zA-Z0-9_]+$', error='Username must contain only letters, numbers, and underscores')
        )
    )
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        validate=validate.And(
            validate.Length(min=8, max=100),
            validate.Regexp(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
                          error='Password must contain uppercase, lowercase, and numbers')
        )
    )


class WorkSchema(Schema):
    """作品スキーマ"""
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    type = fields.Str(required=True, validate=validate.OneOf(['anime', 'manga']))
    official_url = fields.Url(allow_none=True)


class SearchSchema(Schema):
    """検索スキーマ"""
    query = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    type = fields.Str(validate=validate.OneOf(['anime', 'manga']), allow_none=True)
    page = fields.Int(validate=validate.Range(min=1), missing=1)
    per_page = fields.Int(validate=validate.Range(min=1, max=100), missing=20)

# ========================================
# 11. SSRF対策
# ========================================

ALLOWED_DOMAINS = [
    'graphql.anilist.co',
    'cal.syoboi.jp',
    'news.yahoo.co.jp',
    'www3.nhk.or.jp',
]

def is_safe_url(url: str) -> bool:
    """URLが安全かチェック"""
    if not validators.url(url):
        return False

    from urllib.parse import urlparse
    parsed = urlparse(url)

    # HTTPSのみ許可
    if parsed.scheme != 'https':
        return False

    # ローカルホストを拒否
    if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
        return False

    # プライベートIPを拒否
    import ipaddress
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        pass  # ドメイン名の場合

    # 許可ドメインチェック
    return any(parsed.hostname.endswith(allowed) for allowed in ALLOWED_DOMAINS)

# ========================================
# 12. エラーハンドラー
# ========================================

@app.errorhandler(400)
def bad_request_error(error):
    """400エラーハンドラー"""
    return jsonify({'error': 'Bad request'}), 400


@app.errorhandler(401)
def unauthorized_error(error):
    """401エラーハンドラー"""
    return jsonify({'error': 'Unauthorized'}), 401


@app.errorhandler(403)
def forbidden_error(error):
    """403エラーハンドラー"""
    return jsonify({'error': 'Forbidden'}), 403


@app.errorhandler(404)
def not_found_error(error):
    """404エラーハンドラー"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(429)
def rate_limit_error(error):
    """429エラーハンドラー"""
    return jsonify({'error': 'Too many requests'}), 429


@app.errorhandler(500)
def internal_error(error):
    """500エラーハンドラー"""
    app_logger.error(f"Internal error: {error}")

    if app.config.get('DEBUG'):
        return jsonify({'error': str(error)}), 500
    else:
        return jsonify({'error': 'Internal server error'}), 500

# ========================================
# 13. APIエンドポイント実装例
# ========================================

@app.route('/api/register', methods=['POST'])
@limiter.limit("5 per hour")
def api_register():
    """ユーザー登録"""
    schema = UserRegistrationSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    try:
        user_id = create_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )

        return jsonify({
            'message': 'User created successfully',
            'user_id': user_id
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")
def api_login():
    """ログイン"""
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    try:
        user = authenticate_user(username, password)
        token = generate_token(user['user_id'], user['username'])

        return jsonify({
            'token': token,
            'user': {
                'id': user['user_id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 401


@app.route('/api/manual-collection', methods=['POST'])
@require_auth
@require_role('admin')
@limiter.limit("5 per minute")
def api_manual_collection():
    """手動データ収集（管理者のみ）"""
    # 実装コード
    return jsonify({'message': 'Collection started'}), 202


@app.route('/api/works', methods=['GET'])
@require_auth
@limiter.limit("100 per minute")
def api_works():
    """作品一覧取得"""
    schema = SearchSchema()

    try:
        params = schema.load(request.args)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # 実装コード
    return jsonify({'works': []}), 200


@app.route('/api/profile', methods=['GET'])
@require_auth
def api_profile():
    """プロフィール取得"""
    user = request.current_user

    return jsonify({
        'user_id': user['user_id'],
        'username': user['username']
    }), 200

# ========================================
# 14. データベースバックアップ
# ========================================

def backup_database():
    """データベースをバックアップ"""
    import shutil
    from datetime import datetime

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backup/db_{timestamp}.sqlite3'

    os.makedirs('backup', exist_ok=True)

    shutil.copy2('db.sqlite3', backup_file)

    app_logger.info(f"Database backed up to {backup_file}")

    # 古いバックアップを削除（30日以上）
    import time
    cutoff = time.time() - (30 * 86400)

    for filename in os.listdir('backup'):
        filepath = os.path.join('backup', filename)
        if os.path.getmtime(filepath) < cutoff:
            os.remove(filepath)
            app_logger.info(f"Old backup deleted: {filename}")

# ========================================
# 15. 起動設定
# ========================================

if __name__ == '__main__':
    # データベーステーブル作成
    create_users_table()

    # 本番環境設定
    if app.config.get('ENV') == 'production':
        # SSL証明書を使用
        app.run(
            host='0.0.0.0',
            port=443,
            ssl_context=('cert.pem', 'key.pem'),
            debug=False
        )
    else:
        # 開発環境
        app.run(host='0.0.0.0', port=5000, debug=True)
