# 🔄 ローディング問題解決手順

**問題**: 「API設定を読み込んでいます...」で止まる
**原因**: ブラウザが古いJavaScriptをキャッシュしている

---

## ✅ 確実な解決方法

### **ブラウザキャッシュを完全にクリア**

**1. Ctrl + Shift + Delete を押す**

**2. 以下を選択**:
- 時間範囲: **「全期間」**
- 削除項目:
  - ✅ **キャッシュされた画像とファイル**
  - ✅ **Cookie とサイトデータ** （オプション）

**3. 「データを削除」をクリック**

**4. ブラウザを完全に閉じる**

**5. ブラウザを再起動**

**6. アクセス**:
```
http://192.168.3.135:3030/collection-settings
```

---

## 📊 サーバー側確認済み

### /api/sources ✅
```json
{
  "apis": [
    {"id": "anilist", "name": "AniList GraphQL API", ...},
    {"id": "syoboi", "name": "しょぼいカレンダー", ...}
  ],
  "rss_feeds": [...],
  "summary": {
    "total_sources": 6,
    "enabled_sources": 4
  }
}
```

**ステータス**: 正常動作

### JavaScript修正 ✅
- /api/sourcesから動的読み込み
- エラーハンドリング追加
- フォールバック表示実装

---

## 🎯 期待される動作

### 正常時
```
📡 API収集ソース

┌─ AniList GraphQL API ────┐
│ [表示内容]                │
└──────────────────────────┘

┌─ しょぼいカレンダー ─────┐
│ [表示内容]                │
└──────────────────────────┘
```

### エラー時（JavaScriptエラーの場合）
```
⚠️ API設定の読み込みに失敗しました: [エラーメッセージ]
サーバーに接続できないか、/api/sourcesエンドポイントでエラーが発生しています。
```

---

## 🐛 デバッグ手順（まだ表示されない場合）

### F12 → Console で確認

以下のいずれかが表示されるはずです：

**成功時**:
```
[CollectionSettings] Initializing...
[CollectionSettings] Loaded 2 API sources from server
[CollectionSettings] Rendered 2 API sources
```

**エラー時**:
```
[CollectionSettings] Failed to load API sources: [エラー]
```

### F12 → Network で確認

- `/api/sources`: 200 OK か確認
- `collection-settings.js`: 200 OK（キャッシュクリア後）

---

## ✅ 確認済み事項

- ✅ /api/sources: 正常動作（APIs: 2, RSS: 4）
- ✅ JavaScript: エラーハンドリング追加
- ✅ HTML: apiSourcesContainer存在
- ✅ WebUI: 稼働中

**問題はブラウザキャッシュです。**

---

🔄 **Ctrl + Shift + Delete でブラウザキャッシュを完全にクリアしてください！**

その後、ブラウザを再起動してアクセスしてください。
