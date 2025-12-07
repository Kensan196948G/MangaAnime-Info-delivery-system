# APIキー認証システム統合例

## app/web_app.py への統合

既存の `app/web_app.py` にAPIキー認証を統合する完全な例です。

### 1. Blueprintの登録

```python
# app/web_app.py

from flask import Flask
from flask_login import LoginManager

# 既存のインポート
from app.routes.auth import auth_bp, login_manager
from app.routes.calendar import calendar_bp

# APIキー認証のインポート
from app.routes.api_key import api_key_bp, api_key_required

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# LoginManager初期化
login_manager.init_app(app)

# Blueprintの登録
app.register_blueprint(auth_bp)
app.register_blueprint(calendar_bp)
app.register_blueprint(api_key_bp)  # <- 追加
```

### 2. 既存APIエンドポイントへのAPIキー認証追加

#### 統計APIの保護

```python
from flask import jsonify, g
from app.routes.api_key import api_key_required

@app.route('/api/stats')
@api_key_required(permissions=['read'])
def api_stats():
    """
    統計情報API（APIキー認証）

    使用例:
        curl -H "X-API-Key: YOUR_KEY" https://domain.com/api/stats
    """
    # APIキー情報はg変数からアクセス可能
    user_id = g.api_user_id
    key_name = g.api_key_name

    stats = {
        'total_works': 100,
        'total_releases': 500,
        'api_user': user_id,
        'api_key_name': key_name
    }

    return jsonify(stats)
```

#### データ取得API

```python
@app.route('/api/releases')
@api_key_required(permissions=['read'])
def api_releases():
    """最新リリース情報API"""
    # データベースから取得
    releases = get_recent_releases(limit=20)

    return jsonify({
        'releases': releases,
        'count': len(releases)
    })
```

#### データ更新API（書き込み権限必要）

```python
from flask import request

@app.route('/api/releases', methods=['POST'])
@api_key_required(permissions=['write'])
def api_create_release():
    """リリース情報追加API（書き込み権限必要）"""
    data = request.get_json()

    # バリデーション
    if not data or 'title' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    # データベースに保存
    release_id = create_release(data)

    return jsonify({
        'message': 'Release created',
        'id': release_id
    }), 201
```

### 3. ハイブリッド認証（ログインまたはAPIキー）

ログインユーザーとAPIキーの両方を受け付けるエンドポイント:

```python
from flask_login import current_user
from functools import wraps

def login_or_api_key_required(permissions=None):
    """ログインまたはAPIキー認証のデコレータ"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # ログインユーザーの場合
            if current_user.is_authenticated:
                g.user_id = current_user.id
                g.auth_method = 'login'
                return f(*args, **kwargs)

            # APIキーの場合
            api_key = request.headers.get('X-API-Key')
            if api_key:
                from app.routes.api_key import api_key_store

                key_obj = api_key_store.verify_key(api_key)
                if not key_obj:
                    return jsonify({'error': 'Invalid API key'}), 401

                # 権限チェック
                if permissions and not any(p in key_obj.permissions for p in permissions):
                    return jsonify({'error': 'Insufficient permissions'}), 403

                g.user_id = key_obj.user_id
                g.auth_method = 'api_key'
                return f(*args, **kwargs)

            # どちらでもない場合
            return jsonify({'error': 'Authentication required'}), 401

        return decorated_function
    return decorator


@app.route('/api/user/profile')
@login_or_api_key_required()
def user_profile():
    """ユーザープロフィールAPI（ログインまたはAPIキー認証）"""
    user_id = g.user_id
    auth_method = g.auth_method

    profile = get_user_profile(user_id)

    return jsonify({
        'profile': profile,
        'auth_method': auth_method
    })
```

### 4. Web UIとAPI統合の完全な例

```python
# app/web_app.py - 完全版

from flask import Flask, render_template, jsonify, request, g
from flask_login import LoginManager, login_required, current_user

from app.routes.auth import auth_bp, login_manager
from app.routes.calendar import calendar_bp
from app.routes.api_key import api_key_bp, api_key_required

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# LoginManager初期化
login_manager.init_app(app)

# Blueprintの登録
app.register_blueprint(auth_bp)
app.register_blueprint(calendar_bp)
app.register_blueprint(api_key_bp)


# ======================
# Web UI Routes
# ======================

@app.route('/')
def index():
    """トップページ"""
    return render_template('index.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """ダッシュボード（ログイン必須）"""
    return render_template('dashboard.html', user=current_user)


# ======================
# Public API (読み取り専用)
# ======================

@app.route('/api/public/stats')
def api_public_stats():
    """公開統計API（認証不要）"""
    stats = {
        'total_anime': 1000,
        'total_manga': 2000,
        'last_updated': '2025-12-07T10:00:00Z'
    }
    return jsonify(stats)


# ======================
# Protected API (APIキー認証)
# ======================

@app.route('/api/stats')
@api_key_required(permissions=['read'])
def api_stats():
    """詳細統計API（read権限必要）"""
    user_id = g.api_user_id

    stats = {
        'total_works': 100,
        'total_releases': 500,
        'user_specific_count': get_user_stats(user_id)
    }

    return jsonify(stats)


@app.route('/api/releases')
@api_key_required(permissions=['read'])
def api_releases():
    """リリース一覧API（read権限必要）"""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    releases = get_releases(limit=limit, offset=offset)

    return jsonify({
        'releases': releases,
        'count': len(releases),
        'limit': limit,
        'offset': offset
    })


@app.route('/api/releases', methods=['POST'])
@api_key_required(permissions=['write'])
def api_create_release():
    """リリース作成API（write権限必要）"""
    data = request.get_json()

    # バリデーション
    required_fields = ['title', 'release_date', 'type']
    if not all(field in data for field in required_fields):
        return jsonify({
            'error': 'Missing required fields',
            'required': required_fields
        }), 400

    # データ作成
    release_id = create_release(data, user_id=g.api_user_id)

    return jsonify({
        'message': 'Release created successfully',
        'id': release_id
    }), 201


@app.route('/api/releases/<int:release_id>', methods=['PUT'])
@api_key_required(permissions=['write'])
def api_update_release(release_id):
    """リリース更新API（write権限必要）"""
    data = request.get_json()

    # 更新処理
    success = update_release(release_id, data, user_id=g.api_user_id)

    if success:
        return jsonify({'message': 'Release updated successfully'})
    else:
        return jsonify({'error': 'Release not found'}), 404


@app.route('/api/releases/<int:release_id>', methods=['DELETE'])
@api_key_required(permissions=['write'])
def api_delete_release(release_id):
    """リリース削除API（write権限必要）"""
    success = delete_release(release_id, user_id=g.api_user_id)

    if success:
        return jsonify({'message': 'Release deleted successfully'})
    else:
        return jsonify({'error': 'Release not found'}), 404


# ======================
# Admin API (管理者権限)
# ======================

@app.route('/api/admin/users')
@api_key_required(permissions=['admin'])
def api_admin_users():
    """ユーザー一覧API（admin権限必要）"""
    users = get_all_users()

    return jsonify({
        'users': users,
        'count': len(users)
    })


@app.route('/api/admin/system/health')
@api_key_required(permissions=['admin'])
def api_admin_health():
    """システムヘルスチェックAPI（admin権限必要）"""
    health = {
        'database': check_database_health(),
        'cache': check_cache_health(),
        'api_keys': {
            'total': len(get_all_api_keys()),
            'active': count_active_keys()
        }
    }

    return jsonify(health)


# ======================
# エラーハンドラ
# ======================

@app.errorhandler(401)
def unauthorized(error):
    """401エラー"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Unauthorized'}), 401
    return render_template('errors/401.html'), 401


@app.errorhandler(403)
def forbidden(error):
    """403エラー"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Forbidden'}), 403
    return render_template('errors/403.html'), 403


@app.errorhandler(404)
def not_found(error):
    """404エラー"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('errors/404.html'), 404


# ======================
# ヘルパー関数（実装例）
# ======================

def get_user_stats(user_id):
    """ユーザー固有の統計"""
    # 実装例
    return {
        'favorites': 10,
        'notifications': 5
    }


def get_releases(limit=20, offset=0):
    """リリース一覧取得"""
    # データベースから取得
    return []


def create_release(data, user_id):
    """リリース作成"""
    # データベースに保存
    return 1


def update_release(release_id, data, user_id):
    """リリース更新"""
    # データベース更新
    return True


def delete_release(release_id, user_id):
    """リリース削除"""
    # データベースから削除
    return True


def get_all_users():
    """全ユーザー取得（管理者用）"""
    return []


def check_database_health():
    """データベースヘルスチェック"""
    return 'OK'


def check_cache_health():
    """キャッシュヘルスチェック"""
    return 'OK'


def get_all_api_keys():
    """全APIキー取得"""
    from app.routes.api_key import api_key_store
    return api_key_store.get_all_keys()


def count_active_keys():
    """アクティブキー数"""
    from app.routes.api_key import api_key_store
    return api_key_store.get_stats()['active_keys']


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

## ナビゲーションメニューへの追加

`templates/base.html`:

```html
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <a class="navbar-brand" href="/">MangaAnime Info</a>
    <div class="collapse navbar-collapse">
        <ul class="navbar-nav ml-auto">
            {% if current_user.is_authenticated %}
                <li class="nav-item">
                    <a class="nav-link" href="{{ url_for('dashboard') }}">
                        <i class="fas fa-tachometer-alt"></i> ダッシュボード
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{{ url_for('api_key.index') }}">
                        <i class="fas fa-key"></i> APIキー
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{{ url_for('auth.logout') }}">
                        <i class="fas fa-sign-out-alt"></i> ログアウト
                    </a>
                </li>
            {% else %}
                <li class="nav-item">
                    <a class="nav-link" href="{{ url_for('auth.login') }}">
                        <i class="fas fa-sign-in-alt"></i> ログイン
                    </a>
                </li>
            {% endif %}
        </ul>
    </div>
</nav>
```

## 実行とテスト

### 1. サーバー起動
```bash
python app/web_app.py
```

### 2. Web UIでAPIキー生成
1. http://localhost:5000/login にアクセス
2. ログイン
3. http://localhost:5000/api-keys/ にアクセス
4. 「新しいAPIキーを生成」ボタンをクリック
5. 生成されたキーをコピー

### 3. APIテスト

```bash
# 読み取りAPI
curl -H "X-API-Key: YOUR_KEY" http://localhost:5000/api/stats

# リリース一覧
curl -H "X-API-Key: YOUR_KEY" http://localhost:5000/api/releases

# 新規作成（write権限必要）
curl -X POST \
     -H "X-API-Key: YOUR_KEY" \
     -H "Content-Type: application/json" \
     -d '{"title":"新作アニメ","release_date":"2025-12-10","type":"anime"}' \
     http://localhost:5000/api/releases
```

## まとめ

この統合例により:
- Web UIとAPIの両方を提供
- ログイン認証とAPIキー認証を併用
- 権限レベルに応じたアクセス制御
- RESTful APIの完全な実装

が実現できます。

---

**参照**: [API_KEY_COMPLETE_GUIDE.md](/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/docs/API_KEY_COMPLETE_GUIDE.md)
