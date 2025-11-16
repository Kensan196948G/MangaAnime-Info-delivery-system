# API収集ソーステスト - クイックリファレンス

## すぐに使えるコマンド集

### 1. ソース一覧を確認
```bash
curl http://localhost:3030/api/sources | jq
```

### 2. AniListをテスト
```bash
curl -X POST http://localhost:3030/api/sources/anilist/test | jq
```

### 3. しょぼいカレンダーをテスト
```bash
curl -X POST http://localhost:3030/api/sources/syoboi/test | jq
```

### 4. 少年ジャンプ+をテスト
```bash
curl -X POST http://localhost:3030/api/sources/rss/test \
  -H "Content-Type: application/json" \
  -d '{"feed_id": "少年ジャンプ＋"}' | jq
```

### 5. カスタムRSSフィードをテスト
```bash
curl -X POST http://localhost:3030/api/sources/rss/test \
  -H "Content-Type: application/json" \
  -d '{"feed_url": "https://your-rss-feed.com/rss"}' | jq
```

### 6. AniListを無効化
```bash
curl -X POST http://localhost:3030/api/sources/toggle \
  -H "Content-Type: application/json" \
  -d '{"source_type": "anilist", "enabled": false}' | jq
```

### 7. しょぼいカレンダーを有効化
```bash
curl -X POST http://localhost:3030/api/sources/toggle \
  -H "Content-Type: application/json" \
  -d '{"source_type": "syoboi", "enabled": true}' | jq
```

### 8. 全ソースを一括テスト
```bash
curl -X POST http://localhost:3030/api/sources/test-all | jq
```

---

## Python例

### 基本的な使用例
```python
import requests

BASE_URL = 'http://localhost:3030'

# 1. ソース一覧
sources = requests.get(f'{BASE_URL}/api/sources').json()
print(f"有効: {sources['summary']['enabled_sources']}")

# 2. AniListテスト
result = requests.post(f'{BASE_URL}/api/sources/anilist/test').json()
print(f"AniList: {result['overall_status']}")

# 3. RSSテスト
result = requests.post(
    f'{BASE_URL}/api/sources/rss/test',
    json={'feed_id': '少年ジャンプ＋'}
).json()
print(f"エントリー: {result['tests'][1]['entries_count']}件")

# 4. ソース切り替え
result = requests.post(
    f'{BASE_URL}/api/sources/toggle',
    json={'source_type': 'syoboi', 'enabled': True}
).json()
print(result['message'])
```

---

## テストスクリプト実行

```bash
# 全エンドポイントをテスト
python3 test_api_sources.py

# 期待される出力:
# ✓ PASSED: ソース一覧取得
# ✓ PASSED: AniListテスト
# ✓ PASSED: しょぼいカレンダーテスト
# ✓ PASSED: RSSフィードテスト
# ✓ PASSED: ソース切り替えテスト
# 
# 5/5 tests passed
```

---

## 主要エンドポイント

| メソッド | エンドポイント | 機能 |
|---------|--------------|------|
| GET | `/api/sources` | ソース一覧取得 |
| POST | `/api/sources/anilist/test` | AniListテスト |
| POST | `/api/sources/syoboi/test` | しょぼいカレンダーテスト |
| POST | `/api/sources/rss/test` | RSSフィードテスト |
| POST | `/api/sources/toggle` | ソース有効/無効切り替え |
| POST | `/api/sources/test-all` | 全ソース一括テスト |

---

## レスポンス例

### AniListテスト結果
```json
{
  "source": "anilist",
  "overall_status": "success",
  "success_rate": "100.0%",
  "total_time_ms": 822.39,
  "tests": [
    {
      "name": "basic_connectivity",
      "status": "success",
      "response_time_ms": 405.01
    }
  ]
}
```

### ソース切り替え結果
```json
{
  "success": true,
  "source_type": "anilist",
  "enabled": false,
  "message": "Source disabled successfully"
}
```

---

## トラブルシューティング

### サーバーが起動していない
```bash
# サーバー起動
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 app/web_app.py
```

### ポート3030が使用中
```bash
# プロセス確認
lsof -i :3030

# プロセス終了
kill -9 <PID>
```

### jqコマンドがない
```bash
# Ubuntu/Debian
sudo apt install jq

# macOS
brew install jq
```

---

## 詳細ドキュメント

完全なAPIドキュメント: `docs/API_SOURCES_ENDPOINTS.md`
