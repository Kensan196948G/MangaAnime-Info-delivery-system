# MangaAnime情報配信システム API ガイド

**バージョン:** 1.0.0
**最終更新:** 2025-12-08

---

## 目次

1. [概要](#概要)
2. [認証方式](#認証方式)
3. [エンドポイント一覧](#エンドポイント一覧)
4. [使用例](#使用例)
5. [エラーハンドリング](#エラーハンドリング)
6. [レート制限](#レート制限)
7. [ベストプラクティス](#ベストプラクティス)

---

## 概要

MangaAnime情報配信システムは、アニメとマンガの最新リリース情報を自動収集し、ユーザーに通知するシステムです。このAPIを使用することで、作品情報の取得、ウォッチリストの管理、リリース情報の検索などが可能になります。

### 主な機能

- **作品管理**: アニメ・マンガ作品の検索と詳細情報取得
- **リリース情報**: エピソードや巻の配信・発売情報の取得
- **ウォッチリスト**: お気に入り作品の登録と通知設定
- **カレンダー連携**: Googleカレンダーとの同期
- **ユーザー管理**: アカウント管理とAPIキー発行
- **システム監視**: ヘルスチェックと統計情報

### ベースURL

```
開発環境: http://localhost:5000
本番環境: https://api.mangaanime.example.com
```

---

## 認証方式

### 1. セッションベース認証（推奨：Web UI利用時）

Web UIからログインすると、セッションCookieが自動的に設定されます。

**ログイン:**

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your_password" \
  -c cookies.txt
```

**認証済みリクエスト:**

```bash
curl http://localhost:5000/api/works \
  -b cookies.txt
```

### 2. APIキー認証（推奨：プログラマティック利用）

#### APIキーの取得方法

1. Web UIにログイン
2. `/api-keys/` ページにアクセス
3. 「APIキー生成」ボタンをクリック
4. キー名と権限を設定して生成

#### 使用方法

**ヘッダーで指定（推奨）:**

```bash
curl http://localhost:5000/api/works \
  -H "X-API-Key: your-api-key-here"
```

**クエリパラメータで指定:**

```bash
curl "http://localhost:5000/api/works?api_key=your-api-key-here"
```

### 権限レベル

| 権限 | 説明 |
|-----|------|
| `read` | 情報の取得のみ可能 |
| `write` | 情報の取得と更新が可能 |
| `admin` | 全ての操作が可能（管理者のみ） |

---

## エンドポイント一覧

詳細なAPI仕様は [OpenAPI仕様書](/docs/api/openapi.yaml) を参照してください。

### ヘルスチェック

#### `GET /health`

基本的なヘルスチェック。アプリケーションが稼働しているか確認。

**認証:** 不要

**レスポンス例:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-08T10:30:00Z",
  "service": "manga-anime-info-system"
}
```

#### `GET /health/ready`

詳細な準備状態チェック。データベース接続や設定ファイルの読み込みを確認。

**認証:** 不要

**レスポンス例:**
```json
{
  "status": "ready",
  "checks": {
    "database": {
      "status": "healthy",
      "works_count": 150,
      "releases_count": 450
    },
    "config": {"status": "healthy"}
  },
  "uptime": {
    "uptime_seconds": 3600,
    "uptime_human": "1:00:00"
  }
}
```

#### `GET /metrics`

Prometheus形式のメトリクスを出力。

**認証:** 不要

---

### 認証

#### `POST /auth/login`

ユーザーログイン。セッションを開始します。

**認証:** 不要

**リクエストボディ (form-urlencoded):**
```
username=admin&password=your_password
```

**レスポンス:** 302リダイレクト

#### `GET /auth/logout`

ログアウト。セッションを破棄します。

**認証:** 必須

#### `GET /auth/status`

現在の認証状態を確認。

**認証:** 不要

**レスポンス例:**
```json
{
  "authenticated": true,
  "username": "admin",
  "is_admin": true,
  "last_login": "2025-12-08T10:00:00Z"
}
```

---

### 作品情報

#### `GET /api/works`

作品一覧を取得。フィルタリングとページネーションに対応。

**認証:** 必須

**クエリパラメータ:**
- `type` (string): 作品タイプ (`anime`, `manga`)
- `search` (string): タイトル検索キーワード
- `limit` (integer): 取得件数（1-100、デフォルト: 50）
- `offset` (integer): オフセット（デフォルト: 0）

**レスポンス例:**
```json
{
  "success": true,
  "count": 10,
  "total": 150,
  "works": [
    {
      "id": 1,
      "title": "鬼滅の刃",
      "type": "anime",
      "official_url": "https://kimetsu.com"
    }
  ]
}
```

#### `GET /api/works/{work_id}`

特定の作品の詳細情報とリリース履歴を取得。

**認証:** 必須

**レスポンス例:**
```json
{
  "success": true,
  "work": {
    "id": 1,
    "title": "鬼滅の刃",
    "type": "anime"
  },
  "releases": [
    {
      "id": 1,
      "release_type": "episode",
      "number": "1",
      "platform": "dアニメストア",
      "release_date": "2025-01-10"
    }
  ]
}
```

---

### リリース情報

#### `GET /api/releases/recent`

最近のリリース情報を取得。

**認証:** 必須

**クエリパラメータ:**
- `days` (integer): 取得期間（日数、1-30、デフォルト: 7）
- `type` (string): 作品タイプフィルタ

**レスポンス例:**
```json
{
  "success": true,
  "count": 15,
  "releases": [
    {
      "id": 100,
      "work_id": 1,
      "release_type": "episode",
      "number": "5",
      "platform": "Netflix",
      "release_date": "2025-12-08"
    }
  ]
}
```

#### `GET /api/releases/upcoming`

今後のリリース予定を取得。

**認証:** 必須

**クエリパラメータ:**
- `days` (integer): 今後何日分を取得するか（1-30、デフォルト: 7）

---

### ウォッチリスト

#### `GET /watchlist/api/list`

ユーザーのウォッチリストを取得。

**認証:** 必須（セッション）

**レスポンス例:**
```json
{
  "success": true,
  "count": 3,
  "watchlist": [
    {
      "id": 1,
      "work_id": 1,
      "notify_new_episodes": true,
      "notify_new_volumes": false,
      "work": {
        "title": "鬼滅の刃",
        "type": "anime"
      }
    }
  ]
}
```

#### `POST /watchlist/api/add`

作品をウォッチリストに追加。

**認証:** 必須（セッション）

**リクエストボディ:**
```json
{
  "work_id": 123
}
```

**レスポンス例:**
```json
{
  "success": true,
  "message": "「呪術廻戦」をウォッチリストに追加しました",
  "watchlist_id": 5
}
```

#### `DELETE /watchlist/api/remove/{work_id}`

ウォッチリストから作品を削除。

**認証:** 必須（セッション）

#### `PUT /watchlist/api/update/{work_id}`

ウォッチリストの通知設定を更新。

**認証:** 必須（セッション）

**リクエストボディ:**
```json
{
  "notify_new_episodes": true,
  "notify_new_volumes": false
}
```

#### `GET /watchlist/api/stats`

ウォッチリストの統計情報を取得。

**認証:** 必須（セッション）

**レスポンス例:**
```json
{
  "success": true,
  "stats": {
    "total": 10,
    "anime": 7,
    "manga": 3
  }
}
```

---

### APIキー管理

#### `GET /api-keys/api/list`

ユーザーのAPIキー一覧を取得。

**認証:** 必須（セッション）

**レスポンス例:**
```json
{
  "success": true,
  "count": 2,
  "keys": [
    {
      "key": "sk_abc123...",
      "name": "My Application Key",
      "permissions": "read,write",
      "is_active": true
    }
  ]
}
```

#### `POST /api-keys/generate`

新しいAPIキーを生成。

**認証:** 必須（セッション）

**リクエストボディ (form-urlencoded):**
```
name=My Application Key&permissions=read,write
```

#### `POST /api-keys/revoke/{key}`

APIキーを無効化。

**認証:** 必須（セッション）

---

### ユーザー管理（管理者専用）

#### `GET /users/api/stats`

ユーザー統計情報を取得。

**認証:** 必須（セッション、管理者のみ）

**レスポンス例:**
```json
{
  "total_users": 10,
  "admin_users": 2,
  "regular_users": 8
}
```

#### `POST /users/create`

新規ユーザーを作成。

**認証:** 必須（セッション、管理者のみ）

#### `POST /users/{user_id}/delete`

ユーザーを削除。

**認証:** 必須（セッション、管理者のみ）

#### `POST /users/{user_id}/toggle-admin`

ユーザーの管理者権限を切り替え。

**認証:** 必須（セッション、管理者のみ）

---

### カレンダー連携

#### `POST /api/calendar/sync`

Googleカレンダーとの同期を実行。

**認証:** 必須（セッション）

**レスポンス例:**
```json
{
  "success": true,
  "synced_count": 15,
  "message": "カレンダー同期が完了しました"
}
```

#### `GET /api/calendar/events`

カレンダーイベント一覧を取得。

**認証:** 必須（セッション）

**クエリパラメータ:**
- `start_date` (date): 開始日（YYYY-MM-DD）
- `end_date` (date): 終了日（YYYY-MM-DD）

#### `GET /api/calendar/stats`

カレンダーの統計情報を取得。

**認証:** 必須（セッション）

---

### システム統計

#### `GET /api/stats`

システム全体の統計情報を取得。

**認証:** 必須

**レスポンス例:**
```json
{
  "success": true,
  "stats": {
    "total_works": 150,
    "total_releases": 450,
    "anime_count": 100,
    "manga_count": 50
  }
}
```

---

## 使用例

### Python での使用例

```python
import requests

# APIキー認証
API_KEY = "your-api-key-here"
BASE_URL = "http://localhost:5000"

headers = {
    "X-API-Key": API_KEY
}

# 作品一覧を取得
response = requests.get(
    f"{BASE_URL}/api/works",
    headers=headers,
    params={"type": "anime", "limit": 10}
)

if response.status_code == 200:
    data = response.json()
    print(f"取得した作品数: {data['count']}")
    for work in data['works']:
        print(f"- {work['title']}")

# ウォッチリストに追加（セッション認証）
session = requests.Session()

# ログイン
login_response = session.post(
    f"{BASE_URL}/auth/login",
    data={
        "username": "admin",
        "password": "your_password"
    }
)

if login_response.status_code == 200:
    # ウォッチリストに追加
    add_response = session.post(
        f"{BASE_URL}/watchlist/api/add",
        json={"work_id": 123}
    )

    if add_response.status_code == 200:
        result = add_response.json()
        print(result['message'])
```

### cURL での使用例

```bash
# 作品一覧を取得
curl -X GET "http://localhost:5000/api/works?type=anime&limit=10" \
  -H "X-API-Key: your-api-key-here"

# ログイン
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your_password" \
  -c cookies.txt

# ウォッチリストに追加
curl -X POST http://localhost:5000/watchlist/api/add \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"work_id": 123}'
```

---

## エラーハンドリング

### エラーレスポンス形式

すべてのエラーは統一された形式で返却されます。

```json
{
  "success": false,
  "error": "Error Type",
  "message": "日本語のエラーメッセージ"
}
```

### HTTPステータスコード

| コード | 説明 | 対処方法 |
|-------|------|---------|
| 200 | 成功 | - |
| 302 | リダイレクト | Location headerに従う |
| 400 | リクエストが不正 | リクエストパラメータを確認 |
| 401 | 認証が必要 | ログインまたはAPIキーを確認 |
| 403 | アクセス権限なし | 管理者権限が必要か確認 |
| 404 | リソースが見つからない | URLやIDを確認 |
| 409 | 競合（重複など） | リソースが既に存在する |
| 429 | レート制限超過 | しばらく待ってから再試行 |
| 500 | サーバーエラー | 管理者に連絡 |
| 503 | サービス利用不可 | システムが準備できていない |

---

## レート制限

### デフォルト制限

- **1日あたり**: 200リクエスト
- **1時間あたり**: 50リクエスト

### レート制限超過時

HTTP 429エラーが返却されます。

```json
{
  "error": "Rate limit exceeded",
  "message": "リクエスト制限を超えました。しばらくしてから再試行してください。"
}
```

### ベストプラクティス

1. **リトライロジックの実装**
   - 429エラー時は指数バックオフで再試行

2. **リクエストのバッチ化**
   - 可能な限り1リクエストで必要な情報を取得

3. **キャッシュの活用**
   - 頻繁に変わらないデータはキャッシュ

---

## ベストプラクティス

### セキュリティ

1. **APIキーの管理**
   - APIキーは環境変数で管理
   - ソースコードにハードコーディングしない
   - 定期的にローテーション

2. **HTTPS の使用**
   - 本番環境では必ずHTTPSを使用

3. **権限の最小化**
   - 必要最小限の権限でAPIキーを発行

### パフォーマンス

1. **ページネーションの活用**
   - 大量データの取得時は`limit`と`offset`を使用

2. **フィルタリングの活用**
   - サーバー側でフィルタリング

3. **並列リクエストの制限**
   - レート制限を考慮

---

## サポート

### ドキュメント

- **OpenAPI仕様書**: `/docs/api/openapi.yaml`
- **プロジェクトREADME**: `/README.md`

### よくある質問

**Q: APIキーはどこで取得できますか？**

A: Web UIにログイン後、`/api-keys/`ページから生成できます。

**Q: レート制限を超えた場合はどうなりますか？**

A: HTTP 429エラーが返却されます。しばらく待ってから再試行してください。

**Q: セッション認証とAPIキー認証のどちらを使うべきですか？**

A: Web UIから操作する場合はセッション認証、プログラムから操作する場合はAPIキー認証を推奨します。

**Q: 管理者権限が必要なエンドポイントはどれですか？**

A: `/users/`配下のユーザー管理エンドポイント、`/admin/`配下のエンドポイントは管理者権限が必要です。

---

**最終更新日**: 2025-12-08
**バージョン**: 1.0.0
