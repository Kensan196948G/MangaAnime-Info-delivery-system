-- ウォッチリスト（お気に入り）テーブル
-- 作成日: 2025-12-07
-- 目的: ユーザーが気になる作品を登録し、新エピソード/巻の通知を制御

CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    work_id INTEGER NOT NULL,
    notify_new_episodes INTEGER DEFAULT 1,  -- エピソード通知ON/OFF
    notify_new_volumes INTEGER DEFAULT 1,   -- 巻通知ON/OFF
    priority INTEGER DEFAULT 0,              -- 優先度（0-5）
    notes TEXT,                              -- メモ
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
    UNIQUE(user_id, work_id)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_user_id ON watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_work_id ON watchlist(work_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_priority ON watchlist(priority DESC);

-- updated_at 自動更新トリガー
CREATE TRIGGER IF NOT EXISTS watchlist_updated_at_trigger
AFTER UPDATE ON watchlist
FOR EACH ROW
BEGIN
    UPDATE watchlist SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ウォッチリスト統計ビュー
CREATE VIEW IF NOT EXISTS watchlist_stats AS
SELECT
    w.user_id,
    COUNT(*) as total_watching,
    SUM(CASE WHEN wk.type = 'anime' THEN 1 ELSE 0 END) as anime_count,
    SUM(CASE WHEN wk.type = 'manga' THEN 1 ELSE 0 END) as manga_count,
    SUM(CASE WHEN w.notify_new_episodes = 1 THEN 1 ELSE 0 END) as notify_enabled_count
FROM watchlist w
JOIN works wk ON w.work_id = wk.id
GROUP BY w.user_id;
