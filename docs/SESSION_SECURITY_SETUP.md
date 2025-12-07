# セッションセキュリティ設定ガイド

## 概要

このドキュメントでは、MangaAnime-Info-delivery-systemにおけるFlaskセッション管理の強化について説明します。

## 実装内容

### 1. セキュリティ設定 (`app/utils/security.py`)

#### 主要機能
- **セッションCookie設定**
  - `SESSION_COOKIE_SECURE`: HTTPS通信のみでCookieを送信
  - `SESSION_COOKIE_HTTPONLY`: JavaScriptからのアクセス防止（XSS対策）
  - `SESSION_COOKIE_SAMESITE`: CSRF攻撃の補完的防御
  - `PERMANENT_SESSION_LIFETIME`: セッション有効期限（2時間）

- **Flask-Session（サーバーサイドセッション）**
  - 開発環境: ファイルベースセッション
  - 本番環境: Redis推奨

- **セキュリティヘッダー**
  - X-Content-Type-Options
  - X-Frame-Options
  - X-XSS-Protection
  - Strict-Transport-Security
  - Content-Security-Policy

### 2. 使用方法

#### app/web_app.py への統合

```python
from app.utils.security import SecurityConfig, DevelopmentSecurityConfig

# 環境判定
ENV = os.environ.get('FLASK_ENV', 'development')
app.config['ENV'] = ENV

# セキュリティ設定適用
if ENV == 'production':
    SecurityConfig.init_app(app)
else:
    DevelopmentSecurityConfig.init_app(app)
```

#### 環境変数設定

**開発環境**
```bash
export FLASK_ENV=development
export SECRET_KEY=your-development-secret-key
```

**本番環境**
```bash
export FLASK_ENV=production
export SECRET_KEY=your-production-secret-key-change-this
export REDIS_URL=redis://localhost:6379
```

### 3. Flask-Session インストール

```bash
pip install Flask-Session>=0.5.0
```

または

```bash
pip install -r requirements.txt
```

### 4. セッションストレージ

#### 開発環境（ファイルベース）

セッションデータは `flask_session/` ディレクトリに保存されます。

```
MangaAnime-Info-delivery-system/
├── flask_session/          # セッションファイル（自動生成）
│   ├── 2f7a8b9c...
│   └── 3e8d9f0a...
```

**注意**: `.gitignore` に `flask_session/` を追加してください。

#### 本番環境（Redis）

Redisのインストールと起動:

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# macOS (Homebrew)
brew install redis
brew services start redis
```

Redis接続確認:
```bash
redis-cli ping
# PONG が返ればOK
```

### 5. セキュリティチェックリスト

- [ ] SECRET_KEY を本番環境で変更
- [ ] HTTPS証明書の設定（本番環境）
- [ ] Redis のパスワード設定（本番環境）
- [ ] flask_session/ を .gitignore に追加
- [ ] セッションタイムアウトの調整
- [ ] CORS設定の確認（API利用時）

### 6. トラブルシューティング

#### セッションが保存されない

**原因**: Flask-Session未インストール

**解決策**:
```bash
pip install Flask-Session
```

#### HTTPS環境でCookieが送信されない

**原因**: `SESSION_COOKIE_SECURE=True` がHTTP環境で有効

**解決策**: 開発環境では `DevelopmentSecurityConfig` を使用
```python
DevelopmentSecurityConfig.init_app(app)
```

#### Redisに接続できない

**原因**: Redis未起動またはURL誤り

**解決策**:
```bash
# Redis起動確認
sudo systemctl status redis-server

# 環境変数確認
echo $REDIS_URL
```

### 7. テスト方法

#### セッションセキュリティテスト

```python
# tests/test_session_security.py
import pytest
from app.web_app import app

def test_session_cookie_secure():
    """SESSION_COOKIE_SECUREが設定されているか"""
    assert app.config['SESSION_COOKIE_SECURE'] is True

def test_session_cookie_httponly():
    """SESSION_COOKIE_HTTPONLYが設定されているか"""
    assert app.config['SESSION_COOKIE_HTTPONLY'] is True

def test_session_cookie_samesite():
    """SESSION_COOKIE_SAMESITEが設定されているか"""
    assert app.config['SESSION_COOKIE_SAMESITE'] in ['Lax', 'Strict']
```

実行:
```bash
pytest tests/test_session_security.py -v
```

### 8. 参考資料

- [Flask Session Management](https://flask.palletsprojects.com/en/3.0.x/quickstart/#sessions)
- [Flask-Session Documentation](https://flask-session.readthedocs.io/)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [Redis Documentation](https://redis.io/docs/)

### 9. 更新履歴

| 日付 | バージョン | 変更内容 |
|------|----------|---------|
| 2025-12-07 | 1.0.0 | 初版作成 |

---

**重要**: 本番環境では必ず `FLASK_ENV=production` を設定し、HTTPSを有効化してください。
