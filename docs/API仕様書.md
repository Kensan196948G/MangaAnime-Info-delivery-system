# メール配信システム API仕様書

## 📋 目次

1. [概要](#概要)
2. [認証](#認証)
3. [メール送信API](#メール送信api)
4. [データベースAPI](#データベースapi)
5. [設定管理API](#設定管理api)
6. [監視・統計API](#監視統計api)
7. [エラーハンドリング](#エラーハンドリング)
8. [レート制限](#レート制限)
9. [SDK使用例](#sdk使用例)

---

## 概要

### API バージョン
- **バージョン**: v1.0
- **プロトコル**: HTTP/HTTPS
- **データ形式**: JSON
- **文字エンコーディング**: UTF-8

### ベースURL
```
http://localhost:5000/api/v1
```

### 共通レスポンス形式
```json
{
  "success": true,
  "data": {},
  "message": "操作が正常に完了しました",
  "timestamp": "2024-08-15T12:00:00Z",
  "request_id": "req_1234567890"
}
```

---

## 認証

### API キー認証
```http
Authorization: Bearer YOUR_API_KEY
```

### OAuth2（Gmail API用）
```http
Authorization: Bearer OAUTH2_ACCESS_TOKEN
```

### API キー生成
```python
# scripts/generate_api_key.py
import secrets
import hashlib

def generate_api_key():
    """APIキーを生成"""
    key = secrets.token_urlsafe(32)
    hash_key = hashlib.sha256(key.encode()).hexdigest()
    
    print(f"API Key: {key}")
    print(f"Hash: {hash_key}")
    
    # config.json に追加
    config = {
        "api_keys": {
            hash_key: {
                "name": "admin",
                "permissions": ["read", "write", "admin"],
                "created_at": "2024-08-15T12:00:00Z"
            }
        }
    }
    
    return key

if __name__ == "__main__":
    generate_api_key()
```

---

## メール送信API

### 1. 単一メール送信

#### エンドポイント
```http
POST /api/v1/mail/send
```

#### リクエスト
```json
{
  "to": "kensan1969@gmail.com",
  "subject": "[MangaAnime] テストメール",
  "html_content": "<h1>テスト内容</h1>",
  "text_content": "テスト内容",
  "priority": "normal",
  "attachments": [
    {
      "filename": "image.jpg",
      "content_type": "image/jpeg",
      "data": "base64_encoded_data"
    }
  ]
}
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "message_id": "msg_1234567890",
    "sent_at": "2024-08-15T12:00:00Z",
    "to": "kensan1969@gmail.com",
    "subject": "[MangaAnime] テストメール"
  },
  "message": "メールを送信しました"
}
```

#### Python例
```python
import requests

response = requests.post(
    'http://localhost:5000/api/v1/mail/send',
    headers={
        'Authorization': 'Bearer YOUR_API_KEY',
        'Content-Type': 'application/json'
    },
    json={
        'to': 'kensan1969@gmail.com',
        'subject': 'テストメール',
        'html_content': '<h1>こんにちは</h1>',
        'text_content': 'こんにちは'
    }
)

print(response.json())
```

### 2. バッチメール送信

#### エンドポイント
```http
POST /api/v1/mail/send/batch
```

#### リクエスト
```json
{
  "template": "release_notification",
  "recipients": ["kensan1969@gmail.com"],
  "data": {
    "releases": [
      {
        "title": "進撃の巨人",
        "type": "anime",
        "platform": "dアニメストア",
        "episode": "25",
        "release_date": "2024-08-15"
      }
    ],
    "date_str": "2024年8月15日"
  },
  "schedule": {
    "send_at": "2024-08-15T08:00:00Z",
    "batch_size": 50,
    "delay_between_batches": 2
  }
}
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_1234567890",
    "total_recipients": 1,
    "estimated_send_time": "2024-08-15T08:05:00Z",
    "status": "scheduled"
  },
  "message": "バッチ送信をスケジュールしました"
}
```

### 3. メール送信状況確認

#### エンドポイント
```http
GET /api/v1/mail/status/{message_id}
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "message_id": "msg_1234567890",
    "status": "delivered",
    "sent_at": "2024-08-15T12:00:00Z",
    "delivered_at": "2024-08-15T12:00:05Z",
    "recipient": "kensan1969@gmail.com",
    "retry_count": 0
  }
}
```

---

## データベースAPI

### 1. リリース一覧取得

#### エンドポイント
```http
GET /api/v1/releases
```

#### クエリパラメータ
- `limit` (int): 取得件数（デフォルト: 50）
- `offset` (int): オフセット（デフォルト: 0）
- `notified` (bool): 通知状態でフィルタ
- `type` (string): anime/manga でフィルタ
- `platform` (string): プラットフォームでフィルタ
- `date_from` (string): 開始日（YYYY-MM-DD）
- `date_to` (string): 終了日（YYYY-MM-DD）

#### リクエスト例
```http
GET /api/v1/releases?limit=100&notified=false&type=anime
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "releases": [
      {
        "id": 1,
        "work_id": 1,
        "title": "進撃の巨人",
        "type": "anime",
        "release_type": "episode",
        "number": "25",
        "platform": "dアニメストア",
        "release_date": "2024-08-15",
        "notified": false,
        "created_at": "2024-08-15T10:00:00Z"
      }
    ],
    "total": 1041,
    "limit": 100,
    "offset": 0,
    "has_next": true
  }
}
```

### 2. リリース詳細取得

#### エンドポイント
```http
GET /api/v1/releases/{release_id}
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "id": 1,
    "work": {
      "id": 1,
      "title": "進撃の巨人",
      "title_kana": "しんげきのきょじん",
      "title_en": "Attack on Titan",
      "type": "anime",
      "official_url": "https://example.com"
    },
    "release_type": "episode",
    "number": "25",
    "platform": "dアニメストア",
    "release_date": "2024-08-15",
    "source": "anilist",
    "source_url": "https://anilist.co/anime/123",
    "notified": false,
    "notification_history": []
  }
}
```

### 3. リリース作成

#### エンドポイント
```http
POST /api/v1/releases
```

#### リクエスト
```json
{
  "work": {
    "title": "新作アニメ",
    "title_kana": "しんさくあにめ",
    "title_en": "New Anime",
    "type": "anime",
    "official_url": "https://example.com"
  },
  "release_type": "episode",
  "number": "1",
  "platform": "Netflix",
  "release_date": "2024-08-16",
  "source": "manual",
  "source_url": "https://example.com"
}
```

### 4. 通知状態更新

#### エンドポイント
```http
PATCH /api/v1/releases/{release_id}/notification
```

#### リクエスト
```json
{
  "notified": true,
  "notification_details": {
    "sent_at": "2024-08-15T12:00:00Z",
    "message_id": "msg_1234567890",
    "recipient": "kensan1969@gmail.com"
  }
}
```

---

## 設定管理API

### 1. システム設定取得

#### エンドポイント
```http
GET /api/v1/config
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "email": {
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "sender_email": "kensan1969@gmail.com"
    },
    "notification": {
      "batch_size": 50,
      "delay_between_batches": 2,
      "max_retries": 3
    },
    "schedule": {
      "distribution": {
        "small": {
          "threshold": 100,
          "times": ["08:00"]
        }
      }
    }
  }
}
```

### 2. 設定更新

#### エンドポイント
```http
PUT /api/v1/config
```

#### リクエスト
```json
{
  "notification": {
    "batch_size": 30,
    "delay_between_batches": 3
  }
}
```

### 3. スケジュール管理

#### エンドポイント
```http
GET /api/v1/schedule
POST /api/v1/schedule
DELETE /api/v1/schedule/{schedule_id}
```

---

## 監視・統計API

### 1. システム状態取得

#### エンドポイント
```http
GET /api/v1/system/status
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "status": "running",
    "uptime": 86400,
    "database": {
      "status": "connected",
      "total_works": 500,
      "total_releases": 1301,
      "pending_notifications": 1041
    },
    "email": {
      "status": "authenticated",
      "last_sent": "2024-08-15T11:30:00Z",
      "daily_sent": 45,
      "daily_limit": 250
    },
    "cron_jobs": {
      "active": true,
      "last_run": "2024-08-15T08:00:00Z",
      "next_run": "2024-08-15T12:00:00Z"
    }
  }
}
```

### 2. 配信統計取得

#### エンドポイント
```http
GET /api/v1/stats/delivery
```

#### クエリパラメータ
- `period` (string): day/week/month
- `date_from` (string): 開始日
- `date_to` (string): 終了日

#### レスポンス
```json
{
  "success": true,
  "data": {
    "period": "week",
    "date_range": {
      "from": "2024-08-08",
      "to": "2024-08-15"
    },
    "summary": {
      "total_sent": 245,
      "total_failed": 5,
      "success_rate": 98.0,
      "avg_send_time": 2.3
    },
    "daily_breakdown": [
      {
        "date": "2024-08-15",
        "sent": 45,
        "failed": 1,
        "success_rate": 97.8
      }
    ],
    "platform_breakdown": [
      {
        "platform": "Netflix",
        "count": 89,
        "percentage": 36.3
      }
    ]
  }
}
```

### 3. エラーログ取得

#### エンドポイント
```http
GET /api/v1/logs/errors
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "errors": [
      {
        "timestamp": "2024-08-15T11:45:00Z",
        "level": "ERROR",
        "module": "mailer",
        "message": "Gmail API rate limit exceeded",
        "details": {
          "retry_count": 2,
          "next_retry": "2024-08-15T11:47:00Z"
        }
      }
    ],
    "total": 15,
    "limit": 50,
    "offset": 0
  }
}
```

---

## エラーハンドリング

### エラーレスポンス形式
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力データが無効です",
    "details": {
      "field": "email",
      "reason": "無効なメールアドレス形式"
    }
  },
  "timestamp": "2024-08-15T12:00:00Z",
  "request_id": "req_1234567890"
}
```

### エラーコード一覧

| コード | HTTPステータス | 説明 |
|--------|----------------|------|
| `VALIDATION_ERROR` | 400 | 入力データ検証エラー |
| `AUTHENTICATION_ERROR` | 401 | 認証エラー |
| `AUTHORIZATION_ERROR` | 403 | 認可エラー |
| `NOT_FOUND` | 404 | リソースが見つからない |
| `RATE_LIMIT_EXCEEDED` | 429 | レート制限超過 |
| `INTERNAL_ERROR` | 500 | 内部サーバーエラー |
| `DATABASE_ERROR` | 500 | データベースエラー |
| `EMAIL_SEND_ERROR` | 500 | メール送信エラー |

---

## レート制限

### Gmail API制限
- **1日の送信上限**: 250通
- **1分あたりのAPI呼び出し**: 250回
- **バッチサイズ**: 50通

### API制限
- **認証済みユーザー**: 1000リクエスト/時間
- **未認証ユーザー**: 100リクエスト/時間

### レート制限ヘッダー
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1692097200
```

---

## SDK使用例

### Python SDK

#### インストール
```bash
pip install mangaanime-client
```

#### 基本使用法
```python
from mangaanime import MangaAnimeClient

# クライアント初期化
client = MangaAnimeClient(
    base_url='http://localhost:5000/api/v1',
    api_key='YOUR_API_KEY'
)

# リリース一覧取得
releases = client.releases.list(
    limit=100,
    notified=False,
    type='anime'
)

# メール送信
result = client.mail.send(
    to='kensan1969@gmail.com',
    subject='テストメール',
    html_content='<h1>こんにちは</h1>',
    text_content='こんにちは'
)

# バッチ送信
batch = client.mail.send_batch(
    template='release_notification',
    recipients=['kensan1969@gmail.com'],
    data={
        'releases': releases.data['releases'][:10],
        'date_str': '2024年8月15日'
    }
)

# 統計取得
stats = client.stats.delivery(period='week')
print(f"配信成功率: {stats.data['summary']['success_rate']}%")
```

### JavaScript SDK

#### インストール
```bash
npm install mangaanime-client
```

#### 使用例
```javascript
import { MangaAnimeClient } from 'mangaanime-client';

const client = new MangaAnimeClient({
  baseURL: 'http://localhost:5000/api/v1',
  apiKey: 'YOUR_API_KEY'
});

// リリース取得
const releases = await client.releases.list({
  limit: 100,
  notified: false,
  type: 'anime'
});

// メール送信
const result = await client.mail.send({
  to: 'kensan1969@gmail.com',
  subject: 'テストメール',
  htmlContent: '<h1>こんにちは</h1>',
  textContent: 'こんにちは'
});

// システム状態確認
const status = await client.system.status();
console.log(`システム状態: ${status.data.status}`);
```

---

## Webhook

### 配信完了通知
```http
POST https://your-webhook-url.com/notifications
Content-Type: application/json

{
  "event": "email_sent",
  "data": {
    "message_id": "msg_1234567890",
    "recipient": "kensan1969@gmail.com",
    "subject": "[MangaAnime] 新着情報",
    "sent_at": "2024-08-15T12:00:00Z",
    "status": "delivered"
  },
  "timestamp": "2024-08-15T12:00:05Z"
}
```

### エラー通知
```http
POST https://your-webhook-url.com/notifications
Content-Type: application/json

{
  "event": "email_failed",
  "data": {
    "message_id": "msg_1234567890",
    "recipient": "kensan1969@gmail.com",
    "error": "Rate limit exceeded",
    "retry_count": 3,
    "next_retry": "2024-08-15T12:05:00Z"
  },
  "timestamp": "2024-08-15T12:00:00Z"
}
```

---

## API テスト

### curl例
```bash
# システム状態確認
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:5000/api/v1/system/status

# リリース一覧取得
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "http://localhost:5000/api/v1/releases?limit=10&notified=false"

# メール送信
curl -X POST \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "to": "kensan1969@gmail.com",
       "subject": "テストメール",
       "html_content": "<h1>こんにちは</h1>",
       "text_content": "こんにちは"
     }' \
     http://localhost:5000/api/v1/mail/send
```

### Postman Collection
```json
{
  "info": {
    "name": "MangaAnime API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:5000/api/v1"
    },
    {
      "key": "api_key",
      "value": "YOUR_API_KEY"
    }
  ],
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{api_key}}"
      }
    ]
  }
}
```

---

*最終更新: 2024年8月*