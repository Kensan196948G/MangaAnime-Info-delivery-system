-- Migration: 001_add_recommended_indexes.sql
-- 推奨インデックスの追加
-- 作成日: 2025-12-06
-- 説明: パフォーマンス最適化のための基本インデックスを追加

-- ========================================
-- worksテーブル用インデックス
-- ========================================

-- タイトル検索用（部分一致検索で頻繁に使用）
CREATE INDEX IF NOT EXISTS idx_works_title ON works(title);

-- タイプ別フィルタリング用（anime/manga絞り込み）
CREATE INDEX IF NOT EXISTS idx_works_type ON works(type);

-- 作成日時でのソート用（新着順表示）
CREATE INDEX IF NOT EXISTS idx_works_created_at ON works(created_at DESC);

-- 複合インデックス: タイプ × 作成日時（よく使われる組み合わせ）
CREATE INDEX IF NOT EXISTS idx_works_type_created ON works(type, created_at DESC);


-- ========================================
-- releasesテーブル用インデックス
-- ========================================

-- work_idでのJOIN最適化（最重要）
CREATE INDEX IF NOT EXISTS idx_releases_work_id ON releases(work_id);

-- 配信日検索用（日付範囲検索で頻繁に使用）
CREATE INDEX IF NOT EXISTS idx_releases_date ON releases(release_date);

-- 未通知レコード抽出用（毎日の通知処理で使用）
CREATE INDEX IF NOT EXISTS idx_releases_notified ON releases(notified);

-- プラットフォーム別検索用
CREATE INDEX IF NOT EXISTS idx_releases_platform ON releases(platform);

-- 複合インデックス: 未通知 × 配信日（通知処理の最適化）
CREATE INDEX IF NOT EXISTS idx_releases_notified_date ON releases(notified, release_date DESC);

-- 複合インデックス: work_id × release_date（作品別の最新リリース取得）
CREATE INDEX IF NOT EXISTS idx_releases_work_date ON releases(work_id, release_date DESC);

-- ソース別集計用
CREATE INDEX IF NOT EXISTS idx_releases_source ON releases(source);

-- リリースタイプ別フィルタリング
CREATE INDEX IF NOT EXISTS idx_releases_type ON releases(release_type);


-- ========================================
-- パーティャルインデックス（条件付きインデックス）
-- ========================================

-- 未通知レコードのみインデックス化（容量節約）
CREATE INDEX IF NOT EXISTS idx_releases_unnotified_only ON releases(release_date)
WHERE notified = 0;

-- かな読みが存在するレコードのみ
CREATE INDEX IF NOT EXISTS idx_works_kana_exists ON works(title_kana)
WHERE title_kana IS NOT NULL;


-- ========================================
-- インデックス作成完了
-- ========================================
-- 統計情報の更新
ANALYZE;
