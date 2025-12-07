-- Migration 006: Add Calendar Synchronization Support
-- Created: 2025-12-07
-- Purpose: Add calendar sync columns to releases table and create calendar_sync_log table

-- ========================================
-- Part 1: Alter releases table
-- ========================================

-- Add calendar sync columns to releases table
ALTER TABLE releases ADD COLUMN calendar_synced INTEGER DEFAULT 0;
ALTER TABLE releases ADD COLUMN calendar_event_id TEXT;
ALTER TABLE releases ADD COLUMN calendar_synced_at DATETIME;

-- Add unique constraint for calendar_event_id
CREATE UNIQUE INDEX idx_releases_calendar_event_id
  ON releases(calendar_event_id)
  WHERE calendar_event_id IS NOT NULL;

-- Add index for finding unsynced releases
CREATE INDEX idx_releases_calendar_unsynced
  ON releases(calendar_synced, release_date)
  WHERE calendar_synced = 0;

-- Add index for synced releases with timestamp
CREATE INDEX idx_releases_calendar_synced_at
  ON releases(calendar_synced_at DESC)
  WHERE calendar_synced = 1;

-- ========================================
-- Part 2: Create calendar_sync_log table
-- ========================================

-- Track all calendar sync operations for audit trail
CREATE TABLE IF NOT EXISTS calendar_sync_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  release_id INTEGER NOT NULL,
  work_id INTEGER NOT NULL,
  google_event_id TEXT,
  sync_status TEXT CHECK(sync_status IN ('pending', 'synced', 'failed', 'updated', 'deleted')),
  sync_type TEXT CHECK(sync_type IN ('create', 'update', 'delete')),
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 3,
  synced_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (release_id) REFERENCES releases(id) ON DELETE CASCADE,
  FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
  UNIQUE(release_id, sync_type)
);

-- ========================================
-- Part 3: Create indexes for calendar_sync_log
-- ========================================

CREATE INDEX idx_calendar_sync_log_status
  ON calendar_sync_log(sync_status, created_at DESC);

CREATE INDEX idx_calendar_sync_log_release_id
  ON calendar_sync_log(release_id);

CREATE INDEX idx_calendar_sync_log_work_id
  ON calendar_sync_log(work_id);

CREATE INDEX idx_calendar_sync_log_synced_at
  ON calendar_sync_log(synced_at DESC)
  WHERE synced_at IS NOT NULL;

CREATE INDEX idx_calendar_sync_log_pending
  ON calendar_sync_log(created_at)
  WHERE sync_status = 'pending';

-- ========================================
-- Part 4: Create calendar_metadata table
-- ========================================

-- Store metadata for calendar integration
CREATE TABLE IF NOT EXISTS calendar_metadata (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  release_id INTEGER UNIQUE NOT NULL,
  calendar_title TEXT,
  calendar_description TEXT,
  calendar_location TEXT,
  event_color TEXT,
  reminder_minutes_before INTEGER DEFAULT 1440,
  calendar_id TEXT DEFAULT 'primary',
  is_all_day INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (release_id) REFERENCES releases(id) ON DELETE CASCADE
);

CREATE INDEX idx_calendar_metadata_release_id
  ON calendar_metadata(release_id);

CREATE INDEX idx_calendar_metadata_calendar_id
  ON calendar_metadata(calendar_id);

-- ========================================
-- Part 5: Create view for sync status
-- ========================================

CREATE VIEW IF NOT EXISTS v_calendar_sync_status AS
SELECT
  r.id as release_id,
  w.id as work_id,
  w.title,
  r.number,
  r.platform,
  r.release_date,
  r.calendar_synced,
  r.calendar_event_id,
  r.calendar_synced_at,
  csl.sync_status,
  csl.error_message,
  csl.retry_count,
  CASE
    WHEN r.calendar_synced = 0 AND r.release_date > CURRENT_DATE THEN 'awaiting_sync'
    WHEN r.calendar_synced = 1 THEN 'synced'
    WHEN csl.sync_status = 'failed' THEN 'sync_failed'
    ELSE 'unknown'
  END as current_status
FROM releases r
LEFT JOIN works w ON r.work_id = w.id
LEFT JOIN calendar_sync_log csl ON r.id = csl.release_id AND csl.sync_type = 'create'
ORDER BY r.release_date ASC;

-- ========================================
-- Part 6: Create stored procedure equivalents (SQLite triggers)
-- ========================================

-- Trigger to update calendar_metadata timestamp
CREATE TRIGGER IF NOT EXISTS trg_calendar_metadata_update
AFTER UPDATE ON calendar_metadata
BEGIN
  UPDATE calendar_metadata SET updated_at = CURRENT_TIMESTAMP
  WHERE id = NEW.id;
END;

-- Trigger to update calendar_sync_log timestamp
CREATE TRIGGER IF NOT EXISTS trg_calendar_sync_log_update
AFTER UPDATE ON calendar_sync_log
BEGIN
  UPDATE calendar_sync_log SET updated_at = CURRENT_TIMESTAMP
  WHERE id = NEW.id;
END;

-- Trigger to automatically update releases.calendar_synced_at
CREATE TRIGGER IF NOT EXISTS trg_releases_calendar_synced_at
BEFORE UPDATE OF calendar_synced ON releases
WHEN NEW.calendar_synced = 1
BEGIN
  UPDATE releases SET calendar_synced_at = CURRENT_TIMESTAMP
  WHERE id = NEW.id;
END;

-- ========================================
-- Part 7: Data integrity check
-- ========================================

-- Verify no existing calendar_event_id duplicates
-- This will help identify any data issues before migration

-- Add comment/documentation
-- This migration supports:
-- 1. Tracking calendar sync status for each release
-- 2. Recording sync operations in audit log
-- 3. Storing calendar-specific metadata
-- 4. Providing views for monitoring sync status
-- 5. Enabling retry logic for failed syncs
