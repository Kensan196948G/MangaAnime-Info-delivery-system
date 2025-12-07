# Flask-Limiter レート制限実装ガイド

## 概要

Flask-Limiterを使用したAPIエンドポイントのレート制限実装です。
DDoS攻撃やブルートフォース攻撃から保護し、サーバーリソースを適切に管理します。

## 実装ファイル

### 1. コアモジュール

#### `app/utils/rate_limiter.py`
レート制限の初期化とヘルパー関数

```python
from app.utils.rate_limiter import init_limiter, get_rate_limit

# Flaskアプリケーションで初期化
limiter = init_limiter(app)

# エンドポイントに適用
@app.route('/api/endpoint')
@limiter.limit(get_rate_limit('api_collection'))
def endpoint():
    return jsonify({'status': 'ok'})
```

#### `config/ratelimit_config.py`
環境別の設定管理

```python
from config.ratelimit_config import RateLimitConfig

# 設定取得
login_limit = RateLimitConfig.get_limit('auth', 'login')
```

### 2. 認証ルート

#### `app/routes/auth_with_limiter.py`
認証関連エンドポイントのレート制限実装例

- ログイン: 5回/分
- ログアウト: 10回/分
- パスワードリセット: 3回/時間
- セッション更新: 10回/時間

### 3. Web アプリケーション統合

#### `app/web_app_limiter_integration.py`
既存のweb_app.pyへの統合サンプルコード

## レート制限設定

### デフォルト制限

```python
DEFAULT_LIMITS = ["200 per day", "50 per hour"]
```

### カテゴリ別制限

#### 認証関連
| エンドポイント | 制限 | 理由 |
|-----------|------|------|
| ログイン | 5回/分 | ブルートフォース攻撃防止 |
| パスワードリセット | 3回/時間 | 悪用防止 |
| セッション更新 | 10回/時間 | 過度なリクエスト防止 |

#### API関連
| カテゴリ | 制限 | 理由 |
|---------|------|------|
| 一般API | 100回/時間 | 通常利用 |
| データ収集 | 10回/時間 | サーバー負荷軽減 |
| スクレイピング | 5回/時間 | 外部サーバー保護 |

#### 設定変更
| カテゴリ | 制限 | 理由 |
|---------|------|------|
| 設定読取 | 50回/時間 | 通常利用 |
| 設定更新 | 30回/時間 | 誤操作防止 |

#### 通知・メール
| カテゴリ | 制限 | 理由 |
|---------|------|------|
| 通知送信 | 20回/時間 | スパム防止 |
| メール送信 | 10回/時間 | 配信制限 |

#### カレンダー
| カテゴリ | 制限 | 理由 |
|---------|------|------|
| 同期 | 15回/時間 | API制限対応 |
| 読取 | 50回/時間 | 通常利用 |

#### 管理者
| カテゴリ | 制限 | 理由 |
|---------|------|------|
| 一般操作 | 500回/時間 | 管理作業 |
| 読取 | 1000回/時間 | データ確認 |

## ストレージ設定

### 開発環境

```python
RATELIMIT_STORAGE_URI = 'memory://'
```

- メモリベースの簡易実装
- アプリケーション再起動でリセット
- 単一サーバー構成向け

### 本番環境

```python
RATELIMIT_STORAGE_URI = 'redis://localhost:6379'
```

- Redisを使用した永続化
- 複数サーバー間で共有可能
- スケーラブルな構成

## 使用方法

### 1. 依存関係のインストール

```bash
pip install Flask-Limiter>=3.5.0
```

### 2. 環境変数の設定

```bash
# 開発環境
export RATELIMIT_STORAGE_URI='memory://'

# 本番環境
export RATELIMIT_STORAGE_URI='redis://localhost:6379'
export REDIS_URL='redis://localhost:6379'
```

### 3. アプリケーションへの統合

```python
from flask import Flask
from app.utils.rate_limiter import init_limiter

app = Flask(__name__)

# レート制限の初期化
limiter = init_limiter(app)

# エンドポイントに適用
@app.route('/api/endpoint')
@limiter.limit("10 per hour")
def endpoint():
    return jsonify({'status': 'ok'})
```

### 4. カスタム制限の適用

```python
from app.utils.rate_limiter import get_rate_limit

@app.route('/api/collection')
@limiter.limit(get_rate_limit('api_collection'))
def collection():
    return jsonify({'status': 'started'})
```

## エラーハンドリング

### 429 Too Many Requests

レート制限を超えた場合、自動的に429エラーが返されます。

#### JSON APIの場合

```json
{
  "error": "Rate limit exceeded",
  "message": "リクエスト制限を超えました。しばらくしてから再試行してください。",
  "retry_after": "59 seconds"
}
```

#### Webページの場合

```python
# Flashメッセージで警告
flash('リクエスト回数が多すぎます。しばらくしてからお試しください。', 'warning')
# リファラーにリダイレクト
return redirect(request.referrer or url_for('index'))
```

## カスタマイズ

### ユーザー識別方法の変更

デフォルトではログインユーザーIDまたはIPアドレスで識別します。

```python
def get_user_identifier():
    from flask_login import current_user

    if current_user and current_user.is_authenticated:
        return f"user:{current_user.id}"
    return f"ip:{get_remote_address()}"
```

### 制限値の変更

`config/ratelimit_config.py`を編集:

```python
AUTH_LIMITS = {
    'login': "10 per minute",  # 5 -> 10 に変更
    ...
}
```

### 動的な制限値

```python
@app.route('/api/endpoint')
@limiter.limit(lambda: current_user.rate_limit if current_user.is_authenticated else "10 per hour")
def endpoint():
    return jsonify({'status': 'ok'})
```

## テスト

### ユニットテスト

```bash
pytest tests/test_rate_limiter.py -v
```

### 統合テスト

```bash
pytest tests/test_rate_limiter.py::TestRateLimiterIntegration -v
```

### カバレッジ

```bash
pytest tests/test_rate_limiter.py --cov=app.utils.rate_limiter --cov-report=html
```

## パフォーマンス

### メモリ使用量

- メモリストレージ: 軽量（数MB程度）
- Redisストレージ: 100,000エントリで約10MB

### レスポンス時間

- オーバーヘッド: < 1ms
- Redis使用時: < 5ms

## トラブルシューティング

### 問題: レート制限が機能しない

**確認事項:**
1. Flask-Limiterがインストールされているか
2. `init_limiter(app)`が実行されているか
3. デコレータの順序が正しいか

```python
# 正しい順序
@app.route('/endpoint')
@login_required
@limiter.limit("10 per hour")
def endpoint():
    pass
```

### 問題: Redis接続エラー

**解決方法:**
1. Redisサーバーが起動しているか確認
2. 接続URLが正しいか確認
3. fallbackとしてメモリストレージを使用

```python
RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL', 'memory://')
```

### 問題: 開発中に制限が邪魔

**解決方法:**
テスト環境では制限を無効化

```python
if app.config['TESTING']:
    limiter.enabled = False
```

## セキュリティ考慮事項

### 1. IPスプーフィング対策

```python
# X-Forwarded-Forヘッダーを信頼する設定
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
```

### 2. 分散環境での共有

本番環境では必ずRedisを使用し、複数サーバー間で制限を共有してください。

### 3. ログ記録

```python
@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning(f"Rate limit exceeded: {request.remote_addr} - {request.endpoint}")
    ...
```

## 参考資料

- [Flask-Limiter公式ドキュメント](https://flask-limiter.readthedocs.io/)
- [Redis公式サイト](https://redis.io/)
- [OWASP Rate Limiting](https://owasp.org/www-community/controls/Blocking_Brute_Force_Attacks)

## 更新履歴

- 2025-12-07: 初版作成
- Flask-Limiter 3.5.0対応
- Redis/メモリストレージ対応

---

**作成者**: Backend Developer Agent
**最終更新**: 2025-12-07
