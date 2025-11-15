-- カレンダーイベントテーブル追加マイグレーション
-- 作成日: 2025-11-15

CREATE TABLE IF NOT EXISTS calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    release_id INTEGER,
    event_title TEXT NOT NULL,
    event_date DATE NOT NULL,
    description TEXT,
    location TEXT,
    calendar_id TEXT,
    event_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_id) REFERENCES works(id),
    FOREIGN KEY (release_id) REFERENCES releases(id)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_calendar_events_date ON calendar_events(event_date);
CREATE INDEX IF NOT EXISTS idx_calendar_events_work_id ON calendar_events(work_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_created_at ON calendar_events(created_at DESC);

-- エラーログテーブル追加
CREATE TABLE IF NOT EXISTS error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT CHECK(category IN ('notification', 'calendar', 'collection', 'system')),
    message TEXT NOT NULL,
    stack_trace TEXT,
    severity TEXT CHECK(severity IN ('low', 'medium', 'high', 'critical')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- エラーログインデックス
CREATE INDEX IF NOT EXISTS idx_error_logs_category ON error_logs(category);
CREATE INDEX IF NOT EXISTS idx_error_logs_created_at ON error_logs(created_at DESC);
