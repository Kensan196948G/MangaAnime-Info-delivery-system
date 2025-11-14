# アニメ・マンガ情報配信システム - システムアーキテクチャ仕様書

## 概要

本システムは、ClaudeCodeの並列開発機能（SubAgent）を活用して構築されたアニメ・マンガの最新情報自動配信システムです。AniList GraphQL API、RSS、しょぼいカレンダーAPIから情報を収集し、フィルタリング処理を経てGmail通知とGoogleカレンダー登録を自動実行します。

## システム構成

### 技術スタック

| 機能領域 | 技術 | 詳細 |
|---------|------|------|
| 言語 | Python 3.11+ | 非同期処理対応 |
| データベース | SQLite | 軽量、ファイルベース |
| 情報収集 | AniList GraphQL API, RSS, JSON API | レート制限考慮 |
| 通知 | Gmail API (OAuth2) | HTML形式メール |
| カレンダー | Google Calendar API (OAuth2) | イベント自動登録 |
| スケジュール | cron | Linux環境前提 |
| ログ管理 | Python logging | ローテーション対応 |

### アーキテクチャ概要

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  データ収集層    │    │   処理・保存層   │    │    配信層       │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ AniList API     │────│ フィルタリング   │────│ Gmail API       │
│ しょぼいカレンダー │    │ データ正規化     │    │ Calendar API    │
│ RSS Feeds       │    │ SQLite保存       │    │ HTML生成        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## モジュール構成

### コアモジュール

#### `/modules/config.py`
**設定管理モジュール**

```python
class ConfigManager:
    # 設定ファイル（config.json）の読み込み・管理
    # 環境変数による設定上書き機能
    # ドット記法による階層アクセス（例: database.path）
    # 設定値検証機能
```

**主要メソッド:**
- `get(key, default=None)`: 設定値取得
- `get_ng_keywords()`: NGキーワード取得
- `is_filtered_content()`: フィルタリング判定
- `validate_config()`: 設定検証

#### `/modules/db.py`
**データベース管理モジュール**

```python
class DatabaseManager:
    # SQLiteデータベース操作
    # 自動テーブル作成・インデックス管理
    # 作品・リリース情報のCRUD操作
    # 通知状態管理
```

**データベース設計:**
```sql
-- 作品テーブル
CREATE TABLE works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    title_kana TEXT,
    title_en TEXT,
    type TEXT CHECK(type IN ('anime','manga')) NOT NULL,
    official_url TEXT,
    description TEXT,
    genres TEXT,  -- JSON形式
    tags TEXT,    -- JSON形式
    image_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(title, type)
);

-- リリース情報テーブル
CREATE TABLE releases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    release_type TEXT CHECK(release_type IN ('episode','volume','special')) NOT NULL,
    number TEXT,
    title TEXT,
    platform TEXT,
    release_date DATE NOT NULL,
    release_time TIME,
    source TEXT NOT NULL,
    source_url TEXT,
    notified INTEGER DEFAULT 0,
    calendar_event_id TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(work_id, release_type, number, platform, release_date),
    FOREIGN KEY (work_id) REFERENCES works (id) ON DELETE CASCADE
);
```

#### `/modules/logger.py`
**ログ管理モジュール**

```python
def setup_logging(config_manager, force_reload=False):
    # 色付きコンソール出力
    # ローテーション付きファイル出力
    # JSON形式ログ（本番環境）
    # モジュール別ログレベル調整
```

**機能:**
- コンソール出力（色付き）
- ファイル出力（ローテーション）
- JSON形式ログ（本番用）
- パフォーマンス測定
- レート制限付きログ

### データ収集モジュール

#### `/modules/anime_anilist.py`
**AniList API連携モジュール**

```python
class AniListClient:
    # GraphQL APIクライアント
    # レート制限管理（90req/min）
    # 非同期処理対応
    # リトライ機能

class AniListCollector:
    # 高レベルデータ収集
    # フィルタリング統合
    # データベース連携
```

**API制限:**
- 90リクエスト/分
- 自動レート制限管理
- エラー時の自動リトライ

#### `/modules/manga_rss.py`
**RSS収集モジュール**

```python
class MangaRSSCollector:
    # 汎用RSS収集
    # feedparser使用
    # タイトル・話数抽出

class BookWalkerRSSCollector(MangaRSSCollector):
    # BookWalker専用処理

class DAnimeRSSCollector(MangaRSSCollector):
    # dアニメストア専用処理
```

**対応サイト:**
- BookWalker
- dアニメストア
- マガポケ
- ジャンプBOOKストア
- 楽天Kobo

### データ処理モジュール

#### `/modules/filter_logic.py`
**フィルタリングロジック**

```python
class ContentFilter:
    # NGキーワード判定
    # ジャンル・タグフィルタリング
    # 正規表現パターンマッチング
    # カスタムフィルター対応

@dataclass
class FilterResult:
    is_filtered: bool
    reason: Optional[str]
    matched_keywords: List[str]
    matched_genres: List[str]
    matched_tags: List[str]
```

**フィルタリング対象:**
- タイトル（日本語・英語・ローマ字）
- 説明文
- ジャンル
- タグ
- カスタム正規表現パターン

#### `/modules/models.py`
**データモデル定義**

```python
@dataclass
class Work:
    title: str
    work_type: WorkType
    # その他の属性...

@dataclass
class Release:
    work_id: int
    release_type: ReleaseType
    # その他の属性...

@dataclass
class AniListWork:
    # AniList固有のデータ構造
```

### 配信モジュール

#### `/modules/mailer.py`
**Gmail通知モジュール**

```python
class GmailMailer:
    # OAuth2認証
    # HTML形式メール生成
    # 画像埋め込み対応
    # テンプレートエンジン
```

**メール機能:**
- HTML + テキスト マルチパート
- 作品画像表示
- 配信プラットフォーム情報
- レスポンシブデザイン

#### `/modules/calendar.py`
**Googleカレンダー管理**

```python
class GoogleCalendarManager:
    # OAuth2認証（Gmail共有）
    # イベント自動生成
    # リマインダー設定
    # 色分け機能
```

**カレンダー機能:**
- 作品タイプ別色分け
- 自動リマインダー（60分前・10分前）
- 終日/時刻指定イベント対応
- イベント更新・削除

## メイン実行フロー

### `release_notifier.py` - システムエントリポイント

```python
class ReleaseNotifierSystem:
    def run(self):
        # 1. 情報収集
        raw_items = self.collect_information()
        
        # 2. データ処理・フィルタリング
        processed_items = self.process_and_filter_data(raw_items)
        
        # 3. データベース保存
        self.save_to_database(processed_items)
        
        # 4. 通知処理
        self.send_notifications()
        
        # 5. クリーンアップ
        self.cleanup_old_data()
```

### 実行統計機能

```python
statistics = {
    'processed_sources': 0,
    'new_works': 0,
    'new_releases': 0,
    'notifications_sent': 0,
    'calendar_events_created': 0,
    'filtered_items': 0,
    'errors': 0
}
```

## 設定ファイル構成

### `config.json` - メイン設定

```json
{
  "system": {
    "name": "MangaAnime情報配信システム",
    "version": "1.0.0",
    "environment": "production",
    "timezone": "Asia/Tokyo",
    "log_level": "INFO"
  },
  "database": {
    "path": "./db.sqlite3",
    "backup_enabled": true,
    "backup_retention_days": 30
  },
  "apis": {
    "anilist": {
      "graphql_url": "https://graphql.anilist.co",
      "rate_limit": {
        "requests_per_minute": 90,
        "retry_delay_seconds": 5
      }
    },
    "rss_feeds": {
      "feeds": [...]
    }
  },
  "google": {
    "credentials_file": "./credentials.json",
    "token_file": "./token.json",
    "scopes": [...],
    "gmail": {...},
    "calendar": {...}
  },
  "filtering": {
    "ng_keywords": [...],
    "ng_genres": [...],
    "exclude_tags": [...]
  }
}
```

## エラーハンドリング・信頼性

### エラー処理方針

1. **フェイルセーフ**: 一部のソースでエラーが発生しても他の処理を継続
2. **ログ記録**: 全エラーを詳細にログ記録
3. **リトライ機能**: ネットワークエラー等は自動リトライ
4. **グレースフルデグラデーション**: 一部機能が利用不可でも基本機能は維持

### 信頼性機能

- **重複検出**: データベースレベルでの重複データ防止
- **整合性チェック**: データ投入前の検証
- **ロールバック**: エラー時の部分的データロールバック
- **監視**: 統計情報による動作監視

## パフォーマンス考慮事項

### 最適化ポイント

1. **非同期処理**: AniList API等の複数ソース並列処理
2. **データベースインデックス**: 検索性能向上
3. **メモリ効率**: 大量データ処理時のメモリ管理
4. **レート制限遵守**: API制限に対する適切な制御

### スケーラビリティ

- **設定ベース拡張**: 新RSS源の設定ファイル追加のみで対応
- **モジュラー設計**: 機能単位での独立性確保
- **プラグイン機構**: カスタムフィルター等の拡張機能

## セキュリティ考慮事項

### 認証・認可

- **OAuth2**: Gmail・Calendar API用
- **トークン管理**: 安全な認証情報保存
- **スコープ制限**: 必要最小限のAPI権限

### データ保護

- **機密情報の分離**: 認証情報とアプリ設定の分離
- **ログの安全性**: 機密情報のログ出力防止
- **アクセス制御**: ファイルパーミッションの適切な設定

## 運用・メンテナンス

### 日次運用

```bash
# cron設定例
0 8 * * * python3 release_notifier.py
```

### ログ監視

- `/logs/app.log`: メインログ
- `/logs/app.log.json`: 構造化ログ（本番環境）
- ログローテーション: 10MB単位、5世代保持

### バックアップ

- SQLiteデータベース: 日次自動バックアップ
- 設定ファイル: バージョン管理推奨
- 認証情報: 暗号化保存推奨

## 拡張機能（将来計画）

### Phase 2 機能

- **Web UI**: Flask + Bootstrap
- **Claude連携**: あらすじ生成
- **Googleスプレッドシート**: 管理インターフェース
- **Webhook通知**: Discord、Slack等

### Phase 3 機能

- **機械学習**: おすすめ機能
- **多言語対応**: 国際化対応
- **モバイルアプリ**: プッシュ通知
- **分散処理**: Redis、Celery導入

---

## 並列開発（SubAgent）対応

このシステムは最大10体のSubAgentによる並列開発を前提として設計されています：

### Agent役割分担

1. **CTO Agent**: 全体設計・レビュー
2. **DevUI Agent**: Web UI（将来拡張）
3. **DevAPI Agent**: API連携・データ収集
4. **QA Agent**: テスト・品質管理
5. **Tester Agent**: 自動テスト生成
6. **その他Agents**: 専門領域担当

### 並列開発サポート

- **モジュラー設計**: 各Agent独立開発可能
- **明確なインターフェース**: モジュール間API定義
- **統合テスト**: Agent間連携テスト
- **ドキュメント駆動**: 仕様書ベース開発