# Login Required Implementation Guide

## 目的
app/web_app.py に認証デコレータを追加し、保護されたルートを設定する

## 必要な変更

### 1. インポートの追加（ファイル冒頭）

```python
from flask_login import login_required, current_user
from app.routes.auth import admin_required
```

### 2. ログイン必須ルート（@login_required 追加）

以下のルートに `@login_required` デコレータを追加:

#### 設定管理
- `@app.route('/config', methods=['POST'])`

#### データソース管理
- `@app.route('/api/sources', methods=['POST'])`
- `@app.route('/api/sources/<int:source_id>', methods=['PUT'])`
- `@app.route('/api/sources/<int:source_id>', methods=['DELETE'])`

#### RSS フィード管理
- `@app.route('/api/rss-feeds', methods=['POST'])`
- `@app.route('/api/rss-feeds/<int:feed_id>', methods=['DELETE'])`
- `@app.route('/api/rss-feeds/<int:feed_id>', methods=['PUT'])`

#### 通知管理
- `@app.route('/api/notifications', methods=['POST'])`
- `@app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])`

#### データ変更系
- `@app.route('/api/works/<int:work_id>', methods=['DELETE'])`
- `@app.route('/api/releases/<int:release_id>', methods=['DELETE'])`

### 3. 管理者専用ルート（@admin_required 追加）

将来実装予定:
- `@app.route('/api/users', methods=['POST', 'DELETE'])`
- データベース全体のクリア/リセット機能

### 4. 認証不要ルート（デコレータ不要）

以下のルートは認証不要:
- `/api/health`
- `/api/status`
- `/ready`
- `/metrics`
- すべての GET専用エンドポイント（読み取り専用）
- `/login`, `/logout`, `/register`（認証関連）

## 実装例

```python
@app.route('/config', methods=['POST'])
@login_required
def update_config():
    """設定更新（ログインユーザーのみ）"""
    # 既存のコード
    pass

@app.route('/api/sources', methods=['POST'])
@login_required
def create_source():
    """新しいデータソースを作成（ログインユーザーのみ）"""
    # 既存のコード
    pass

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """ユーザー削除（管理者のみ）"""
    # 既存のコード
    pass
```

## 注意事項

1. デコレータの順序: `@app.route()` の直後に `@login_required` を配置
2. 既存の機能を壊さないこと
3. API レスポンスで 401 Unauthorized を返すこと
4. フロントエンドでログインページへのリダイレクト処理を実装すること

## テスト確認項目

- [ ] ログインなしでPOSTリクエストを送信 → 401エラー
- [ ] ログイン後にPOSTリクエストを送信 → 正常動作
- [ ] 管理者以外が管理者専用機能にアクセス → 403エラー
- [ ] GETリクエスト（読み取り）は認証なしで動作
- [ ] ヘルスチェックエンドポイントは常にアクセス可能

## 実装ステータス

- [ ] インポート追加
- [ ] /config ルート保護
- [ ] /api/sources ルート保護
- [ ] /api/rss-feeds ルート保護
- [ ] /api/notifications ルート保護
- [ ] データ削除系ルート保護
- [ ] テスト実行
- [ ] ドキュメント更新
