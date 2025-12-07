-- Migration: 003_add_user_and_filters.sql
-- Date: 2025-08-17
-- Description: ユーザー管理とフィルタリング機能テーブル追加
-- Author: Database Designer Agent

BEGIN TRANSACTION;

-- ========================================
-- ユーザーマスターテーブル
-- ========================================
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL CHECK(LENGTH(email) > 0 AND email LIKE '%@%'),
  name TEXT,
  is_active INTEGER DEFAULT 1 CHECK(is_active IN (0,1)),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_login_at DATETIME
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- 更新日時トリガー
CREATE TRIGGER IF NOT EXISTS users_update_timestamp
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
  UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ========================================
-- ユーザー設定テーブル
-- ========================================
CREATE TABLE IF NOT EXISTS user_preferences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  notify_anime INTEGER DEFAULT 1 CHECK(notify_anime IN (0,1)),
  notify_manga INTEGER DEFAULT 1 CHECK(notify_manga IN (0,1)),
  notify_email INTEGER DEFAULT 1 CHECK(notify_email IN (0,1)),
  notify_calendar INTEGER DEFAULT 1 CHECK(notify_calendar IN (0,1)),
  timezone TEXT DEFAULT 'Asia/Tokyo',
  language TEXT DEFAULT 'ja' CHECK(language IN ('ja','en')),
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE(user_id)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id
  ON user_preferences(user_id);

-- 更新日時トリガー
CREATE TRIGGER IF NOT EXISTS user_preferences_update_timestamp
AFTER UPDATE ON user_preferences
FOR EACH ROW
BEGIN
  UPDATE user_preferences SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ========================================
-- NGワードマスターテーブル
-- ========================================
CREATE TABLE IF NOT EXISTS ng_keywords (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  keyword TEXT UNIQUE NOT NULL CHECK(LENGTH(TRIM(keyword)) > 0),
  category TEXT CHECK(category IN ('adult','genre','other')),
  is_active INTEGER DEFAULT 1 CHECK(is_active IN (0,1)),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- デフォルトNGワード挿入
INSERT OR IGNORE INTO ng_keywords(keyword, category) VALUES
  ('エロ', 'adult'),
  ('R18', 'adult'),
  ('成人向け', 'adult'),
  ('BL', 'genre'),
  ('百合', 'genre'),
  ('ボーイズラブ', 'genre');

-- インデックス
CREATE INDEX IF NOT EXISTS idx_ng_keywords_keyword
  ON ng_keywords(keyword COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_ng_keywords_active
  ON ng_keywords(is_active);

-- ========================================
-- ジャンルフィルターテーブル
-- ========================================
CREATE TABLE IF NOT EXISTS genre_filters (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  genre_name TEXT NOT NULL,
  is_blocked INTEGER DEFAULT 0 CHECK(is_blocked IN (0,1)),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE(user_id, genre_name)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_genre_filters_user_id
  ON genre_filters(user_id);

-- ========================================
-- プラットフォームフィルターテーブル
-- ========================================
CREATE TABLE IF NOT EXISTS platform_filters (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  platform_name TEXT NOT NULL,
  is_enabled INTEGER DEFAULT 1 CHECK(is_enabled IN (0,1)),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE(user_id, platform_name)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_platform_filters_user_id
  ON platform_filters(user_id);

-- ========================================
-- マイグレーション記録
-- ========================================
INSERT INTO schema_migrations(version, description, script_name)
VALUES(3, 'Add users, preferences, and filter tables', '003_add_user_and_filters.sql');

COMMIT;
