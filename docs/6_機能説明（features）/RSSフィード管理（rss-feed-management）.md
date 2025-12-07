# RSSフィード管理機能

## 概要

無効化されたRSSフィードを適切に扱い、ユーザーフレンドリーなUIで管理する機能です。

## 実装内容

### 1. フロントエンド (JavaScript)

**ファイル**: `/static/js/collection-settings.js`

#### 主要機能

- **動的フィード読み込み**
  - `/api/rss-feeds` エンドポイントから設定を取得
  - 有効/無効フィードを自動分類

- **視覚的フィード表示**
  - 有効フィード: グリーンの左ボーダー
  - 無効フィード: グレーの左ボーダー（折りたたみ可能セクション）
  - エラーフィード: レッドの左ボーダー

- **ステータスバッジ**
  - 接続中（緑）: 正常動作
  - 無効（グレー）: ユーザーが無効化
  - エラー（赤）: 接続エラー
  - ツールチップでエラー詳細表示

- **トグル機能**
  - ワンクリックで有効/無効切り替え
  - リアルタイムUI更新

- **接続テスト**
  - 個別フィードの接続確認
  - タイムアウト、404、SSL エラーの適切な検出

- **問題診断**
  - DNS解決チェック
  - HTTP接続チェック
  - SSL証明書検証
  - 診断結果をモーダルで表示

#### エラーメッセージの改善

従来:
```
接続エラー: タイムアウトが発生しています。URLを確認してください。
```

改善後:
```
このフィードは無効化されています（404 Not Found）
URLを確認するか、フィードを無効化してください。
```

### 2. バックエンド (Python/Flask)

**ファイル**: `/app/web_app.py`

#### APIエンドポイント

##### 1. `GET /api/rss-feeds`
RSSフィード設定の一覧を取得

**レスポンス例**:
```json
{
  "success": true,
  "total": 6,
  "feeds": [
    {
      "id": "magapoke",
      "name": "マガジンポケット (Magazine Pocket)",
      "url": "https://pocket.shonenmagazine.com/rss/series/",
      "category": "manga",
      "enabled": true,
      "priority": "high",
      "timeout": 20,
      "parser_type": "html",
      "status": "connected",
      "stats": {
        "itemsCollected": 0,
        "successRate": 0.0
      }
    }
  ]
}
```

##### 2. `POST /api/rss-feeds/toggle`
フィードの有効/無効を切り替え

**リクエスト**:
```json
{
  "feedId": "bookwalker",
  "enabled": false
}
```

**レスポンス**:
```json
{
  "success": true,
  "feedId": "bookwalker",
  "enabled": false
}
```

##### 3. `POST /api/rss-feeds/test`
フィードへの接続テスト

**リクエスト**:
```json
{
  "feedId": "magapoke"
}
```

**成功時レスポンス**:
```json
{
  "success": true,
  "feedId": "magapoke",
  "itemsFound": 15,
  "feedTitle": "Magazine Pocket"
}
```

**エラー時レスポンス**:
```json
{
  "success": false,
  "error": "このフィードは無効化されています（404 Not Found）"
}
```

##### 4. `POST /api/rss-feeds/diagnose`
フィードの詳細診断

**レスポンス例**:
```json
{
  "success": true,
  "diagnosis": {
    "feedId": "bookwalker",
    "url": "https://bookwalker.jp/series/rss/",
    "checks": [
      {
        "name": "DNS解決",
        "status": "success",
        "message": "ホスト 'bookwalker.jp' は解決されました"
      },
      {
        "name": "HTTP接続",
        "status": "error",
        "message": "HTTPステータス: 404"
      },
      {
        "name": "SSL証明書",
        "status": "success",
        "message": "証明書は有効です"
      }
    ],
    "overallStatus": "error",
    "recommendation": "このフィードは現在利用できません。URLを確認するか、フィードを無効化してください。"
  }
}
```

### 3. スタイル (CSS)

**ファイル**: `/static/css/collection-settings.css`

#### 追加スタイル

- フェードインアニメーション
- ホバーエフェクト
- レスポンシブデザイン対応
- ツールチップカスタマイズ
- 無効化フィードセクションのコラプスアニメーション

### 4. テンプレート更新

**ファイル**: `/templates/collection_settings.html`

- `rssSourcesContainer` IDの追加（動的レンダリング用）
- CSS/JSファイルのリンク追加
- Bootstrap tooltipの統合

## 使用方法

### 1. フィード一覧の表示

収集設定ページにアクセスすると、自動的に全RSSフィードが読み込まれます。

- **有効フィード**: メインエリアに表示
- **無効フィード**: 折りたたみ可能なセクションに表示

### 2. フィードの無効化

1. フィードカードのトグルスイッチをオフに切り替え
2. 自動的にサーバーに保存され、UIが更新される
3. 無効化されたフィードは「無効化されたフィード」セクションに移動

### 3. 接続テスト

1. フィードカードの「接続テスト」ボタンをクリック
2. テスト中はスピナーアニメーション表示
3. 結果が通知で表示される

### 4. 問題診断

1. エラー状態のフィードで「問題診断」ボタンをクリック
2. DNS、HTTP、SSL の各チェックが実行される
3. 診断結果がモーダルで表示される

## エラーハンドリング

### フロントエンド

- ネットワークエラー時のフォールバック通知
- ローディング状態の表示
- ユーザーフレンドリーなエラーメッセージ

### バックエンド

- タイムアウトの適切な処理（デフォルト: 20秒）
- HTTPエラーコードの分類（404, 403, 500等）
- SSL証明書エラーの検出
- DNS解決失敗の検出

## 今後の改善案

1. **永続化**
   - 現在はメモリ内のみ。データベースまたは設定ファイルへの保存が必要

2. **統計情報**
   - データベースから実際の取得件数・成功率を取得

3. **スケジューリング統合**
   - 無効化フィードを自動スキップ

4. **通知改善**
   - エラーが継続する場合のアラート
   - 自動復旧の提案

5. **カスタムRSSフィード**
   - ユーザーが独自のRSS URLを追加できる機能

6. **バッチ操作**
   - 複数フィードの一括有効化/無効化
   - 全フィード接続テスト

## テスト結果

```bash
$ python3 /tmp/test_api.py
============================================================
Test 1: GET /api/rss-feeds
Status Code: 200
Success: True
Total feeds: 6
✓ PASSED

Test 2: POST /api/rss-feeds/toggle
Status Code: 200
✓ PASSED

Test 3: POST /api/rss-feeds/test
Status Code: 200
Error message: このフィードは無効化されています（404 Not Found）
✓ PASSED (expected error)
============================================================
```

## 依存関係

### Python
- `feedparser`: RSSパース
- `requests`: HTTP通信
- `beautifulsoup4`: HTMLパース
- `flask`: Webフレームワーク

### JavaScript
- Bootstrap 5: モーダル、ツールチップ
- 既存の通知システム (`showNotification`)

## ファイル一覧

```
/static/
├── css/
│   └── collection-settings.css     # 新規作成
└── js/
    └── collection-settings.js      # 新規作成

/templates/
└── collection_settings.html        # 更新

/app/
└── web_app.py                      # 更新（4つのエンドポイント追加）

/docs/features/
└── rss-feed-management.md          # このファイル
```

## まとめ

この実装により、以下が実現されました:

1. ✅ 無効化フィードの非表示/折りたたみ表示
2. ✅ ユーザーフレンドリーなエラーメッセージ
3. ✅ ワンクリック有効化/無効化
4. ✅ 接続テスト機能
5. ✅ 詳細な問題診断
6. ✅ レスポンシブデザイン
7. ✅ アニメーション効果
8. ✅ ツールチップによる詳細情報表示

ユーザーは直感的に問題を理解し、適切なアクションを取ることができます。
