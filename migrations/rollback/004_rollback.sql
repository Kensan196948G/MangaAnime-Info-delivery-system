-- Rollback: 004_rollback.sql
-- Description: Rollback for 004_add_api_logs_and_cache.sql
-- Author: Database Designer Agent

BEGIN TRANSACTION;

-- トリガー削除
DROP TRIGGER IF EXISTS anilist_cache_cleanup;

-- インデックス削除
DROP INDEX IF EXISTS idx_api_logs_api_name;
DROP INDEX IF EXISTS idx_api_logs_called_at;
DROP INDEX IF EXISTS idx_api_logs_status;
DROP INDEX IF EXISTS idx_api_logs_name_date;

DROP INDEX IF EXISTS idx_error_logs_level;
DROP INDEX IF EXISTS idx_error_logs_module;
DROP INDEX IF EXISTS idx_error_logs_occurred_at;

DROP INDEX IF EXISTS idx_anilist_cache_id;
DROP INDEX IF EXISTS idx_anilist_cache_expires;

DROP INDEX IF EXISTS idx_rss_cache_url;
DROP INDEX IF EXISTS idx_rss_cache_fetched;

DROP INDEX IF EXISTS idx_rss_items_feed_id;
DROP INDEX IF EXISTS idx_rss_items_guid;
DROP INDEX IF EXISTS idx_rss_items_pub_date;

DROP INDEX IF EXISTS idx_system_stats_date;

-- テーブル削除
DROP TABLE IF EXISTS system_stats;
DROP TABLE IF EXISTS rss_items;
DROP TABLE IF EXISTS rss_cache;
DROP TABLE IF EXISTS anilist_cache;
DROP TABLE IF EXISTS error_logs;
DROP TABLE IF EXISTS api_call_logs;

-- マイグレーション記録削除
DELETE FROM schema_migrations WHERE version = 4;

COMMIT;
