# セッションセキュリティ強化インストールガイド

## クイックスタート

### 1. 自動インストール（推奨）

```bash
# スクリプトに実行権限を付与
chmod +x scripts/install_session_security.sh

# インストール実行
./scripts/install_session_security.sh
```

### 2. 手動インストール

```bash
# Flask-Session インストール
pip install Flask-Session>=0.5.0

# Redis（本番環境用、オプション）
pip install redis>=5.0.0

# セッションディレクトリ作成
mkdir -p flask_session

# .gitignore 更新
cat .gitignore.session >> .gitignore
```

## 環境変数設定

### 開発環境

```bash
export FLASK_ENV=development
export SECRET_KEY=dev-secret-key-$(openssl rand -hex 16)
```

### 本番環境

```bash
export FLASK_ENV=production
export SECRET_KEY=$(openssl rand -hex 32)
export REDIS_URL=redis://localhost:6379  # Redisを使用する場合
```

## 統合

### app/web_app.py への統合

詳細は `docs/WEB_APP_INTEGRATION_GUIDE.md` を参照してください。

最小限の統合例:

```python
from app.utils.security import SecurityConfig, DevelopmentSecurityConfig

ENV = os.environ.get('FLASK_ENV', 'development')
app.config['ENV'] = ENV

if ENV == 'production':
    SecurityConfig.init_app(app)
else:
    DevelopmentSecurityConfig.init_app(app)
```

## テスト実行

```bash
# セキュリティ設定テスト
pytest tests/test_session_security.py -v

# 全テスト実行
pytest tests/ -v
```

## 動作確認

```bash
# アプリケーション起動
python app/web_app.py

# ログで確認
# 開発環境: "Session security: DISABLED (HTTP)"
# 本番環境: "Session security: ENABLED"
```

## ファイル一覧

作成されたファイル:

```
MangaAnime-Info-delivery-system/
├── app/
│   └── utils/
│       ├── __init__.py                  # パッケージ初期化
│       └── security.py                  # セキュリティ設定モジュール
├── tests/
│   └── test_session_security.py         # セキュリティテスト
├── scripts/
│   └── install_session_security.sh      # 自動インストールスクリプト
├── docs/
│   ├── SESSION_SECURITY_SETUP.md        # 詳細セットアップガイド
│   └── WEB_APP_INTEGRATION_GUIDE.md     # 統合ガイド
├── requirements-session.txt             # 追加依存関係
├── .gitignore.session                   # .gitignore追加内容
└── INSTALL_SESSION_SECURITY.md          # このファイル
```

## 次のステップ

1. **Flask-Login統合**: `app/routes/auth.py` との統合
2. **CSRF保護**: Flask-WTFの導入検討
3. **Redis設定**: 本番環境でのRedis導入
4. **HTTPS設定**: 本番環境でのSSL/TLS設定

## トラブルシューティング

問題が発生した場合は `docs/SESSION_SECURITY_SETUP.md` の「トラブルシューティング」セクションを参照してください。

## サポート

- ドキュメント: `docs/SESSION_SECURITY_SETUP.md`
- 統合ガイド: `docs/WEB_APP_INTEGRATION_GUIDE.md`
- テストコード: `tests/test_session_security.py`

---

**最終更新**: 2025-12-07
