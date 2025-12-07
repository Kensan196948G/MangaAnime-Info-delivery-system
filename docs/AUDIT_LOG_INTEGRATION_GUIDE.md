# 監査ログビューア統合ガイド

## 概要

このガイドでは、監査ログビューアUIを既存のFlaskアプリケーションに統合する手順を説明します。

## 前提条件

- Flask 2.0 以上
- SQLite3
- Bootstrap 5.3
- Python 3.8 以上

## 統合手順

### ステップ1: ファイルの配置確認

以下のファイルが正しい場所に配置されていることを確認:

```
/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/
├── app/
│   └── routes/
│       └── audit.py          # 監査ログルート
├── modules/
│   └── audit_log.py          # 監査ログモジュール
└── templates/
    └── admin/
        └── audit_logs.html   # 監査ログテンプレート
```

### ステップ2: app/web_app.py の修正

既存の `app/web_app.py` に監査ログBlueprintを登録します。

#### 2-1. インポート追加

```python
# ファイル先頭付近に追加
from app.routes.audit import audit_bp
```

#### 2-2. Blueprint登録

```python
# アプリケーション設定後に追加（他のBlueprint登録の近く）
app.register_blueprint(audit_bp)
```

完全な例:

```python
from flask import Flask, render_template
from app.routes.audit import audit_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# Blueprintの登録
app.register_blueprint(audit_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### ステップ3: ナビゲーションメニューの追加

`templates/base.html` の管理者メニューに監査ログリンクを追加します。

#### 3-1. base.html の確認

既存の管理者メニュー部分を探します:

```html
<!-- 管理者メニュー例 -->
<ul class="navbar-nav">
    <li class="nav-item dropdown">
        <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
            <i class="bi bi-gear"></i> 管理
        </a>
        <ul class="dropdown-menu">
            <!-- 既存のメニュー項目 -->
            <li><a class="dropdown-item" href="/admin/dashboard">ダッシュボード</a></li>
            <li><a class="dropdown-item" href="/admin/settings">設定</a></li>
        </ul>
    </li>
</ul>
```

#### 3-2. 監査ログリンクの追加

```html
<ul class="dropdown-menu">
    <!-- 既存のメニュー項目 -->
    <li><a class="dropdown-item" href="/admin/dashboard">ダッシュボード</a></li>
    <li><a class="dropdown-item" href="/admin/settings">設定</a></li>

    <!-- 監査ログリンク追加 -->
    <li><hr class="dropdown-divider"></li>
    <li>
        <a class="dropdown-item" href="{{ url_for('audit.audit_logs') }}">
            <i class="bi bi-file-earmark-text"></i> 監査ログ
        </a>
    </li>
</ul>
```

### ステップ4: データベースの初期化

監査ログテーブルを作成します。

#### 4-1. 自動初期化（推奨）

`modules/audit_log.py` の `AuditLogger` クラスは初期化時に自動でテーブルを作成します。

```python
from modules.audit_log import audit_logger

# これだけでテーブルが作成される
audit_logger.log('system', 'System initialized', status='info')
```

#### 4-2. 手動初期化

必要に応じて手動でテーブルを作成:

```bash
sqlite3 db.sqlite3 < migrations/audit_logs.sql
```

`migrations/audit_logs.sql`:

```sql
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    user_id TEXT,
    ip_address TEXT,
    user_agent TEXT,
    details TEXT,
    status TEXT CHECK(status IN ('success', 'failure', 'warning', 'info')),
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id);
```

### ステップ5: 監査ログの記録

アプリケーションの各所で監査ログを記録します。

#### 5-1. ログイン時

```python
from flask import request
from modules.audit_log import audit_logger

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if authenticate(username, password):
        # 成功ログ
        audit_logger.log(
            event_type='user_login',
            details=f'User {username} logged in successfully',
            user_id=username,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            status='success'
        )
        return redirect('/dashboard')
    else:
        # 失敗ログ
        audit_logger.log(
            event_type='user_login',
            details=f'Failed login attempt for user {username}',
            user_id=username,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            status='failure'
        )
        return 'Login failed', 401
```

#### 5-2. API呼び出し時

```python
@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        data = fetch_external_api()

        # 成功ログ
        audit_logger.log(
            event_type='api_call',
            details='Successfully fetched data from external API',
            user_id=get_current_user(),
            status='success',
            metadata={'endpoint': '/api/data', 'records': len(data)}
        )

        return jsonify(data)
    except Exception as e:
        # エラーログ
        audit_logger.log(
            event_type='api_call',
            details=f'Error fetching data: {str(e)}',
            user_id=get_current_user(),
            status='failure',
            metadata={'error': str(e), 'endpoint': '/api/data'}
        )

        return jsonify({'error': 'Internal server error'}), 500
```

#### 5-3. データ更新時

```python
@app.route('/admin/settings', methods=['POST'])
def update_settings():
    old_value = get_setting('key')
    new_value = request.form['value']

    update_setting('key', new_value)

    # 変更ログ
    audit_logger.log(
        event_type='settings_update',
        details=f'Setting changed from {old_value} to {new_value}',
        user_id=get_current_user(),
        ip_address=request.remote_addr,
        status='success',
        metadata={'old_value': old_value, 'new_value': new_value}
    )

    return 'Updated'
```

### ステップ6: 権限管理の実装

`app/routes/audit.py` の `admin_required` デコレータを実装します。

#### 6-1. セッションベースの認証

```python
from flask import session, redirect, url_for
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))

        if not session.get('is_admin'):
            return 'Forbidden', 403

        return f(*args, **kwargs)
    return decorated_function
```

#### 6-2. JWT認証

```python
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        user = get_jwt_identity()

        if not user.get('is_admin'):
            return 'Forbidden', 403

        return f(*args, **kwargs)
    return decorated_function
```

### ステップ7: 動作確認

#### 7-1. 開発サーバー起動

```bash
python app/web_app.py
```

#### 7-2. ブラウザでアクセス

```
http://localhost:5000/admin/audit-logs
```

#### 7-3. サンプルデータ投入

```python
from modules.audit_log import audit_logger
import random

event_types = ['login', 'logout', 'api_call', 'data_update']
statuses = ['success', 'failure', 'warning', 'info']
users = ['admin', 'user1', 'user2']

for i in range(50):
    audit_logger.log(
        event_type=random.choice(event_types),
        details=f'Sample log entry {i}',
        user_id=random.choice(users),
        ip_address=f'192.168.1.{random.randint(1, 255)}',
        status=random.choice(statuses)
    )
```

### ステップ8: 本番環境へのデプロイ

#### 8-1. 環境変数の設定

```bash
export FLASK_ENV=production
export SECRET_KEY="production-secret-key"
export DATABASE_PATH="/var/lib/app/db.sqlite3"
```

#### 8-2. ログローテーションの設定

cron で古いログを定期削除:

```bash
# crontab -e
0 3 * * * python -c "from modules.audit_log import audit_logger; audit_logger.cleanup_old_logs(90)"
```

#### 8-3. パフォーマンスチューニング

大量のログがある場合、インデックスを追加:

```sql
CREATE INDEX idx_audit_composite ON audit_logs(event_type, timestamp DESC);
CREATE INDEX idx_audit_user_timestamp ON audit_logs(user_id, timestamp DESC);
```

## トラブルシューティング

### エラー: ImportError: No module named 'audit'

**原因**: Blueprintのインポートパスが間違っている

**解決策**:
```python
# 間違い
from routes.audit import audit_bp

# 正しい
from app.routes.audit import audit_bp
```

### エラー: TemplateNotFound: admin/audit_logs.html

**原因**: テンプレートディレクトリの設定が間違っている

**解決策**:
```python
app = Flask(__name__, template_folder='../templates')
```

### エラー: sqlite3.OperationalError: no such table: audit_logs

**原因**: データベーステーブルが作成されていない

**解決策**:
```python
from modules.audit_log import audit_logger
# 初期化により自動でテーブル作成
audit_logger.log('system', 'Init', status='info')
```

### フィルタが動作しない

**原因**: URLパラメータの処理が正しくない

**解決策**: ブラウザの開発者ツールでネットワークタブを確認し、クエリパラメータが正しく送信されているか確認

## よくある質問

### Q: ログの保持期間は?
A: デフォルトは無期限。`cleanup_old_logs(days=90)` で90日以前のログを削除可能。

### Q: ログのバックアップ方法は?
A: SQLiteファイル全体をバックアップするか、CSVエクスポート機能を使用。

### Q: 大量のログがある場合のパフォーマンスは?
A: インデックスを適切に設定し、ページネーションで表示件数を制限することで対応可能。100万件程度まで問題なし。

### Q: 複数サーバーでのログ共有は?
A: 共有データベース（PostgreSQL、MySQL等）への移行を推奨。

## 次のステップ

1. **リアルタイム監視**: WebSocketでログをリアルタイム表示
2. **アラート設定**: 特定条件でメール通知
3. **ログ分析**: Elasticsearchとの統合
4. **ダッシュボード**: Chart.jsでグラフ表示
5. **監査レポート**: 定期的なPDFレポート生成

## サポート

問題が発生した場合は、以下を確認:

1. Flaskのデバッグモードでエラーメッセージを確認
2. ブラウザの開発者ツールでコンソールエラーを確認
3. SQLiteデータベースの整合性チェック
4. Python依存パッケージのバージョン確認

---

**最終更新**: 2025-12-07
**バージョン**: 1.0.0
