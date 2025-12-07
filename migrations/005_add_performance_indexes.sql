-- Migration: 005_add_performance_indexes.sql
-- Date: 2025-12-07
-- Description: パフォーマンス最適化のための追加インデックス
-- Author: Database Designer Agent
-- Priority: HIGH - 即時実行推奨

BEGIN TRANSACTION;

-- ========================================
-- パフォーマンス最適化インデックス
-- ========================================

-- 通知対象検索の最適化（最重要）
-- 使用クエリ: SELECT * FROM releases WHERE notified=0 AND release_date >= CURRENT_DATE
CREATE INDEX IF NOT EXISTS idx_releases_notified_date_optimized
  ON releases(notified, release_date)
  WHERE notified = 0;  -- Partial index（未通知のみ）

-- API統計集計の最適化
-- 使用クエリ: SELECT COUNT(*), AVG(response_time_ms) FROM api_call_logs WHERE api_name='anilist' AND called_at >= ...
CREATE INDEX IF NOT EXISTS idx_api_logs_stats
  ON api_call_logs(api_name, called_at DESC, response_time_ms);

-- キャッシュ有効期限チェックの最適化
-- 使用クエリ: DELETE FROM anilist_cache WHERE expires_at < CURRENT_TIMESTAMP
CREATE INDEX IF NOT EXISTS idx_anilist_cache_cleanup
  ON anilist_cache(expires_at)
  WHERE expires_at < CURRENT_TIMESTAMP;  -- Partial index

-- RSS取得頻度管理の最適化
-- 使用クエリ: SELECT * FROM rss_cache WHERE is_active=1 ORDER BY last_fetched_at
CREATE INDEX IF NOT EXISTS idx_rss_cache_active_fetched
  ON rss_cache(is_active, last_fetched_at)
  WHERE is_active = 1;

-- エラーログ検索の最適化
-- 使用クエリ: SELECT * FROM error_logs WHERE error_level='ERROR' AND occurred_at >= ...
CREATE INDEX IF NOT EXISTS idx_error_logs_level_time
  ON error_logs(error_level, occurred_at DESC);

-- カレンダーイベント同期チェックの最適化
-- 使用クエリ: SELECT * FROM calendar_events WHERE synced_at IS NULL OR synced_at < ...
CREATE INDEX IF NOT EXISTS idx_calendar_events_sync_status
  ON calendar_events(synced_at)
  WHERE synced_at IS NULL;

-- ユーザー設定取得の最適化
-- 使用クエリ: SELECT * FROM users u JOIN user_preferences p ON u.id=p.user_id WHERE u.is_active=1
CREATE INDEX IF NOT EXISTS idx_users_active
  ON users(is_active, id)
  WHERE is_active = 1;

-- ========================================
-- 統計情報更新
-- ========================================

-- 新しいインデックスの統計情報を生成
ANALYZE releases;
ANALYZE api_call_logs;
ANALYZE anilist_cache;
ANALYZE rss_cache;
ANALYZE error_logs;
ANALYZE calendar_events;
ANALYZE users;

-- ========================================
-- マイグレーション記録
-- ========================================
INSERT INTO schema_migrations(version, description, script_name)
VALUES(5, 'Add performance optimization indexes', '005_add_performance_indexes.sql');

COMMIT;

-- ========================================
-- 検証クエリ（実行後の確認用）
-- ========================================
--
-- インデックス一覧確認:
-- SELECT name, tbl_name, sql FROM sqlite_master
-- WHERE type='index' AND name LIKE 'idx_%'
-- ORDER BY tbl_name, name;
--
-- インデックスサイズ推定:
-- SELECT name, pgsize FROM dbstat
-- WHERE name LIKE 'idx_%'
-- ORDER BY pgsize DESC;
--
-- クエリプラン確認（通知対象検索）:
-- EXPLAIN QUERY PLAN
-- SELECT * FROM releases
-- WHERE notified=0 AND release_date >= DATE('now');
