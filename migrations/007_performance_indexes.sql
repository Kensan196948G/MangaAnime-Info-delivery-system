-- Migration 007: Performance Indexes
-- パフォーマンス最適化のための追加インデックス
-- Created: 2025-12-08

-- =====================================================
-- releases テーブルのインデックス
-- =====================================================

-- 未通知リリース検索用（notified=0 かつ release_date順）
CREATE INDEX IF NOT EXISTS idx_releases_notified_date
ON releases(notified, release_date);

-- 作品別リリース検索用
CREATE INDEX IF NOT EXISTS idx_releases_work_platform_date
ON releases(work_id, platform, release_date DESC);

-- プラットフォーム別検索用
CREATE INDEX IF NOT EXISTS idx_releases_platform_date
ON releases(platform, release_date);

-- カレンダー同期用
CREATE INDEX IF NOT EXISTS idx_releases_calendar_synced
ON releases(calendar_synced, release_date);

-- =====================================================
-- works テーブルのインデックス
-- =====================================================

-- タイプ別検索用
CREATE INDEX IF NOT EXISTS idx_works_type
ON works(type);

-- タイトル検索用（部分一致）
CREATE INDEX IF NOT EXISTS idx_works_title
ON works(title);

-- =====================================================
-- notification_logs テーブルのインデックス
-- =====================================================

-- 送信ステータス別検索用
CREATE INDEX IF NOT EXISTS idx_notification_logs_status
ON notification_logs(status, sent_at);

-- リリースID別検索用
CREATE INDEX IF NOT EXISTS idx_notification_logs_release_id
ON notification_logs(release_id);

-- =====================================================
-- audit_logs テーブルのインデックス
-- =====================================================

-- ユーザー・アクション別検索用
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action
ON audit_logs(user_id, action, timestamp);

-- タイムスタンプ検索用
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp
ON audit_logs(timestamp);

-- =====================================================
-- SQLite最適化設定
-- =====================================================

-- WALモード有効化（並行アクセス最適化）
PRAGMA journal_mode = WAL;

-- 外部キー制約有効化
PRAGMA foreign_keys = ON;

-- 自動最適化有効化
PRAGMA optimize;
