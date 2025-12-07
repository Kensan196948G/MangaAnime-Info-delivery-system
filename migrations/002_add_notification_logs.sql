-- Migration: 002_add_notification_logs.sql
-- Date: 2025-08-16
-- Description: 通知ログとカレンダーイベントテーブル追加
-- Author: Database Designer Agent

BEGIN TRANSACTION;

-- ========================================
-- 通知ログテーブル
-- ========================================
CREATE TABLE IF NOT EXISTS notification_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  release_id INTEGER NOT NULL,
  notification_type TEXT NOT NULL CHECK(notification_type IN ('email','calendar','both')),
  sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT NOT NULL CHECK(status IN ('success','failed','pending')) DEFAULT 'pending',
  email_message_id TEXT,
  error_message TEXT,
  retry_count INTEGER DEFAULT 0 CHECK(retry_count >= 0),

  FOREIGN KEY (release_id) REFERENCES releases(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_notification_logs_release_id
  ON notification_logs(release_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_sent_at
  ON notification_logs(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_notification_logs_status
  ON notification_logs(status);
CREATE INDEX IF NOT EXISTS idx_notification_logs_type_status
  ON notification_logs(notification_type, status);

-- ========================================
-- カレンダーイベントテーブル
-- ========================================
CREATE TABLE IF NOT EXISTS calendar_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  release_id INTEGER NOT NULL,
  google_event_id TEXT UNIQUE NOT NULL,
  calendar_id TEXT NOT NULL DEFAULT 'primary',
  event_title TEXT NOT NULL,
  event_description TEXT,
  start_datetime DATETIME NOT NULL,
  end_datetime DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  synced_at DATETIME,

  FOREIGN KEY (release_id) REFERENCES releases(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_calendar_events_release_id
  ON calendar_events(release_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_google_id
  ON calendar_events(google_event_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_start
  ON calendar_events(start_datetime DESC);
CREATE INDEX IF NOT EXISTS idx_calendar_events_synced
  ON calendar_events(synced_at);

-- 更新日時トリガー
CREATE TRIGGER IF NOT EXISTS calendar_events_update_timestamp
AFTER UPDATE ON calendar_events
FOR EACH ROW
BEGIN
  UPDATE calendar_events SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ========================================
-- マイグレーション記録
-- ========================================
INSERT INTO schema_migrations(version, description, script_name)
VALUES(2, 'Add notification_logs and calendar_events tables', '002_add_notification_logs.sql');

COMMIT;
