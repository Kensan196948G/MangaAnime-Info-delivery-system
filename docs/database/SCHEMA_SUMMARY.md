# データベーススキーマ概要

## 全体構成

本システムは、**4層のテーブル構成**で設計されています：

### 1. コア層（Core Layer）
- `works` - 作品マスター
- `releases` - リリース情報

### 2. 通知層（Notification Layer）
- `notification_logs` - 通知履歴
- `calendar_events` - カレンダーイベント

### 3. ユーザー層（User Layer）
- `users` - ユーザーマスター
- `user_preferences` - ユーザー設定
- `genre_filters` - ジャンルフィルター
- `platform_filters` - プラットフォームフィルター
- `ng_keywords` - NGワードマスター

### 4. システム層（System Layer）
- `api_call_logs` - API呼び出しログ
- `error_logs` - エラーログ
- `anilist_cache` - AniList APIキャッシュ
- `rss_cache` - RSSフィードキャッシュ
- `rss_items` - RSSアイテムキャッシュ
- `system_stats` - システム統計
- `schema_migrations` - マイグレーション管理

---

## テーブル詳細

### works（作品マスター）

```
用途: アニメ・マンガ作品の基本情報を管理
行数: 可変（新作追加で増加）
```

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 作品ID |
| title | TEXT | NOT NULL, CHECK | 作品タイトル（日本語） |
| title_kana | TEXT | | タイトルかな |
| title_en | TEXT | | 英語タイトル |
| type | TEXT | NOT NULL, CHECK | 'anime' or 'manga' |
| official_url | TEXT | | 公式サイトURL |
| created_at | DATETIME | DEFAULT | 登録日時 |
| updated_at | DATETIME | DEFAULT | 更新日時 |

**インデックス**:
- `idx_works_type` (type)
- `idx_works_title` (title COLLATE NOCASE)
- `idx_works_unique_title_type` (title, type) UNIQUE

---

### releases（リリース情報）

```
用途: 各作品のエピソード配信・巻数発売情報
行数: 大量（1作品あたり10〜100件程度）
```

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | リリースID |
| work_id | INTEGER | NOT NULL, FK | 作品ID |
| release_type | TEXT | NOT NULL, CHECK | 'episode' or 'volume' |
| number | TEXT | CHECK | エピソード番号/巻数 |
| platform | TEXT | | 配信プラットフォーム |
| release_date | DATE | NOT NULL, CHECK | 配信/発売日 |
| source | TEXT | | 情報ソース名 |
| source_url | TEXT | | ソースURL |
| notified | INTEGER | DEFAULT 0, CHECK | 通知済みフラグ |
| created_at | DATETIME | DEFAULT | 登録日時 |
| updated_at | DATETIME | DEFAULT | 更新日時 |

**インデックス**:
- `idx_releases_work_id` (work_id)
- `idx_releases_date` (release_date DESC)
- `idx_releases_notified_date` (notified, release_date)
- `idx_releases_work_platform_date` (work_id, platform, release_date DESC)

**外部キー**:
- `work_id` → `works(id)` ON DELETE CASCADE

---

### notification_logs（通知ログ）

```
用途: Gmail/Calendar通知の履歴管理
行数: 大量（通知ごとに1レコード）
```

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PK | ログID |
| release_id | INTEGER | NOT NULL, FK | リリースID |
| notification_type | TEXT | NOT NULL, CHECK | 'email', 'calendar', 'both' |
| sent_at | DATETIME | DEFAULT | 送信日時 |
| status | TEXT | NOT NULL, CHECK | 'success', 'failed', 'pending' |
| email_message_id | TEXT | | GmailメッセージID |
| error_message | TEXT | | エラーメッセージ |
| retry_count | INTEGER | DEFAULT 0 | リトライ回数 |

**外部キー**:
- `release_id` → `releases(id)` ON DELETE CASCADE

---

### calendar_events（カレンダーイベント）

```
用途: Googleカレンダー登録イベントの管理
行数: releasesとほぼ同数
```

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PK | イベントID |
| release_id | INTEGER | NOT NULL, FK | リリースID |
| google_event_id | TEXT | UNIQUE, NOT NULL | GoogleイベントID |
| calendar_id | TEXT | NOT NULL, DEFAULT | カレンダーID |
| event_title | TEXT | NOT NULL | イベントタイトル |
| event_description | TEXT | | イベント説明 |
| start_datetime | DATETIME | NOT NULL | 開始日時 |
| end_datetime | DATETIME | | 終了日時 |
| created_at | DATETIME | DEFAULT | 作成日時 |
| updated_at | DATETIME | DEFAULT | 更新日時 |
| synced_at | DATETIME | | 同期日時 |

**外部キー**:
- `release_id` → `releases(id)` ON DELETE CASCADE

---

### users（ユーザーマスター）

```
用途: 通知受信ユーザーの管理
行数: 少数（1〜10名程度）
```

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PK | ユーザーID |
| email | TEXT | UNIQUE, NOT NULL, CHECK | メールアドレス |
| name | TEXT | | ユーザー名 |
| is_active | INTEGER | DEFAULT 1, CHECK | 有効フラグ |
| created_at | DATETIME | DEFAULT | 登録日時 |
| updated_at | DATETIME | DEFAULT | 更新日時 |
| last_login_at | DATETIME | | 最終ログイン |

---

### user_preferences（ユーザー設定）

```
用途: ユーザーごとの通知設定
行数: users と1:1
```

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PK | 設定ID |
| user_id | INTEGER | NOT NULL, FK, UNIQUE | ユーザーID |
| notify_anime | INTEGER | DEFAULT 1 | アニメ通知ON/OFF |
| notify_manga | INTEGER | DEFAULT 1 | マンガ通知ON/OFF |
| notify_email | INTEGER | DEFAULT 1 | メール通知ON/OFF |
| notify_calendar | INTEGER | DEFAULT 1 | カレンダー通知ON/OFF |
| timezone | TEXT | DEFAULT | タイムゾーン |
| language | TEXT | DEFAULT, CHECK | 言語設定 |
| updated_at | DATETIME | DEFAULT | 更新日時 |

**外部キー**:
- `user_id` → `users(id)` ON DELETE CASCADE

---

### ng_keywords（NGワードマスター）

```
用途: フィルタリング用NGワード管理
行数: 少数（10〜50件程度）
```

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PK | キーワードID |
| keyword | TEXT | UNIQUE, NOT NULL, CHECK | NGワード |
| category | TEXT | CHECK | 'adult', 'genre', 'other' |
| is_active | INTEGER | DEFAULT 1 | 有効フラグ |
| created_at | DATETIME | DEFAULT | 登録日時 |

**デフォルトデータ**:
- エロ (adult)
- R18 (adult)
- 成人向け (adult)
- BL (genre)
- 百合 (genre)
- ボーイズラブ (genre)

---

### api_call_logs（API呼び出しログ）

```
用途: 外部API呼び出しの監視・レート制限管理
行数: 大量（API呼び出しごとに1レコード）
```

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PK | ログID |
| api_name | TEXT | NOT NULL, CHECK | API名 |
| endpoint | TEXT | NOT NULL | エンドポイント |
| http_method | TEXT | CHECK | HTTPメソッド |
| status_code | INTEGER | | ステータスコード |
| response_time_ms | INTEGER | CHECK | レスポンス時間 |
| error_message | TEXT | | エラーメッセージ |
| called_at | DATETIME | DEFAULT | 呼び出し日時 |
| rate_limit_remaining | INTEGER | | 残りAPI呼び出し数 |
| rate_limit_reset | DATETIME | | レート制限リセット時刻 |

**API種類**:
- `anilist` - AniList GraphQL API
- `shoboical` - しょぼいカレンダーAPI
- `rss` - RSSフィード
- `gmail` - Gmail API
- `gcalendar` - Google Calendar API

---

### anilist_cache（AniList APIキャッシュ）

```
用途: AniList API レスポンスのキャッシュ
行数: 可変（キャッシュ期限で自動削除）
```

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PK | キャッシュID |
| anilist_id | INTEGER | UNIQUE, NOT NULL | AniList作品ID |
| title_romaji | TEXT | | ローマ字タイトル |
| title_english | TEXT | | 英語タイトル |
| title_native | TEXT | | ネイティブタイトル |
| genres | TEXT | | ジャンル（JSON配列） |
| tags | TEXT | | タグ（JSON配列） |
| description | TEXT | | あらすじ |
| cover_image_url | TEXT | | カバー画像URL |
| banner_image_url | TEXT | | バナー画像URL |
| episodes | INTEGER | | エピソード数 |
| status | TEXT | | 配信状態 |
| season | TEXT | | シーズン |
| season_year | INTEGER | | 年度 |
| streaming_episodes | TEXT | | 配信エピソード（JSON） |
| cached_at | DATETIME | DEFAULT | キャッシュ日時 |
| expires_at | DATETIME | NOT NULL | 有効期限 |

---

## リレーションシップ図（簡易版）

```
users (1) ──< (N) user_preferences
users (1) ──< (N) genre_filters
users (1) ──< (N) platform_filters

works (1) ──< (N) releases
releases (1) ──< (N) notification_logs
releases (1) ──< (1) calendar_events

rss_cache (1) ──< (N) rss_items
```

---

## データフロー

### 情報収集フロー
```
1. API呼び出し
   ↓
2. api_call_logs に記録
   ↓
3. anilist_cache / rss_cache にキャッシュ
   ↓
4. works テーブルに作品登録（新規の場合）
   ↓
5. releases テーブルにリリース情報登録
   ↓
6. ng_keywords でフィルタリング
```

### 通知フロー
```
1. releases で notified=0 のレコード抽出
   ↓
2. user_preferences で通知設定確認
   ↓
3. Gmail API で通知送信
   ↓
4. notification_logs に結果記録
   ↓
5. Google Calendar API でイベント登録
   ↓
6. calendar_events に登録情報保存
   ↓
7. releases.notified を 1 に更新
```

---

## パフォーマンス考慮事項

### 高頻度アクセステーブル
- `releases` (notified=0の検索)
- `api_call_logs` (レート制限チェック)
- `anilist_cache` (キャッシュヒット確認)

### インデックス最適化必須
- `idx_releases_notified_date` - 通知対象検索
- `idx_api_logs_name_date` - API統計
- `idx_anilist_cache_expires` - キャッシュ期限チェック

### 定期メンテナンス
- `VACUUM` - 週次実行推奨
- `ANALYZE` - 日次実行推奨
- キャッシュクリーンアップ - トリガーで自動実行

---

**最終更新**: 2025-12-07
**担当**: Database Designer Agent
