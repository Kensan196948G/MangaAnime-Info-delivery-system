# APIキー認証システム完全ガイド

## 概要

MangaAnime-Info-delivery-systemの完全なAPIキー認証システムです。外部アプリケーションやサービスから安全にAPIにアクセスするための機能を提供します。

## 主要機能

### 1. APIキー管理
- セキュアなAPIキー生成（`sk_` プレフィックス + 32バイトランダム文字列）
- キーの有効化/無効化
- キーの完全削除
- 使用状況の追跡

### 2. 権限管理
- **read**: 読み取り専用アクセス
- **write**: 書き込みアクセス
- **admin**: 管理者権限

### 3. セキュリティ機能
- キーのハッシュ化による高速検索
- ユーザー別権限チェック
- 使用回数と最終使用時刻の記録
- 無効化されたキーの自動拒否

## アーキテクチャ

```
app/routes/api_key.py
├── APIKey (データクラス)
│   ├── key: str
│   ├── user_id: str
│   ├── name: str
│   ├── created_at: datetime
│   ├── last_used: Optional[datetime]
│   ├── is_active: bool
│   ├── permissions: List[str]
│   └── usage_count: int
│
├── APIKeyStore (ストレージ)
│   ├── generate_key()
│   ├── verify_key()
│   ├── get_keys_by_user()
│   ├── revoke_key()
│   ├── delete_key()
│   └── get_stats()
│
└── api_key_required (デコレータ)
    └── 権限チェック機能
```

## インストールと設定

### 1. Blueprint登録

`app/web_app.py` に以下を追加:

```python
from app.routes.api_key import api_key_bp

app.register_blueprint(api_key_bp)
```

### 2. ナビゲーションメニューに追加

`templates/base.html` のナビゲーションメニューに追加:

```html
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('api_key.index') }}">
        <i class="fas fa-key"></i> APIキー
    </a>
</li>
```

## 使用方法

### Web UI（ユーザー向け）

#### 1. APIキーの生成

1. `/api-keys/` にアクセス
2. 「新しいAPIキーを生成」ボタンをクリック
3. キー名と権限を設定
4. 生成されたキーを安全に保存（再表示されません）

#### 2. キーの管理

- **無効化**: キーを一時的に無効化（削除はしない）
- **削除**: キーを完全に削除（取り消し不可）

### API使用例

#### cURL
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
     https://your-domain.com/api/stats
```

#### Python
```python
import requests

headers = {'X-API-Key': 'YOUR_API_KEY'}
response = requests.get('https://your-domain.com/api/stats', headers=headers)
data = response.json()
```

#### JavaScript
```javascript
fetch('https://your-domain.com/api/stats', {
    headers: {
        'X-API-Key': 'YOUR_API_KEY'
    }
})
.then(response => response.json())
.then(data => console.log(data));
```

## API実装例

### 基本的な使い方

```python
from app.routes.api_key import api_key_required
from flask import Blueprint, jsonify, g

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/data')
@api_key_required(permissions=['read'])
def get_data():
    """読み取り専用APIエンドポイント"""
    user_id = g.api_user_id  # APIキーのユーザーID
    key_name = g.api_key_name  # APIキー名

    return jsonify({
        'message': 'Success',
        'user': user_id
    })
```

### 書き込み権限が必要なAPI

```python
@api_bp.route('/api/update', methods=['POST'])
@api_key_required(permissions=['write'])
def update_data():
    """書き込み可能なAPIエンドポイント"""
    data = request.get_json()

    # データ更新処理

    return jsonify({'message': 'Updated'})
```

### 管理者権限が必要なAPI

```python
@api_bp.route('/api/admin/users')
@api_key_required(permissions=['admin'])
def manage_users():
    """管理者専用APIエンドポイント"""
    # 管理者操作

    return jsonify({'users': []})
```

### 複数の権限を許可

```python
@api_bp.route('/api/flexible')
@api_key_required(permissions=['read', 'write'])
def flexible_endpoint():
    """read または write 権限があればアクセス可能"""
    return jsonify({'message': 'OK'})
```

## エラーレスポンス

### 401 Unauthorized - APIキーなし
```json
{
    "error": "API key required",
    "message": "Please provide X-API-Key header"
}
```

### 401 Unauthorized - 無効なキー
```json
{
    "error": "Invalid API key",
    "message": "The provided API key is invalid or inactive"
}
```

### 403 Forbidden - 権限不足
```json
{
    "error": "Insufficient permissions",
    "message": "Required permissions: ['admin']",
    "your_permissions": ["read"]
}
```

## JSON API

### APIキー一覧取得
```http
GET /api-keys/api/list
Authorization: Cookie (ログイン必須)
```

**レスポンス:**
```json
{
    "api_keys": [
        {
            "key": "sk_abc123...xyz",
            "name": "Production Key",
            "user_id": "user1",
            "created_at": "2025-12-07T10:00:00",
            "last_used": "2025-12-07T15:30:00",
            "is_active": true,
            "permissions": ["read", "write"],
            "usage_count": 42
        }
    ],
    "count": 1
}
```

### APIキー生成
```http
POST /api-keys/api/generate
Content-Type: application/json
Authorization: Cookie (ログイン必須)

{
    "name": "New Key",
    "permissions": ["read"]
}
```

**レスポンス:**
```json
{
    "message": "API key generated successfully",
    "api_key": {
        "key": "sk_fullkeyhere",
        "name": "New Key",
        "permissions": ["read"]
    },
    "warning": "Save this key securely. It will not be shown again."
}
```

### APIキー無効化
```http
DELETE /api-keys/api/revoke/{key}
Authorization: Cookie (ログイン必須)
```

## 管理者機能

### 全APIキー一覧
```http
GET /api-keys/admin/all
```

管理者は全ユーザーのAPIキーを閲覧できます。

### 統計情報
```http
GET /api-keys/admin/api/stats
```

**レスポンス:**
```json
{
    "global_stats": {
        "total_keys": 50,
        "active_keys": 45,
        "inactive_keys": 5,
        "total_usage": 1234
    },
    "user_stats": {
        "user1": {
            "total": 3,
            "active": 2,
            "usage": 100
        }
    }
}
```

## セキュリティベストプラクティス

### 1. キーの保管
- 環境変数に保存
- `.env` ファイルを `.gitignore` に追加
- 暗号化されたストレージに保存

### 2. キーのローテーション
- 定期的にキーを再生成
- 古いキーは無効化

### 3. 権限の最小化
- 必要最小限の権限のみ付与
- 用途ごとに別々のキーを使用

### 4. モニタリング
- 使用状況を定期的にチェック
- 異常なアクセスパターンを監視

## トラブルシューティング

### Q: APIキーを紛失した
**A:** セキュリティ上、再表示できません。新しいキーを生成してください。

### Q: 401エラーが発生する
**A:**
1. `X-API-Key` ヘッダーが正しく設定されているか確認
2. キーが有効か確認（Web UIで確認）
3. キーのタイプミスがないか確認

### Q: 403エラーが発生する
**A:** キーに必要な権限がありません。権限を追加した新しいキーを生成してください。

### Q: キーを大量に生成してしまった
**A:** 不要なキーは削除してください。管理画面から一括管理できます。

## データベース移行（将来の拡張）

現在はメモリベースですが、PostgreSQL/MySQLに移行する場合:

```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    permissions TEXT[] NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    INDEX idx_user_id (user_id),
    INDEX idx_key_hash (key_hash)
);
```

## テスト

```bash
# 全テスト実行
pytest tests/test_api_key_full.py -v

# カバレッジ付き
pytest tests/test_api_key_full.py --cov=app.routes.api_key --cov-report=html
```

## まとめ

このAPIキー認証システムは:
- セキュアなキー生成と管理
- 柔軟な権限管理
- 詳細な使用状況追跡
- シンプルで使いやすいUI

を提供し、外部アプリケーションからの安全なAPI利用を実現します。

---

**更新日**: 2025-12-07
**バージョン**: 1.0.0
**作成者**: Backend Developer Agent
