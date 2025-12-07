# API Sources Testing & Configuration Endpoints

## 概要

このドキュメントは、アニメ・マンガ情報配信システムの収集ソース（API/RSS）のテスト・設定用エンドポイントについて説明します。

## エンドポイント一覧

### 1. GET /api/sources

すべての収集ソースの一覧と設定を取得します。

**リクエスト:**
```
GET /api/sources
```

**レスポンス:**
```json
{
  "apis": [
    {
      "id": "anilist",
      "name": "AniList GraphQL API",
      "type": "api",
      "enabled": true,
      "url": "https://graphql.anilist.co",
      "rate_limit": 90,
      "timeout": 30,
      "description": "アニメ情報取得用GraphQL API",
      "data_type": "anime",
      "health_status": "unknown"
    }
  ],
  "rss_feeds": [
    {
      "id": "少年ジャンプ＋",
      "name": "少年ジャンプ＋",
      "type": "rss",
      "enabled": true,
      "url": "https://shonenjumpplus.com/rss",
      "description": "週刊少年ジャンプ系列の無料Web漫画サービス",
      "data_type": "manga",
      "verified": true,
      "timeout": 25,
      "retry_count": 3
    }
  ],
  "summary": {
    "total_sources": 6,
    "enabled_sources": 3,
    "disabled_sources": 3,
    "last_updated": "2025-11-15T16:00:00"
  }
}
```

---

### 2. POST /api/sources/anilist/test

AniList GraphQL APIの接続テストを実行します。

**リクエスト:**
```
POST /api/sources/anilist/test
```

**レスポンス:**
```json
{
  "source": "anilist",
  "timestamp": "2025-11-15T16:00:00",
  "overall_status": "success",
  "success_rate": "100.0%",
  "total_time_ms": 1001.14,
  "tests": [
    {
      "name": "basic_connectivity",
      "status": "success",
      "response_time_ms": 405.01,
      "http_status": 200,
      "details": "GraphQL API responding"
    },
    {
      "name": "current_season_query",
      "status": "success",
      "response_time_ms": 416.91,
      "results_count": 5,
      "details": "FALL 2025シーズンのアニメ5件取得"
    },
    {
      "name": "rate_limit_info",
      "status": "info",
      "details": "AniList rate limit: 90 requests/minute",
      "configured_limit": 90
    }
  ]
}
```

**テスト内容:**
1. 基本接続テスト (GraphQLクエリ送信)
2. 現在シーズンのアニメ取得テスト
3. レート制限情報の確認

---

### 3. POST /api/sources/syoboi/test

しょぼいカレンダーAPIの接続テストを実行します。

**リクエスト:**
```
POST /api/sources/syoboi/test
```

**レスポンス:**
```json
{
  "source": "syoboi",
  "timestamp": "2025-11-15T16:00:00",
  "overall_status": "success",
  "success_rate": "100.0%",
  "total_time_ms": 2096.56,
  "tests": [
    {
      "name": "title_lookup",
      "status": "success",
      "response_time_ms": 235.48,
      "http_status": 200,
      "details": "タイトル検索APIアクセス成功",
      "data_format": "valid_json"
    },
    {
      "name": "program_lookup",
      "status": "success",
      "response_time_ms": 1861.01,
      "http_status": 200,
      "details": "番組スケジュール取得成功"
    }
  ]
}
```

**テスト内容:**
1. タイトル検索API接続テスト
2. 番組スケジュール取得テスト

---

### 4. POST /api/sources/rss/test

RSSフィードの接続・パーステストを実行します。

**リクエスト:**
```json
POST /api/sources/rss/test
Content-Type: application/json

{
  "feed_id": "少年ジャンプ＋"
}
```

または

```json
{
  "feed_url": "https://shonenjumpplus.com/rss"
}
```

**レスポンス:**
```json
{
  "source": "少年ジャンプ＋",
  "url": "https://shonenjumpplus.com/rss",
  "timestamp": "2025-11-15T16:00:00",
  "overall_status": "success",
  "success_rate": "100.0%",
  "total_time_ms": 528.42,
  "tests": [
    {
      "name": "http_connectivity",
      "status": "success",
      "response_time_ms": 345.76,
      "http_status": 200,
      "content_type": "application/xml",
      "content_length": 125678,
      "details": "HTTP 200"
    },
    {
      "name": "rss_parsing",
      "status": "success",
      "response_time_ms": 131.58,
      "entries_count": 267,
      "feed_title": "少年ジャンプ＋",
      "has_valid_structure": true,
      "details": "267件のエントリー検出"
    }
  ],
  "sample_entry": {
    "title": "[4073回]猫田びより",
    "link": "https://shonenjumpplus.com/episode/17107094912077655936",
    "published": "Fri, 14 Nov 2025 15:00:00 +0000",
    "has_description": true
  }
}
```

**テスト内容:**
1. HTTP接続テスト
2. RSS/XMLパーステスト
3. サンプルエントリーの取得

---

### 5. POST /api/sources/toggle

収集ソースの有効/無効を切り替えます。

**リクエスト (API):**
```json
POST /api/sources/toggle
Content-Type: application/json

{
  "source_type": "anilist",
  "enabled": false
}
```

**リクエスト (RSS Feed):**
```json
{
  "source_type": "rss_feed",
  "source_id": "少年ジャンプ＋",
  "enabled": true
}
```

**パラメータ:**
- `source_type`: `"anilist"` | `"syoboi"` | `"rss_feed"`
- `source_id`: RSSフィードの場合のみ必須
- `enabled`: `true` | `false`

**レスポンス:**
```json
{
  "success": true,
  "source_type": "anilist",
  "source_id": null,
  "enabled": false,
  "message": "Source disabled successfully",
  "timestamp": "2025-11-15T16:00:00"
}
```

---

### 6. POST /api/sources/test-all

すべての有効な収集ソースを並列でテストします。

**リクエスト:**
```
POST /api/sources/test-all
```

**レスポンス:**
```json
{
  "timestamp": "2025-11-15T16:00:00",
  "sources": [
    {
      "source": "anilist",
      "overall_status": "success",
      "tests": [...]
    },
    {
      "source": "少年ジャンプ＋",
      "overall_status": "success",
      "tests": [...]
    }
  ],
  "summary": {
    "total": 3,
    "success": 3,
    "failed": 0,
    "errors": 0
  }
}
```

---

## 使用例

### Python (requests)

```python
import requests

# ソース一覧取得
response = requests.get('http://localhost:3030/api/sources')
sources = response.json()

# AniListテスト
response = requests.post('http://localhost:3030/api/sources/anilist/test')
result = response.json()
print(f"AniList status: {result['overall_status']}")

# RSSフィードテスト
response = requests.post(
    'http://localhost:3030/api/sources/rss/test',
    json={'feed_id': '少年ジャンプ＋'}
)
result = response.json()
print(f"RSS entries: {result['tests'][1]['entries_count']}")

# ソース切り替え
response = requests.post(
    'http://localhost:3030/api/sources/toggle',
    json={'source_type': 'syoboi', 'enabled': True}
)
print(f"Toggle result: {response.json()['message']}")
```

### curl

```bash
# ソース一覧取得
curl http://localhost:3030/api/sources

# AniListテスト
curl -X POST http://localhost:3030/api/sources/anilist/test

# RSSフィードテスト
curl -X POST http://localhost:3030/api/sources/rss/test \
  -H "Content-Type: application/json" \
  -d '{"feed_id": "少年ジャンプ＋"}'

# ソース切り替え
curl -X POST http://localhost:3030/api/sources/toggle \
  -H "Content-Type: application/json" \
  -d '{"source_type": "anilist", "enabled": false}'
```

---

## ステータスコード

- `200 OK`: 成功
- `400 Bad Request`: リクエストパラメータが不正
- `404 Not Found`: 指定されたソースが見つからない
- `500 Internal Server Error`: サーバーエラー

---

## 注意事項

1. **レート制限**: AniListは90リクエスト/分、しょぼいカレンダーは60リクエスト/分の制限があります
2. **タイムアウト**: RSSフィードのテストは最大25秒、APIテストは最大5秒でタイムアウトします
3. **並列テスト**: `/api/sources/test-all`は最大5並列でテストを実行します
4. **設定保存**: `/api/sources/toggle`の変更は`config.json`に即座に反映されます

---

## トラブルシューティング

### タイムアウトエラー
- ネットワーク接続を確認
- ファイアウォール設定を確認
- タイムアウト値を増やす（config.json）

### RSS パースエラー
- URLが正しいか確認
- RSSフィードが有効か確認
- User-Agentヘッダーをチェック

### レート制限エラー
- リクエスト間隔を空ける
- 並列実行数を減らす

---

## テストスクリプト

プロジェクトルートに`test_api_sources.py`というテストスクリプトが用意されています。

```bash
python3 test_api_sources.py
```

このスクリプトは全エンドポイントをテストし、結果をわかりやすく表示します。

