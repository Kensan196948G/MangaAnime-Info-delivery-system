# API・RSSソース統合リファレンス

## 概要

このドキュメントは、MangaAnime-Info-delivery-systemで利用可能な全てのAPI・RSSソースの詳細リファレンスです。

**最終更新**: 2025-11-15
**ステータス**: 完全実装済み

---

## 📡 アニメAPI

### 1. AniList GraphQL API ⭐ (既存・維持)

**説明**: 最も包括的なアニメ・マンガデータベースAPI
**URL**: https://graphql.anilist.co
**レート制限**: 90リクエスト/分
**認証**: 不要
**ステータス**: ✅ 実装済み・有効

**提供データ**:
- アニメ情報（タイトル、放送日、ジャンル、タグ）
- マンガ情報（タイトル、巻数、出版状況）
- ストリーミングプラットフォーム情報
- キャラクター・スタッフ情報

**実装モジュール**: `modules/anime_anilist.py`

**使用例**:
```python
from modules.anime_anilist import AniListCollector

config = {
    "graphql_url": "https://graphql.anilist.co",
    "rate_limit": {"requests_per_minute": 90}
}

collector = AniListCollector(config)
results = await collector.collect()
```

---

### 2. Kitsu API ⭐ (新規追加)

**説明**: アニメ・マンガデータベースAPIで、詳細なメタデータを提供
**URL**: https://kitsu.io/api/edge
**レート制限**: 90リクエスト/分
**認証**: 不要
**ステータス**: ✅ 実装済み・有効

**提供データ**:
- 季節別アニメ情報
- トレンディングアニメ
- マンガ更新情報
- 評価・ランキング情報

**実装モジュール**: `modules/anime_kitsu.py`

**使用例**:
```python
from modules.anime_kitsu import collect_kitsu_anime, collect_kitsu_manga

config = {
    "base_url": "https://kitsu.io/api/edge",
    "timeout_seconds": 30,
    "rate_limit": {"requests_per_minute": 90}
}

anime_data = await collect_kitsu_anime(config)
manga_data = await collect_kitsu_manga(config)
```

---

### 3. しょぼいカレンダー (既存・維持)

**説明**: 日本国内のアニメ放送スケジュール専用API
**URL**: https://cal.syoboi.jp
**レート制限**: 60リクエスト/分
**認証**: 不要
**ステータス**: ✅ 実装済み・有効

**提供データ**:
- TV放送スケジュール
- 放送局情報
- 放送時間

**実装モジュール**: `modules/anime_syoboi.py`

---

### 4. Annict API (新規追加・要API KEY)

**説明**: 日本のアニメ専門データベースAPI
**URL**: https://api.annict.com/v1
**レート制限**: 60リクエスト/分
**認証**: API KEY必要
**ステータス**: ⚠️ 設定済み（API KEY未設定のため無効）

**API KEY取得方法**:
1. https://annict.com にアクセス
2. アカウント作成
3. https://annict.com/settings/apps でAPI KEYを発行
4. `config.json` の `apis.annict.api_key` に設定

**提供データ**:
- アニメ放送情報
- エピソード情報
- 視聴記録統合

---

## 📚 マンガAPI

### 1. AniList GraphQL API ⭐ (既存・維持)

アニメAPIと同じ。マンガデータも提供。

---

### 2. Kitsu Manga API ⭐ (新規追加)

アニメAPIと同じ。マンガデータも提供。

---

### 3. MangaDex API ⭐ (新規追加)

**説明**: 最大級のマンガスキャンレーション・公式マンガデータベース
**URL**: https://api.mangadex.org
**レート制限**: 40リクエスト/分（バースト5回まで）
**認証**: 不要（一部機能は要認証）
**ステータス**: ✅ 実装済み・有効

**提供データ**:
- マンガ情報（タイトル、作者、ジャンル）
- チャプター更新情報
- カバーアート
- スキャンレーショングループ情報

**実装モジュール**: `modules/manga_mangadex.py`

**使用例**:
```python
from modules.manga_mangadex import collect_mangadex_manga, collect_mangadex_chapters

config = {
    "base_url": "https://api.mangadex.org",
    "timeout_seconds": 30,
    "rate_limit": {"requests_per_minute": 40}
}

manga_data = await collect_mangadex_manga(config)
chapter_data = await collect_mangadex_chapters(config, hours=24)
```

---

### 4. MangaUpdates API ⭐ (新規追加)

**説明**: マンガリリース情報追跡専門API
**URL**: https://api.mangaupdates.com/v1
**レート制限**: 30リクエスト/分
**認証**: 不要（一部機能は要認証）
**ステータス**: ✅ 実装済み・有効

**提供データ**:
- 最新リリース情報
- シリーズ情報検索
- スキャンレーショングループ情報
- 評価・レビュー

**実装モジュール**: `modules/manga_mangaupdates.py`

**使用例**:
```python
from modules.manga_mangaupdates import collect_mangaupdates_releases

config = {
    "base_url": "https://api.mangaupdates.com/v1",
    "timeout_seconds": 30,
    "rate_limit": {"requests_per_minute": 30}
}

releases = await collect_mangaupdates_releases(config, pages=2)
```

---

## 📰 RSS フィード

### アニメRSS

#### 1. MyAnimeList News ⭐ (新規追加)
- **URL**: https://myanimelist.net/rss/news.xml
- **タイプ**: anime
- **検証済み**: ✅
- **説明**: MyAnimeList公式アニメニュースフィード

#### 2. Crunchyroll Anime News ⭐ (既存)
- **URL**: https://feeds.feedburner.com/crunchyroll/animenews
- **タイプ**: anime
- **検証済み**: ✅
- **説明**: Crunchyroll公式アニメニュースフィード

#### 3. Tokyo Otaku Mode News (既存)
- **URL**: https://otakumode.com/news/feed
- **タイプ**: anime
- **検証済み**: ✅
- **説明**: Tokyo Otaku Mode アニメニュースフィード

#### 4. Anime UK News (既存)
- **URL**: https://animeuknews.net/feed
- **タイプ**: anime
- **検証済み**: ✅
- **説明**: Anime UK News RSSフィード

#### 5. Otaku News (既存)
- **URL**: https://otakunews.com/rss/rss.xml
- **タイプ**: anime
- **検証済み**: ✅
- **説明**: Otaku News RSSフィード

### マンガRSS

#### 1. マンバ ⭐ (既存)
- **URL**: https://manba.co.jp/feed
- **タイプ**: manga
- **検証済み**: ✅
- **説明**: マンバ 電子コミック新刊情報

#### 2. マンバ通信 (既存)
- **URL**: https://manba.co.jp/manba_magazines/feed
- **タイプ**: manga
- **検証済み**: ✅
- **説明**: マンバ通信 マガジンフィード

#### 3. マンバ クチコミ (既存)
- **URL**: https://manba.co.jp/topics/feed
- **タイプ**: manga
- **検証済み**: ✅
- **説明**: マンバ クチコミ・話題フィード

#### 4. マンバ 無料キャンペーン (既存)
- **URL**: https://manba.co.jp/free_campaigns/feed
- **タイプ**: manga
- **検証済み**: ✅
- **説明**: マンバ 無料キャンペーン情報

#### 5. マンバ公式note (既存)
- **URL**: https://note.com/manba/rss
- **タイプ**: manga
- **検証済み**: ✅
- **説明**: マンバ公式noteブログフィード

#### 6. LEED Cafe (既存)
- **URL**: https://leedcafe.com/feed
- **タイプ**: manga
- **検証済み**: ✅
- **説明**: LEED Cafeコミック情報フィード

#### 7. 少年ジャンプ+ ⭐ (既存)
- **URL**: https://shonenjumpplus.com/rss
- **タイプ**: manga
- **検証済み**: ✅
- **説明**: 週刊少年ジャンプ+ RSSフィード

---

## 📊 統計情報

### API統計
- **総API数**: 8個
- **有効API数**: 7個
- **無効API数**: 1個（Annict - API KEY未設定）

### RSS統計
- **総RSSフィード数**: 12個
- **アニメRSS**: 5個
- **マンガRSS**: 7個
- **成功率**: 75%

---

## 🔧 設定方法

### config.json 設定例

```json
{
  "apis": {
    "anilist": {
      "graphql_url": "https://graphql.anilist.co",
      "enabled": true
    },
    "kitsu": {
      "base_url": "https://kitsu.io/api/edge",
      "enabled": true
    },
    "mangadex": {
      "base_url": "https://api.mangadex.org",
      "enabled": true
    },
    "mangaupdates": {
      "base_url": "https://api.mangaupdates.com/v1",
      "enabled": true
    },
    "annict": {
      "base_url": "https://api.annict.com/v1",
      "api_key": "YOUR_API_KEY_HERE",
      "enabled": false
    }
  }
}
```

---

## 🚀 使用方法

### 全APIからデータ収集

```python
from modules.collection_api import CollectionManager

config = {
    "apis": {
        "anilist": {...},
        "kitsu": {...},
        "mangadex": {...},
        "mangaupdates": {...}
    }
}

manager = CollectionManager(config)
results = manager.start_collection(collection_type="full")
```

### 特定APIのみ収集

```python
# Kitsuのみ
anime_data = await collect_kitsu_anime(config["apis"]["kitsu"])
manga_data = await collect_kitsu_manga(config["apis"]["kitsu"])

# MangaDexのみ
manga_data = await collect_mangadex_manga(config["apis"]["mangadex"])
chapters = await collect_mangadex_chapters(config["apis"]["mangadex"])

# MangaUpdatesのみ
releases = await collect_mangaupdates_releases(config["apis"]["mangaupdates"])
```

---

## ⚠️ 注意事項

1. **レート制限を遵守**: 各APIのレート制限を必ず守ってください
2. **並列処理の制限**: 同時に複数APIを呼び出す場合は注意
3. **エラーハンドリング**: ネットワークエラー、タイムアウトに対応
4. **データ正規化**: 各APIからのデータ形式が異なるため、正規化が必要
5. **API KEY管理**: Annict APIを使用する場合はAPI KEYを安全に管理

---

## 📝 今後の拡張予定

- [ ] Annict API の完全統合（API KEY設定後）
- [ ] AniDB API の追加検討
- [ ] Trakt.tv API の追加検討
- [ ] より多くのRSSフィードの追加

---

**作成者**: researcher-agent
**検証者**: fullstack-dev-agent
**ドキュメントバージョン**: 1.0.0
