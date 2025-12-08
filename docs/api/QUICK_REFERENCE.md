# API クイックリファレンス

MangaAnime Information Delivery System APIの主要エンドポイント早見表

## 目次

- [認証](#認証)
- [作品管理](#作品管理)
- [リリース情報](#リリース情報)
- [ウォッチリスト](#ウォッチリスト)
- [カレンダー](#カレンダー)
- [データ収集](#データ収集)
- [ヘルスチェック](#ヘルスチェック)

---

## 認証

### ログイン
```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}
```

### ログアウト
```http
POST /auth/logout
Cookie: session=xxx
```

### ユーザー登録
```http
POST /auth/register
Content-Type: application/json

{
  "username": "newuser",
  "password": "secure123",
  "email": "user@example.com"
}
```

---

## 作品管理

### 作品一覧取得
```http
GET /api/works?type=anime&limit=20&offset=0&sort=created_at_desc
X-API-Key: your-api-key
```

**パラメータ:**
- `type`: `anime` | `manga`
- `limit`: 1-100 (デフォルト: 50)
- `offset`: ページネーション用
- `sort`: `created_at_desc` | `created_at_asc` | `title_asc` | `title_desc`
- `search`: タイトル検索キーワード

**レスポンス例:**
```json
{
  "success": true,
  "count": 20,
  "total": 150,
  "works": [
    {
      "id": 1,
      "title": "鬼滅の刃",
      "title_en": "Demon Slayer",
      "type": "anime",
      "official_url": "https://kimetsu.com",
      "status": "ongoing"
    }
  ]
}
```

### 作品詳細取得
```http
GET /api/works/{workId}
X-API-Key: your-api-key
```

**レスポンス例:**
```json
{
  "success": true,
  "work": {
    "id": 1,
    "title": "鬼滅の刃",
    "type": "anime",
    "description": "...",
    "image_url": "https://..."
  },
  "releases": [
    {
      "id": 101,
      "release_type": "episode",
      "number": "1",
      "platform": "dアニメストア",
      "release_date": "2025-12-08"
    }
  ],
  "statistics": {
    "total_episodes": 26,
    "latest_release_date": "2025-12-08"
  }
}
```

---

## リリース情報

### 最近のリリース
```http
GET /api/releases/recent?days=7&type=anime
X-API-Key: your-api-key
```

**パラメータ:**
- `days`: 1-30 (デフォルト: 7)
- `type`: `anime` | `manga`

### 今後のリリース予定
```http
GET /api/releases/upcoming?days=7
X-API-Key: your-api-key
```

**レスポンス例:**
```json
{
  "success": true,
  "count": 15,
  "releases": [
    {
      "id": 101,
      "work_id": 1,
      "release_type": "episode",
      "number": "2",
      "platform": "Netflix",
      "release_date": "2025-12-15",
      "work": {
        "id": 1,
        "title": "鬼滅の刃",
        "type": "anime"
      }
    }
  ]
}
```

---

## ウォッチリスト

### ウォッチリスト一覧
```http
GET /watchlist/api/list
Cookie: session=xxx
```

**レスポンス例:**
```json
{
  "success": true,
  "count": 5,
  "watchlist": [
    {
      "id": 1,
      "work_id": 1,
      "notify_new_episodes": true,
      "notify_new_volumes": false,
      "priority": 3,
      "work": {
        "id": 1,
        "title": "鬼滅の刃",
        "type": "anime"
      }
    }
  ]
}
```

### 作品を追加
```http
POST /watchlist/api/add
Cookie: session=xxx
Content-Type: application/json

{
  "work_id": 1
}
```

### 作品を削除
```http
DELETE /watchlist/api/remove/{workId}
Cookie: session=xxx
```

### 通知設定を更新
```http
PUT /watchlist/api/update/{workId}
Cookie: session=xxx
Content-Type: application/json

{
  "notify_new_episodes": true,
  "notify_new_volumes": false
}
```

### ウォッチリスト統計
```http
GET /watchlist/api/stats
Cookie: session=xxx
```

**レスポンス例:**
```json
{
  "success": true,
  "stats": {
    "total": 10,
    "anime": 6,
    "manga": 4,
    "notify_episodes": 8,
    "notify_volumes": 5
  }
}
```

### 登録確認
```http
GET /watchlist/api/check/{workId}
Cookie: session=xxx
```

---

## カレンダー

### カレンダー同期実行
```http
POST /api/calendar/sync
Cookie: session=xxx
```

**レスポンス例:**
```json
{
  "success": true,
  "synced_count": 15,
  "failed_count": 2,
  "message": "カレンダーに15件のイベントを同期しました"
}
```

### カレンダーイベント一覧
```http
GET /api/calendar/events?start_date=2025-12-01&end_date=2025-12-31
Cookie: session=xxx
```

### カレンダー統計
```http
GET /api/calendar/stats
Cookie: session=xxx
```

**レスポンス例:**
```json
{
  "success": true,
  "stats": {
    "total_events": 100,
    "synced_events": 95,
    "pending_sync": 5,
    "last_sync": "2025-12-08T10:30:00Z"
  }
}
```

---

## データ収集

### 手動データ収集
```http
POST /api/manual-collection
Cookie: session=xxx
Content-Type: application/json

{
  "source": "anilist"
}
```

**sourceオプション:**
- `all`: 全ソース
- `anilist`: AniList API
- `rss`: 一般RSS
- `bookwalker`: BookWalker RSS
- `danime`: dアニメストア RSS

**レスポンス例:**
```json
{
  "success": true,
  "job_id": "job_20251208_103000_abc1",
  "message": "データ収集を開始しました"
}
```

### 収集ステータス確認
```http
GET /api/collection-status
Cookie: session=xxx
```

**レスポンス例:**
```json
{
  "status": "running",
  "current_job": {
    "job_id": "job_20251208_103000_abc1",
    "started_at": "2025-12-08T10:30:00Z",
    "progress": 0.65,
    "collected_items": 50
  }
}
```

### データソース一覧
```http
GET /api/sources
Cookie: session=xxx
```

**レスポンス例:**
```json
{
  "success": true,
  "sources": [
    {
      "id": "anilist",
      "name": "AniList API",
      "type": "api",
      "status": "active",
      "last_run": "2025-12-08T10:00:00Z",
      "success_rate": 0.98,
      "items_collected": 1500
    }
  ]
}
```

---

## ヘルスチェック

### 基本ヘルスチェック
```http
GET /health
```

**レスポンス例:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-08T10:30:00Z",
  "service": "manga-anime-info-system"
}
```

### Readiness Probe
```http
GET /health/ready
```

### Liveness Probe
```http
GET /health/live
```

### 詳細ヘルスチェック
```http
GET /health/detailed
```

**レスポンス例:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-08T10:30:00Z",
  "version": "1.0.0",
  "environment": "production",
  "uptime": {
    "started_at": "2025-12-08T00:00:00Z",
    "uptime_seconds": 37800,
    "uptime_human": "10:30:00"
  },
  "checks": {
    "database": {
      "status": "healthy",
      "works_count": 150,
      "releases_count": 500
    },
    "config": {
      "status": "healthy",
      "config_loaded": true
    },
    "disk": {
      "status": "healthy",
      "free_human": "50.25 GB",
      "used_percent": 65.5
    },
    "memory": {
      "status": "healthy",
      "max_rss_human": "128.50 MB"
    }
  }
}
```

### Prometheusメトリクス
```http
GET /metrics
```

**レスポンス例:**
```
# HELP mangaanime_uptime_seconds Application uptime in seconds
# TYPE mangaanime_uptime_seconds gauge
mangaanime_uptime_seconds 37800

# HELP mangaanime_works_total Total number of works in database
# TYPE mangaanime_works_total gauge
mangaanime_works_total 150

# HELP mangaanime_releases_total Total number of releases in database
# TYPE mangaanime_releases_total gauge
mangaanime_releases_total 500
```

---

## 統計情報

### システム統計
```http
GET /api/stats
X-API-Key: your-api-key
```

**レスポンス例:**
```json
{
  "success": true,
  "stats": {
    "total_works": 150,
    "total_releases": 500,
    "anime_count": 90,
    "manga_count": 60,
    "recent_releases": 25,
    "upcoming_releases": 30
  }
}
```

### 通知ステータス
```http
GET /api/notification-status
Cookie: session=xxx
```

**レスポンス例:**
```json
{
  "success": true,
  "status": {
    "pending_notifications": 10,
    "last_notification": "2025-12-08T08:00:00Z",
    "total_sent_today": 45,
    "success_rate": 0.96
  }
}
```

---

## APIキー管理

### APIキー一覧（JSON）
```http
GET /api-keys/api/list
Cookie: session=xxx
```

### APIキー生成
```http
POST /api-keys/generate
Cookie: session=xxx
Content-Type: application/x-www-form-urlencoded

name=MyAPIKey&permissions=read,write
```

### APIキー無効化
```http
POST /api-keys/revoke/{key}
Cookie: session=xxx
```

---

## ユーザー管理（管理者のみ）

### ユーザー統計
```http
GET /users/api/stats
Cookie: session=xxx
```

**レスポンス例:**
```json
{
  "total_users": 25,
  "admin_users": 3,
  "regular_users": 22
}
```

---

## エラーレスポンス

全てのエラーレスポンスは以下の形式:

```json
{
  "success": false,
  "error": "Error Type",
  "message": "詳細なエラーメッセージ（日本語）",
  "details": {
    "field": "追加情報"
  }
}
```

### 一般的なステータスコード

| コード | 説明 |
|------|------|
| 200 | 成功 |
| 201 | 作成成功 |
| 400 | リクエストが不正 |
| 401 | 認証が必要 |
| 403 | アクセス権限なし |
| 404 | リソースが見つからない |
| 409 | 競合（既に存在） |
| 429 | レート制限超過 |
| 500 | サーバーエラー |
| 503 | サービス利用不可 |

---

## Tips

### 1. デバッグ用のヘッダー

```bash
curl -v http://localhost:5000/api/works \
  -H "X-API-Key: your-key" \
  -H "X-Request-ID: debug-123"
```

### 2. JSONの整形

```bash
curl http://localhost:5000/api/works | jq .
```

### 3. レスポンスタイムの測定

```bash
curl -w "\nTime: %{time_total}s\n" \
  http://localhost:5000/api/works
```

### 4. 大量データの取得

```bash
# ページネーションを使用
for i in {0..10}; do
  offset=$((i * 50))
  curl "http://localhost:5000/api/works?limit=50&offset=$offset"
done
```

### 5. 並列リクエスト

```bash
# GNU parallelを使用
parallel -j 5 curl ::: \
  http://localhost:5000/api/works \
  http://localhost:5000/api/releases/recent \
  http://localhost:5000/api/stats \
  http://localhost:5000/health/detailed \
  http://localhost:5000/api/calendar/stats
```

---

## 関連ドキュメント

- [詳細なAPI仕様書](./openapi.yaml)
- [API使用ガイド](./README.md)
- [システムアーキテクチャ](../technical/)
- [セットアップガイド](../setup/)

---

最終更新: 2025-12-08
