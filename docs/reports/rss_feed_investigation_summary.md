# RSSフィード調査結果サマリー

**調査日**: 2025-11-15
**調査者**: Claude (Anthropic AI)

---

## 調査結果概要

両方のRSSフィードURLでエラーが発生していることを確認しました。

### 1. BookWalker RSS

**URL**: `https://bookwalker.jp/rss/`

**状態**: ❌ アクセス拒否

**HTTPステータス**: 403 Forbidden

**エラーメッセージ**:
```
You don't have permission to access this resource.
```

**原因分析**:
- ボット・スクレイピング対策により、単純なHTTPリクエストがブロックされている
- WAF（Web Application Firewall）による保護が有効
- User-Agentだけでは不十分（Cookieやリファラーも必要な可能性）

**対応策**:
1. **公式APIの利用**: BookWalkerが公式APIを提供していないか確認
2. **代替RSS**: 楽天Kobo、Amazonマンガなど他の電子書籍ストアのRSS
3. **スクレイピング**: Selenium/Playwrightで実ブラウザ経由でアクセス（利用規約要確認）
4. **非公式API**: サードパーティAPIサービスの利用（信頼性・継続性に課題）

---

### 2. dアニメストア RSS

**旧URL**: `https://anime.dmkt-sp.jp/animestore/CF/rss/`

**状態**: ⚠️ リダイレクト + 404エラー

**HTTPステータス**: 301 → 404

**リダイレクト先**: `https://animestore.docomo.ne.jp/animestore/CF/rss/`

**最終ステータス**: 404 Not Found

**原因分析**:
- RSSフィードURLが廃止された
- ドメインが `anime.dmkt-sp.jp` → `animestore.docomo.ne.jp` に変更された
- リダイレクト先でもRSSが見つからない（RSSフィード自体が廃止された可能性）

**対応策**:
1. **公式サイト確認**: dアニメストアの公式サイトで新しいRSS URLを探す
2. **代替データソース**:
   - AniList GraphQL API（すでに実装済み）
   - しょぼいカレンダーAPI（実装可能）
   - Annict API（日本のアニメ情報サービス）
3. **スクレイピング**: 公式サイトの新着ページをスクレイピング（利用規約要確認）
4. **通知機能**: dアニメストアの公式アプリ通知やTwitter連携

---

## 技術的詳細

### BookWalker テスト結果

```bash
$ curl -I -A "Mozilla/5.0" "https://bookwalker.jp/rss/"

HTTP/2 403
date: Sat, 15 Nov 2025 04:09:22 GMT
content-type: text/html; charset=iso-8859-1
server: Apache
```

### dアニメストア テスト結果

```bash
$ curl -I -A "Mozilla/5.0" "https://anime.dmkt-sp.jp/animestore/CF/rss/"

HTTP/2 301
location: https://animestore.docomo.ne.jp:443/animestore/CF/rss/

$ curl -L -I "https://animestore.docomo.ne.jp/animestore/CF/rss/"

HTTP/2 404
```

---

## 推奨される修正方針

### 短期対応（今週中）

1. **config.jsonの修正**
   - BookWalker RSSを無効化
   - dアニメストア RSSを無効化または削除

```json
{
  "apis": {
    "rss_feeds": {
      "feeds": [
        {
          "name": "BookWalker",
          "url": "https://bookwalker.jp/rss/",
          "type": "manga",
          "enabled": false,
          "notes": "403 Forbidden - アクセス拒否のため無効化"
        },
        {
          "name": "dアニメストア",
          "url": "https://animestore.docomo.ne.jp/animestore/CF/rss/",
          "type": "anime",
          "enabled": false,
          "notes": "404 Not Found - RSSフィード廃止のため無効化"
        }
      ]
    }
  }
}
```

2. **代替RSSフィードの追加**

```json
{
  "apis": {
    "rss_feeds": {
      "feeds": [
        {
          "name": "楽天Kobo新刊マンガ",
          "url": "https://books.rakuten.co.jp/rss/rankings/001001_weekly.xml",
          "type": "manga",
          "enabled": true
        },
        {
          "name": "Amazonマンガベストセラー",
          "url": "https://www.amazon.co.jp/gp/rss/bestsellers/digital-text/2430733051",
          "type": "manga",
          "enabled": true
        },
        {
          "name": "コミックナタリー",
          "url": "https://natalie.mu/comic/feed/news",
          "type": "manga",
          "enabled": true
        },
        {
          "name": "アニメ！アニメ！",
          "url": "https://animeanime.jp/feed",
          "type": "anime",
          "enabled": true
        }
      ]
    }
  }
}
```

### 中期対応（今月中）

1. **AniList APIの活用強化**
   - すでに実装済みのAniList GraphQL APIをメインデータソースとする
   - streaming情報を取得してdアニメストア配信作品を推定

2. **しょぼいカレンダーAPIの実装**
   - 日本のアニメ放送スケジュールを取得
   - AniListと組み合わせて精度向上

3. **複数データソースの統合**
   - AniList + しょぼいカレンダー + 代替RSS
   - データ重複排除と正規化

### 長期対応（来月以降）

1. **公式API調査**
   - BookWalker、dアニメストアの公式APIの有無を確認
   - 必要に応じてAPI利用申請

2. **スクレイピング基盤構築**
   - Playwright/Seleniumによる自動収集
   - CloudflareやWAFの回避手法
   - 利用規約の遵守確認

3. **サードパーティサービス検討**
   - MyAnimeList API
   - Annict API
   - Kitsu API

---

## 代替データソース候補

### マンガ情報

| サービス | RSSあり | API | スクレイピング | 優先度 |
|---|---|---|---|---|
| 楽天Kobo | ✅ | ⚠️（非公式） | 可能 | 高 |
| Amazon | ✅（制限あり） | ❌ | 困難 | 中 |
| コミックナタリー | ✅ | ❌ | 可能 | 高 |
| マガポケ | ❓ | ❌ | 可能 | 中 |
| ジャンプ+ | ❌ | ❌ | 可能 | 中 |

### アニメ情報

| サービス | RSSあり | API | スクレイピング | 優先度 |
|---|---|---|---|---|
| AniList | ❌ | ✅ | 不要 | **最高** |
| しょぼいカレンダー | ✅ | ✅ | 不要 | **最高** |
| MyAnimeList | ❌ | ✅ | 可能 | 高 |
| Annict | ❌ | ✅ | 可能 | 高 |
| アニメ！アニメ！ | ✅ | ❌ | 可能 | 中 |
| Netflix | ❌ | ❌ | 困難 | 低 |
| Prime Video | ❌ | ❌ | 困難 | 低 |

---

## 実装例：代替RSSフィードのテスト

### 楽天Koboテスト

```bash
curl -I "https://books.rakuten.co.jp/rss/rankings/001001_weekly.xml"
# → HTTPステータス確認
```

### コミックナタリーテスト

```bash
curl -I "https://natalie.mu/comic/feed/news"
# → HTTPステータス確認
```

### アニメ！アニメ！テスト

```bash
curl -I "https://animeanime.jp/feed"
# → HTTPステータス確認
```

---

## まとめ

### 問題の本質

1. **BookWalker**: ボット対策により403エラー
2. **dアニメストア**: RSSフィード自体が廃止（404エラー）

### 結論

- **両方のRSSフィードは使用不可**
- 代替データソースへの移行が必須
- AniList APIとしょぼいカレンダーAPIをメインに据えるべき

### 次のステップ

1. ✅ **即座実施**: config.jsonで両RSSを無効化
2. 🔄 **今週中**: 代替RSSフィードを追加・テスト
3. 📝 **今月中**: しょぼいカレンダーAPIを実装
4. 🚀 **来月**: スクレイピング基盤構築（必要に応じて）

---

**調査完了日**: 2025-11-15 13:09 JST
