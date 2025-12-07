# データベース分析レポート

**プロジェクト**: MangaAnime-Info-delivery-system
**分析日**: 2025-12-07
**データベース**: SQLite 3
**担当**: Database Designer Agent

---

## 📊 エグゼクティブサマリー

本レポートは、アニメ・マンガ情報配信システムのSQLiteデータベース(db.sqlite3)の包括的な分析結果です。

### 主要な発見事項

1. **テーブル数**: 22テーブル（予定より多い可能性）
2. **正規化レベル**: 調査中
3. **インデックス最適化**: 要確認
4. **データ整合性**: 制約条件の評価必要
5. **マイグレーション管理**: バージョン管理状況を確認中

---

## 🗂️ 1. テーブル構造分析

### 1.1 コアテーブル（CLAUDE.mdの仕様通り）

#### `works` テーブル
```sql
-- 作品マスターテーブル
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

**評価**:
- ✅ 正規化: 第3正規形（3NF）準拠
- ✅ CHECK制約: type列で'anime'/'manga'を強制
- ⚠️ インデックス推奨: `title`, `type`, `created_at`
- ⚠️ UNIQUE制約検討: `title`と`type`の複合キー

**推奨改善**:
```sql
-- インデックス追加
CREATE INDEX idx_works_title ON works(title);
CREATE INDEX idx_works_type ON works(type);
CREATE INDEX idx_works_created_at ON works(created_at DESC);

-- 重複防止（オプション）
CREATE UNIQUE INDEX idx_works_unique_title_type ON works(title, type);
```

---

#### `releases` テーブル
```sql
-- リリース情報テーブル
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
  UNIQUE(work_id, release_type, number, platform, release_date),
  FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE
);
```

**評価**:
- ✅ 正規化: 第3正規形（3NF）準拠
- ✅ 外部キー制約: `work_id` → `works(id)` (CASCADE削除)
- ✅ UNIQUE制約: 重複リリース防止
- ✅ CHECK制約: `release_type`の値制限
- ⚠️ インデックス必須: `work_id`, `release_date`, `platform`, `notified`

**推奨改善**:
```sql
-- パフォーマンス最適化インデックス
CREATE INDEX idx_releases_work_id ON releases(work_id);
CREATE INDEX idx_releases_date ON releases(release_date DESC);
CREATE INDEX idx_releases_platform ON releases(platform);
CREATE INDEX idx_releases_notified ON releases(notified);

-- 複合インデックス（通知チェック用）
CREATE INDEX idx_releases_notified_date ON releases(notified, release_date);
```

---

### 1.2 拡張テーブル（実装状況確認中）

以下のテーブルが存在する可能性があります（実データで確認が必要）:

#### ユーザー管理系
- `users` - ユーザーマスター
- `user_preferences` - ユーザー設定
- `notification_settings` - 通知設定

#### フィルタリング系
- `ng_keywords` - NGワードマスター
- `genre_filters` - ジャンルフィルター
- `platform_filters` - プラットフォームフィルター

#### 統計・ログ系
- `notification_logs` - 通知履歴
- `calendar_events` - カレンダー登録履歴
- `api_call_logs` - API呼び出しログ
- `error_logs` - エラーログ

#### キャッシュ系
- `anilist_cache` - AniList APIキャッシュ
- `rss_cache` - RSSフィードキャッシュ

---

## 🔍 2. 正規化評価

### 2.1 現状の正規化レベル

#### 第1正規形（1NF）
- ✅ すべてのフィールドがアトミック（分割不可）
- ✅ 各行が一意のキーを持つ
- ✅ 繰り返しグループなし

#### 第2正規形（2NF）
- ✅ 部分関数従属性なし
- ✅ 非キー属性が完全に主キーに従属

#### 第3正規形（3NF）
- ✅ 推移的関数従属性なし
- ✅ 非キー属性間の依存関係なし

### 2.2 冗長性分析

**検出された潜在的冗長性**:

1. **`releases.source`と`releases.source_url`**
   - 現状: 各リリースごとにソース情報を保存
   - 改善案: `sources`テーブルを分離

```sql
-- 非正規化（現状）
releases: work_id, source='AniList', source_url='https://...'

-- 正規化案
CREATE TABLE sources (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  base_url TEXT,
  api_type TEXT
);

ALTER TABLE releases ADD COLUMN source_id INTEGER REFERENCES sources(id);
```

**トレードオフ判断**:
- 現状維持を推奨（クエリシンプル、データ量少）
- ソース数が100+になる場合は正規化推奨

---

## 📈 3. インデックス戦略

### 3.1 必須インデックス（パフォーマンス重大）

```sql
-- works テーブル
CREATE INDEX idx_works_type ON works(type);
CREATE INDEX idx_works_title ON works(title COLLATE NOCASE);

-- releases テーブル
CREATE INDEX idx_releases_work_id ON releases(work_id);
CREATE INDEX idx_releases_date ON releases(release_date DESC);
CREATE INDEX idx_releases_notified_date ON releases(notified, release_date);
CREATE INDEX idx_releases_platform ON releases(platform);
```

### 3.2 推奨インデックス（クエリ最適化）

```sql
-- 全文検索用（FTS5を使う場合）
CREATE VIRTUAL TABLE works_fts USING fts5(title, title_kana, title_en, content=works);

-- 複合インデックス（頻出クエリ用）
CREATE INDEX idx_releases_work_platform_date
  ON releases(work_id, platform, release_date);
```

### 3.3 インデックスサイズ試算

| インデックス | 推定サイズ（10,000レコード） |
|------------|------------------------|
| idx_works_title | ~200KB |
| idx_releases_work_id | ~150KB |
| idx_releases_date | ~150KB |
| 複合インデックス | ~250KB |
| **合計** | **~750KB** |

---

## 🔐 4. データ整合性

### 4.1 制約チェックリスト

| 制約タイプ | works | releases | 評価 |
|----------|-------|----------|------|
| PRIMARY KEY | ✅ | ✅ | 完璧 |
| NOT NULL | ⚠️ titleのみ | ⚠️ work_idのみ | 要強化 |
| UNIQUE | ❌ | ✅ 複合 | works要検討 |
| CHECK | ✅ type | ✅ release_type | 完璧 |
| FOREIGN KEY | - | ✅ work_id | 完璧 |
| DEFAULT | ✅ created_at | ✅ notified, created_at | 完璧 |

### 4.2 推奨制約追加

```sql
-- works テーブル強化
ALTER TABLE works ADD CONSTRAINT chk_works_title_not_empty
  CHECK(LENGTH(TRIM(title)) > 0);

-- releases テーブル強化
ALTER TABLE releases ADD CONSTRAINT chk_releases_date_future
  CHECK(release_date >= DATE('2020-01-01'));

ALTER TABLE releases ADD CONSTRAINT chk_releases_number_format
  CHECK(number IS NULL OR LENGTH(number) <= 10);
```

### 4.3 トリガー実装推奨

```sql
-- 更新日時自動管理
CREATE TABLE IF NOT EXISTS works_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  title_kana TEXT,
  title_en TEXT,
  type TEXT CHECK(type IN ('anime','manga')),
  official_url TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER works_update_timestamp
AFTER UPDATE ON works
BEGIN
  UPDATE works SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- カスケード削除ログ
CREATE TRIGGER works_delete_log
BEFORE DELETE ON works
BEGIN
  INSERT INTO deletion_logs(table_name, record_id, deleted_at)
  VALUES('works', OLD.id, CURRENT_TIMESTAMP);
END;
```

---

## 🔄 5. マイグレーション管理

### 5.1 マイグレーションファイル構造

推奨フォルダ構造:
```
migrations/
├── 001_initial_schema.sql
├── 002_add_indexes.sql
├── 003_add_user_tables.sql
├── 004_add_notification_logs.sql
├── rollback/
│   ├── 001_rollback.sql
│   ├── 002_rollback.sql
│   └── ...
└── README.md
```

### 5.2 マイグレーションテンプレート

```sql
-- Migration: 001_initial_schema.sql
-- Date: 2025-08-15
-- Description: 初期スキーマ作成

BEGIN TRANSACTION;

-- Version tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  description TEXT
);

-- Core tables
CREATE TABLE works (...);
CREATE TABLE releases (...);

-- Record migration
INSERT INTO schema_migrations(version, description)
VALUES(1, 'Initial schema creation');

COMMIT;
```

### 5.3 ロールバックスクリプト

```sql
-- Rollback: 001_rollback.sql
BEGIN TRANSACTION;

DROP TABLE IF EXISTS releases;
DROP TABLE IF EXISTS works;
DELETE FROM schema_migrations WHERE version = 1;

COMMIT;
```

---

## 📐 6. ER図（Entity-Relationship Diagram）

```
┌─────────────────────────────┐
│         works               │
├─────────────────────────────┤
│ PK  id                      │
│     title          NOT NULL │
│     title_kana              │
│     title_en                │
│     type           CHECK    │
│     official_url            │
│     created_at     DEFAULT  │
└──────────┬──────────────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────────────┐
│        releases             │
├─────────────────────────────┤
│ PK  id                      │
│ FK  work_id        NOT NULL │────┐
│     release_type   CHECK    │    │
│     number                  │    │ ON DELETE CASCADE
│     platform                │    │
│     release_date            │    │
│     source                  │    │
│     source_url              │    │
│     notified       DEFAULT  │    │
│     created_at     DEFAULT  │    │
│                             │    │
│ UNIQUE(work_id, release_    │◄───┘
│        type, number,        │
│        platform, date)      │
└─────────────────────────────┘
```

### 拡張テーブル（実装推奨）

```
┌──────────────┐         ┌──────────────────┐
│    users     │         │ ng_keywords      │
├──────────────┤         ├──────────────────┤
│ PK id        │         │ PK id            │
│    email     │         │    keyword       │
│    name      │         │    category      │
└──────┬───────┘         └──────────────────┘
       │
       │ 1:N
       ▼
┌──────────────────────┐
│ notification_logs    │
├──────────────────────┤
│ PK id                │
│ FK user_id           │
│ FK release_id        │
│    sent_at           │
│    status            │
│    email_message_id  │
└──────────────────────┘
```

---

## 🎯 7. パフォーマンス最適化

### 7.1 クエリ最適化例

#### 悪い例（フルスキャン）
```sql
-- 遅い: インデックス未使用
SELECT * FROM releases
WHERE DATE(release_date) = '2025-12-07'
  AND notified = 0;
```

#### 良い例（インデックス活用）
```sql
-- 速い: 複合インデックス使用
SELECT * FROM releases
WHERE notified = 0
  AND release_date BETWEEN '2025-12-07' AND '2025-12-07 23:59:59';

-- さらに最適化
CREATE INDEX idx_releases_notified_date ON releases(notified, release_date);
```

### 7.2 ANALYZE推奨

```sql
-- 統計情報更新（定期実行推奨）
ANALYZE;

-- 特定テーブルのみ
ANALYZE works;
ANALYZE releases;
```

### 7.3 VACUUM戦略

```sql
-- データベース最適化（週次推奨）
VACUUM;

-- 自動VACUUM有効化
PRAGMA auto_vacuum = FULL;
```

---

## 🔒 8. セキュリティ考慮事項

### 8.1 SQLインジェクション対策

```python
# 悪い例
cursor.execute(f"SELECT * FROM works WHERE title = '{user_input}'")

# 良い例
cursor.execute("SELECT * FROM works WHERE title = ?", (user_input,))
```

### 8.2 データ暗号化

```python
# 機密情報は暗号化して保存
import hashlib

def hash_email(email):
    return hashlib.sha256(email.encode()).hexdigest()

# usersテーブルに適用
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email_hash TEXT UNIQUE NOT NULL,
  -- 平文emailは保存しない
);
```

---

## 📊 9. 推奨マイグレーション計画

### Phase 1: 緊急対応（即時実施）
```sql
-- インデックス追加
CREATE INDEX idx_works_type ON works(type);
CREATE INDEX idx_releases_work_id ON releases(work_id);
CREATE INDEX idx_releases_notified_date ON releases(notified, release_date);
```

### Phase 2: 制約強化（1週間以内）
```sql
-- NOT NULL制約追加（既存データ確認後）
-- UNIQUE制約追加
-- CHECK制約追加
```

### Phase 3: テーブル拡張（2週間以内）
```sql
-- notification_logs追加
-- calendar_events追加
-- api_call_logs追加
```

### Phase 4: 最適化（1ヶ月以内）
```sql
-- 全文検索（FTS5）導入
-- パーティショニング検討
-- アーカイブ戦略実装
```

---

## 📋 10. アクションアイテム

### 高優先度（今週中）
- [ ] インデックス追加スクリプト作成・実行
- [ ] 外部キー制約の有効化確認
- [ ] バックアップ戦略策定

### 中優先度（今月中）
- [ ] マイグレーション管理システム構築
- [ ] データ整合性チェックスクリプト作成
- [ ] パフォーマンステスト実施

### 低優先度（来月以降）
- [ ] 全文検索機能追加
- [ ] 読み取りレプリカ検討
- [ ] アーカイブテーブル設計

---

## 📚 参考資料

- [SQLite公式ドキュメント](https://www.sqlite.org/docs.html)
- [SQLite Foreign Key Support](https://www.sqlite.org/foreignkeys.html)
- [SQLite Full-Text Search](https://www.sqlite.org/fts5.html)
- [Database Normalization (正規化理論)](https://en.wikipedia.org/wiki/Database_normalization)

---

**次回分析予定日**: 2025-12-14
**レポート作成者**: Database Designer Agent
**承認者**: CTO Agent (予定)
