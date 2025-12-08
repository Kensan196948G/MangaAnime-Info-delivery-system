# MangaAnime Information Delivery System API Documentation

このディレクトリには、MangaAnime情報配信システムのAPI仕様書が含まれています。

## ファイル一覧

- **openapi.yaml**: OpenAPI 3.0形式のAPI仕様書

## API仕様書の利用方法

### 1. Swagger UIで閲覧

オンラインのSwagger Editorを使用して閲覧・テストできます:

```bash
# openapi.yamlをブラウザで開く
https://editor.swagger.io/
```

ファイルをドラッグ&ドロップまたはコピー&ペーストして閲覧してください。

### 2. ローカルでSwagger UIを起動

Dockerを使用してローカル環境で閲覧:

```bash
# プロジェクトルートで実行
docker run -p 8080:8080 \
  -e SWAGGER_JSON=/docs/openapi.yaml \
  -v $(pwd)/docs/api:/docs \
  swaggerapi/swagger-ui

# ブラウザで http://localhost:8080 を開く
```

### 3. VS Codeで閲覧

VS Code拡張機能を使用:

1. 拡張機能「OpenAPI (Swagger) Editor」をインストール
2. `openapi.yaml`を開く
3. 右上の「Preview」ボタンをクリック

### 4. コマンドラインで検証

OpenAPI仕様の妥当性を検証:

```bash
# npmでopenapi-lintをインストール
npm install -g @stoplight/spectral-cli

# 検証実行
spectral lint docs/api/openapi.yaml
```

## API概要

### 認証方式

このAPIは2つの認証方式をサポートしています:

#### 1. セッションベース認証（Web UI用）
```bash
# ログイン
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}' \
  -c cookies.txt

# 認証が必要なエンドポイントへアクセス
curl http://localhost:5000/api/works \
  -b cookies.txt
```

#### 2. APIキー認証

```bash
# APIキーをヘッダーで送信
curl http://localhost:5000/api/works \
  -H "X-API-Key: your-api-key-here"

# または、クエリパラメータで送信
curl "http://localhost:5000/api/works?api_key=your-api-key-here"
```

### 主要なエンドポイント

#### ヘルスチェック
```bash
# 基本的なヘルスチェック
curl http://localhost:5000/health

# 詳細なヘルスチェック
curl http://localhost:5000/health/detailed

# Prometheusメトリクス
curl http://localhost:5000/metrics
```

#### 作品情報
```bash
# 作品一覧取得
curl http://localhost:5000/api/works?type=anime&limit=10

# 作品詳細取得
curl http://localhost:5000/api/works/1

# 作品検索
curl "http://localhost:5000/api/works?search=鬼滅"
```

#### リリース情報
```bash
# 最近のリリース
curl http://localhost:5000/api/releases/recent?days=7

# 今後のリリース予定
curl http://localhost:5000/api/releases/upcoming?days=7
```

#### ウォッチリスト
```bash
# ウォッチリスト一覧
curl http://localhost:5000/watchlist/api/list \
  -b cookies.txt

# ウォッチリストに追加
curl -X POST http://localhost:5000/watchlist/api/add \
  -H "Content-Type: application/json" \
  -d '{"work_id": 1}' \
  -b cookies.txt

# ウォッチリストから削除
curl -X DELETE http://localhost:5000/watchlist/api/remove/1 \
  -b cookies.txt
```

#### カレンダー同期
```bash
# カレンダー同期実行
curl -X POST http://localhost:5000/api/calendar/sync \
  -b cookies.txt

# カレンダーイベント一覧
curl http://localhost:5000/api/calendar/events \
  -b cookies.txt
```

#### データ収集
```bash
# 手動データ収集トリガー
curl -X POST http://localhost:5000/api/manual-collection \
  -H "Content-Type: application/json" \
  -d '{"source": "anilist"}' \
  -b cookies.txt

# 収集ステータス確認
curl http://localhost:5000/api/collection-status \
  -b cookies.txt
```

#### 統計情報
```bash
# システム統計
curl http://localhost:5000/api/stats \
  -H "X-API-Key: your-api-key"

# ウォッチリスト統計
curl http://localhost:5000/watchlist/api/stats \
  -b cookies.txt
```

## レスポンス形式

### 成功レスポンス
```json
{
  "success": true,
  "count": 10,
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

### エラーレスポンス
```json
{
  "success": false,
  "error": "Not Found",
  "message": "指定されたリソースが見つかりません"
}
```

## エラーコード

| ステータスコード | 説明 |
|---------------|------|
| 200 | 成功 |
| 201 | 作成成功 |
| 400 | リクエストが不正 |
| 401 | 認証が必要 |
| 403 | アクセス権限なし |
| 404 | リソースが見つからない |
| 409 | 競合（既に存在する） |
| 429 | レート制限超過 |
| 500 | サーバーエラー |
| 503 | サービス利用不可 |

## レート制限

- デフォルト: 1日あたり200リクエスト、1時間あたり50リクエスト
- 超過時は429ステータスコードが返されます
- `Retry-After`ヘッダーで再試行可能時刻を確認できます

## ページネーション

一覧取得エンドポイントは以下のパラメータでページネーションをサポート:

- `limit`: 取得件数（デフォルト: 50、最大: 100）
- `offset`: オフセット（デフォルト: 0）

```bash
# 例: 2ページ目を取得（1ページ50件）
curl "http://localhost:5000/api/works?limit=50&offset=50"
```

## フィルタリングとソート

### 作品一覧のフィルタ
- `type`: anime / manga
- `search`: タイトル検索キーワード
- `sort`: created_at_desc / created_at_asc / title_asc / title_desc

```bash
# 例: アニメ作品を新着順で取得
curl "http://localhost:5000/api/works?type=anime&sort=created_at_desc"
```

## APIキーの生成

1. Web UIにログイン
2. APIキー管理ページ（/api-keys/）にアクセス
3. 「新規APIキー生成」ボタンをクリック
4. キー名と権限を設定
5. 生成されたAPIキーをコピー（再表示不可）

### 権限の種類

- `read`: 読み取り専用
- `write`: 書き込み可能
- `admin`: 管理者権限

複数の権限を指定する場合はカンマ区切り: `read,write`

## クライアントライブラリ

### Python

```python
import requests

# APIキー認証
headers = {"X-API-Key": "your-api-key"}
response = requests.get("http://localhost:5000/api/works", headers=headers)
works = response.json()

# セッション認証
session = requests.Session()
session.post(
    "http://localhost:5000/auth/login",
    json={"username": "admin", "password": "password"}
)
response = session.get("http://localhost:5000/api/works")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

// APIキー認証
const response = await axios.get('http://localhost:5000/api/works', {
  headers: { 'X-API-Key': 'your-api-key' }
});

// セッション認証
const session = axios.create({
  baseURL: 'http://localhost:5000',
  withCredentials: true
});

await session.post('/auth/login', {
  username: 'admin',
  password: 'password'
});

const works = await session.get('/api/works');
```

### cURL

```bash
# APIキー認証の例
API_KEY="your-api-key"
curl -H "X-API-Key: $API_KEY" \
  http://localhost:5000/api/works
```

## コード生成

OpenAPI仕様書からクライアントコードを自動生成できます:

### OpenAPI Generator

```bash
# Pythonクライアント生成
openapi-generator-cli generate \
  -i docs/api/openapi.yaml \
  -g python \
  -o client/python

# TypeScriptクライアント生成
openapi-generator-cli generate \
  -i docs/api/openapi.yaml \
  -g typescript-axios \
  -o client/typescript
```

## テスト

### Postmanでテスト

1. Postmanを開く
2. Import → File → `openapi.yaml`を選択
3. コレクションが自動生成されます
4. 環境変数を設定（baseUrl, apiKey等）
5. リクエストを実行

### 自動テスト

```bash
# Drakovを使用したモックサーバー
npm install -g drakov
drakov -f docs/api/openapi.yaml -p 3000

# テスト実行
pytest tests/test_api.py
```

## トラブルシューティング

### 401 Unauthorized

- APIキーが正しいか確認
- セッションが有効か確認（ログイン済みか）
- リクエストヘッダーが正しいか確認

### 403 Forbidden

- 必要な権限があるか確認
- 管理者権限が必要な操作ではないか確認

### 429 Rate Limit Exceeded

- リクエスト頻度を下げる
- `Retry-After`ヘッダーを確認
- 本番環境ではRedisベースのレート制限を推奨

### 500 Internal Server Error

- サーバーログを確認（logs/）
- データベース接続を確認
- 設定ファイル（config.json）を確認

## セキュリティ

### 本番環境での注意事項

1. **HTTPSを使用**: 必ずHTTPS経由でアクセス
2. **強力なAPIキー**: 長く複雑なAPIキーを使用
3. **定期的なキーローテーション**: APIキーを定期的に更新
4. **権限の最小化**: 必要最小限の権限のみ付与
5. **レート制限の強化**: Redisベースのレート制限を使用
6. **監査ログの確認**: audit_logsテーブルを定期的に確認

## サポート

質問や問題がある場合:

1. GitHubのIssueを作成
2. ドキュメント（docs/）を確認
3. システムログ（logs/）を確認

## ライセンス

MIT License

## 更新履歴

- 2025-12-08: 初版作成
  - 全APIエンドポイントを定義
  - 認証方式を実装
  - エラーハンドリングを標準化
