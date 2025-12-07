-- Migration: 003_add_enhanced_tables.sql
-- 拡張テーブルの追加
-- 作成日: 2025-12-06
-- 説明: 通知ログ、ユーザー設定、プラットフォーム管理テーブルを追加

BEGIN TRANSACTION;

-- ========================================
-- notification_logsテーブル（通知履歴管理）
-- ========================================
CREATE TABLE IF NOT EXISTS notification_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  release_id INTEGER NOT NULL,
  notification_type TEXT CHECK(notification_type IN ('email','calendar')) NOT NULL,
  status TEXT CHECK(status IN ('success','failed','pending')) NOT NULL,
  error_message TEXT,
  sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (release_id) REFERENCES releases(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_notification_logs_release ON notification_logs(release_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_status ON notification_logs(status);
CREATE INDEX IF NOT EXISTS idx_notification_logs_sent_at ON notification_logs(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_notification_logs_type_status ON notification_logs(notification_type, status);


-- ========================================
-- user_settingsテーブル（ユーザー設定管理）
-- ========================================
CREATE TABLE IF NOT EXISTS user_settings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_email TEXT NOT NULL UNIQUE,
  notify_anime INTEGER DEFAULT 1 CHECK(notify_anime IN (0,1)),
  notify_manga INTEGER DEFAULT 1 CHECK(notify_manga IN (0,1)),
  preferred_platforms TEXT, -- JSON配列: ["dアニメストア", "Netflix"]
  ng_keywords TEXT, -- JSON配列: ["エロ", "R18"]
  notification_time TIME DEFAULT '08:00:00',
  timezone TEXT DEFAULT 'Asia/Tokyo',
  language TEXT DEFAULT 'ja',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_user_settings_email ON user_settings(user_email);


-- ========================================
-- platformsテーブル（配信プラットフォーム管理）
-- ========================================
CREATE TABLE IF NOT EXISTS platforms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  type TEXT CHECK(type IN ('anime','manga','both')) NOT NULL,
  official_url TEXT,
  icon_url TEXT,
  color_code TEXT, -- カレンダー表示用の色コード（例: "#FF5733"）
  active INTEGER DEFAULT 1 CHECK(active IN (0,1)),
  priority INTEGER DEFAULT 0, -- 表示優先度（数値が大きいほど優先）
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_platforms_name ON platforms(name);
CREATE INDEX IF NOT EXISTS idx_platforms_type ON platforms(type);
CREATE INDEX IF NOT EXISTS idx_platforms_active ON platforms(active);


-- ========================================
-- デフォルトプラットフォームデータの挿入
-- ========================================
INSERT INTO platforms (name, type, official_url, color_code, priority) VALUES
  ('dアニメストア', 'anime', 'https://anime.dmkt-sp.jp/', '#FF6B6B', 100),
  ('Netflix', 'both', 'https://www.netflix.com/', '#E50914', 90),
  ('Amazon Prime Video', 'both', 'https://www.amazon.co.jp/primevideo', '#00A8E1', 90),
  ('U-NEXT', 'both', 'https://video.unext.jp/', '#FF5A00', 80),
  ('Hulu', 'anime', 'https://www.hulu.jp/', '#3DBB3D', 70),
  ('ABEMA', 'anime', 'https://abema.tv/', '#00C4CC', 70),
  ('BookWalker', 'manga', 'https://bookwalker.jp/', '#FF9500', 80),
  ('マガポケ', 'manga', 'https://pocket.shonenmagazine.com/', '#E60012', 75),
  ('ジャンプ+', 'manga', 'https://shonenjumpplus.com/', '#009944', 75),
  ('楽天Kobo', 'manga', 'https://books.rakuten.co.jp/e-book/', '#BF0000', 70),
  ('Kindle', 'manga', 'https://www.amazon.co.jp/kindle', '#FF9900', 70)
ON CONFLICT(name) DO NOTHING;


-- ========================================
-- work_genresテーブル（作品ジャンル中間テーブル）
-- ========================================
CREATE TABLE IF NOT EXISTS genres (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  name_en TEXT,
  description TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS work_genres (
  work_id INTEGER NOT NULL,
  genre_id INTEGER NOT NULL,
  PRIMARY KEY (work_id, genre_id),
  FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
  FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_work_genres_work ON work_genres(work_id);
CREATE INDEX IF NOT EXISTS idx_work_genres_genre ON work_genres(genre_id);


-- ========================================
-- 既存テーブルへのカラム追加
-- SQLiteでは ALTER TABLE ADD COLUMN に非定数のDEFAULTは使用不可
-- ========================================

-- worksテーブルに追加カラム
ALTER TABLE works ADD COLUMN updated_at DATETIME DEFAULT NULL;
ALTER TABLE works ADD COLUMN deleted_at DATETIME DEFAULT NULL;
ALTER TABLE works ADD COLUMN description TEXT;
ALTER TABLE works ADD COLUMN image_url TEXT;
ALTER TABLE works ADD COLUMN status TEXT DEFAULT 'upcoming';

-- releasesテーブルに追加カラム
ALTER TABLE releases ADD COLUMN updated_at DATETIME DEFAULT NULL;
ALTER TABLE releases ADD COLUMN notified_at DATETIME DEFAULT NULL;
ALTER TABLE releases ADD COLUMN notification_retry_count INTEGER DEFAULT 0;
ALTER TABLE releases ADD COLUMN last_error TEXT DEFAULT NULL;

-- updated_at カラムを現在時刻で初期化
UPDATE works SET updated_at = DATETIME('now') WHERE updated_at IS NULL;
UPDATE releases SET updated_at = DATETIME('now') WHERE updated_at IS NULL;


-- ========================================
-- トリガー: updated_at自動更新
-- ========================================

-- worksテーブル用
CREATE TRIGGER IF NOT EXISTS update_works_timestamp
AFTER UPDATE ON works
FOR EACH ROW
BEGIN
  UPDATE works SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- releasesテーブル用
CREATE TRIGGER IF NOT EXISTS update_releases_timestamp
AFTER UPDATE ON releases
FOR EACH ROW
BEGIN
  UPDATE releases SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- user_settingsテーブル用
CREATE TRIGGER IF NOT EXISTS update_user_settings_timestamp
AFTER UPDATE ON user_settings
FOR EACH ROW
BEGIN
  UPDATE user_settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- platformsテーブル用
CREATE TRIGGER IF NOT EXISTS update_platforms_timestamp
AFTER UPDATE ON platforms
FOR EACH ROW
BEGIN
  UPDATE platforms SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;


-- ========================================
-- ビュー: よく使うクエリの最適化
-- ========================================

-- 未通知リリース一覧（通知処理用）
CREATE VIEW IF NOT EXISTS v_pending_notifications AS
SELECT
  r.id as release_id,
  r.release_type,
  r.number,
  r.platform,
  r.release_date,
  r.source,
  r.source_url,
  w.id as work_id,
  w.title as work_title,
  w.type as work_type,
  w.image_url as work_image_url
FROM releases r
INNER JOIN works w ON r.work_id = w.id
WHERE r.notified = 0
  AND r.release_date <= DATE('now')
  AND w.deleted_at IS NULL
ORDER BY r.release_date, w.title;


-- 作品別最新リリース
CREATE VIEW IF NOT EXISTS v_latest_releases AS
SELECT
  w.id as work_id,
  w.title,
  w.type,
  r.id as release_id,
  r.release_type,
  r.number,
  r.platform,
  r.release_date,
  r.notified
FROM works w
INNER JOIN (
  SELECT work_id, MAX(release_date) as max_date
  FROM releases
  GROUP BY work_id
) latest ON w.id = latest.work_id
INNER JOIN releases r ON r.work_id = latest.work_id AND r.release_date = latest.max_date
WHERE w.deleted_at IS NULL;


-- 通知統計（日別）
CREATE VIEW IF NOT EXISTS v_notification_stats_daily AS
SELECT
  DATE(sent_at) as date,
  notification_type,
  status,
  COUNT(*) as count
FROM notification_logs
GROUP BY DATE(sent_at), notification_type, status
ORDER BY date DESC;


COMMIT;

-- 統計情報の更新
ANALYZE;
