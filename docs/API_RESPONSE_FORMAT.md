# API レスポンス形式ガイド

## 概要

このドキュメントでは、アニメ・マンガ情報配信システムのAPIエンドポイントで使用される統一されたレスポンス形式について説明します。

## 標準レスポンス形式

すべてのAPIエンドポイントは、以下の統一された形式でレスポンスを返します。

### 成功レスポンス

```json
{
  "success": true,
  "message": "操作が成功しました",
  "data": {
    "timestamp": "2025-11-14T10:30:00.000000",
    "output": "処理結果の詳細...",
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

### エラーレスポンス

```json
{
  "success": false,
  "message": "エラーが発生しました",
  "data": null,
  "error": {
    "message": "エラーメッセージ",
    "details": "詳細なエラー情報",
    "code": "ERROR_CODE"
  }
}
```

## レスポンスフィールド

| フィールド | 型 | 必須 | 説明 |
|----------|-----|------|------|
| `success` | boolean | ✓ | 操作が成功したかどうか |
| `message` | string | ✓ | 人間が読めるメッセージ |
| `data` | object/null | ✓ | レスポンスデータ（成功時） |
| `error` | object/null | ✓ | エラー情報（失敗時） |

### errorオブジェクト

| フィールド | 型 | 必須 | 説明 |
|----------|-----|------|------|
| `message` | string | ✓ | エラーメッセージ |
| `details` | string | - | 詳細なエラー情報 |
| `code` | string | - | エラーコード |

## HTTPステータスコード

| コード | 説明 | 使用例 |
|-------|------|--------|
| 200 | OK | 成功 |
| 400 | Bad Request | 不正なリクエスト |
| 404 | Not Found | リソースが見つからない |
| 500 | Internal Server Error | サーバーエラー |

## エラーコード一覧

### `/api/refresh-data` エンドポイント

| コード | 説明 |
|-------|------|
| `SCRIPT_NOT_FOUND` | データ投入スクリプトが見つからない |
| `UPDATE_FAILED` | データ更新処理が失敗 |
| `TIMEOUT` | 処理がタイムアウト |
| `INTERNAL_ERROR` | 予期しない内部エラー |

## CORSヘッダー

すべての `/api/*` エンドポイントには、以下のCORSヘッダーが自動的に追加されます。

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Content-Type: application/json; charset=utf-8
```

## 使用例

### JavaScript (Fetch API)

```javascript
// データ更新APIの呼び出し
async function refreshData() {
  try {
    const response = await fetch('/api/refresh-data');
    const result = await response.json();

    if (result.success) {
      console.log('成功:', result.message);
      console.log('統計:', result.data.stats);
    } else {
      console.error('エラー:', result.error.message);
      console.error('詳細:', result.error.details);
      console.error('コード:', result.error.code);
    }
  } catch (error) {
    console.error('通信エラー:', error);
  }
}
```

### Python (requests)

```python
import requests

def refresh_data():
    try:
        response = requests.get('http://localhost:5000/api/refresh-data')
        result = response.json()

        if result['success']:
            print(f"成功: {result['message']}")
            print(f"統計: {result['data']['stats']}")
        else:
            error = result['error']
            print(f"エラー: {error['message']}")
            print(f"詳細: {error.get('details', '')}")
            print(f"コード: {error.get('code', '')}")
    except Exception as e:
        print(f"通信エラー: {e}")
```

## ヘルパー関数

### create_api_response()

標準的なAPIレスポンスを生成します。

```python
def create_api_response(success, message, data=None, error=None, status_code=200):
    """
    標準化されたAPIレスポンスを作成

    Args:
        success (bool): 操作が成功したかどうか
        message (str): 人間が読めるメッセージ
        data (dict, optional): レスポンスデータ
        error (dict, optional): エラー情報
        status_code (int): HTTPステータスコード

    Returns:
        Flask response object
    """
```

#### 使用例

```python
# 成功レスポンス
return create_api_response(
    success=True,
    message="データ更新が完了しました",
    data={
        "timestamp": datetime.now().isoformat(),
        "count": 100
    }
)

# エラーレスポンス（詳細版）
return create_api_response(
    success=False,
    message="エラーが発生しました",
    error={
        "message": "処理に失敗しました",
        "details": "詳細なエラー情報",
        "code": "PROCESSING_ERROR"
    },
    status_code=500
)
```

### create_error_response()

エラーレスポンスを簡単に生成します。

```python
def create_error_response(message, details=None, code=None, status_code=500):
    """
    標準化されたエラーレスポンスを作成

    Args:
        message (str): エラーメッセージ
        details (str, optional): 詳細情報
        code (str, optional): エラーコード
        status_code (int): HTTPステータスコード

    Returns:
        Flask response object
    """
```

#### 使用例

```python
# シンプルなエラー
return create_error_response(
    message="リソースが見つかりません",
    status_code=404
)

# 詳細なエラー
return create_error_response(
    message="データベースエラー",
    details="接続がタイムアウトしました",
    code="DB_TIMEOUT",
    status_code=500
)
```

## ベストプラクティス

1. **常に統一された形式を使用する**
   - すべてのAPIエンドポイントで同じレスポンス形式を使用します
   - `create_api_response()` または `create_error_response()` を使用します

2. **適切なHTTPステータスコードを設定する**
   - 成功: 200
   - クライアントエラー: 400, 404
   - サーバーエラー: 500

3. **詳細なエラー情報を提供する**
   - `error.message`: ユーザー向けのメッセージ
   - `error.details`: デバッグ用の詳細情報
   - `error.code`: プログラムで判定可能なエラーコード

4. **適切なContent-Typeを設定する**
   - すべてのJSONレスポンスに `Content-Type: application/json; charset=utf-8` が自動設定されます

5. **ログを記録する**
   - エラー時は `logger.error()` でログを記録します
   - 重要な操作は `logger.info()` でログを記録します

## 既存のエンドポイントへの適用

既存のAPIエンドポイントは段階的に新しい形式に移行します。

### 移行済み
- ✅ `/api/refresh-data`

### 移行予定
- `/api/stats`
- `/api/collection-status`
- `/api/works`
- `/api/manual-collection`
- その他すべてのAPIエンドポイント

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-11-14 | 1.0.0 | 初版作成、統一レスポンス形式の定義 |
