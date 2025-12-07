-- Rollback: 005_rollback.sql
-- Description: Rollback for 005_add_performance_indexes.sql
-- Author: Database Designer Agent

BEGIN TRANSACTION;

-- ========================================
-- インデックス削除
-- ========================================

DROP INDEX IF EXISTS idx_releases_notified_date_optimized;
DROP INDEX IF EXISTS idx_api_logs_stats;
DROP INDEX IF EXISTS idx_anilist_cache_cleanup;
DROP INDEX IF EXISTS idx_rss_cache_active_fetched;
DROP INDEX IF EXISTS idx_error_logs_level_time;
DROP INDEX IF EXISTS idx_calendar_events_sync_status;
DROP INDEX IF EXISTS idx_users_active;

-- ========================================
-- マイグレーション記録削除
-- ========================================

DELETE FROM schema_migrations WHERE version = 5;

COMMIT;

-- 確認クエリ
-- SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;
