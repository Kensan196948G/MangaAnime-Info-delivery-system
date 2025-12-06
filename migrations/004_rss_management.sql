-- Migration 004: RSS管理テーブルとカレンダー同期機能の追加
-- 作成日: 2025-12-06
-- 説明: RSSソースの管理、カレンダー同期状態の追跡、エラーログの記録

-- ============================================================
-- RSS ソース管理テーブル
-- ============================================================

CREATE TABLE IF NOT EXISTS rss_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- ソース名（例: "BookWalker"）
    url TEXT NOT NULL,                      -- RSS Feed URL
    enabled INTEGER DEFAULT 1,              -- 有効/無効フラグ
    etag TEXT,                              -- HTTP ETag（キャッシュ用）
    last_modified TEXT,                     -- Last-Modified ヘッダー
    last_fetch DATETIME,                    -- 最終取得日時
    last_success DATETIME,                  -- 最終成功日時
    fetch_count INTEGER DEFAULT 0,          -- 取得回数
    error_count INTEGER DEFAULT 0,          -- エラー回数
    consecutive_errors INTEGER DEFAULT 0,   -- 連続エラー回数
    last_error TEXT,                        -- 最終エラーメッセージ
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_rss_enabled ON rss_sources(enabled);
CREATE INDEX IF NOT EXISTS idx_rss_last_fetch ON rss_sources(last_fetch);
CREATE INDEX IF NOT EXISTS idx_rss_error_count ON rss_sources(error_count);

-- ============================================================
-- releases テーブルの拡張
-- ============================================================

-- カレンダー同期フラグの追加
ALTER TABLE releases ADD COLUMN calendar_synced INTEGER DEFAULT 0;
ALTER TABLE releases ADD COLUMN calendar_event_id TEXT;
ALTER TABLE releases ADD COLUMN calendar_synced_at DATETIME;

-- 通知履歴フィールドの追加
ALTER TABLE releases ADD COLUMN email_sent INTEGER DEFAULT 0;
ALTER TABLE releases ADD COLUMN email_sent_at DATETIME;

-- インデックス
CREATE INDEX IF NOT EXISTS idx_releases_calendar_synced ON releases(calendar_synced);
CREATE INDEX IF NOT EXISTS idx_releases_notified ON releases(notified);
CREATE INDEX IF NOT EXISTS idx_releases_email_sent ON releases(email_sent);
CREATE INDEX IF NOT EXISTS idx_releases_release_date ON releases(release_date);

-- ============================================================
-- API 呼び出しログテーブル
-- ============================================================

CREATE TABLE IF NOT EXISTS api_call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_name TEXT NOT NULL,                 -- API名（anilist, syoboi, gmail, calendar等）
    endpoint TEXT,                          -- エンドポイント
    method TEXT DEFAULT 'GET',              -- HTTPメソッド
    status_code INTEGER,                    -- HTTPステータスコード
    success INTEGER DEFAULT 1,              -- 成功/失敗フラグ
    response_time REAL,                     -- レスポンス時間（秒）
    error_message TEXT,                     -- エラーメッセージ
    request_data TEXT,                      -- リクエストデータ（JSON）
    response_data TEXT,                     -- レスポンスデータ（JSON、省略可）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_api_logs_api_name ON api_call_logs(api_name);
CREATE INDEX IF NOT EXISTS idx_api_logs_created_at ON api_call_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_api_logs_success ON api_call_logs(success);

-- ============================================================
-- システムメトリクステーブル
-- ============================================================

CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,              -- メトリクス名
    metric_value REAL NOT NULL,             -- メトリクス値
    metric_type TEXT DEFAULT 'gauge',       -- メトリクスタイプ（gauge, counter, histogram）
    tags TEXT,                              -- タグ（JSON形式）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_metrics_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_created_at ON system_metrics(created_at);

-- ============================================================
-- カレンダーイベントテーブル
-- ============================================================

CREATE TABLE IF NOT EXISTS calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    release_id INTEGER NOT NULL,            -- releases.id への外部キー
    event_id TEXT NOT NULL UNIQUE,          -- Google Calendar Event ID
    title TEXT NOT NULL,                    -- イベントタイトル
    event_date DATE NOT NULL,               -- イベント日付
    category TEXT,                          -- カテゴリ（anime, manga, movie等）
    color_id TEXT,                          -- カレンダーの色ID
    synced INTEGER DEFAULT 1,               -- 同期状態
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (release_id) REFERENCES releases(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_calendar_events_release_id ON calendar_events(release_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_event_date ON calendar_events(event_date);
CREATE INDEX IF NOT EXISTS idx_calendar_events_synced ON calendar_events(synced);

-- ============================================================
-- 通知履歴テーブル
-- ============================================================

CREATE TABLE IF NOT EXISTS notification_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_type TEXT NOT NULL,        -- email, calendar, slack, discord等
    recipient TEXT,                         -- 送信先
    subject TEXT,                           -- 件名
    content TEXT,                           -- 本文/内容
    status TEXT DEFAULT 'pending',          -- pending, sent, failed
    error_message TEXT,                     -- エラーメッセージ
    sent_at DATETIME,                       -- 送信日時
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_notification_type ON notification_history(notification_type);
CREATE INDEX IF NOT EXISTS idx_notification_status ON notification_history(status);
CREATE INDEX IF NOT EXISTS idx_notification_sent_at ON notification_history(sent_at);

-- ============================================================
-- スケジュール実行履歴テーブル
-- ============================================================

CREATE TABLE IF NOT EXISTS schedule_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,                -- タスク名
    status TEXT DEFAULT 'running',          -- running, completed, failed
    start_time DATETIME NOT NULL,           -- 開始時刻
    end_time DATETIME,                      -- 終了時刻
    duration REAL,                          -- 実行時間（秒）
    items_processed INTEGER DEFAULT 0,      -- 処理件数
    items_failed INTEGER DEFAULT 0,         -- 失敗件数
    error_message TEXT,                     -- エラーメッセージ
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_schedule_task_name ON schedule_history(task_name);
CREATE INDEX IF NOT EXISTS idx_schedule_status ON schedule_history(status);
CREATE INDEX IF NOT EXISTS idx_schedule_start_time ON schedule_history(start_time);

-- ============================================================
-- 初期データの投入
-- ============================================================

-- デフォルトRSSソースの登録
INSERT OR IGNORE INTO rss_sources (name, url, enabled) VALUES
    ('BookWalker', 'https://bookwalker.jp/rss/', 1),
    ('MagaPoke', 'https://pocket.shonenmagazine.com/rss', 1),
    ('Rakuten Kobo', 'https://books.rakuten.co.jp/rss/new-comics/', 1);

-- ============================================================
-- ビューの作成（レポート用）
-- ============================================================

-- API呼び出しサマリービュー
CREATE VIEW IF NOT EXISTS api_call_summary AS
SELECT
    api_name,
    COUNT(*) as total_calls,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_calls,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_calls,
    ROUND(AVG(response_time), 3) as avg_response_time,
    ROUND(MAX(response_time), 3) as max_response_time,
    MAX(created_at) as last_call
FROM api_call_logs
GROUP BY api_name;

-- 今日のリリーススケジュール
CREATE VIEW IF NOT EXISTS todays_releases AS
SELECT
    w.title,
    w.type,
    r.release_type,
    r.number,
    r.platform,
    r.release_date,
    r.notified,
    r.calendar_synced
FROM releases r
JOIN works w ON r.work_id = w.id
WHERE r.release_date = DATE('now', 'localtime')
ORDER BY r.release_date, w.title;

-- 未同期のカレンダーイベント
CREATE VIEW IF NOT EXISTS unsynced_calendar_events AS
SELECT
    w.title,
    r.release_date,
    r.platform,
    r.release_type,
    r.number
FROM releases r
JOIN works w ON r.work_id = w.id
WHERE r.calendar_synced = 0
AND r.release_date >= DATE('now', 'localtime')
ORDER BY r.release_date;

-- ============================================================
-- トリガーの作成
-- ============================================================

-- rss_sources の updated_at 自動更新
CREATE TRIGGER IF NOT EXISTS update_rss_sources_timestamp
AFTER UPDATE ON rss_sources
BEGIN
    UPDATE rss_sources SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- calendar_events の updated_at 自動更新
CREATE TRIGGER IF NOT EXISTS update_calendar_events_timestamp
AFTER UPDATE ON calendar_events
BEGIN
    UPDATE calendar_events SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- 連続エラー回数のリセット（成功時）
CREATE TRIGGER IF NOT EXISTS reset_consecutive_errors
AFTER UPDATE OF last_success ON rss_sources
WHEN NEW.last_success > OLD.last_success
BEGIN
    UPDATE rss_sources SET consecutive_errors = 0
    WHERE id = NEW.id;
END;

-- ============================================================
-- マイグレーション完了
-- ============================================================

-- マイグレーション履歴テーブル（存在しない場合のみ作成）
CREATE TABLE IF NOT EXISTS migration_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL UNIQUE,
    description TEXT,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- このマイグレーションの記録
INSERT OR IGNORE INTO migration_history (version, description)
VALUES ('004', 'RSS管理とカレンダー同期機能の追加');
