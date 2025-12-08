# API Overview - MangaAnime Information Delivery System

## システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│  (Web Browser, Mobile App, CLI Tools, External Services)    │
└────────────┬────────────────────────────────────────────────┘
             │
             │ HTTP/HTTPS
             │
┌────────────▼────────────────────────────────────────────────┐
│                      Flask Web Server                        │
│                     (Port 5000/HTTPS)                        │
├──────────────────────────────────────────────────────────────┤
│  Authentication Layer                                         │
│  ├─ Session-based (Cookie)                                   │
│  └─ API Key (X-API-Key header)                              │
├──────────────────────────────────────────────────────────────┤
│  Rate Limiting (Flask-Limiter)                               │
│  └─ 200 req/day, 50 req/hour (default)                      │
├──────────────────────────────────────────────────────────────┤
│  Security Headers                                             │
│  ├─ CSRF Protection                                          │
│  ├─ XSS Protection                                           │
│  └─ Content Security Policy                                  │
└────────────┬────────────────────────────────────────────────┘
             │
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐    ┌──────▼──────┐
│ SQLite │    │   Modules   │
│  DB    │    │  (Business  │
│        │    │    Logic)   │
└───┬────┘    └──────┬──────┘
    │                │
    │                │
    │         ┌──────▼──────────────┐
    │         │  External APIs       │
    │         ├──────────────────────┤
    │         │ - AniList GraphQL   │
    │         │ - RSS Feeds         │
    │         │ - Google Calendar   │
    │         │ - Gmail API         │
    │         └─────────────────────┘
    │
    │
┌───▼─────────────────────────────────────┐
│          Database Schema                 │
├──────────────────────────────────────────┤
│ - works (作品)                           │
│ - releases (リリース)                    │
│ - users (ユーザー)                       │
│ - watchlist (ウォッチリスト)             │
│ - calendar_events (カレンダー)          │
│ - notification_logs (通知ログ)          │
│ - audit_logs (監査ログ)                 │
└──────────────────────────────────────────┘
```

## APIエンドポイント構成

### 1. Health & Monitoring (公開)
```
/health                  基本ヘルスチェック
/health/live            Liveness probe
/health/ready           Readiness probe
/health/detailed        詳細ヘルスチェック
/metrics                Prometheusメトリクス
```

### 2. Authentication (公開 + 要認証)
```
/auth/login             ログイン
/auth/logout            ログアウト
/auth/register          ユーザー登録
/auth/password-reset    パスワードリセット
```

### 3. Works (要認証)
```
GET    /api/works                作品一覧
GET    /api/works/{id}           作品詳細
POST   /api/works                作品登録 (管理者)
PUT    /api/works/{id}           作品更新 (管理者)
DELETE /api/works/{id}           作品削除 (管理者)
```

### 4. Releases (要認証)
```
GET /api/releases/recent         最近のリリース
GET /api/releases/upcoming       今後の予定
GET /api/releases/{id}           リリース詳細
```

### 5. Watchlist (要認証)
```
GET    /watchlist/api/list               一覧
POST   /watchlist/api/add                追加
DELETE /watchlist/api/remove/{workId}    削除
PUT    /watchlist/api/update/{workId}    設定更新
GET    /watchlist/api/check/{workId}     登録確認
GET    /watchlist/api/stats              統計
```

### 6. Calendar (要認証)
```
POST /api/calendar/sync          カレンダー同期
GET  /api/calendar/events        イベント一覧
GET  /api/calendar/stats         統計情報
GET  /api/calendar/monthly       月次カレンダー
```

### 7. Collection (要認証)
```
POST /api/manual-collection      手動収集トリガー
GET  /api/collection-status      収集ステータス
GET  /api/sources                ソース一覧
POST /api/sources/toggle         ソース有効化切替
POST /api/sources/test-all       全ソーステスト
```

### 8. API Keys (要認証)
```
GET    /api-keys/api/list        APIキー一覧
POST   /api-keys/generate        APIキー生成
POST   /api-keys/revoke/{key}    APIキー無効化
```

### 9. Users (管理者のみ)
```
GET    /users/                   ユーザー一覧
POST   /users/create             ユーザー作成
DELETE /users/{id}/delete        ユーザー削除
POST   /users/{id}/toggle-admin  管理者権限切替
GET    /users/api/stats          ユーザー統計
```

### 10. Statistics (要認証)
```
GET /api/stats                   システム統計
GET /api/notification-status     通知ステータス
GET /api/collection-stats        収集統計
```

## データフロー

### 1. データ収集フロー
```
External APIs → Collection Modules → Data Normalizer
    ↓
Filter Logic → Database (works, releases)
    ↓
Dashboard Integration → Metrics
```

### 2. 通知フロー
```
Scheduled Job (cron) → Check Pending Notifications
    ↓
Pending Releases → Email Notifier (Gmail API)
    ↓                    ↓
Calendar Manager     Update notified flag
    ↓
Google Calendar API
```

### 3. リクエストフロー（認証あり）
```
Client Request
    ↓
Rate Limiter Check
    ↓
Authentication (Session/API Key)
    ↓
Authorization (Permissions)
    ↓
CSRF Validation (if POST/PUT/DELETE)
    ↓
Route Handler
    ↓
Business Logic (Modules)
    ↓
Database Query
    ↓
JSON Response
```

## 認証・認可システム

### セッション認証フロー
```
1. POST /auth/login
   ├─ Username/Password validation
   ├─ Password hash verification (bcrypt)
   └─ Session creation (Flask-Login)

2. Cookie設定
   ├─ HttpOnly: true
   ├─ SameSite: Lax
   └─ Secure: true (production)

3. 認証状態の維持
   └─ Flask-Loginによる自動セッション管理
```

### APIキー認証フロー
```
1. APIキー生成
   ├─ POST /api-keys/generate
   ├─ ランダムキー生成 (secrets.token_urlsafe)
   └─ データベースに保存 (api_keys table)

2. リクエスト時
   ├─ Header: X-API-Key または
   ├─ Query: ?api_key=xxx
   └─ キー検証 (active & permissions)

3. 権限チェック
   ├─ read: 読み取り操作
   ├─ write: 書き込み操作
   └─ admin: 管理者操作
```

## セキュリティ機能

### 実装済み
- ✅ CSRF保護 (Flask-WTF)
- ✅ XSS保護ヘッダー
- ✅ SQLインジェクション対策 (Parameterized queries)
- ✅ パスワードハッシュ (bcrypt)
- ✅ セッション管理 (Flask-Login)
- ✅ レート制限 (Flask-Limiter)
- ✅ セキュリティヘッダー (CSP, X-Frame-Options等)
- ✅ 監査ログ (audit_logs table)
- ✅ 環境変数による秘密情報管理

### 推奨する追加対策
- 🔲 API Gatewayの導入
- 🔲 OAuth2.0サポート
- 🔲 JWTトークン認証
- 🔲 Two-Factor Authentication (2FA)
- 🔲 IPホワイトリスト
- 🔲 Request signing

## パフォーマンス最適化

### データベース
- インデックスの最適化
  - works: title, type, created_at
  - releases: work_id, release_date, notified
  - watchlist: user_id, work_id

### キャッシュ戦略
```python
# API Status Cache (30秒)
api_status_cache = {
    "data": None,
    "timestamp": 0
}
CACHE_DURATION = 30
```

### レート制限
```python
# デフォルト設定
default_limits = [
    "200 per day",
    "50 per hour"
]

# エンドポイント別設定
@limiter.limit("10 per minute")
def high_frequency_endpoint():
    pass
```

## 監視とログ

### ログファイル
```
logs/
├── dashboard_system.log    システムログ
├── error.log              エラーログ
└── access.log             アクセスログ
```

### メトリクス
```
# Prometheus形式
mangaanime_uptime_seconds           アップタイム
mangaanime_works_total              作品総数
mangaanime_releases_total           リリース総数
mangaanime_database_healthy         DB健全性
mangaanime_requests_total           リクエスト総数
mangaanime_request_duration_seconds リクエスト時間
```

### ヘルスチェックエンドポイント
```bash
# Kubernetes Liveness
curl http://localhost:5000/health/live

# Kubernetes Readiness
curl http://localhost:5000/health/ready

# 詳細チェック
curl http://localhost:5000/health/detailed
```

## エラーハンドリング

### 標準エラーレスポンス
```json
{
  "success": false,
  "error": "Error Type",
  "message": "ユーザー向けメッセージ（日本語）",
  "details": {
    "field": "field_name",
    "reason": "詳細理由"
  }
}
```

### HTTPステータスコード使い分け
```
200 OK                  成功
201 Created             リソース作成成功
400 Bad Request         リクエストエラー
401 Unauthorized        認証エラー
403 Forbidden           権限エラー
404 Not Found           リソース不在
409 Conflict            競合エラー
429 Too Many Requests   レート制限超過
500 Internal Error      サーバーエラー
503 Service Unavailable サービス停止中
```

## 開発・テスト環境

### ローカル開発
```bash
# 開発サーバー起動
python app/web_app.py

# テスト実行
pytest tests/

# API仕様書確認
open docs/api/openapi.yaml
```

### Dockerコンテナ
```bash
# ビルド
docker build -t mangaanime-api .

# 実行
docker run -p 5000:5000 \
  -e SECRET_KEY=xxx \
  -e DATABASE_PATH=/data/db.sqlite3 \
  mangaanime-api
```

### CI/CD
```yaml
# GitHub Actions例
- name: Test API
  run: |
    pytest tests/test_api.py
    spectral lint docs/api/openapi.yaml
```

## バージョニング

現在のバージョン: **1.0.0**

### 今後の予定
- v1.1: GraphQL APIサポート
- v1.2: WebSocket通知
- v2.0: マイクロサービス化

## サポートとコントリビューション

### ドキュメント
- OpenAPI仕様書: `docs/api/openapi.yaml`
- 使用ガイド: `docs/api/README.md`
- クイックリファレンス: `docs/api/QUICK_REFERENCE.md`

### 問い合わせ
- GitHub Issues
- Email: support@example.com

### ライセンス
MIT License

---

最終更新: 2025-12-08
作成者: OpenAPI Documentation Specialist (Claude Agent)
