-- Migration: 002_add_foreign_keys.sql
-- 外部キー制約の追加
-- 作成日: 2025-12-06
-- 説明: データ整合性を保証するため外部キー制約を追加
-- 注意: SQLiteでは既存テーブルに外部キーを追加できないため、テーブル再作成が必要

-- ========================================
-- 準備: 外部キー制約を有効化
-- ========================================
PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- ========================================
-- releasesテーブルの再作成
-- ========================================

-- 新しいスキーマでテーブル作成
CREATE TABLE IF NOT EXISTS releases_new (
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

-- 既存データを移行
INSERT INTO releases_new (
  id, work_id, release_type, number, platform,
  release_date, source, source_url, notified, created_at
)
SELECT
  id, work_id, release_type, number, platform,
  release_date, source, source_url, notified, created_at
FROM releases;

-- 古いテーブルを削除
DROP TABLE releases;

-- 新しいテーブルをリネーム
ALTER TABLE releases_new RENAME TO releases;

-- インデックスを再作成（001_add_recommended_indexes.sqlの内容）
CREATE INDEX IF NOT EXISTS idx_releases_work_id ON releases(work_id);
CREATE INDEX IF NOT EXISTS idx_releases_date ON releases(release_date);
CREATE INDEX IF NOT EXISTS idx_releases_notified ON releases(notified);
CREATE INDEX IF NOT EXISTS idx_releases_platform ON releases(platform);
CREATE INDEX IF NOT EXISTS idx_releases_notified_date ON releases(notified, release_date DESC);
CREATE INDEX IF NOT EXISTS idx_releases_work_date ON releases(work_id, release_date DESC);
CREATE INDEX IF NOT EXISTS idx_releases_source ON releases(source);
CREATE INDEX IF NOT EXISTS idx_releases_type ON releases(release_type);
CREATE INDEX IF NOT EXISTS idx_releases_unnotified_only ON releases(release_date) WHERE notified = 0;

COMMIT;

-- 外部キー制約を有効化
PRAGMA foreign_keys = ON;

-- 整合性チェック
PRAGMA foreign_key_check;

-- 統計情報の更新
ANALYZE;
