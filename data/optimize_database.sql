-- ==============================================================================
-- データベース最適化スクリプト - MangaAnime-Info-delivery-system
-- 作成日: 2025-09-07
-- 目的: パフォーマンス向上、データ整合性強化、クエリ最適化
-- ==============================================================================

-- バックアップテーブル作成（安全のため）
CREATE TABLE IF NOT EXISTS works_backup AS SELECT * FROM works;
CREATE TABLE IF NOT EXISTS releases_backup AS SELECT * FROM releases;

-- ==============================================================================
-- 1. 複合インデックスの追加（パフォーマンス最適化）
-- ==============================================================================

-- 最も頻繁なクエリパターンに対応：type + created_at での絞り込み
CREATE INDEX IF NOT EXISTS idx_works_type_created 
ON works(type, created_at DESC);

-- タイトル検索用（部分マッチクエリ対応）
CREATE INDEX IF NOT EXISTS idx_works_title_type 
ON works(title COLLATE NOCASE, type);

-- 英語・ひらがな・ネイティブタイトル検索用
CREATE INDEX IF NOT EXISTS idx_works_title_variants 
ON works(title_en COLLATE NOCASE, title_kana COLLATE NOCASE, title_native COLLATE NOCASE);

-- リリース情報の最重要複合インデックス（通知対象絞り込み）
CREATE INDEX IF NOT EXISTS idx_releases_notification_ready 
ON releases(notified, release_date, work_id) 
WHERE notified = 0 AND release_date >= date('now');

-- プラットフォーム別リリース検索用
CREATE INDEX IF NOT EXISTS idx_releases_platform_date 
ON releases(platform, release_date DESC, work_id);

-- 作品別リリース検索用（詳細表示）
CREATE INDEX IF NOT EXISTS idx_releases_work_details 
ON releases(work_id, release_type, release_date DESC);

-- 統計・集計用インデックス
CREATE INDEX IF NOT EXISTS idx_releases_stats 
ON releases(release_type, platform, release_date);

-- ==============================================================================
-- 2. データ整合性制約の強化
-- ==============================================================================

-- 新しいテーブルバージョンの作成（制約強化版）
CREATE TABLE IF NOT EXISTS works_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL CHECK(length(trim(title)) > 0),
    title_kana TEXT CHECK(title_kana IS NULL OR length(trim(title_kana)) > 0),
    title_en TEXT CHECK(title_en IS NULL OR length(trim(title_en)) > 0),
    title_native TEXT CHECK(title_native IS NULL OR length(trim(title_native)) > 0),
    type TEXT NOT NULL CHECK(type IN ('anime','manga')),
    official_url TEXT CHECK(official_url IS NULL OR (
        official_url LIKE 'http://%' OR 
        official_url LIKE 'https://%'
    )),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS releases_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    release_type TEXT NOT NULL CHECK(release_type IN ('episode','volume','season','chapter')),
    number TEXT CHECK(number IS NULL OR length(trim(number)) > 0),
    platform TEXT NOT NULL CHECK(length(trim(platform)) > 0),
    release_date DATE NOT NULL CHECK(release_date >= '2000-01-01'),
    source TEXT CHECK(source IS NULL OR length(trim(source)) > 0),
    source_url TEXT CHECK(source_url IS NULL OR (
        source_url LIKE 'http://%' OR 
        source_url LIKE 'https://%'
    )),
    notified INTEGER NOT NULL DEFAULT 0 CHECK(notified IN (0,1)),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_id) REFERENCES works_new (id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE(work_id, release_type, number, platform, release_date)
);

-- ==============================================================================
-- 3. トリガーによるデータ検証とメンテナンス
-- ==============================================================================

-- updated_at自動更新トリガー（works）
CREATE TRIGGER IF NOT EXISTS trigger_works_updated_at
AFTER UPDATE ON works_new
FOR EACH ROW
BEGIN
    UPDATE works_new SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- updated_at自動更新トリガー（releases）
CREATE TRIGGER IF NOT EXISTS trigger_releases_updated_at
AFTER UPDATE ON releases_new
FOR EACH ROW
BEGIN
    UPDATE releases_new SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- データ整合性チェックトリガー
CREATE TRIGGER IF NOT EXISTS trigger_release_validation
BEFORE INSERT ON releases_new
FOR EACH ROW
BEGIN
    -- 未来の日付制限（1年以内）
    SELECT CASE 
        WHEN NEW.release_date > date('now', '+1 year') THEN
            RAISE(ABORT, 'Release date cannot be more than 1 year in the future')
    END;
    
    -- episode/volumeの場合、numberが必要
    SELECT CASE 
        WHEN NEW.release_type IN ('episode', 'volume', 'chapter') AND 
             (NEW.number IS NULL OR trim(NEW.number) = '') THEN
            RAISE(ABORT, 'Number is required for episodes, volumes, and chapters')
    END;
END;

-- 重複通知防止トリガー
CREATE TRIGGER IF NOT EXISTS trigger_prevent_duplicate_notifications
BEFORE UPDATE OF notified ON releases_new
FOR EACH ROW
WHEN NEW.notified = 1 AND OLD.notified = 1
BEGIN
    SELECT RAISE(IGNORE); -- 既に通知済みの場合は更新を無視
END;

-- ==============================================================================
-- 4. パフォーマンス最適化用ビューの作成
-- ==============================================================================

-- 通知待ちリリース一覧ビュー
CREATE VIEW IF NOT EXISTS v_pending_notifications AS
SELECT 
    w.id as work_id,
    w.title,
    w.type as work_type,
    r.id as release_id,
    r.release_type,
    r.number,
    r.platform,
    r.release_date,
    r.source_url,
    CASE 
        WHEN r.release_date = date('now') THEN 'today'
        WHEN r.release_date = date('now', '+1 day') THEN 'tomorrow'
        WHEN r.release_date BETWEEN date('now') AND date('now', '+7 days') THEN 'this_week'
        ELSE 'future'
    END as urgency_level
FROM works_new w
JOIN releases_new r ON w.id = r.work_id
WHERE r.notified = 0 
    AND r.release_date >= date('now')
ORDER BY r.release_date, w.title;

-- プラットフォーム別統計ビュー
CREATE VIEW IF NOT EXISTS v_platform_stats AS
SELECT 
    r.platform,
    w.type as work_type,
    COUNT(*) as total_releases,
    COUNT(CASE WHEN r.notified = 0 THEN 1 END) as pending_notifications,
    MIN(r.release_date) as earliest_release,
    MAX(r.release_date) as latest_release
FROM works_new w
JOIN releases_new r ON w.id = r.work_id
GROUP BY r.platform, w.type;

-- ==============================================================================
-- 5. データマイグレーション（段階的移行）
-- ==============================================================================

-- データ移行は手動で実行する場合のSQL
-- INSERT INTO works_new (id, title, title_kana, title_en, title_native, type, official_url, created_at)
-- SELECT id, title, title_kana, title_en, title_native, type, official_url, created_at FROM works;

-- INSERT INTO releases_new (id, work_id, release_type, number, platform, release_date, source, source_url, notified, created_at)
-- SELECT id, work_id, release_type, number, platform, release_date, source, source_url, notified, created_at FROM releases;

-- ==============================================================================
-- 6. パフォーマンステスト用クエリ
-- ==============================================================================

-- 最適化後のパフォーマンステスト用クエリ（実行時間計測用）
-- SELECT '=== Performance Test Queries ===' as info;

-- 1. 今日リリース予定のアニメ一覧（最重要クエリ）
-- EXPLAIN QUERY PLAN 
-- SELECT w.title, r.platform, r.release_type, r.number 
-- FROM works_new w 
-- JOIN releases_new r ON w.id = r.work_id 
-- WHERE w.type = 'anime' 
--   AND r.notified = 0 
--   AND r.release_date = date('now')
-- ORDER BY r.platform, w.title;

-- 2. 特定プラットフォームの今週のリリース
-- EXPLAIN QUERY PLAN
-- SELECT w.title, r.release_date, r.release_type, r.number
-- FROM works_new w
-- JOIN releases_new r ON w.id = r.work_id
-- WHERE r.platform = 'Netflix'
--   AND r.release_date BETWEEN date('now') AND date('now', '+7 days')
-- ORDER BY r.release_date, w.title;

-- ==============================================================================
-- 7. メンテナンス用ストアドプロシージャ風SQL
-- ==============================================================================

-- 古いデータクリーンアップ（1年以上前の通知済みレコード）
-- DELETE FROM releases_new 
-- WHERE notified = 1 
--   AND created_at < date('now', '-1 year')
--   AND release_date < date('now', '-1 year');

-- データベース最適化実行
-- PRAGMA optimize;
-- VACUUM;
-- ANALYZE;

-- ==============================================================================
-- 8. 設定の最適化
-- ==============================================================================

-- SQLite設定の最適化
PRAGMA journal_mode = WAL;           -- Write-Ahead Loggingで並行性向上
PRAGMA synchronous = NORMAL;         -- パフォーマンスと安全性のバランス
PRAGMA cache_size = 10000;           -- キャッシュサイズ増加（約40MB）
PRAGMA temp_store = memory;          -- 一時的なデータをメモリに保存
PRAGMA mmap_size = 134217728;        -- メモリマップファイルサイズ（128MB）

-- ==============================================================================
-- 実行完了メッセージ
-- ==============================================================================
SELECT 'Database optimization script completed successfully!' as status,
       datetime('now') as timestamp;