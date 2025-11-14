# APIエンドポイント仕様書

## 新規追加エンドポイント

### 1. `/api/refresh-data` - データ更新エンドポイント

#### 概要
サンプルデータ投入スクリプトを実行して、最新データをデータベースに投入します。

#### リクエスト
- **メソッド**: GET
- **URL**: `/api/refresh-data`
- **認証**: 不要

#### レスポンス

**成功時 (200 OK)**
```json
{
  "success": true,
  "message": "データ更新が完了しました",
  "timestamp": "2025-11-14T10:30:00",
  "output": "サンプルデータ投入スクリプトの出力"
}
```

**エラー時 (500 Internal Server Error)**
```json
{
  "success": false,
  "error": "データ更新中にエラーが発生しました",
  "details": "エラー詳細"
}
```

**タイムアウト時 (500 Internal Server Error)**
```json
{
  "success": false,
  "error": "データ更新がタイムアウトしました"
}
```

**スクリプトが見つからない時 (404 Not Found)**
```json
{
  "success": false,
  "error": "データ投入スクリプトが見つかりません"
}
```

#### 機能詳細
1. `insert_sample_data.py` スクリプトを実行
2. 実行結果を `data/last_update.json` に保存
3. タイムアウト: 30秒
4. 実行時のログを記録

---

### 2. `/api/data-status` - データステータスエンドポイント

#### 概要
最後のデータ更新時刻とデータベースの統計情報を返します。

#### リクエスト
- **メソッド**: GET
- **URL**: `/api/data-status`
- **認証**: 不要

#### レスポンス

**成功時 (200 OK)**
```json
{
  "last_update": "2025-11-14T10:30:00",
  "update_success": true,
  "statistics": {
    "total_works": 12,
    "total_releases": 23,
    "anime_count": 7,
    "manga_count": 5,
    "pending_notifications": 10,
    "recent_releases": 15
  },
  "platforms": [
    {"platform": "dアニメストア", "count": 8},
    {"platform": "Netflix", "count": 5},
    {"platform": "BookWalker", "count": 10}
  ],
  "database_size": 245760,
  "timestamp": "2025-11-14T11:00:00"
}
```

**エラー時 (500 Internal Server Error)**
```json
{
  "success": false,
  "error": "エラーメッセージ"
}
```

#### レスポンスフィールド説明

| フィールド | 型 | 説明 |
|----------|-----|------|
| last_update | string/null | 最終更新時刻 (ISO 8601形式) |
| update_success | boolean/null | 最終更新の成功可否 |
| statistics.total_works | integer | 総作品数 |
| statistics.total_releases | integer | 総リリース数 |
| statistics.anime_count | integer | アニメ作品数 |
| statistics.manga_count | integer | マンガ作品数 |
| statistics.pending_notifications | integer | 未通知リリース数 |
| statistics.recent_releases | integer | 直近7日間のリリース数 |
| platforms | array | プラットフォーム別リリース数 |
| database_size | integer | データベースファイルサイズ (バイト) |
| timestamp | string | レスポンス生成時刻 |

---

## 自動データ投入機能

### 起動時自動投入

アプリケーション起動時、データベースが空の場合は自動的にサンプルデータを投入します。

#### 動作フロー
1. データベースの作品数をチェック
2. 作品数が0の場合、`insert_sample_data.py` を実行
3. 実行結果を `data/last_update.json` に保存
4. ログに実行結果を記録

#### ログ出力例
```
INFO - データベースが空です。サンプルデータを自動投入します...
INFO - サンプルデータ投入スクリプトを実行: /path/to/insert_sample_data.py
INFO - サンプルデータの投入が完了しました
```

---

## 最終更新時刻の記録

### 保存先
`data/last_update.json`

### ファイル形式
```json
{
  "last_update": "2025-11-14T10:30:00",
  "success": true,
  "output": "スクリプト実行時の標準出力",
  "error": null,
  "type": "auto_init"
}
```

### フィールド説明

| フィールド | 型 | 説明 |
|----------|-----|------|
| last_update | string | 更新時刻 (ISO 8601形式) |
| success | boolean | 更新の成功可否 |
| output | string | スクリプトの標準出力 |
| error | string/null | エラーがある場合のエラーメッセージ |
| type | string | 更新タイプ ("auto_init", "manual", etc.) |

---

## エラーハンドリング

### ログレベル

| レベル | 用途 |
|--------|------|
| INFO | 正常な処理フロー |
| WARNING | 警告（処理は継続） |
| ERROR | エラー（処理失敗） |

### ログ出力例

**成功時**
```
INFO - データ更新リクエストを受信しました
INFO - データ投入スクリプトを実行中: /path/to/script.py
INFO - データ更新が完了しました
```

**エラー時**
```
ERROR - スクリプトが見つかりません: /path/to/script.py
ERROR - データ更新エラー: [エラー詳細]
ERROR - データ更新がタイムアウトしました
```

---

## 使用例

### curlコマンド

**データ更新**
```bash
curl http://localhost:3030/api/refresh-data
```

**データステータス取得**
```bash
curl http://localhost:3030/api/data-status
```

### JavaScriptでの使用例

**データ更新**
```javascript
fetch('/api/refresh-data')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log('データ更新成功:', data.message);
    } else {
      console.error('データ更新失敗:', data.error);
    }
  });
```

**データステータス取得**
```javascript
fetch('/api/data-status')
  .then(response => response.json())
  .then(data => {
    console.log('最終更新:', data.last_update);
    console.log('総作品数:', data.statistics.total_works);
  });
```

---

## セキュリティ考慮事項

1. **タイムアウト制限**: スクリプト実行は30秒でタイムアウト
2. **パス検証**: スクリプトパスは絶対パスで指定し、検証済み
3. **出力サニタイズ**: スクリプトの出力はログに記録されるが、ユーザー入力は含まれない
4. **認証**: 現在は認証なし（将来的に追加を検討）

---

## 今後の改善案

1. **リアルタイム進捗通知**: Server-Sent Events (SSE) による進捗表示
2. **バックグラウンド実行**: 長時間処理をバックグラウンドジョブ化
3. **認証機能**: APIキーやOAuthによる認証追加
4. **レート制限**: DoS攻撃対策としてレート制限実装
5. **Webhook**: 更新完了時の通知機能

---

## 関連ファイル

- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/web_app.py` - Flask アプリケーション本体
- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/insert_sample_data.py` - サンプルデータ投入スクリプト
- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/last_update.json` - 最終更新記録
