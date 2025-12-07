-- Rollback: 001_rollback.sql
-- Description: Rollback for 001_initial_schema.sql
-- Author: Database Designer Agent

BEGIN TRANSACTION;

-- トリガー削除
DROP TRIGGER IF EXISTS works_update_timestamp;
DROP TRIGGER IF EXISTS releases_update_timestamp;

-- インデックス削除
DROP INDEX IF EXISTS idx_works_type;
DROP INDEX IF EXISTS idx_works_title;
DROP INDEX IF EXISTS idx_works_created_at;
DROP INDEX IF EXISTS idx_works_unique_title_type;

DROP INDEX IF EXISTS idx_releases_work_id;
DROP INDEX IF EXISTS idx_releases_date;
DROP INDEX IF EXISTS idx_releases_platform;
DROP INDEX IF EXISTS idx_releases_notified;
DROP INDEX IF EXISTS idx_releases_notified_date;
DROP INDEX IF EXISTS idx_releases_work_platform_date;

-- テーブル削除（releasesが先、外部キー制約のため）
DROP TABLE IF EXISTS releases;
DROP TABLE IF EXISTS works;

-- マイグレーション記録削除
DELETE FROM schema_migrations WHERE version = 1;

COMMIT;

-- 確認クエリ
-- SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
