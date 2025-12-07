# 🔄 ブラウザキャッシュクリア手順

**問題**: API収集ソースが表示されない
**原因**: ブラウザが古いHTML/JavaScriptをキャッシュしている

---

## ✅ 解決方法

### 方法1: ハードリフレッシュ（最速）

**Windows/Linux**:
```
Ctrl + Shift + R
```

**Mac**:
```
Cmd + Shift + R
```

### 方法2: ブラウザキャッシュクリア（確実）

**1. Chromeの場合**:
```
1. Ctrl + Shift + Delete
2. 「時間範囲」を「全期間」に選択
3. 「キャッシュされた画像とファイル」をチェック
4. 「データを削除」をクリック
5. ページを再読み込み
```

**2. Firefoxの場合**:
```
1. Ctrl + Shift + Delete
2. 「すべての履歴」を選択
3. 「キャッシュ」をチェック
4. 「今すぐ消去」をクリック
5. ページを再読み込み
```

**3. Edgeの場合**:
```
1. Ctrl + Shift + Delete
2. 「時間の範囲」を「すべて」に選択
3. 「キャッシュされた画像とファイル」をチェック
4. 「今すぐクリア」をクリック
5. ページを再読み込み
```

### 方法3: シークレット/プライベートモード（一時的確認）

**Chrome**:
```
Ctrl + Shift + N
```

**Firefox**:
```
Ctrl + Shift + P
```

シークレットモードで以下にアクセス:
```
http://192.168.3.135:3030/collection-settings
```

---

## 🎯 期待される表示

キャッシュクリア後、以下が表示されます：

```
┌─────────────────────────────────┐
│ 📡 API収集ソース                 │
│                                  │
│ ┌─ AniList GraphQL API ─────┐  │
│ │ URL: https://graphql.anilist.co
│ │ レート制限: 90 requests/min
│ │ ステータス: ✅ 接続成功
│ │ 取得作品数: 1,247
│ │ 成功率: 98.5%
│ │ [接続テスト] [ON/OFFトグル]
│ └───────────────────────────┘  │
│                                  │
│ ┌─ しょぼいカレンダーAPI ───┐  │
│ │ URL: http://cal.syoboi.jp
│ │ レート制限: 60 requests/min
│ │ ステータス: ✅ 接続成功
│ │ 放送局数: 89
│ │ 成功率: 87.2%
│ │ [接続テスト] [ON/OFFトグル]
│ └───────────────────────────┘  │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 📰 RSS収集ソース                │
│                                  │
│ ✅ 少年ジャンプ+                 │
│ ✅ となりのヤングジャンプ        │
└─────────────────────────────────┘
```

---

## 🔧 確認手順

1. **ブラウザキャッシュをクリア**（上記方法のいずれか）
2. **ページにアクセス**
   ```
   http://192.168.3.135:3030/collection-settings
   ```
3. **「収集ソース」タブをクリック**
4. **API収集ソースセクションが表示されることを確認**

---

## 🐛 まだ表示されない場合

### デバッグ手順

1. **ブラウザの開発者ツールを開く**
   ```
   F12キー
   ```

2. **Consoleタブを確認**
   - エラーメッセージがないか確認
   - 以下のログが表示されるはずです：
     ```
     [CollectionSettings] Initializing...
     [CollectionSettings] Loaded 2 API sources
     [CollectionSettings] Rendered 2 API sources
     ```

3. **Networkタブを確認**
   - `collection-settings.js` が200 OKで読み込まれているか
   - `/api/rss-feeds` が200 OKか

4. **Elementsタブで確認**
   - `apiSourcesContainer`のidを持つ要素が存在するか
   - その中に`.col-lg-6`の子要素があるか

---

## 📝 実装確認

実装は完全に完了しています：

- ✅ HTML: apiSourcesContainer存在（templates/collection_settings.html:265）
- ✅ JavaScript: renderApiSources()実装（static/js/collection-settings.js:116）
- ✅ JavaScript読み込み: HTML末尾で読み込み（:1261）
- ✅ APIエンドポイント: /api/sources実装（app/web_app.py:2008）

**問題はブラウザキャッシュです。**

---

🔄 **ブラウザキャッシュをクリアしてから、再度アクセスしてください！**
