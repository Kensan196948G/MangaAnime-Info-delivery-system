-- 監査ログテーブル作成マイグレーション
-- 作成日: 2025-12-07
-- 目的: セキュリティイベントとユーザーアクションの永続化

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,              -- ログインログアウト, データ変更, エラー等
    user_id TEXT,                          -- ユーザーID (匿名可)
    username TEXT,                         -- ユーザー名
    ip_address TEXT,                       -- リクエスト元IP
    user_agent TEXT,                       -- ブラウザ/クライアント情報
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,  -- イベント発生時刻
    details TEXT,                          -- JSON形式の詳細情報
    success INTEGER DEFAULT 1,             -- 成功=1, 失敗=0
    session_id TEXT,                       -- セッションID
    endpoint TEXT,                         -- APIエンドポイント
    method TEXT,                           -- HTTPメソッド (GET, POST等)
    status_code INTEGER,                   -- HTTPステータスコード
    response_time_ms INTEGER,              -- レスポンス時間(ミリ秒)
    error_message TEXT,                    -- エラー時のメッセージ
    resource_type TEXT,                    -- 操作対象リソース種別
    resource_id TEXT,                      -- 操作対象リソースID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- パフォーマンス最適化インデックス
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp
    ON audit_logs(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id
    ON audit_logs(user_id)
    WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type
    ON audit_logs(event_type);

CREATE INDEX IF NOT EXISTS idx_audit_logs_success
    ON audit_logs(success);

CREATE INDEX IF NOT EXISTS idx_audit_logs_session_id
    ON audit_logs(session_id)
    WHERE session_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_audit_logs_ip_address
    ON audit_logs(ip_address)
    WHERE ip_address IS NOT NULL;

-- 複合インデックス: ユーザーの失敗ログ検索用
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_failure
    ON audit_logs(user_id, success, timestamp DESC)
    WHERE success = 0;

-- 複合インデックス: イベントタイプ別の時系列検索用
CREATE INDEX IF NOT EXISTS idx_audit_logs_type_time
    ON audit_logs(event_type, timestamp DESC);

-- セキュリティ統計用ビュー
CREATE VIEW IF NOT EXISTS v_audit_summary AS
SELECT
    event_type,
    COUNT(*) as total_count,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failure_count,
    MIN(timestamp) as first_occurrence,
    MAX(timestamp) as last_occurrence,
    AVG(response_time_ms) as avg_response_time
FROM audit_logs
GROUP BY event_type;

-- ユーザー別統計ビュー
CREATE VIEW IF NOT EXISTS v_user_activity AS
SELECT
    user_id,
    username,
    COUNT(*) as action_count,
    COUNT(DISTINCT DATE(timestamp)) as active_days,
    MAX(timestamp) as last_activity,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count
FROM audit_logs
WHERE user_id IS NOT NULL
GROUP BY user_id, username;

-- セキュリティアラート用ビュー (失敗が5回以上のIP)
CREATE VIEW IF NOT EXISTS v_security_alerts AS
SELECT
    ip_address,
    event_type,
    COUNT(*) as failure_count,
    MAX(timestamp) as last_attempt,
    GROUP_CONCAT(DISTINCT user_id) as attempted_users
FROM audit_logs
WHERE success = 0 AND ip_address IS NOT NULL
GROUP BY ip_address, event_type
HAVING COUNT(*) >= 5;

-- データ保持ポリシー: 古いログを削除するトリガー (オプション)
-- 本番環境では90日以上のログを外部アーカイブに移行することを推奨
CREATE TRIGGER IF NOT EXISTS trg_audit_log_retention
AFTER INSERT ON audit_logs
BEGIN
    DELETE FROM audit_logs
    WHERE timestamp < datetime('now', '-90 days')
    AND id NOT IN (
        SELECT id FROM audit_logs
        WHERE success = 0
        OR event_type IN ('security_violation', 'admin_action', 'data_breach')
        ORDER BY timestamp DESC
        LIMIT 50000
    );
END;

-- マイグレーション完了ログ
INSERT INTO audit_logs (event_type, details, user_id, username)
VALUES (
    'migration_executed',
    '{"migration": "006_audit_logs", "status": "completed", "version": "1.0"}',
    'system',
    'migration_script'
);
