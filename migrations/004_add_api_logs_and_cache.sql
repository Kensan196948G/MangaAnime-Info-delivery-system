-- Migration: 004_add_api_logs_and_cache.sql
-- Date: 2025-08-18
-- Description: APIログとキャッシュテーブル追加
-- Author: Database Designer Agent

BEGIN TRANSACTION;

-- ========================================
-- API呼び出しログテーブル
-- ========================================
CREATE TABLE IF NOT EXISTS api_call_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  api_name TEXT NOT NULL CHECK(api_name IN ('anilist','shoboical','rss','gmail','gcalendar')),
  endpoint TEXT NOT NULL,
  http_method TEXT CHECK(http_method IN ('GET','POST','PUT','DELETE')),
  status_code INTEGER,
  response_time_ms INTEGER CHECK(response_time_ms >= 0),
  error_message TEXT,
  called_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  rate_limit_remaining INTEGER,
  rate_limit_reset DATETIME
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_api_logs_api_name
  ON api_call_logs(api_name);
CREATE INDEX IF NOT EXISTS idx_api_logs_called_at
  ON api_call_logs(called_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_logs_status
  ON api_call_logs(status_code);

-- 複合インデックス（API別の統計用）
CREATE INDEX IF NOT EXISTS idx_api_logs_name_date
  ON api_call_logs(api_name, called_at DESC);

-- ========================================
-- エラーログテーブル
-- ========================================
CREATE TABLE IF NOT EXISTS error_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  error_level TEXT NOT NULL CHECK(error_level IN ('DEBUG','INFO','WARNING','ERROR','CRITICAL')),
  module_name TEXT NOT NULL,
  function_name TEXT,
  error_message TEXT NOT NULL,
  stack_trace TEXT,
  context_data TEXT, -- JSON形式
  occurred_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_error_logs_level
  ON error_logs(error_level);
CREATE INDEX IF NOT EXISTS idx_error_logs_module
  ON error_logs(module_name);
CREATE INDEX IF NOT EXISTS idx_error_logs_occurred_at
  ON error_logs(occurred_at DESC);

-- ========================================
-- AniList APIキャッシュテーブル
-- ========================================
CREATE TABLE IF NOT EXISTS anilist_cache (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  anilist_id INTEGER UNIQUE NOT NULL,
  title_romaji TEXT,
  title_english TEXT,
  title_native TEXT,
  genres TEXT, -- JSON配列
  tags TEXT, -- JSON配列
  description TEXT,
  cover_image_url TEXT,
  banner_image_url TEXT,
  episodes INTEGER,
  status TEXT,
  season TEXT,
  season_year INTEGER,
  streaming_episodes TEXT, -- JSON配列
  cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME NOT NULL
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_anilist_cache_id
  ON anilist_cache(anilist_id);
CREATE INDEX IF NOT EXISTS idx_anilist_cache_expires
  ON anilist_cache(expires_at);

-- 期限切れキャッシュ削除トリガー
CREATE TRIGGER IF NOT EXISTS anilist_cache_cleanup
AFTER INSERT ON anilist_cache
BEGIN
  DELETE FROM anilist_cache WHERE expires_at < CURRENT_TIMESTAMP;
END;

-- ========================================
-- RSSフィードキャッシュテーブル
-- ========================================
CREATE TABLE IF NOT EXISTS rss_cache (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  feed_url TEXT UNIQUE NOT NULL,
  feed_title TEXT,
  last_fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_modified TEXT, -- ETag/Last-Modified header
  etag TEXT,
  item_count INTEGER DEFAULT 0,
  is_active INTEGER DEFAULT 1 CHECK(is_active IN (0,1))
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_rss_cache_url
  ON rss_cache(feed_url);
CREATE INDEX IF NOT EXISTS idx_rss_cache_fetched
  ON rss_cache(last_fetched_at DESC);

-- ========================================
-- RSSアイテムキャッシュテーブル
-- ========================================
CREATE TABLE IF NOT EXISTS rss_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  feed_id INTEGER NOT NULL,
  item_guid TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  link TEXT,
  description TEXT,
  pub_date DATETIME,
  author TEXT,
  categories TEXT, -- JSON配列
  cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (feed_id) REFERENCES rss_cache(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_rss_items_feed_id
  ON rss_items(feed_id);
CREATE INDEX IF NOT EXISTS idx_rss_items_guid
  ON rss_items(item_guid);
CREATE INDEX IF NOT EXISTS idx_rss_items_pub_date
  ON rss_items(pub_date DESC);

-- ========================================
-- システム統計テーブル
-- ========================================
CREATE TABLE IF NOT EXISTS system_stats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stat_date DATE UNIQUE NOT NULL,
  total_works INTEGER DEFAULT 0,
  total_releases INTEGER DEFAULT 0,
  total_notifications INTEGER DEFAULT 0,
  api_calls_anilist INTEGER DEFAULT 0,
  api_calls_rss INTEGER DEFAULT 0,
  api_calls_gmail INTEGER DEFAULT 0,
  api_calls_gcalendar INTEGER DEFAULT 0,
  errors_count INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_system_stats_date
  ON system_stats(stat_date DESC);

-- ========================================
-- マイグレーション記録
-- ========================================
INSERT INTO schema_migrations(version, description, script_name)
VALUES(4, 'Add API logs, error logs, and cache tables', '004_add_api_logs_and_cache.sql');

COMMIT;
