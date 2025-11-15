# バックエンドAPIとデフォルト設定 - 実装完了レポート

## 実装日時
2025-11-15

## 概要
アニメ・マンガ情報配信システムに、バックエンドAPIエンドポイントとデフォルト設定機能を実装しました。

## 実装内容

### 1. データベーススキーマ拡張

#### settingsテーブルの追加
```sql
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    value_type TEXT CHECK(value_type IN ('string','integer','boolean','json')),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key);
```

#### デフォルト設定
システム起動時に以下のデフォルト設定が自動投入されます：

| キー | 値 | 型 | 説明 |
|-----|-----|-----|------|
| notification_email | kensan1969@gmail.com | string | デフォルト通知先メールアドレス |
| check_interval_hours | 1 | integer | チェック間隔（時間） |
| email_notifications_enabled | true | boolean | メール通知を有効化 |
| calendar_enabled | false | boolean | カレンダー登録を有効化 |
| max_notifications_per_day | 50 | integer | 1日あたりの最大通知数 |

### 2. データベースマネージャー拡張

**ファイル**: `modules/db.py`

#### 新規メソッド

##### `get_setting(key, default=None)`
設定値を取得し、型に応じて自動変換します。

```python
email = db.get_setting('notification_email', 'default@example.com')
interval = db.get_setting('check_interval_hours', 1)
enabled = db.get_setting('email_notifications_enabled', True)
```

##### `set_setting(key, value, value_type='string', description='')`
設定値を保存または更新します。

```python
db.set_setting('notification_email', 'new@example.com', 'string', '通知先メール')
db.set_setting('check_interval_hours', 2, 'integer', 'チェック間隔')
db.set_setting('email_notifications_enabled', False, 'boolean', '通知有効化')
```

##### `get_all_settings()`
すべての設定を辞書形式で取得します。

```python
settings = db.get_all_settings()
# => {
#     'notification_email': 'kensan1969@gmail.com',
#     'check_interval_hours': 1,
#     'email_notifications_enabled': True,
#     'calendar_enabled': False,
#     'max_notifications_per_day': 50
# }
```

##### `update_settings(settings)`
複数の設定を一括更新します。

```python
db.update_settings({
    'check_interval_hours': 2,
    'email_notifications_enabled': False
})
```

### 3. APIエンドポイント

**ファイル**: `app/web_app.py`

#### GET /api/settings
現在の設定を取得します。

**レスポンス例:**
```json
{
    "success": true,
    "settings": {
        "notification_email": "kensan1969@gmail.com",
        "check_interval_hours": 1,
        "email_notifications_enabled": true,
        "calendar_enabled": false,
        "max_notifications_per_day": 50
    }
}
```

#### POST /api/settings
設定を更新します。

**リクエストボディ例:**
```json
{
    "notification_email": "newemail@example.com",
    "check_interval_hours": 2,
    "email_notifications_enabled": false
}
```

**レスポンス例:**
```json
{
    "success": true,
    "message": "設定を保存しました",
    "settings": {
        "notification_email": "newemail@example.com",
        "check_interval_hours": 2,
        "email_notifications_enabled": false,
        "calendar_enabled": false,
        "max_notifications_per_day": 50
    }
}
```

#### POST /api/refresh-upcoming
今後の予定を更新します。

**レスポンス例:**
```json
{
    "success": true,
    "message": "今後の予定を更新しました",
    "timestamp": "2025-11-15T10:30:00",
    "count": 0
}
```

#### POST /api/refresh-history
リリース履歴を更新します。

**レスポンス例:**
```json
{
    "success": true,
    "message": "リリース履歴を更新しました",
    "timestamp": "2025-11-15T10:30:00",
    "count": 0
}
```

### 4. フロントエンド実装

**ファイル**: `templates/collection_settings.html`

#### 設定フォームフィールド
通知設定タブに以下のフィールドを追加：

- **通知先メールアドレス** (name="notification_email")
  - デフォルト: kensan1969@gmail.com
  - 入力タイプ: email

- **チェック間隔（時間）** (name="check_interval_hours")
  - デフォルト: 1
  - 入力タイプ: number (1-24)

- **1日あたりの最大通知数** (name="max_notifications_per_day")
  - デフォルト: 50
  - 入力タイプ: number (1-200)

- **メール通知を有効にする** (name="email_notifications_enabled")
  - デフォルト: checked
  - 入力タイプ: checkbox

- **Googleカレンダーへの登録を有効にする** (name="calendar_enabled")
  - デフォルト: unchecked
  - 入力タイプ: checkbox

#### JavaScript機能

##### `loadSettings()`
ページ読み込み時に設定を取得してフォームに反映します。

```javascript
async function loadSettings() {
    const response = await fetch('/api/settings');
    const data = await response.json();
    // フォームフィールドに設定値を反映
}
```

##### `saveAllSettings()`
フォームの値を収集してAPIに送信します。

```javascript
async function saveAllSettings() {
    const settings = {
        notification_email: emailInput.value,
        check_interval_hours: parseInt(intervalInput.value),
        // ...
    };

    const response = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    });
}
```

### 5. config.json更新

**ファイル**: `config.json`

新しい`settings`セクションを追加：

```json
{
    "settings": {
        "notification_email": "kensan1969@gmail.com",
        "check_interval_hours": 1,
        "email_notifications_enabled": true,
        "calendar_enabled": false,
        "max_notifications_per_day": 50
    }
}
```

## テスト結果

### データベーステスト
```
Database health score: 1.00
Performance grade: A

Current settings:
- notification_email: kensan1969@gmail.com (str)
- check_interval_hours: 1 (int)
- email_notifications_enabled: True (bool)
- calendar_enabled: False (bool)
- max_notifications_per_day: 50 (int)
```

### 設定更新テスト
- 設定の取得: ✅ 成功
- 設定の更新: ✅ 成功
- 型変換: ✅ 正常動作（string, integer, boolean）
- 一括更新: ✅ 成功

## 使用方法

### 1. データベース初期化
データベースは自動的にsettingsテーブルを作成し、デフォルト値を投入します。

```python
from modules.db import DatabaseManager

db = DatabaseManager('./db.sqlite3')
# settingsテーブルが自動作成され、デフォルト値が投入される
```

### 2. 設定の取得
```python
from modules.db import get_db

db = get_db()
email = db.get_setting('notification_email', 'default@example.com')
interval = db.get_setting('check_interval_hours', 1)
```

### 3. 設定の更新
```python
db.update_settings({
    'notification_email': 'new@example.com',
    'check_interval_hours': 2
})
```

### 4. Web UIから設定
1. ブラウザで `http://localhost:5000/collection-settings` にアクセス
2. 「通知設定」タブを選択
3. 設定値を入力
4. 「すべて保存」ボタンをクリック

## ファイル一覧

### 修正ファイル
- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/modules/db.py`
- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/web_app.py`
- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/templates/collection_settings.html`
- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config.json`

### 新規ファイル
- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/docs/API_SETTINGS_IMPLEMENTATION.md` (このファイル)

## 次のステップ

### 推奨される改善
1. 設定のバリデーション強化
   - メールアドレスの形式チェック
   - 数値範囲の検証

2. 設定のエクスポート/インポート機能
   - JSON形式での設定バックアップ
   - 設定の復元機能

3. 設定変更履歴の記録
   - 誰がいつ変更したかの記録
   - 変更前後の値の保存

4. 設定プリセット機能
   - よく使う設定の保存
   - ワンクリックでの設定切り替え

## まとめ

バックエンドAPIとデフォルト設定機能の実装が完了しました。以下の要件をすべて満たしています：

- ✅ APIエンドポイント追加（/api/refresh-upcoming, /api/refresh-history, /api/settings）
- ✅ デフォルト設定の実装（通知先、チェック間隔、通知有効化など）
- ✅ settingsテーブルの作成とデフォルト値の自動投入
- ✅ 設定UI連携（フォームからの読み込み・保存）

すべての機能が正常に動作し、テストも成功しています。
