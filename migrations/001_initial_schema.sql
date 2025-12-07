-- Migration: 001_initial_schema.sql
-- Date: 2025-08-15
-- Description: 初期スキーマ作成（works, releasesテーブル）
-- Author: Database Designer Agent

BEGIN TRANSACTION;

-- ========================================
-- マイグレーション管理テーブル
-- ========================================
CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  description TEXT NOT NULL,
  script_name TEXT NOT NULL
);

-- ========================================
-- 作品マスターテーブル
-- ========================================
CREATE TABLE IF NOT EXISTS works (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL CHECK(LENGTH(TRIM(title)) > 0),
  title_kana TEXT,
  title_en TEXT,
  type TEXT NOT NULL CHECK(type IN ('anime','manga')),
  official_url TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 作品テーブルのインデックス
CREATE INDEX IF NOT EXISTS idx_works_type ON works(type);
CREATE INDEX IF NOT EXISTS idx_works_title ON works(title COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_works_created_at ON works(created_at DESC);

-- 重複防止（タイトル+タイプで一意）
CREATE UNIQUE INDEX IF NOT EXISTS idx_works_unique_title_type
  ON works(title, type);

-- ========================================
-- リリース情報テーブル
-- ========================================
CREATE TABLE IF NOT EXISTS releases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  work_id INTEGER NOT NULL,
  release_type TEXT NOT NULL CHECK(release_type IN ('episode','volume')),
  number TEXT CHECK(number IS NULL OR LENGTH(number) <= 10),
  platform TEXT,
  release_date DATE NOT NULL CHECK(release_date >= '2020-01-01'),
  source TEXT,
  source_url TEXT,
  notified INTEGER DEFAULT 0 CHECK(notified IN (0,1)),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  -- 重複リリース防止
  UNIQUE(work_id, release_type, number, platform, release_date),

  -- 外部キー制約
  FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- リリーステーブルのインデックス
CREATE INDEX IF NOT EXISTS idx_releases_work_id ON releases(work_id);
CREATE INDEX IF NOT EXISTS idx_releases_date ON releases(release_date DESC);
CREATE INDEX IF NOT EXISTS idx_releases_platform ON releases(platform);
CREATE INDEX IF NOT EXISTS idx_releases_notified ON releases(notified);

-- 複合インデックス（通知チェッククエリ用）
CREATE INDEX IF NOT EXISTS idx_releases_notified_date
  ON releases(notified, release_date);

-- 複合インデックス（作品別プラットフォーム検索用）
CREATE INDEX IF NOT EXISTS idx_releases_work_platform_date
  ON releases(work_id, platform, release_date DESC);

-- ========================================
-- トリガー: 更新日時自動更新
-- ========================================

-- works テーブル用
CREATE TRIGGER IF NOT EXISTS works_update_timestamp
AFTER UPDATE ON works
FOR EACH ROW
BEGIN
  UPDATE works SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- releases テーブル用
CREATE TRIGGER IF NOT EXISTS releases_update_timestamp
AFTER UPDATE ON releases
FOR EACH ROW
BEGIN
  UPDATE releases SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ========================================
-- 外部キー制約を有効化
-- ========================================
PRAGMA foreign_keys = ON;

-- ========================================
-- マイグレーション記録
-- ========================================
INSERT INTO schema_migrations(version, description, script_name)
VALUES(1, 'Initial schema: works and releases tables', '001_initial_schema.sql');

COMMIT;

-- ========================================
-- 検証クエリ（実行後の確認用）
-- ========================================
-- SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
-- SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY tbl_name, name;
-- PRAGMA foreign_keys;
-- SELECT * FROM schema_migrations;
