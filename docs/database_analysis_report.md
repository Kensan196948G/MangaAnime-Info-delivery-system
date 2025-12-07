# データベース構造解析レポート

**プロジェクト**: MangaAnime-Info-delivery-system
**解析日時**: 2025-12-06
**データベース**: SQLite3 (db.sqlite3)

---

## 📊 1. テーブル構造とリレーション

### 1.1 テーブル一覧

本システムは以下の3つの主要テーブルで構成されています：

| テーブル名 | 用途 | 主キー |
|----------|------|--------|
| `works` | 作品マスタ（アニメ・マンガ） | `id` (INTEGER) |
| `releases` | リリース情報（エピソード・巻） | `id` (INTEGER) |
| `notification_history` | 通知履歴 | `id` (INTEGER) |

### 1.2 worksテーブル（作品マスタ）

```sql
CREATE TABLE works (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  title_kana TEXT,
  title_en TEXT,
  type TEXT CHECK(type IN ('anime','manga')),
  official_url TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**カラム詳細**:
- `id`: 自動採番の主キー
- `title`: 作品タイトル（必須）
- `title_kana`: かな表記（オプション）
- `title_en`: 英語表記（オプション）
- `type`: 作品種別（'anime' または 'manga'）
- `official_url`: 公式サイトURL
- `created_at`: 登録日時（自動設定）

**制約**:
- `type`に対するCHECK制約あり（'anime'/'manga'のみ許可）

### 1.3 releasesテーブル（リリース情報）

```sql
CREATE TABLE releases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  work_id INTEGER NOT NULL,
  release_type TEXT CHECK(release_type IN ('episode','volume')),
  number TEXT,
  platform TEXT,
  release_date DATE,
  source TEXT,
  source_url TEXT,
  notified INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(work_id, release_type, number, platform, release_date)
);
```

**カラム詳細**:
- `id`: 自動採番の主キー
- `work_id`: worksテーブルへの外部キー参照
- `release_type`: リリース種別（'episode' または 'volume'）
- `number`: エピソード番号/巻数
- `platform`: 配信プラットフォーム
- `release_date`: リリース日
- `source`: データソース名
- `source_url`: ソースURL
- `notified`: 通知済みフラグ（0=未通知, 1=通知済み）
- `created_at`: 登録日時

**制約**:
- `release_type`に対するCHECK制約
- UNIQUE制約（work_id, release_type, number, platform, release_date）で重複防止

### 1.4 notification_historyテーブル（通知履歴）

```sql
CREATE TABLE notification_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  release_id INTEGER NOT NULL,
  notification_type TEXT CHECK(notification_type IN ('email','calendar','both')),
  status TEXT CHECK(status IN ('success','failed','pending')),
  error_message TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (release_id) REFERENCES releases(id) ON DELETE CASCADE
);
```

**カラム詳細**:
- `id`: 主キー
- `release_id`: releasesテーブルへの外部キー
- `notification_type`: 通知タイプ（email/calendar/both）
- `status`: 通知ステータス（success/failed/pending）
- `error_message`: エラーメッセージ（失敗時）
- `created_at`: 通知実行日時

**制約**:
- 外部キー制約（CASCADE DELETE）
- CHECK制約（notification_type, status）

---

## 📈 2. 現在のデータ統計

### 2.1 テーブル別レコード数

```
実行クエリで取得予定:
SELECT 'works' as table_name, COUNT(*) as count FROM works
UNION ALL SELECT 'releases', COUNT(*) FROM releases
UNION ALL SELECT 'notification_history', COUNT(*) FROM notification_history;
```

### 2.2 作品タイプ別分布（works）

```
実行クエリで取得予定:
SELECT type, COUNT(*) as count FROM works GROUP BY type;
```

**予想される分布**:
- anime: XX件
- manga: XX件

### 2.3 リリースタイプ別分布（releases）

```
実行クエリで取得予定:
SELECT release_type, COUNT(*) as count FROM releases GROUP BY release_type;
```

**予想される分布**:
- episode: XX件（アニメエピソード）
- volume: XX件（マンガ巻数）

### 2.4 プラットフォーム別分布（上位10件）

```
SELECT platform, COUNT(*) as count
FROM releases
GROUP BY platform
ORDER BY count DESC
LIMIT 10;
```

**主要プラットフォーム**:
- dアニメストア
- Netflix
- Amazon Prime Video
- BookWalker
- マガポケ
- ジャンプBOOKストア
- 楽天Kobo

### 2.5 データソース別分布

```
SELECT source, COUNT(*) as count
FROM releases
GROUP BY source
ORDER BY count DESC;
```

**データソース**:
- AniList GraphQL API
- しょぼいカレンダーAPI
- 各種RSS（BookWalker, マガポケ等）

---

## 🔍 3. インデックスの状態

### 3.1 現在のインデックス

```sql
-- 実行クエリ
SELECT name, tbl_name, sql
FROM sqlite_master
WHERE type='index' AND sql IS NOT NULL;
```

### 3.2 インデックス評価

**現状の問題点**:
1. **外部キー制約が未定義** - work_idに対する物理的な外部キー制約がない
2. **検索用インデックスが不足** - 以下のカラムにインデックスがない可能性
   - `releases.work_id` - JOIN時のパフォーマンス
   - `releases.release_date` - 日付範囲検索
   - `releases.notified` - 未通知データ抽出
   - `releases.platform` - プラットフォーム別検索
   - `works.type` - 作品種別フィルタ
   - `notification_history.release_id` - 履歴検索
   - `notification_history.status` - ステータス別集計

**推奨インデックス**:
```sql
-- リリーステーブル
CREATE INDEX idx_releases_work_id ON releases(work_id);
CREATE INDEX idx_releases_date ON releases(release_date);
CREATE INDEX idx_releases_notified ON releases(notified);
CREATE INDEX idx_releases_platform ON releases(platform);

-- 作品テーブル
CREATE INDEX idx_works_type ON works(type);
CREATE INDEX idx_works_title ON works(title);

-- 通知履歴テーブル
CREATE INDEX idx_notification_release_id ON notification_history(release_id);
CREATE INDEX idx_notification_status ON notification_history(status);

-- 複合インデックス（頻繁な検索パターン用）
CREATE INDEX idx_releases_work_date ON releases(work_id, release_date);
CREATE INDEX idx_releases_notified_date ON releases(notified, release_date);
```

---

## ⚠️ 4. データ品質問題

### 4.1 NULL値分析

```sql
-- NULL値カウント
SELECT 'works.title_kana' as field, COUNT(*) as null_count
FROM works WHERE title_kana IS NULL
UNION ALL
SELECT 'works.title_en', COUNT(*) FROM works WHERE title_en IS NULL
UNION ALL
SELECT 'works.official_url', COUNT(*) FROM works WHERE official_url IS NULL
UNION ALL
SELECT 'releases.number', COUNT(*) FROM releases WHERE number IS NULL;
```

**想定される問題**:
- `title_kana`: オプション項目だが、日本語ソートに影響
- `title_en`: 国際化対応に必要
- `official_url`: ユーザー体験向上のため重要
- `number`: エピソード/巻数の欠損はデータ品質問題

### 4.2 データ整合性チェック

```sql
-- 孤立したリリースデータ（work_idが存在しない）
SELECT COUNT(*) as orphaned_releases
FROM releases
WHERE work_id NOT IN (SELECT id FROM works);
```

**結果が0以上の場合**: データ整合性に問題あり（外部キー制約がないため発生可能）

### 4.3 重複データチェック

```sql
-- UNIQUE制約違反の可能性
SELECT work_id, release_type, number, platform, release_date, COUNT(*) as duplicates
FROM releases
GROUP BY work_id, release_type, number, platform, release_date
HAVING COUNT(*) > 1;
```

### 4.4 日付形式チェック

```sql
-- 不正な日付形式の検出
SELECT release_date, COUNT(*) as count
FROM releases
WHERE release_date IS NOT NULL
  AND release_date NOT LIKE '____-__-__'
GROUP BY release_date;
```

---

## 🚀 5. パフォーマンス改善提案

### 5.1 緊急度: 高

#### 1. 外部キー制約の追加

**問題**: 現在、releasesテーブルのwork_idに対する外部キー制約が定義されていない
**影響**: データ整合性が保証されず、孤立データが発生する可能性

**解決策**:
```sql
-- 新しいテーブルを作成（外部キー制約付き）
CREATE TABLE releases_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  work_id INTEGER NOT NULL,
  release_type TEXT CHECK(release_type IN ('episode','volume')),
  number TEXT,
  platform TEXT,
  release_date DATE,
  source TEXT,
  source_url TEXT,
  notified INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(work_id, release_type, number, platform, release_date),
  FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE
);

-- データ移行
INSERT INTO releases_new SELECT * FROM releases;

-- テーブル入れ替え
DROP TABLE releases;
ALTER TABLE releases_new RENAME TO releases;
```

#### 2. 必須インデックスの追加

```sql
-- 最優先インデックス
CREATE INDEX idx_releases_work_id ON releases(work_id);
CREATE INDEX idx_releases_notified_date ON releases(notified, release_date);
CREATE INDEX idx_notification_release_id ON notification_history(release_id);
```

**期待効果**:
- JOIN操作: 10-100倍高速化
- 未通知データ抽出: 5-50倍高速化

### 5.2 緊急度: 中

#### 3. データ正規化の強化

**問題**: platformカラムが自由テキストのため、表記揺れの可能性

**解決策**: platformsマスタテーブルの追加
```sql
CREATE TABLE platforms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  type TEXT CHECK(type IN ('anime','manga','both')),
  official_url TEXT
);

-- releasesテーブルを変更
ALTER TABLE releases ADD COLUMN platform_id INTEGER REFERENCES platforms(id);
```

#### 4. 全文検索対応

```sql
-- FTS5仮想テーブルの作成
CREATE VIRTUAL TABLE works_fts USING fts5(
  title, title_kana, title_en,
  content='works',
  content_rowid='id'
);

-- トリガーで自動同期
CREATE TRIGGER works_ai AFTER INSERT ON works BEGIN
  INSERT INTO works_fts(rowid, title, title_kana, title_en)
  VALUES (new.id, new.title, new.title_kana, new.title_en);
END;
```

### 5.3 緊急度: 低

#### 5. パーティショニング（将来対応）

大規模データ（10万件以上）になった場合:
```sql
-- 年度別テーブル分割
CREATE TABLE releases_2025 AS SELECT * FROM releases WHERE release_date >= '2025-01-01';
CREATE TABLE releases_2024 AS SELECT * FROM releases WHERE release_date >= '2024-01-01' AND release_date < '2025-01-01';
```

#### 6. アーカイブ戦略

```sql
-- 古い通知履歴のアーカイブ
CREATE TABLE notification_history_archive AS
SELECT * FROM notification_history
WHERE created_at < date('now', '-1 year');

DELETE FROM notification_history
WHERE id IN (SELECT id FROM notification_history_archive);
```

---

## 📋 6. modules/db.py コード分析

### 6.1 現在の実装状況

**確認項目**:
- [ ] トランザクション管理
- [ ] コネクションプーリング
- [ ] エラーハンドリング
- [ ] SQLインジェクション対策
- [ ] ロギング

### 6.2 推奨されるベストプラクティス

```python
import sqlite3
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='db.sqlite3'):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def get_connection(self):
        """コネクション管理（自動クローズ）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 辞書形式でアクセス
        conn.execute("PRAGMA foreign_keys = ON")  # 外部キー制約有効化
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def insert_work(self, title, type, **kwargs):
        """作品登録（パラメータ化クエリ）"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO works (title, type, title_kana, title_en, official_url)
                VALUES (?, ?, ?, ?, ?)
            """, (title, type, kwargs.get('title_kana'),
                  kwargs.get('title_en'), kwargs.get('official_url')))
            return cursor.lastrowid
```

---

## 🎯 7. 優先実装ロードマップ

### フェーズ1（即時対応）
1. **インデックス追加** - パフォーマンス改善
2. **外部キー制約追加** - データ整合性保証
3. **NULL値チェック強化** - データ品質向上

### フェーズ2（1週間以内）
4. **platformsマスタ作成** - 正規化
5. **全文検索対応** - UX向上
6. **監視クエリ整備** - 運用改善

### フェーズ3（1ヶ月以内）
7. **アーカイブ戦略実装** - ストレージ最適化
8. **分析用ビュー作成** - レポート機能
9. **バックアップ自動化** - 災害対策

---

## 📊 8. 推奨される定期チェック項目

```sql
-- 1. データ増加率チェック（週次）
SELECT
  date(created_at) as date,
  COUNT(*) as new_records
FROM releases
WHERE created_at >= date('now', '-7 days')
GROUP BY date(created_at);

-- 2. 通知成功率チェック（日次）
SELECT
  status,
  COUNT(*) * 100.0 / (SELECT COUNT(*) FROM notification_history) as percentage
FROM notification_history
WHERE created_at >= date('now', '-1 day')
GROUP BY status;

-- 3. データ品質チェック（日次）
SELECT
  'Missing title_kana' as issue,
  COUNT(*) as count
FROM works
WHERE title_kana IS NULL
UNION ALL
SELECT 'Orphaned releases', COUNT(*)
FROM releases
WHERE work_id NOT IN (SELECT id FROM works);

-- 4. パフォーマンスチェック（EXPLAIN QUERY PLAN）
EXPLAIN QUERY PLAN
SELECT w.title, r.release_date, r.platform
FROM releases r
JOIN works w ON r.work_id = w.id
WHERE r.notified = 0
  AND r.release_date >= date('now')
ORDER BY r.release_date;
```

---

## 🔧 9. 実行推奨マイグレーションSQL

以下のマイグレーションスクリプトを`migrations/`ディレクトリに保存することを推奨します。

**ファイル**: `migrations/001_add_recommended_indexes.sql`
```sql
-- インデックス追加マイグレーション
CREATE INDEX IF NOT EXISTS idx_releases_work_id ON releases(work_id);
CREATE INDEX IF NOT EXISTS idx_releases_date ON releases(release_date);
CREATE INDEX IF NOT EXISTS idx_releases_notified ON releases(notified);
CREATE INDEX IF NOT EXISTS idx_releases_platform ON releases(platform);
CREATE INDEX IF NOT EXISTS idx_works_type ON works(type);
CREATE INDEX IF NOT EXISTS idx_notification_release_id ON notification_history(release_id);
CREATE INDEX IF NOT EXISTS idx_notification_status ON notification_history(status);
CREATE INDEX IF NOT EXISTS idx_releases_work_date ON releases(work_id, release_date);
CREATE INDEX IF NOT EXISTS idx_releases_notified_date ON releases(notified, release_date);
```

**ファイル**: `migrations/002_add_foreign_keys.sql`
```sql
-- 外部キー制約追加（テーブル再作成が必要）
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

-- releases テーブル再作成
CREATE TABLE releases_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  work_id INTEGER NOT NULL,
  release_type TEXT CHECK(release_type IN ('episode','volume')),
  number TEXT,
  platform TEXT,
  release_date DATE,
  source TEXT,
  source_url TEXT,
  notified INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(work_id, release_type, number, platform, release_date),
  FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE
);

INSERT INTO releases_new SELECT * FROM releases;
DROP TABLE releases;
ALTER TABLE releases_new RENAME TO releases;

COMMIT;
PRAGMA foreign_keys=ON;
```

---

## 📝 10. まとめ

### 現状の強み
- シンプルで理解しやすいスキーマ設計
- CHECK制約による基本的なデータ検証
- UNIQUE制約による重複防止

### 改善が必要な点
- インデックスの不足（パフォーマンス）
- 外部キー制約の未実装（データ整合性）
- NULL値の管理（データ品質）

### 推奨アクション
1. **即座に実施**: インデックス追加（migrations/001）
2. **計画的に実施**: 外部キー制約追加（migrations/002）
3. **継続的に実施**: データ品質チェックの自動化

---

**次のステップ**:
1. このレポートを確認
2. `scripts/analyze_database.py` で実データを取得
3. マイグレーションスクリプトの実行

**解析担当**: Database Designer Agent
**レビュー**: CTO Agent推奨
