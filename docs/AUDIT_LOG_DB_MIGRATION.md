# 監査ログDB永続化マイグレーションガイド

**作成日**: 2025-12-07
**ステータス**: 実装完了
**担当**: Database Designer Agent

## 概要

監査ログシステムをメモリベースからSQLite永続化に移行します。

## アーキテクチャ

### 移行前
```
AuditLogger (modules/audit_log.py)
  └─> メモリ内リスト (_logs)
       └─> 再起動時にデータ消失
```

### 移行後
```
AuditLoggerDB (modules/audit_log_db.py)
  └─> SQLite (db.sqlite3)
       └─> audit_logs テーブル
            ├─> インデックス最適化
            ├─> 統計ビュー
            └─> 自動保持ポリシー (90日)
```

## データベーススキーマ

### テーブル定義

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,          -- イベント種別
    user_id TEXT,                      -- ユーザーID
    username TEXT,                     -- ユーザー名
    ip_address TEXT,                   -- IPアドレス
    user_agent TEXT,                   -- User-Agent
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    details TEXT,                      -- JSON詳細
    success INTEGER DEFAULT 1,         -- 成功フラグ
    session_id TEXT,                   -- セッションID
    endpoint TEXT,                     -- APIエンドポイント
    method TEXT,                       -- HTTPメソッド
    status_code INTEGER,               -- ステータスコード
    response_time_ms INTEGER,          -- レスポンス時間
    error_message TEXT,                -- エラーメッセージ
    resource_type TEXT,                -- リソース種別
    resource_id TEXT,                  -- リソースID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### インデックス戦略

```sql
-- 時系列検索用
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);

-- イベントタイプ検索用
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);

-- ユーザー検索用
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id)
    WHERE user_id IS NOT NULL;

-- 失敗ログ検索用（複合インデックス）
CREATE INDEX idx_audit_logs_user_failure
    ON audit_logs(user_id, success, timestamp DESC)
    WHERE success = 0;

-- セキュリティ監視用
CREATE INDEX idx_audit_logs_ip_address ON audit_logs(ip_address)
    WHERE ip_address IS NOT NULL;
```

### 統計ビュー

#### v_audit_summary - イベント別統計
```sql
CREATE VIEW v_audit_summary AS
SELECT
    event_type,
    COUNT(*) as total_count,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failure_count,
    AVG(response_time_ms) as avg_response_time
FROM audit_logs
GROUP BY event_type;
```

#### v_user_activity - ユーザー別統計
```sql
CREATE VIEW v_user_activity AS
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
```

#### v_security_alerts - セキュリティアラート
```sql
CREATE VIEW v_security_alerts AS
SELECT
    ip_address,
    event_type,
    COUNT(*) as failure_count,
    MAX(timestamp) as last_attempt
FROM audit_logs
WHERE success = 0 AND ip_address IS NOT NULL
GROUP BY ip_address, event_type
HAVING COUNT(*) >= 5;
```

## マイグレーション手順

### 1. マイグレーション実行

```bash
# 基本実行
python scripts/migrate_audit_logs.py

# 検証付き実行
python scripts/migrate_audit_logs.py --verify

# メモリログ移行 + 検証
python scripts/migrate_audit_logs.py --migrate-memory --verify
```

### 2. 環境変数設定

```bash
# .env ファイルに追加
USE_DB_AUDIT_LOG=true
```

### 3. 既存コードの更新

```python
# Before (メモリ版)
from modules.audit_log import audit_logger

# After (DB版 - 自動切り替え)
from modules.audit_log_db import audit_logger
```

## API仕様

### ログ記録

```python
from modules.audit_log_db import AuditLoggerDB

logger = AuditLoggerDB()

# 基本的な記録
logger.log_event(
    event_type="login_success",
    user_id="user123",
    username="testuser",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0...",
    success=True
)

# 詳細情報付き
logger.log_event(
    event_type="api_request",
    user_id="user123",
    endpoint="/api/v1/data",
    method="POST",
    status_code=200,
    response_time_ms=45,
    details={"action": "create", "resource": "article"}
)
```

### ログ取得

```python
# 最新100件取得
logs = logger.get_logs(limit=100)

# フィルタリング
logs = logger.get_logs(
    event_type="login_failure",
    user_id="user123",
    success=False,
    limit=50
)

# 日付範囲指定
from datetime import datetime, timedelta

start_date = datetime.now() - timedelta(days=7)
logs = logger.get_logs(
    start_date=start_date,
    end_date=datetime.now()
)
```

### 統計情報取得

```python
# 全体統計
stats = logger.get_statistics()
print(f"総ログ数: {stats['total_logs']}")
print(f"成功率: {stats['success_rate']}%")

# ユーザーアクティビティ
activity = logger.get_user_activity(user_id="user123", days=30)
print(f"30日間のアクション: {activity['total_actions']}")

# セキュリティアラート
alerts = logger.get_security_alerts(threshold=5, hours=24)
for alert in alerts:
    print(f"警告: IP {alert['ip_address']} が {alert['failure_count']} 回失敗")
```

## パフォーマンス最適化

### インデックス活用

```sql
-- 時系列検索（インデックス使用）
SELECT * FROM audit_logs
WHERE timestamp > datetime('now', '-7 days')
ORDER BY timestamp DESC;

-- イベント別集計（インデックス使用）
SELECT event_type, COUNT(*)
FROM audit_logs
GROUP BY event_type;

-- ユーザー失敗ログ（複合インデックス使用）
SELECT * FROM audit_logs
WHERE user_id = 'user123'
  AND success = 0
ORDER BY timestamp DESC;
```

### クエリプラン確認

```sql
EXPLAIN QUERY PLAN
SELECT * FROM audit_logs
WHERE event_type = 'login_failure'
  AND timestamp > datetime('now', '-1 day');
```

## データ保持ポリシー

### 自動削除トリガー

90日以上経過したログを自動削除（重要ログは除外）:

```sql
CREATE TRIGGER trg_audit_log_retention
AFTER INSERT ON audit_logs
BEGIN
    DELETE FROM audit_logs
    WHERE timestamp < datetime('now', '-90 days')
    AND success = 1
    AND event_type NOT IN ('security_violation', 'admin_action');
END;
```

### 手動クリーンアップ

```python
# 180日より古いログを削除
logger.cleanup_old_logs(days=180, keep_critical=True)
```

## 運用ガイドライン

### 日次メンテナンス

```bash
# VACUUM実行（月1回推奨）
sqlite3 db.sqlite3 "VACUUM;"

# 統計情報更新
sqlite3 db.sqlite3 "ANALYZE;"
```

### バックアップ

```bash
# SQLiteバックアップ
cp db.sqlite3 backup/db_$(date +%Y%m%d).sqlite3

# エクスポート（CSV）
sqlite3 -header -csv db.sqlite3 "SELECT * FROM audit_logs" > audit_logs_export.csv
```

### モニタリング

```python
# 定期統計レポート
def daily_audit_report():
    logger = AuditLoggerDB()

    stats = logger.get_statistics()
    alerts = logger.get_security_alerts(threshold=5, hours=24)

    print(f"総ログ数: {stats['total_logs']}")
    print(f"過去24時間の失敗: {stats['recent_failures_24h']}")
    print(f"セキュリティアラート: {len(alerts)} 件")

    return stats
```

## トラブルシューティング

### 問題: マイグレーション失敗

```bash
# テーブル確認
sqlite3 db.sqlite3 "SELECT name FROM sqlite_master WHERE type='table';"

# 手動テーブル作成
sqlite3 db.sqlite3 < migrations/006_audit_logs_complete.sql
```

### 問題: パフォーマンス低下

```sql
-- インデックス再構築
REINDEX audit_logs;

-- 統計情報更新
ANALYZE;

-- VACUUMでDBファイル最適化
VACUUM;
```

### 問題: ディスク容量不足

```python
# 古いログ削除
logger.cleanup_old_logs(days=30, keep_critical=True)
```

## ベストプラクティス

### 1. イベントタイプの標準化

```python
# 推奨イベントタイプ
EVENT_TYPES = {
    "login_success", "login_failure", "logout",
    "create", "update", "delete",
    "api_request", "api_error",
    "security_violation", "admin_action"
}
```

### 2. 詳細情報のJSON化

```python
# 構造化された詳細情報
logger.log_event(
    event_type="data_change",
    details={
        "action": "update",
        "resource_type": "article",
        "resource_id": 123,
        "changes": {
            "title": {"old": "旧タイトル", "new": "新タイトル"}
        }
    }
)
```

### 3. セキュリティ監視

```python
# 定期アラートチェック
def check_security_alerts():
    alerts = logger.get_security_alerts(threshold=5, hours=1)

    if alerts:
        for alert in alerts:
            send_alert_notification(
                f"IP {alert['ip_address']} から異常なアクセス"
            )
```

## ファイル一覧

- `/migrations/006_audit_logs_complete.sql` - マイグレーションSQL
- `/modules/audit_log_db.py` - DB版ロガー実装
- `/scripts/migrate_audit_logs.py` - マイグレーションスクリプト
- `/docs/AUDIT_LOG_DB_MIGRATION.md` - このドキュメント

## 参考リンク

- [SQLite公式ドキュメント](https://www.sqlite.org/docs.html)
- [SQLiteパフォーマンスチューニング](https://www.sqlite.org/optoverview.html)
- [監査ログベストプラクティス](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
