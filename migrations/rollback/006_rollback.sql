-- Rollback Migration 006: Remove Calendar Synchronization Support
-- Created: 2025-12-07
-- Purpose: Safely remove all calendar sync related tables, columns, and indexes

-- ========================================
-- Part 1: Drop views
-- ========================================

DROP VIEW IF EXISTS v_calendar_sync_status;

-- ========================================
-- Part 2: Drop triggers
-- ========================================

DROP TRIGGER IF EXISTS trg_calendar_metadata_update;
DROP TRIGGER IF EXISTS trg_calendar_sync_log_update;
DROP TRIGGER IF EXISTS trg_releases_calendar_synced_at;

-- ========================================
-- Part 3: Drop tables
-- ========================================

DROP TABLE IF EXISTS calendar_metadata;
DROP TABLE IF EXISTS calendar_sync_log;

-- ========================================
-- Part 4: Remove columns from releases table
-- ========================================

-- SQLite doesn't support ALTER TABLE DROP COLUMN in older versions
-- So we need to use the column-removal workaround with a temporary table

-- Create temporary table with original columns (excluding calendar sync columns)
CREATE TABLE releases_temp AS
SELECT
  id,
  work_id,
  release_type,
  number,
  platform,
  release_date,
  source,
  source_url,
  notified,
  created_at
FROM releases;

-- Drop original table
DROP TABLE releases;

-- Rename temporary table back to original name
ALTER TABLE releases_temp RENAME TO releases;

-- ========================================
-- Part 5: Recreate indexes that were removed
-- ========================================

-- Recreate the original indexes from migration 005 (if they exist)
CREATE INDEX IF NOT EXISTS idx_releases_work_id
  ON releases(work_id);

CREATE INDEX IF NOT EXISTS idx_releases_release_date
  ON releases(release_date);

CREATE INDEX IF NOT EXISTS idx_releases_notified
  ON releases(notified);

CREATE INDEX IF NOT EXISTS idx_releases_work_release_type
  ON releases(work_id, release_type);

CREATE UNIQUE INDEX IF NOT EXISTS idx_releases_unique
  ON releases(work_id, release_type, number, platform, release_date);

-- ========================================
-- Part 6: Verify rollback
-- ========================================

-- The following queries should work after rollback:
-- SELECT * FROM releases;
-- SELECT * FROM works;
-- The following should NOT work after rollback:
-- SELECT * FROM calendar_sync_log;
-- SELECT * FROM calendar_metadata;
-- SELECT calendar_synced FROM releases;

-- ========================================
-- Notes
-- ========================================

-- After running this rollback:
-- 1. All calendar sync columns are removed from releases
-- 2. All calendar sync tables are deleted
-- 3. All calendar sync indexes are removed
-- 4. The releases table will revert to its pre-migration state
-- 5. No data loss occurs to the core releases and works tables
-- 6. To restore: Re-run migration 006
