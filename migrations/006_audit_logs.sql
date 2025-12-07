-- 監査ログテーブル作成マイグレーション
-- 作成日: 2025-12-07
-- 目的: セキュリティ監査、コンプライアンス、トラブルシューティング用のログ記録

-- メインテーブル
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,           -- イベントタイプ (auth.login.success等)
    user_id TEXT,                        -- ユーザーID
    username TEXT,                       -- ユーザー名
    ip_address TEXT,                     -- クライアントIPアドレス
    user_agent TEXT,                     -- User-Agentヘッダ
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,  -- イベント発生時刻
    details TEXT,                        -- 詳細情報（JSON形式）
    success INTEGER DEFAULT 1,           -- 成功(1)/失敗(0)
    severity TEXT DEFAULT 'info'         -- 深刻度: info/warning/error/critical
);

-- パフォーマンス最適化インデックス
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp
    ON audit_logs(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id
    ON audit_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type
    ON audit_logs(event_type);

CREATE INDEX IF NOT EXISTS idx_audit_logs_severity
    ON audit_logs(severity);

CREATE INDEX IF NOT EXISTS idx_audit_logs_success
    ON audit_logs(success);

CREATE INDEX IF NOT EXISTS idx_audit_logs_ip_address
    ON audit_logs(ip_address);

-- 複合インデックス（よく使われるクエリパターン用）
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_timestamp
    ON audit_logs(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_event_timestamp
    ON audit_logs(event_type, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_severity_timestamp
    ON audit_logs(severity, timestamp DESC);

-- サンプルデータ（開発・テスト用）
INSERT INTO audit_logs (event_type, user_id, username, ip_address, user_agent, details, success, severity)
VALUES
    ('auth.login.success', 'admin', 'admin', '127.0.0.1', 'Mozilla/5.0', '{"method": "password", "session_id": "test123"}', 1, 'info'),
    ('config.update', 'admin', 'admin', '127.0.0.1', 'Mozilla/5.0', '{"key": "notification_enabled", "old_value": false, "new_value": true}', 1, 'info'),
    ('auth.login.failure', NULL, 'unknown', '192.168.1.100', 'curl/7.68.0', '{"reason": "invalid_password", "attempts": 3}', 0, 'warning');

-- 統計ビュー（パフォーマンス向上用）
CREATE VIEW IF NOT EXISTS audit_logs_stats AS
SELECT
    event_type,
    COUNT(*) as total_count,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failure_count,
    MAX(timestamp) as last_occurrence
FROM audit_logs
GROUP BY event_type;

-- ユーザーアクティビティビュー
CREATE VIEW IF NOT EXISTS user_activity_stats AS
SELECT
    user_id,
    username,
    COUNT(*) as total_actions,
    COUNT(DISTINCT event_type) as unique_events,
    MAX(timestamp) as last_activity,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_actions
FROM audit_logs
WHERE user_id IS NOT NULL
GROUP BY user_id, username;

-- セキュリティイベントビュー
CREATE VIEW IF NOT EXISTS security_events AS
SELECT *
FROM audit_logs
WHERE severity IN ('error', 'critical')
   OR success = 0
   OR event_type LIKE 'security.%'
ORDER BY timestamp DESC;

-- 最近のアクティビティビュー（直近24時間）
CREATE VIEW IF NOT EXISTS recent_activity AS
SELECT *
FROM audit_logs
WHERE timestamp >= datetime('now', '-1 day')
ORDER BY timestamp DESC;
