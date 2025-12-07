-- Rollback: 003_rollback.sql
-- Description: Rollback for 003_add_user_and_filters.sql
-- Author: Database Designer Agent

BEGIN TRANSACTION;

-- トリガー削除
DROP TRIGGER IF EXISTS users_update_timestamp;
DROP TRIGGER IF EXISTS user_preferences_update_timestamp;

-- インデックス削除
DROP INDEX IF EXISTS idx_users_email;
DROP INDEX IF EXISTS idx_users_active;

DROP INDEX IF EXISTS idx_user_preferences_user_id;

DROP INDEX IF EXISTS idx_ng_keywords_keyword;
DROP INDEX IF EXISTS idx_ng_keywords_active;

DROP INDEX IF EXISTS idx_genre_filters_user_id;

DROP INDEX IF EXISTS idx_platform_filters_user_id;

-- テーブル削除（外部キー制約の逆順）
DROP TABLE IF EXISTS platform_filters;
DROP TABLE IF EXISTS genre_filters;
DROP TABLE IF EXISTS ng_keywords;
DROP TABLE IF EXISTS user_preferences;
DROP TABLE IF EXISTS users;

-- マイグレーション記録削除
DELETE FROM schema_migrations WHERE version = 3;

COMMIT;
