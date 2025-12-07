# 📊 API・RSS URL確認レポート

**確認日時**: 2025-11-15 21:05
**ステータス**: ✅ **確認完了**

---

## ✅ **有効なAPI・RSS（実装可能）**

### アニメAPI（3個）
1. ✅ **AniList GraphQL API** - 最優先 ★★★★★
   - URL: https://graphql.anilist.co
   - ステータス: 200 OK
   - データ豊富、認証不要

2. ✅ **Annict API** - 要調査
   - URL: https://api.annict.com/
   - ステータス: 200 OK（Webサイト）

3. ✅ **しょぼいカレンダー** - 要調査
   - URL: https://cal.syoboi.jp/
   - ステータス: 200 OK（Webサイト）

### マンガAPI（3個）
1. ✅ **Kitsu Manga API** - 最優先 ★★★★★
   - URL: https://kitsu.io/api/edge/manga
   - ステータス: 200 OK
   - JSON API、データ充実

2. ✅ **MangaDex API**
   - URL: https://api.mangadex.org
   - ステータス: 308（リダイレクト）

3. ✅ **MangaPi API**
   - URL: https://mangapi.vercel.app/
   - ステータス: 200 OK

### アニメRSS（6個）
1. ✅ **MyAnimeList News** - 最優先 ★★★★★
   - URL: https://myanimelist.net/rss/news.xml
   - ステータス: 200 OK

2. ✅ **Crunchyroll News**
   - URL: https://feeds.feedburner.com/crunchyroll/animenews
   - ステータス: 200 OK

3. ✅ **Tokyo Otaku Mode**
   - URL: https://otakumode.com/news/feed
   - ステータス: 200 OK

4. ✅ **Otaku News**
   - URL: https://otakunews.com/rss/rss.xml
   - ステータス: 200 OK

5. ✅ **ANN Encyclopedia**
   - URL: https://cdn.animenewsnetwork.com/encyclopedia/api.xml
   - ステータス: 200 OK

6. ⚠️ **Anime News Network**
   - URL: https://animenewsnetwork.com/all/rss
   - ステータス: 301（リダイレクト）

### マンガRSS（1個）
1. ✅ **マンバ** - 最優先 ★★★★
   - URL: https://manba.co.jp/feed
   - ステータス: 200 OK

---

## ❌ **無効なURL（実装対象外）**

### アニメAPI（6個）
- Kitsu Anime: 404 Not Found
- Animumemo MADB: ドキュメントページのみ
- メディア芸術DB: SSL証明書エラー
- Shikimori: 301リダイレクト
- AniDB: 403 Forbidden
- ANN API: 404 Not Found

### マンガAPI（4個）
- Shikimori Manga: 404 Not Found
- Manga Hook: 404 Not Found
- Manga API Heroku: 404 Not Found（サービス終了）

### RSS（3個）
- Anime UK News: 301リダイレクト
- AniTrendz: 301リダイレクト
- マガポケ: 404 Not Found

---

## 📋 **実装推奨（優先順位）**

### 最優先実装（3個）
1. AniList GraphQL API（アニメ・マンガ両対応）
2. Kitsu Manga API
3. MyAnimeList RSS

### 優先実装（4個）
4. マンバRSS
5. Tokyo Otaku Mode RSS
6. Otaku News RSS
7. Crunchyroll RSS

### 今後検討（3個）
8. しょぼいカレンダー（APIエンドポイント要調査）
9. Annict（APIエンドポイント要調査）
10. MangaPi

**合計実装可能**: 約10-13個

---

**確認完了日**: 2025-11-15
**有効URL**: 13個
**無効URL**: 13個
**実装推奨**: 10個

次のステップ: 有効URLを設定ファイルに追加・実装
