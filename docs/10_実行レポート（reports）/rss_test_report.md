# RSSフィード テスト結果レポート

**テスト実施日時**: 2025-11-15 20:45:11

## テスト結果サマリー

- **アニメフィード**: 5/7 有効 (71.4%)
- **マンガフィード**: 7/9 有効 (77.8%)
- **合計**: 12/16 有効

## 有効なRSSフィード

### アニメ情報フィード

- **MyAnimeList News**
  - URL: https://myanimelist.net/rss/news.xml
  - エントリ数: 20
  - レスポンス時間: 0.95s

- **Crunchyroll News**
  - URL: https://feeds.feedburner.com/crunchyroll/animenews
  - エントリ数: 0
  - レスポンス時間: 1.07s

- **Tokyo Otaku Mode**
  - URL: https://otakumode.com/news/feed
  - エントリ数: 10
  - レスポンス時間: 1.3s

- **Anime UK News**
  - URL: https://animeuknews.net/feed
  - エントリ数: 20
  - レスポンス時間: 1.93s

- **Otaku News**
  - URL: https://otakunews.com/rss/rss.xml
  - エントリ数: 50
  - レスポンス時間: 2.37s

### マンガ情報フィード

- **マンバ**
  - URL: https://manba.co.jp/feed
  - エントリ数: 21
  - レスポンス時間: 0.77s

- **マンバ通信**
  - URL: https://manba.co.jp/manba_magazines/feed
  - エントリ数: 20
  - レスポンス時間: 0.12s

- **マンバ クチコミ**
  - URL: https://manba.co.jp/topics/feed
  - エントリ数: 20
  - レスポンス時間: 0.85s

- **マンバ 無料キャンペーン**
  - URL: https://manba.co.jp/free_campaigns/feed
  - エントリ数: 100
  - レスポンス時間: 0.24s

- **マンバ公式note**
  - URL: https://note.com/manba/rss
  - エントリ数: 25
  - レスポンス時間: 0.66s

- **LEED Cafe**
  - URL: https://leedcafe.com/feed
  - エントリ数: 0
  - レスポンス時間: 0.44s

- **少年ジャンプ+**
  - URL: https://shonenjumpplus.com/rss
  - エントリ数: 267
  - レスポンス時間: 0.42s

## テスト結果（全体）

### アニメ情報フィード

| 名前 | URL | ステータス | エラー | エントリ数 |
|------|-----|----------|--------|----------|
| ✗ Anime News Network | https://animenewsnetwork.com/all/rss | not_found | 404 Not Found | 0 |
| ✓ MyAnimeList News | https://myanimelist.net/rss/news.xml | valid_rss | - | 20 |
| ✓ Crunchyroll News | https://feeds.feedburner.com/crunchyroll/animenews | valid_rss | - | 0 |
| ✓ Tokyo Otaku Mode | https://otakumode.com/news/feed | valid_rss | - | 10 |
| ✓ Anime UK News | https://animeuknews.net/feed | valid_rss | - | 20 |
| ✗ Anime Trending | https://anitrendz.net/news/feed | http_error | HTTP 403 | 0 |
| ✓ Otaku News | https://otakunews.com/rss/rss.xml | valid_rss | - | 50 |

### マンガ情報フィード

| 名前 | URL | ステータス | エラー | エントリ数 |
|------|-----|----------|--------|----------|
| ✓ マンバ | https://manba.co.jp/feed | valid_rss | - | 21 |
| ✓ マンバ通信 | https://manba.co.jp/manba_magazines/feed | valid_rss | - | 20 |
| ✓ マンバ クチコミ | https://manba.co.jp/topics/feed | valid_rss | - | 20 |
| ✓ マンバ 無料キャンペーン | https://manba.co.jp/free_campaigns/feed | valid_rss | - | 100 |
| ✓ マンバ公式note | https://note.com/manba/rss | valid_rss | - | 25 |
| ✓ LEED Cafe | https://leedcafe.com/feed | valid_rss | - | 0 |
| ✓ 少年ジャンプ+ | https://shonenjumpplus.com/rss | valid_rss | - | 267 |
| ✗ マガポケ | https://pocket.shonenmagazine.com/feed | not_found | 404 Not Found | 0 |
| ✗ comix.fyi | https://comix.fyi/rss | not_found | 404 Not Found | 0 |
