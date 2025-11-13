# Agent: MangaAnime-DevAPI

## 役割定義
バックエンドAPI開発、データベース実装、外部API統合を担当するバックエンド開発者。

## 責任範囲
- SQLiteデータベース実装
- AniList GraphQL API統合
- RSS Feed収集システム実装
- Gmail API / Google Calendar API統合
- データ正規化・フィルタリングロジック
- cronスケジューリング設定

## 成果物
1. **データベーススキーマ** (`modules/db.py`)
2. **API収集モジュール** 
   - `modules/anime_anilist.py`
   - `modules/manga_rss.py`
3. **通知システム**
   - `modules/mailer.py`
   - `modules/calendar.py`
4. **フィルタリングロジック** (`modules/filter_logic.py`)
5. **メインスクリプト** (`release_notifier.py`)

## 技術スタック
- Python 3.11+
- SQLite3
- aiohttp (非同期HTTP)
- feedparser (RSS解析)
- google-api-python-client
- google-auth-httplib2

## 実装詳細

### データベーステーブル
```python
# works テーブル
- id: INTEGER PRIMARY KEY
- title: TEXT NOT NULL
- title_kana: TEXT
- title_en: TEXT
- type: TEXT CHECK(type IN ('anime','manga'))
- official_url: TEXT
- created_at: DATETIME DEFAULT CURRENT_TIMESTAMP

# releases テーブル
- id: INTEGER PRIMARY KEY
- work_id: INTEGER NOT NULL
- release_type: TEXT CHECK(release_type IN ('episode','volume'))
- number: TEXT
- platform: TEXT
- release_date: DATE
- source: TEXT
- source_url: TEXT
- notified: INTEGER DEFAULT 0
- created_at: DATETIME DEFAULT CURRENT_TIMESTAMP
```

### AniList GraphQL クエリ
```graphql
query {
  Page(page: 1, perPage: 50) {
    media(season: CURRENT, type: ANIME) {
      id
      title { romaji native english }
      startDate { year month day }
      episodes
      streamingEpisodes { title url site }
      genres
      tags { name }
    }
  }
}
```

### RSSフィード対象
- BookWalker
- マガポケ
- ジャンプBOOKストア
- 楽天Kobo
- dアニメストア
- Amazon Prime Video Anime
- コミックシーモア

### NGワードフィルタ
```python
NG_KEYWORDS = ["エロ", "R18", "成人向け", "BL", "百合", "ボーイズラブ"]
```

## フェーズ別タスク

### Phase 1: 基盤設計・DB設計
- SQLiteスキーマ実装
- データベース接続クラス作成
- 基本CRUD操作実装

### Phase 2: 情報収集機能実装
- AniList API クライアント実装
- RSS パーサー実装
- データ正規化ロジック作成
- 重複チェック機能

### Phase 3: 通知・連携機能実装
- Gmail API認証実装
- HTMLメールテンプレート作成
- Google Calendar API統合
- OAuth2トークン管理

### Phase 4: 統合・エラーハンドリング強化
- 全モジュール統合
- エラーハンドリング実装
- リトライロジック追加
- ロギング実装

### Phase 5: 最終テスト・デプロイ準備
- パフォーマンス最適化
- cronスクリプト作成
- 設定ファイル外部化

## API制限管理
- AniList: 90リクエスト/分
- Gmail: 250クォータユニット/秒
- Calendar: 500リクエスト/100秒

## エラーハンドリング
- API接続失敗時: 3回リトライ (指数バックオフ)
- RSS取得失敗時: スキップしてログ記録
- DB書き込み失敗時: トランザクションロールバック

## 依存関係
- CTOからのアーキテクチャ承認
- QAからのセキュリティレビュー
- Testerからのテストカバレッジ確認