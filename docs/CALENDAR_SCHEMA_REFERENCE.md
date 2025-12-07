# カレンダー統合スキーマリファレンス

**バージョン**: 1.0
**作成日**: 2025-12-07

---

## 1. スキーマ概要図

```
┌──────────────────────────┐
│     works（既存）         │
│  id, title, type, ...   │
└────────────┬─────────────┘
             │
             │ 1:N
             │
┌────────────▼─────────────┐
│     releases（拡張）      │
│ ├─ 基本カラム            │
│ │  id, work_id,        │
│ │  release_type,       │
│ │  number, platform,   │
│ │  release_date        │
│ │                      │
│ └─ カレンダー同期カラム  │
│    ├─ calendar_synced  │
│    ├─ calendar_event_id│
│    └─ calendar_synced_at│
└────────────┬─────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
 ┌──────────┐ ┌──────────────────┐
 │calendar_ │ │calendar_sync_log │
 │metadata  │ │                  │
 └──────────┘ └──────────────────┘
```

---

## 2. スキーマ詳細定義

### 2.1 releases テーブル（拡張）

#### 既存カラム
| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | INTEGER | PK, NOT NULL | リリースID |
| work_id | INTEGER | FK, NOT NULL | 作品ID |
| release_type | TEXT | CHECK, NOT NULL | episode/volume |
| number | TEXT | | エピソード/巻番号 |
| platform | TEXT | | Netflix, dアニメ等 |
| release_date | DATE | NOT NULL | リリース日 |
| source | TEXT | | 情報ソース |
| source_url | TEXT | | ソースURL |
| notified | INTEGER | DEFAULT 0 | 0: 未送信, 1: 送信済み |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 作成日時 |

#### 新規追加カラム

```sql
-- 1. calendar_synced (INTEGER)
-- 説明: カレンダー同期状態フラグ
-- デフォルト: 0
-- 値: 0 = 未同期, 1 = 同期済み
-- インデックス: YES (複合インデックス)
-- 目的: 同期対象リリースの高速検索
ALTER TABLE releases ADD COLUMN calendar_synced INTEGER DEFAULT 0;

-- 2. calendar_event_id (TEXT)
-- 説明: GoogleカレンダーイベントID
-- デフォルト: NULL
-- ユニーク制約: YES (NULL を除く)
-- 目的: Google Calendar イベントとの紐付け
-- 形式例: "event123abc456def"
ALTER TABLE releases ADD COLUMN calendar_event_id TEXT;

-- 3. calendar_synced_at (DATETIME)
-- 説明: カレンダー同期実行日時
-- デフォルト: NULL
-- 更新: 同期時にトリガーで自動更新
-- 目的: 同期実行の監査証跡
ALTER TABLE releases ADD COLUMN calendar_synced_at DATETIME;
```

#### インデックス戦略

```sql
-- インデックス 1: 未同期リリース高速検索
CREATE INDEX idx_releases_calendar_unsynced
  ON releases(calendar_synced, release_date)
  WHERE calendar_synced = 0;
-- 説明: 同期対象リリースをスキャン
-- 使用クエリ:
--   SELECT * FROM releases
--   WHERE calendar_synced = 0 AND release_date >= TODAY

-- インデックス 2: calendar_event_id の一意性
CREATE UNIQUE INDEX idx_releases_calendar_event_id
  ON releases(calendar_event_id)
  WHERE calendar_event_id IS NOT NULL;
-- 説明: Googleイベントとの重複登録を防止
-- 使用クエリ:
--   SELECT * FROM releases
--   WHERE calendar_event_id = 'event123abc'

-- インデックス 3: 同期完了した履歴検索
CREATE INDEX idx_releases_calendar_synced_at
  ON releases(calendar_synced_at DESC)
  WHERE calendar_synced = 1;
-- 説明: 同期履歴の時系列検索
-- 使用クエリ:
--   SELECT * FROM releases
--   WHERE calendar_synced_at > '2025-12-01'
```

#### クエリ例

```sql
-- Q1: 今月未同期のアニメリリースを取得
SELECT r.*, w.title FROM releases r
JOIN works w ON r.work_id = w.id
WHERE r.calendar_synced = 0
  AND r.release_date BETWEEN '2025-12-01' AND '2025-12-31'
  AND w.type = 'anime'
ORDER BY r.release_date ASC;

-- Q2: 過去1日に同期されたリリースを確認
SELECT r.id, r.calendar_event_id, r.calendar_synced_at
FROM releases r
WHERE r.calendar_synced_at > datetime('now', '-1 day')
ORDER BY r.calendar_synced_at DESC;

-- Q3: 同期済みの特定作品のリリース
SELECT r.calendar_event_id, r.release_date
FROM releases r
WHERE r.work_id = ? AND r.calendar_synced = 1;
```

---

### 2.2 calendar_sync_log テーブル

#### 目的
同期操作の完全な監査証跡を記録し、エラー追跡・リトライ管理を実現

#### テーブル定義

```sql
CREATE TABLE calendar_sync_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  -- 外部キー・紐付け
  release_id INTEGER NOT NULL,
  work_id INTEGER NOT NULL,
  google_event_id TEXT,

  -- 同期状態
  sync_status TEXT CHECK(sync_status IN
    ('pending', 'synced', 'failed', 'updated', 'deleted')),
  sync_type TEXT CHECK(sync_type IN ('create', 'update', 'delete')),

  -- エラー情報
  error_message TEXT,

  -- リトライ管理
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 3,

  -- タイムスタンプ
  synced_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  -- 制約
  FOREIGN KEY (release_id) REFERENCES releases(id) ON DELETE CASCADE,
  FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
  UNIQUE(release_id, sync_type)
);
```

#### カラム詳細

| カラム | 型 | 説明 | 値の例 |
|-------|-----|------|--------|
| id | INTEGER | プライマリキー | 1, 2, 3, ... |
| release_id | INTEGER | リリースID（FK） | 100 |
| work_id | INTEGER | 作品ID（FK） | 50 |
| google_event_id | TEXT | GoogleカレンダーイベントID | "3d92r28d0..." |
| sync_status | TEXT | 同期状態 | pending, synced, failed, updated, deleted |
| sync_type | TEXT | 操作タイプ | create, update, delete |
| error_message | TEXT | エラーメッセージ | "Authentication failed" |
| retry_count | INTEGER | 実行済みリトライ回数 | 0, 1, 2, 3 |
| max_retries | INTEGER | 最大リトライ回数 | 3 |
| synced_at | DATETIME | 同期完了日時 | 2025-12-07 10:30:45 |
| created_at | DATETIME | ログ作成日時 | 2025-12-07 10:15:20 |
| updated_at | DATETIME | ログ更新日時 | 2025-12-07 10:35:00 |

#### 同期状態遷移

```
pending ──(成功)──► synced
  ▲                   │
  │                   ▼
  └─(リトライ)    (更新検出)
                      │
                      ▼
                   updated ──(削除)──► deleted
                      │
                      └──(失敗)──► failed
```

#### インデックス戦略

```sql
-- インデックス 1: 同期状態による検索
CREATE INDEX idx_calendar_sync_log_status
  ON calendar_sync_log(sync_status, created_at DESC);
-- 使用: failed/pending レコード検索

-- インデックス 2: リリースIDによる検索
CREATE INDEX idx_calendar_sync_log_release_id
  ON calendar_sync_log(release_id);
-- 使用: 特定リリースの同期履歴検索

-- インデックス 3: 作品IDによる検索
CREATE INDEX idx_calendar_sync_log_work_id
  ON calendar_sync_log(work_id);
-- 使用: 作品ごとの同期統計

-- インデックス 4: 完了時刻による検索
CREATE INDEX idx_calendar_sync_log_synced_at
  ON calendar_sync_log(synced_at DESC)
  WHERE synced_at IS NOT NULL;
-- 使用: 日付範囲での同期完了レコード検索

-- インデックス 5: ペンディング処理検索
CREATE INDEX idx_calendar_sync_log_pending
  ON calendar_sync_log(created_at)
  WHERE sync_status = 'pending';
-- 使用: リトライ対象の検出
```

#### クエリ例

```sql
-- Q1: 同期失敗したリリースを取得
SELECT csl.*, r.id release_id, w.title
FROM calendar_sync_log csl
JOIN releases r ON csl.release_id = r.id
JOIN works w ON csl.work_id = w.id
WHERE csl.sync_status = 'failed'
  AND csl.retry_count < csl.max_retries
ORDER BY csl.created_at ASC
LIMIT 10;

-- Q2: 本日の同期統計
SELECT
  sync_status,
  COUNT(*) as count,
  sync_type
FROM calendar_sync_log
WHERE DATE(created_at) = DATE('now')
GROUP BY sync_status, sync_type;

-- Q3: リトライ対象リリース（3回以内）
SELECT r.id, r.number, csl.retry_count, csl.error_message
FROM calendar_sync_log csl
JOIN releases r ON csl.release_id = r.id
WHERE csl.sync_status = 'pending'
  AND csl.retry_count < 3
ORDER BY csl.created_at ASC;

-- Q4: 特定リリースの同期履歴
SELECT * FROM calendar_sync_log
WHERE release_id = ?
ORDER BY created_at DESC;
```

---

### 2.3 calendar_metadata テーブル

#### 目的
カレンダーイベント固有のメタデータを保存。ユーザーの設定やカスタマイズを反映

#### テーブル定義

```sql
CREATE TABLE calendar_metadata (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  -- 紐付け
  release_id INTEGER UNIQUE NOT NULL,

  -- イベント情報
  calendar_title TEXT,
  calendar_description TEXT,
  calendar_location TEXT,

  -- イベント設定
  event_color TEXT,
  reminder_minutes_before INTEGER DEFAULT 1440,
  calendar_id TEXT DEFAULT 'primary',
  is_all_day INTEGER DEFAULT 0,

  -- タイムスタンプ
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  -- 制約
  FOREIGN KEY (release_id) REFERENCES releases(id) ON DELETE CASCADE
);
```

#### カラム詳細

| カラム | 型 | デフォルト | 説明 |
|-------|-----|----------|------|
| id | INTEGER | | プライマリキー |
| release_id | INTEGER | | リリースID（一意キー） |
| calendar_title | TEXT | | イベントタイトル |
| calendar_description | TEXT | | 説明文（HTMLサポート） |
| calendar_location | TEXT | | 場所（プラットフォーム名） |
| event_color | TEXT | | イベント色ID（"1"～"11"） |
| reminder_minutes_before | INTEGER | 1440 | リマインダー時間（分） |
| calendar_id | TEXT | 'primary' | ターゲットカレンダーID |
| is_all_day | INTEGER | 0 | 0: 時刻有, 1: 終日イベント |
| created_at | DATETIME | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | DATETIME | CURRENT_TIMESTAMP | 更新日時 |

#### イベント色マッピング

```python
EVENT_COLORS = {
    '1': 'Tomato (赤)',
    '2': 'Flamingo (ピンク)',
    '3': 'Tangerine (オレンジ)',
    '4': 'Banana (黄)',
    '5': 'Sage (緑)',
    '6': 'Basil (濃緑)',
    '7': 'Peacock (青)',
    '8': 'Blueberry (濃青)',
    '9': 'Lavender (紫)',
    '10': 'Grape (濃紫)',
    '11': 'Graphite (灰)'
}

# デフォルト色分け
WORK_TYPE_COLORS = {
    'anime': '7',    # Peacock (青)
    'manga': '5'     # Sage (緑)
}
```

#### リマインダー設定

```python
REMINDER_PRESETS = {
    'at_release': 0,           # リリース時
    '1_hour_before': 60,       # 1時間前
    '1_day_before': 1440,      # 1日前（デフォルト）
    '3_days_before': 4320,     # 3日前
    '1_week_before': 10080     # 1週間前
}
```

#### インデックス

```sql
CREATE INDEX idx_calendar_metadata_release_id
  ON calendar_metadata(release_id);

CREATE INDEX idx_calendar_metadata_calendar_id
  ON calendar_metadata(calendar_id);
```

---

## 3. ビュー定義

### 3.1 v_calendar_sync_status ビュー

#### 目的
リリースのカレンダー同期状態を一元的に把握

#### 定義

```sql
CREATE VIEW v_calendar_sync_status AS
SELECT
  r.id as release_id,
  w.id as work_id,
  w.title,
  r.number,
  r.platform,
  r.release_date,
  r.calendar_synced,
  r.calendar_event_id,
  r.calendar_synced_at,
  csl.sync_status,
  csl.error_message,
  csl.retry_count,
  CASE
    WHEN r.calendar_synced = 0 AND r.release_date > CURRENT_DATE
      THEN 'awaiting_sync'
    WHEN r.calendar_synced = 1
      THEN 'synced'
    WHEN csl.sync_status = 'failed'
      THEN 'sync_failed'
    ELSE 'unknown'
  END as current_status
FROM releases r
LEFT JOIN works w ON r.work_id = w.id
LEFT JOIN calendar_sync_log csl
  ON r.id = csl.release_id AND csl.sync_type = 'create'
ORDER BY r.release_date ASC;
```

#### 使用例

```sql
-- 同期待ち状態のリリース
SELECT * FROM v_calendar_sync_status
WHERE current_status = 'awaiting_sync'
ORDER BY release_date ASC
LIMIT 10;

-- 同期失敗したリリース
SELECT * FROM v_calendar_sync_status
WHERE current_status = 'sync_failed'
ORDER BY release_date DESC;

-- 本日同期されたリリース
SELECT * FROM v_calendar_sync_status
WHERE current_status = 'synced'
  AND DATE(calendar_synced_at) = DATE('now');
```

---

## 4. トリガー定義

### 4.1 自動タイムスタンプ更新トリガー

```sql
-- calendar_metadata の更新時刻自動更新
CREATE TRIGGER trg_calendar_metadata_update
AFTER UPDATE ON calendar_metadata
BEGIN
  UPDATE calendar_metadata SET updated_at = CURRENT_TIMESTAMP
  WHERE id = NEW.id;
END;

-- calendar_sync_log の更新時刻自動更新
CREATE TRIGGER trg_calendar_sync_log_update
AFTER UPDATE ON calendar_sync_log
BEGIN
  UPDATE calendar_sync_log SET updated_at = CURRENT_TIMESTAMP
  WHERE id = NEW.id;
END;

-- releases への calendar_synced_at 自動設定
CREATE TRIGGER trg_releases_calendar_synced_at
BEFORE UPDATE OF calendar_synced ON releases
WHEN NEW.calendar_synced = 1
BEGIN
  UPDATE releases SET calendar_synced_at = CURRENT_TIMESTAMP
  WHERE id = NEW.id;
END;
```

---

## 5. パフォーマンス最適化

### 5.1 ページング例

```sql
-- 大量レコード取得時はオフセットを使用
SELECT * FROM calendar_sync_log
WHERE sync_status = 'pending'
ORDER BY created_at ASC
LIMIT 100 OFFSET 0;  -- ページ0（最初の100件）
```

### 5.2 バッチ処理例

```sql
-- 複数リリースを一括更新
UPDATE releases
SET calendar_synced = 1, calendar_synced_at = CURRENT_TIMESTAMP
WHERE id IN (1, 2, 3, 4, 5);
```

### 5.3 集計クエリ

```sql
-- 日別の同期統計
SELECT
  DATE(created_at) as sync_date,
  sync_status,
  COUNT(*) as count
FROM calendar_sync_log
GROUP BY DATE(created_at), sync_status
ORDER BY sync_date DESC, sync_status;
```

---

## 6. 整合性チェック

### 6.1 外部キー制約の確認

```sql
-- 有効な外部キー制約を確認
PRAGMA foreign_keys = ON;

-- 孤立したレコード検出
SELECT r.id FROM releases r
WHERE r.work_id NOT IN (SELECT id FROM works);
```

### 6.2 ユニーク制約の確認

```sql
-- 重複した calendar_event_id を検出
SELECT calendar_event_id, COUNT(*)
FROM releases
WHERE calendar_event_id IS NOT NULL
GROUP BY calendar_event_id
HAVING COUNT(*) > 1;
```

---

## 7. マイグレーション実行手順

```bash
# 1. バックアップ作成
sqlite3 data/db.sqlite3 ".backup 'data/backup_$(date +%Y%m%d_%H%M%S).sqlite3'"

# 2. マイグレーション実行
sqlite3 data/db.sqlite3 < migrations/006_add_calendar_sync.sql

# 3. スキーマ検証
sqlite3 data/db.sqlite3 ".schema calendar_sync_log"
sqlite3 data/db.sqlite3 ".schema calendar_metadata"

# 4. インデックス確認
sqlite3 data/db.sqlite3 "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='releases';"
```

---

## 8. よくあるクエリ

### 8.1 同期状態の確認

```sql
-- 全体サマリー
SELECT
  COUNT(*) as total_releases,
  SUM(CASE WHEN calendar_synced = 1 THEN 1 ELSE 0 END) as synced_count,
  SUM(CASE WHEN calendar_synced = 0 THEN 1 ELSE 0 END) as unsynced_count,
  ROUND(100.0 * SUM(CASE WHEN calendar_synced = 1 THEN 1 ELSE 0 END) /
        COUNT(*), 2) as sync_percentage
FROM releases;
```

### 8.2 エラー分析

```sql
-- エラーの種類別集計
SELECT
  error_message,
  COUNT(*) as error_count,
  MAX(created_at) as last_occurrence
FROM calendar_sync_log
WHERE sync_status = 'failed'
GROUP BY error_message
ORDER BY error_count DESC;
```

---

## 9. トラブルシューティング

### 9.1 同期が進まない

```sql
-- ペンディング中のレコードを確認
SELECT r.id, r.number, csl.retry_count, csl.error_message
FROM releases r
LEFT JOIN calendar_sync_log csl ON r.id = csl.release_id
WHERE r.calendar_synced = 0
  AND r.release_date > DATE('now');
```

### 9.2 重複イベント

```sql
-- 重複したイベントIDを検出
SELECT calendar_event_id, COUNT(*) as count
FROM releases
WHERE calendar_event_id IS NOT NULL
GROUP BY calendar_event_id
HAVING COUNT(*) > 1;
```

---

## 付録: SQL DDL完全リファレンス

```sql
-- テーブル一覧
SELECT name FROM sqlite_master
WHERE type='table' AND name LIKE 'calendar%';

-- インデックス一覧
SELECT name, tbl_name, sql FROM sqlite_master
WHERE type='index' AND tbl_name LIKE 'calendar%';

-- トリガー一覧
SELECT name, tbl_name, sql FROM sqlite_master
WHERE type='trigger' AND tbl_name LIKE 'calendar%';

-- ビュー一覧
SELECT name, sql FROM sqlite_master
WHERE type='view' AND name LIKE 'v_calendar%';
```
