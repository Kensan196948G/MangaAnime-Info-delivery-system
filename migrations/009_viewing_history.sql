-- 視聴履歴テーブル
-- 作成日: 2025-12-07
-- 目的: 視聴済みエピソード・既読巻の記録、進捗管理

CREATE TABLE IF NOT EXISTS viewing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    work_id INTEGER NOT NULL,
    episode_number TEXT,     -- "1", "2", "SP1" 等
    volume_number TEXT,      -- "1", "2" 等
    watched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),  -- 5段階評価
    notes TEXT,              -- 感想メモ
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
    UNIQUE(user_id, work_id, episode_number, volume_number)
);

CREATE INDEX IF NOT EXISTS idx_viewing_history_user_id ON viewing_history(user_id);
CREATE INDEX IF NOT EXISTS idx_viewing_history_work_id ON viewing_history(work_id);
CREATE INDEX IF NOT EXISTS idx_viewing_history_watched_at ON viewing_history(watched_at DESC);

-- 視聴進捗ビュー
CREATE VIEW IF NOT EXISTS viewing_progress AS
SELECT
    vh.user_id,
    vh.work_id,
    w.title,
    w.type as work_type,
    COUNT(DISTINCT vh.episode_number) as episodes_watched,
    COUNT(DISTINCT vh.volume_number) as volumes_read,
    MAX(vh.watched_at) as last_watched,
    AVG(vh.rating) as average_rating
FROM viewing_history vh
JOIN works w ON vh.work_id = w.id
GROUP BY vh.user_id, vh.work_id, w.title, w.type;

-- 最近見た作品ビュー
CREATE VIEW IF NOT EXISTS recently_watched AS
SELECT
    vh.*,
    w.title,
    w.type as work_type,
    w.title_en
FROM viewing_history vh
JOIN works w ON vh.work_id = w.id
ORDER BY vh.watched_at DESC
LIMIT 20;
