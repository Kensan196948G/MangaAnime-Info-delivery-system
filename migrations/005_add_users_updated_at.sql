-- Migration: Add updated_at column to users table for password reset tracking
-- Version: 005
-- Date: 2025-12-07
-- Description: Adds updated_at timestamp to track password changes

-- Add updated_at column if it doesn't exist
ALTER TABLE users ADD COLUMN updated_at DATETIME DEFAULT NULL;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_updated_at ON users(updated_at);

-- Update existing rows to have current timestamp
UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;
