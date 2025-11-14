# API クイックリファレンス

## データ更新API (`/api/refresh-data`)

### エンドポイント

```
GET /api/refresh-data
```

### レスポンス形式

#### 成功時 (200 OK)

```json
{
  "success": true,
  "message": "データ更新が完了しました",
  "data": {
    "timestamp": "2025-11-14T10:30:00.000000",
    "output": "処理結果...",
    "stats": {
      "total_works": 150,
      "total_releases": 450,
      "anime_count": 80,
      "manga_count": 70
    }
  },
  "error": null
}
```

#### エラー時 (400/500)

```json
{
  "success": false,
  "message": "データ更新中にエラーが発生しました",
  "data": {
    "timestamp": "2025-11-14T10:30:00.000000"
  },
  "error": {
    "message": "データ更新中にエラーが発生しました",
    "details": "詳細なエラー情報...",
    "code": "UPDATE_FAILED"
  }
}
```

### エラーコード

| コード | 説明 | HTTPステータス |
|-------|------|---------------|
| `SCRIPT_NOT_FOUND` | データ投入スクリプトが見つからない | 404 |
| `UPDATE_FAILED` | データ更新処理が失敗 | 500 |
| `TIMEOUT` | 処理がタイムアウト（30秒） | 500 |
| `INTERNAL_ERROR` | 予期しない内部エラー | 500 |

### JavaScriptでの使用例

```javascript
// APIクライアントを使用
const response = await API.refreshData();

if (response.isSuccess()) {
    console.log('成功:', response.getMessage());
    console.log('統計:', response.getData().stats);
} else {
    console.error('エラーコード:', response.getErrorCode());
    console.error('メッセージ:', response.getErrorMessage());
    console.error('詳細:', response.getErrorDetails());
}

// アラート表示
displayApiAlert(response);
```

### Pythonでの使用例

```python
import requests

response = requests.get('http://localhost:5000/api/refresh-data')
result = response.json()

if result['success']:
    print(f"成功: {result['message']}")
    print(f"統計: {result['data']['stats']}")
else:
    error = result['error']
    print(f"エラーコード: {error['code']}")
    print(f"メッセージ: {error['message']}")
    print(f"詳細: {error['details']}")
```

### cURLでの使用例

```bash
curl -X GET http://localhost:5000/api/refresh-data
```

## ヘッダー

すべてのAPIレスポンスには以下のヘッダーが含まれます:

```
Content-Type: application/json; charset=utf-8
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

## テスト

```bash
# テストスクリプトの実行
python3 tests/test_api_response_format.py
```

## ドキュメント

- 詳細仕様: `docs/API_RESPONSE_FORMAT.md`
- 改善レポート: `docs/IMPROVEMENT_API_RESPONSE_FORMAT.md`
- JavaScriptクライアント: `app/static/js/api-client.js`
