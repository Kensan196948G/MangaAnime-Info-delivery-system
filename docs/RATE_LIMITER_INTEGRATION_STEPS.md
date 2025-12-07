# Flask-Limiter 統合手順書

## 既存プロジェクトへの統合ステップ

このドキュメントでは、既存の`app/web_app.py`にFlask-Limiterを統合する具体的な手順を説明します。

## 前提条件

- Flaskアプリケーションが`app/web_app.py`に実装されている
- Flask-Login（認証機能）が実装されている
- Python 3.7以上

## Step 1: 依存関係のインストール

### requirements.txtの更新

```bash
# requirements.txtに以下を追加
Flask-Limiter>=3.5.0
redis>=4.0.0  # 本番環境用
```

### インストール実行

```bash
pip install -r requirements.txt
```

## Step 2: 環境変数の設定

### .envファイルの作成

```bash
# 開発環境
FLASK_ENV=development
RATELIMIT_STORAGE_URI=memory://

# 本番環境
# FLASK_ENV=production
# RATELIMIT_STORAGE_URI=redis://localhost:6379
# REDIS_URL=redis://localhost:6379
```

## Step 3: web_app.pyの修正

### 3-1. インポートの追加

`app/web_app.py`の冒頭に以下を追加:

```python
# 既存のインポート
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from flask_cors import CORS

# 追加: レート制限関連
from app.utils.rate_limiter import init_limiter, get_rate_limit
```

### 3-2. アプリケーション設定の追加

Flask appインスタンス作成後に以下を追加:

```python
app = Flask(__name__)

# 既存の設定
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')

# 追加: レート制限設定
app.config['RATELIMIT_STORAGE_URI'] = os.environ.get(
    'RATELIMIT_STORAGE_URI',
    'memory://'
)
app.config['RATELIMIT_DEFAULT'] = ["200 per day", "50 per hour"]
```

### 3-3. Limiterの初期化

CORS、LoginManager初期化の後に追加:

```python
# 既存の初期化
CORS(app)
login_manager = LoginManager()
login_manager.init_app(app)

# 追加: レート制限の初期化
limiter = init_limiter(app)
```

### 3-4. エンドポイントへの適用

各エンドポイントにデコレータを追加:

#### 認証エンドポイント

```python
# ログイン
@app.route('/auth/login', methods=['POST'])
@limiter.limit(get_rate_limit('auth_login'))  # 追加
def login():
    # 既存のコード
    pass

# ログアウト
@app.route('/auth/logout', methods=['POST'])
@login_required
@limiter.limit(get_rate_limit('auth_logout'))  # 追加
def logout():
    # 既存のコード
    pass
```

#### APIエンドポイント

```python
# データ収集
@app.route('/api/manual-collection', methods=['POST'])
@login_required
@limiter.limit(get_rate_limit('api_collection'))  # 追加
def api_manual_collection():
    # 既存のコード
    pass

# 設定取得/更新
@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
@limiter.limit(get_rate_limit('api_settings'))  # 追加
def api_settings():
    # 既存のコード
    pass

# カレンダー同期
@app.route('/api/calendar/sync', methods=['POST'])
@login_required
@limiter.limit(get_rate_limit('api_calendar_sync'))  # 追加
def api_calendar_sync():
    # 既存のコード
    pass
```

#### 一般ページ

```python
# トップページ
@app.route('/')
@limiter.limit("100 per minute")  # 追加
def index():
    # 既存のコード
    pass

# ダッシュボード
@app.route('/dashboard')
@login_required
@limiter.limit("200 per hour")  # 追加
def dashboard():
    # 既存のコード
    pass
```

## Step 4: エラーハンドラの確認

`init_limiter()`関数が自動的に429エラーハンドラを登録しますが、
カスタマイズが必要な場合は以下を`web_app.py`に追加:

```python
@app.errorhandler(429)
def custom_ratelimit_handler(e):
    """カスタムレート制限エラーハンドラ"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'リクエスト制限を超えました。しばらくしてから再試行してください。',
            'retry_after': e.description
        }), 429

    flash('リクエスト回数が多すぎます。しばらくしてからお試しください。', 'warning')
    return redirect(request.referrer or url_for('index'))
```

## Step 5: Blueprintへの適用（オプション）

### 既存のBlueprintがある場合

```python
# app/routes/auth.py
from flask import Blueprint
from app.utils.rate_limiter import get_rate_limit

auth_bp = Blueprint('auth', __name__)

# web_app.pyでlimiterを渡す必要がある
def init_auth_routes(limiter):
    @auth_bp.route('/login', methods=['POST'])
    @limiter.limit(get_rate_limit('auth_login'))
    def login():
        pass

    return auth_bp
```

### web_app.pyでの登録

```python
# Limiter初期化後
limiter = init_limiter(app)

# Blueprintの登録
from app.routes.auth import init_auth_routes
auth_bp = init_auth_routes(limiter)
app.register_blueprint(auth_bp, url_prefix='/auth')
```

## Step 6: テストの実施

### 6-1. 基本動作確認

```bash
# アプリケーション起動
python app/web_app.py
```

### 6-2. レート制限のテスト

```bash
# curlでテスト（ログインエンドポイント: 5回/分）
for i in {1..6}; do
  curl -X POST http://localhost:5000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' \
    -w "\nStatus: %{http_code}\n\n"
done
```

期待される結果:
- 1-5回目: 200 OK（または401 Unauthorized）
- 6回目: 429 Too Many Requests

### 6-3. ユニットテストの実行

```bash
pytest tests/test_rate_limiter.py -v
```

## Step 7: ログの確認

### ログ出力の追加

```python
import logging

logger = logging.getLogger(__name__)

@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning(
        f"Rate limit exceeded: "
        f"IP={request.remote_addr}, "
        f"Endpoint={request.endpoint}, "
        f"User={current_user.username if current_user.is_authenticated else 'Anonymous'}"
    )
    # エラーレスポンス
```

### ログファイルの確認

```bash
tail -f logs/app.log | grep "Rate limit"
```

## Step 8: 本番環境への展開

### Redis のセットアップ

```bash
# Ubuntuの場合
sudo apt-get update
sudo apt-get install redis-server

# Redisの起動
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 動作確認
redis-cli ping
# PONG が返ればOK
```

### 環境変数の設定

```bash
# 本番環境の.envファイル
FLASK_ENV=production
RATELIMIT_STORAGE_URI=redis://localhost:6379
REDIS_URL=redis://localhost:6379
```

### アプリケーションの再起動

```bash
# systemdサービスの場合
sudo systemctl restart manga-anime-app

# または直接実行
python app/web_app.py
```

## Step 9: モニタリング

### Redisの監視

```bash
# Redis接続数の確認
redis-cli CLIENT LIST | wc -l

# メモリ使用量の確認
redis-cli INFO memory | grep used_memory_human

# レート制限キーの確認
redis-cli KEYS "flask-limiter:*"
```

### アプリケーションログの監視

```bash
# レート制限関連のログを監視
tail -f logs/app.log | grep -E "(Rate limit|429)"
```

## トラブルシューティング

### 問題1: ImportError: No module named 'flask_limiter'

**解決方法:**
```bash
pip install Flask-Limiter>=3.5.0
```

### 問題2: Redis接続エラー

**解決方法:**
```bash
# Redisが起動しているか確認
sudo systemctl status redis-server

# 一時的にメモリストレージを使用
export RATELIMIT_STORAGE_URI='memory://'
```

### 問題3: レート制限が反映されない

**確認事項:**
1. `init_limiter(app)`が実行されているか
2. デコレータの順序が正しいか（@limiter.limitは最も内側）
3. Flaskアプリが再起動されているか

### 問題4: 開発中に制限が邪魔

**解決方法:**
```python
# テストモードでは無効化
if app.config['TESTING']:
    limiter.enabled = False
```

## チェックリスト

統合完了前に以下を確認:

- [ ] Flask-Limiterがインストールされている
- [ ] 環境変数が設定されている
- [ ] `init_limiter(app)`が実行されている
- [ ] 重要なエンドポイントにデコレータが追加されている
- [ ] 429エラーハンドラが動作している
- [ ] ユニットテストがパスしている
- [ ] ログが正しく出力されている
- [ ] 本番環境でRedisが動作している（本番の場合）
- [ ] モニタリングが設定されている

## まとめ

この手順に従って統合すれば、以下が実現できます:

1. **セキュリティ向上**: ブルートフォース攻撃、DDoS攻撃からの保護
2. **リソース管理**: サーバー負荷の適切な管理
3. **ユーザー体験**: 公平なリソース配分
4. **運用監視**: レート制限違反の検出とログ記録

## 次のステップ

- [ ] 実際の使用パターンに基づいた制限値の調整
- [ ] ユーザー別の制限カスタマイズ
- [ ] Grafana等でのモニタリングダッシュボード構築
- [ ] アラート設定（異常なレート制限違反の検出）

---

**作成者**: Backend Developer Agent
**最終更新**: 2025-12-07
