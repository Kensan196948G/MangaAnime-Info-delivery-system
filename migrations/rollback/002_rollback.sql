-- Rollback: 002_rollback.sql
-- Description: Rollback for 002_add_notification_logs.sql
-- Author: Database Designer Agent

BEGIN TRANSACTION;

-- トリガー削除
DROP TRIGGER IF EXISTS calendar_events_update_timestamp;

-- インデックス削除
DROP INDEX IF EXISTS idx_notification_logs_release_id;
DROP INDEX IF EXISTS idx_notification_logs_sent_at;
DROP INDEX IF EXISTS idx_notification_logs_status;
DROP INDEX IF EXISTS idx_notification_logs_type_status;

DROP INDEX IF EXISTS idx_calendar_events_release_id;
DROP INDEX IF EXISTS idx_calendar_events_google_id;
DROP INDEX IF EXISTS idx_calendar_events_start;
DROP INDEX IF EXISTS idx_calendar_events_synced;

-- テーブル削除
DROP TABLE IF EXISTS calendar_events;
DROP TABLE IF EXISTS notification_logs;

-- マイグレーション記録削除
DELETE FROM schema_migrations WHERE version = 2;

COMMIT;
