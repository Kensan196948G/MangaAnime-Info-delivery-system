# BookWalker RSS フィード無効化について

## 概要
BookWalker RSSフィード（https://bookwalker.jp/rss/new-releases.xml）が404 Not Foundエラーで利用できないため、完全に無効化しました。

## 実施した変更

### 1. config.json
```json
"enabled_sources": {
    "anilist": true,
    "shobo_calendar": true,
    "bookwalker_rss": false,  // 無効化
    "mangapocket_rss": true
}
```

### 2. templates/collection_settings.html
- BookWalkerセクションを「disabled」状態に変更
- チェックボックスを無効化（disabled属性追加）
- 赤いアラートメッセージで「フィード利用不可」を明示
- 代替フィード（少年ジャンプ+、となりのヤングジャンプ）を案内

### 3. templates/config.html
- BookWalkerチェックボックスを無効化
- 「無効化済み」バッジを追加
- 「404 Not Found」エラーメッセージを表示

### 4. templates/collection_dashboard.html
- BookWalkerの表示名を「BookWalker RSS (無効化済み - 404エラー)」に変更

## ユーザーへの影響

### 表示される内容
1. **収集設定画面**: 
   - BookWalkerカードは灰色（disabled）表示
   - チェックボックスは無効化
   - 赤いアラート: "フィード利用不可（404 Not Found）"
   - 代替フィードの案内

2. **設定画面**:
   - チェックボックスは無効化
   - 「無効化済み」バッジ表示
   - エラーメッセージ表示

3. **ダッシュボード**:
   - 「BookWalker RSS (無効化済み - 404エラー)」と表示

### 推奨される代替フィード
- 少年ジャンプ+ (https://shonenjumpplus.com/rss) - 有効
- となりのヤングジャンプ (https://tonarinoyj.jp/rss) - 有効

## 技術的詳細

### エラー内容
```
HTTPError: 404 Client Error: Not Found
URL: https://bookwalker.jp/rss/new-releases.xml
```

### 対応方針
1. フィードを完全に無効化
2. UIで明確に「利用不可」と表示
3. 代替フィードを案内
4. 将来的にBookWalkerがRSSフィードを復活させた場合、URLを更新して再度有効化可能

## 関連ファイル
- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config.json`
- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/templates/collection_settings.html`
- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/templates/config.html`
- `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/templates/collection_dashboard.html`

## 更新日
2025-11-15

---

*このドキュメントは、BookWalker RSSフィード無効化対応の記録です。*
