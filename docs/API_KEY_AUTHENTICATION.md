# APIキー認証機能ドキュメント

## 概要

MangaAnime-Info-delivery-systemに実装されたAPIキー認証機能により、REST APIエンドポイントへの安全なアクセスが可能になります。

## 主な機能

1. **APIキー生成・管理**
   - ユーザーごとに複数のAPIキーを生成可能
   - キーの名前付け（用途管理）
   - レート制限設定（オプション）
   - 最終利用時刻の記録

2. **認証方式**
   - HTTPヘッダー: `X-API-Key`（推奨）
   - クエリパラメータ: `api_key`

3. **セキュリティ**
   - キー形式: `sk_<32バイトランダム文字列>`
   - ユーザーごとのキー管理
   - キーの無効化・削除機能

## セットアップ

### 1. アプリケーション起動

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python app/web_app_with_api_auth.py
```

デフォルトユーザー:
- **ユーザー名**: admin
- **パスワード**: admin123

### 2. ログイン

```
http://127.0.0.1:5000/login
```

### 3. APIキー生成

#### Web UIから生成

```
http://127.0.0.1:5000/api-keys/manage
```

1. 「新しいAPIキーを生成」フォームにキー名を入力
2. 必要に応じてレート制限を設定
3. 「APIキーを生成」ボタンをクリック
4. **重要**: 生成されたキーは一度しか表示されないため、安全な場所に保存

#### APIから生成

```bash
curl -X POST http://127.0.0.1:5000/auth/api-keys/generate \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key", "rate_limit": 60}' \
  --cookie "session=YOUR_SESSION_COOKIE"
```

レスポンス例:
```json
{
  "success": true,
  "api_key": {
    "key": "sk_AbCdEf123456...",
    "name": "My API Key",
    "created_at": "2025-12-07T10:00:00",
    "rate_limit": 60
  },
  "message": "API key generated successfully..."
}
```

## API使用方法

### 1. HTTPヘッダーで認証（推奨）

```bash
curl -H "X-API-Key: sk_YOUR_API_KEY" \
     http://127.0.0.1:5000/api/stats
```

### 2. クエリパラメータで認証

```bash
curl "http://127.0.0.1:5000/api/stats?api_key=sk_YOUR_API_KEY"
```

### 3. Pythonでの使用例

```python
import requests

API_KEY = "sk_YOUR_API_KEY"
BASE_URL = "http://127.0.0.1:5000"

# ヘッダー認証
headers = {"X-API-Key": API_KEY}
response = requests.get(f"{BASE_URL}/api/stats", headers=headers)
print(response.json())

# クエリパラメータ認証
response = requests.get(f"{BASE_URL}/api/stats", params={"api_key": API_KEY})
print(response.json())
```

### 4. JavaScriptでの使用例

```javascript
const API_KEY = 'sk_YOUR_API_KEY';
const BASE_URL = 'http://127.0.0.1:5000';

// Fetch API
fetch(`${BASE_URL}/api/stats`, {
  headers: {
    'X-API-Key': API_KEY
  }
})
.then(response => response.json())
.then(data => console.log(data));

// Axios
axios.get(`${BASE_URL}/api/stats`, {
  headers: {
    'X-API-Key': API_KEY
  }
})
.then(response => console.log(response.data));
```

## 利用可能なAPIエンドポイント

### 1. 統計情報API

**エンドポイント**: `GET /api/stats`

**レスポンス**:
```json
{
  "success": true,
  "stats": {
    "total_works": 100,
    "anime_count": 60,
    "manga_count": 40,
    "total_releases": 500,
    "notified_releases": 450
  },
  "user_id": "admin"
}
```

**使用例**:
```bash
curl -H "X-API-Key: sk_YOUR_API_KEY" \
     http://127.0.0.1:5000/api/stats
```

### 2. リリース一覧API

**エンドポイント**: `GET /api/releases`

**クエリパラメータ**:
- `type`: anime/manga (optional)
- `limit`: int (default: 50)
- `offset`: int (default: 0)

**レスポンス**:
```json
{
  "success": true,
  "count": 50,
  "limit": 50,
  "offset": 0,
  "releases": [
    {
      "id": 1,
      "work_id": 10,
      "release_type": "episode",
      "number": "3",
      "platform": "dアニメストア",
      "release_date": "2025-12-10",
      "title": "作品名"
    }
  ]
}
```

**使用例**:
```bash
# アニメのみ取得
curl -H "X-API-Key: sk_YOUR_API_KEY" \
     "http://127.0.0.1:5000/api/releases?type=anime&limit=10"
```

### 3. 今後のリリース情報API

**エンドポイント**: `GET /api/releases/upcoming`

**クエリパラメータ**:
- `days`: int (default: 7) - 今後何日分のリリースを取得するか
- `type`: anime/manga (optional)

**レスポンス**:
```json
{
  "success": true,
  "count": 20,
  "days": 7,
  "releases": [...]
}
```

**使用例**:
```bash
# 今後14日間のマンガリリース
curl -H "X-API-Key: sk_YOUR_API_KEY" \
     "http://127.0.0.1:5000/api/releases/upcoming?days=14&type=manga"
```

### 4. 作品一覧API

**エンドポイント**: `GET /api/works`

**クエリパラメータ**:
- `type`: anime/manga (optional)
- `search`: 検索キーワード (optional)
- `limit`: int (default: 50)
- `offset`: int (default: 0)

**レスポンス**:
```json
{
  "success": true,
  "count": 50,
  "limit": 50,
  "offset": 0,
  "works": [
    {
      "id": 1,
      "title": "作品名",
      "type": "anime",
      "official_url": "https://example.com"
    }
  ]
}
```

**使用例**:
```bash
# キーワード検索
curl -H "X-API-Key: sk_YOUR_API_KEY" \
     "http://127.0.0.1:5000/api/works?search=進撃&type=anime"
```

### 5. 作品詳細API

**エンドポイント**: `GET /api/works/<work_id>`

**レスポンス**:
```json
{
  "success": true,
  "work": {
    "id": 1,
    "title": "作品名",
    "type": "anime"
  },
  "releases": [...]
}
```

**使用例**:
```bash
curl -H "X-API-Key: sk_YOUR_API_KEY" \
     http://127.0.0.1:5000/api/works/1
```

## APIキー管理エンドポイント

### 1. APIキー生成

**エンドポイント**: `POST /auth/api-keys/generate`

**認証**: ログイン必須（セッションCookie）

**リクエストボディ**:
```json
{
  "name": "My API Key",
  "rate_limit": 60
}
```

**レスポンス**:
```json
{
  "success": true,
  "api_key": {
    "key": "sk_...",
    "name": "My API Key",
    "created_at": "2025-12-07T10:00:00",
    "rate_limit": 60
  }
}
```

### 2. APIキー一覧取得

**エンドポイント**: `GET /auth/api-keys`

**認証**: ログイン必須

**レスポンス**:
```json
{
  "success": true,
  "count": 2,
  "api_keys": [
    {
      "key_preview": "sk_abc123...xyz",
      "full_key": "sk_...",
      "name": "My API Key",
      "created_at": "2025-12-07T10:00:00",
      "last_used": "2025-12-07T12:30:00",
      "is_active": true,
      "rate_limit": 60
    }
  ]
}
```

### 3. APIキー無効化

**エンドポイント**: `DELETE /auth/api-keys/<key>`

**認証**: ログイン必須

**レスポンス**:
```json
{
  "success": true,
  "message": "API key revoked successfully"
}
```

### 4. APIキー削除

**エンドポイント**: `DELETE /auth/api-keys/<key>/delete`

**認証**: ログイン必須

**レスポンス**:
```json
{
  "success": true,
  "message": "API key deleted successfully"
}
```

### 5. APIキー検証

**エンドポイント**: `GET /auth/api-keys/verify`

**認証**: APIキー必須

**レスポンス**:
```json
{
  "success": true,
  "user_id": "admin",
  "key_name": "My API Key",
  "key_preview": "sk_abc123...xyz",
  "message": "API key is valid and active"
}
```

## エラーレスポンス

### 401 Unauthorized - APIキーが必要

```json
{
  "error": "API key required",
  "message": "Please provide API key in X-API-Key header or api_key query parameter",
  "status": 401
}
```

### 401 Unauthorized - 無効なAPIキー

```json
{
  "error": "Invalid or inactive API key",
  "message": "The provided API key is invalid or has been revoked",
  "status": 401
}
```

### 404 Not Found

```json
{
  "success": false,
  "error": "Endpoint not found",
  "status": 404
}
```

### 500 Internal Server Error

```json
{
  "success": false,
  "error": "Internal server error",
  "status": 500
}
```

## セキュリティベストプラクティス

### 1. APIキーの安全な保管

- **環境変数に保存**:
  ```bash
  export MANGA_ANIME_API_KEY="sk_YOUR_API_KEY"
  ```

- **.env ファイル** (推奨):
  ```
  MANGA_ANIME_API_KEY=sk_YOUR_API_KEY
  ```

- **Pythonでの使用**:
  ```python
  import os
  from dotenv import load_dotenv

  load_dotenv()
  API_KEY = os.getenv('MANGA_ANIME_API_KEY')
  ```

### 2. HTTPSの使用（本番環境）

本番環境では必ずHTTPSを使用してください:

```python
# 本番環境
BASE_URL = "https://your-domain.com"

# 開発環境のみHTTP
BASE_URL = "http://localhost:5000"
```

### 3. レート制限の設定

高頻度アクセスが予想される場合は、レート制限を設定:

```json
{
  "name": "Production API Key",
  "rate_limit": 60  // 60リクエスト/分
}
```

### 4. 定期的なキーのローテーション

セキュリティ向上のため、定期的にAPIキーを再生成:

1. 新しいキーを生成
2. アプリケーションを新しいキーに更新
3. 古いキーを無効化/削除

### 5. キーの用途別管理

異なる用途ごとにAPIキーを分ける:

- `production-web-app`
- `mobile-app-android`
- `mobile-app-ios`
- `development-testing`

## トラブルシューティング

### Q: APIキーが認証されない

**A**: 以下を確認してください:

1. APIキーが正しくコピーされているか
2. ヘッダー名が `X-API-Key` になっているか
3. キーが無効化されていないか
4. キーが削除されていないか

### Q: APIキーを紛失した

**A**: セキュリティ上、紛失したキーは再表示できません:

1. 紛失したキーを無効化
2. 新しいキーを生成
3. アプリケーションを更新

### Q: レート制限に達した

**A**: しばらく待ってから再試行、または管理者に連絡してレート制限を緩和してもらってください。

## 今後の拡張予定

- [ ] レート制限の実装
- [ ] APIキーの有効期限設定
- [ ] IPアドレス制限
- [ ] スコープ/権限管理
- [ ] 使用統計の記録
- [ ] Webhook通知

## サポート

問題が発生した場合は、以下を確認してください:

1. ログファイル: `/var/log/manga-anime-api.log`
2. テストスクリプト: `tests/test_api_key_auth.py`
3. サンプルコード: `docs/API_KEY_AUTHENTICATION.md`

---

**作成日**: 2025-12-07
**バージョン**: 1.0.0
**担当**: Backend Developer Agent
