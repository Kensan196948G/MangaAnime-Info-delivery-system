# web_app.py セキュリティ統合ガイド

## 概要

既存の `app/web_app.py` にセッションセキュリティ機能を統合する手順を説明します。

## 統合手順

### 1. インポート追加

`app/web_app.py` の冒頭に以下を追加:

```python
from datetime import timedelta  # 既存のdatetimeインポートに追加
from app.utils.security import SecurityConfig, DevelopmentSecurityConfig
```

### 2. 環境判定の追加

Flaskアプリケーション作成後、セキュリティ設定適用前に追加:

```python
app = Flask(__name__, static_folder='static', template_folder='templates')

# 環境判定（この行を追加）
ENV = os.environ.get('FLASK_ENV', 'development')
app.config['ENV'] = ENV
```

### 3. セキュリティ設定の適用

既存の `SECRET_KEY` 設定の後に追加:

```python
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# セキュリティ設定適用（この部分を追加）
if ENV == 'production':
    SecurityConfig.init_app(app)
else:
    DevelopmentSecurityConfig.init_app(app)
```

## 完全な統合例

```python
from flask import Flask, render_template, jsonify, request, send_from_directory
from modules.db import Database
import os
import logging
from datetime import datetime, timedelta
import sys
from pathlib import Path

# プロジェクトルートのmodulesをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.config import Config
from app.utils.security import SecurityConfig, DevelopmentSecurityConfig

app = Flask(__name__, static_folder='static', template_folder='templates')

# 環境判定
ENV = os.environ.get('FLASK_ENV', 'development')
app.config['ENV'] = ENV

# 基本設定
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# セキュリティ設定適用
if ENV == 'production':
    SecurityConfig.init_app(app)
else:
    DevelopmentSecurityConfig.init_app(app)

# 以下、既存のコードをそのまま継続...
```

## 動作確認

### 1. 開発環境での起動

```bash
export FLASK_ENV=development
export SECRET_KEY=dev-secret-key
python app/web_app.py
```

起動ログで確認:
```
Session security: DISABLED (HTTP)
```

### 2. 本番環境での起動

```bash
export FLASK_ENV=production
export SECRET_KEY=production-secret-key-change-this
python app/web_app.py
```

起動ログで確認:
```
Session security: ENABLED
```

### 3. セッション動作確認

Pythonインタラクティブシェルで:

```python
from app.web_app import app

# 設定確認
print(f"SESSION_COOKIE_SECURE: {app.config.get('SESSION_COOKIE_SECURE')}")
print(f"SESSION_COOKIE_HTTPONLY: {app.config.get('SESSION_COOKIE_HTTPONLY')}")
print(f"SESSION_COOKIE_SAMESITE: {app.config.get('SESSION_COOKIE_SAMESITE')}")
print(f"SESSION_TYPE: {app.config.get('SESSION_TYPE')}")
```

期待される出力（開発環境）:
```
SESSION_COOKIE_SECURE: False
SESSION_COOKIE_HTTPONLY: True
SESSION_COOKIE_SAMESITE: Lax
SESSION_TYPE: filesystem
```

## トラブルシューティング

### ImportError: cannot import name 'SecurityConfig'

**原因**: `app/utils/__init__.py` が存在しないか、正しく設定されていない

**解決策**:
```bash
# app/utils/__init__.py を確認
cat app/utils/__init__.py
```

内容が以下と一致するか確認:
```python
from .security import SecurityConfig, DevelopmentSecurityConfig
__all__ = ['SecurityConfig', 'DevelopmentSecurityConfig']
```

### ModuleNotFoundError: No module named 'flask_session'

**原因**: Flask-Session未インストール

**解決策**:
```bash
pip install Flask-Session>=0.5.0
```

### セッションが保存されない

**原因**: `flask_session/` ディレクトリの権限エラー

**解決策**:
```bash
mkdir -p flask_session
chmod 755 flask_session
```

## 統合チェックリスト

- [ ] `app/utils/security.py` が存在する
- [ ] `app/utils/__init__.py` が存在する
- [ ] `Flask-Session>=0.5.0` がインストール済み
- [ ] `flask_session/` ディレクトリが作成済み
- [ ] `.gitignore` に `flask_session/` を追加済み
- [ ] 環境変数 `FLASK_ENV` が設定済み
- [ ] 環境変数 `SECRET_KEY` が設定済み
- [ ] テストが通る（`pytest tests/test_session_security.py`）

## 次のステップ

1. **Flask-Login統合**: 既存の `app/routes/auth.py` との統合
2. **CSRF保護**: Flask-WTFの導入
3. **Redis設定**: 本番環境でのRedisセッション設定

詳細は `docs/SESSION_SECURITY_SETUP.md` を参照してください。

---

**最終更新**: 2025-12-07
