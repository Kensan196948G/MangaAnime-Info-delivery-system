# 監査ログシステム ドキュメント

## 概要

MangaAnime-Info-delivery-systemの監査ログシステムは、すべてのセキュリティイベント、ユーザーアクション、システム変更を記録・追跡する包括的な監査証跡システムです。

## 目的

- **セキュリティ監査**: 不正アクセスや不審なアクティビティの検出
- **コンプライアンス**: 監査要件への対応
- **トラブルシューティング**: 問題発生時の原因調査
- **ユーザーアクティビティ追跡**: システム利用状況の把握

## アーキテクチャ

### コンポーネント

```
modules/
└── audit_log.py          # 監査ログコアモジュール
    ├── AuditEventType    # イベントタイプ定義
    ├── AuditLog          # ログエントリデータクラス
    ├── AuditLogger       # ログ管理クラス
    └── ヘルパー関数       # log_auth_event, log_security_event等

app/routes/
└── auth_audit.py         # 認証ルート（監査ログ統合版）

migrations/
└── 006_audit_logs.sql    # データベーススキーマ

tests/
└── test_audit_log.py     # テストスイート
```

## イベントタイプ

### 認証イベント

| イベント | 説明 | 深刻度 |
|---------|------|--------|
| `AUTH_LOGIN_SUCCESS` | ログイン成功 | info |
| `AUTH_LOGIN_FAILURE` | ログイン失敗 | warning |
| `AUTH_LOGOUT` | ログアウト | info |
| `AUTH_SESSION_REFRESH` | セッション更新 | info |
| `AUTH_PASSWORD_RESET` | パスワードリセット | info |
| `AUTH_PASSWORD_CHANGE` | パスワード変更 | info |

### ユーザー管理イベント

| イベント | 説明 | 深刻度 |
|---------|------|--------|
| `USER_CREATE` | ユーザー作成 | info |
| `USER_DELETE` | ユーザー削除 | warning |
| `USER_UPDATE` | ユーザー情報更新 | info |
| `USER_ROLE_CHANGE` | ロール変更 | warning |

### 設定変更イベント

| イベント | 説明 | 深刻度 |
|---------|------|--------|
| `CONFIG_UPDATE` | 設定更新 | info |
| `CONFIG_RESET` | 設定リセット | warning |
| `CONFIG_EXPORT` | 設定エクスポート | info |
| `CONFIG_IMPORT` | 設定インポート | warning |

### データ操作イベント

| イベント | 説明 | 深刻度 |
|---------|------|--------|
| `DATA_CREATE` | データ作成 | info |
| `DATA_READ` | データ読取 | info |
| `DATA_UPDATE` | データ更新 | info |
| `DATA_DELETE` | データ削除 | warning |
| `DATA_EXPORT` | データエクスポート | warning |

### セキュリティイベント

| イベント | 説明 | 深刻度 |
|---------|------|--------|
| `SECURITY_BREACH_ATTEMPT` | 侵入試行検出 | critical |
| `SECURITY_PERMISSION_DENIED` | 権限拒否 | warning |
| `SECURITY_SUSPICIOUS_ACTIVITY` | 不審なアクティビティ | critical |

## データベーススキーマ

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    user_id TEXT,
    username TEXT,
    ip_address TEXT,
    user_agent TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    details TEXT,  -- JSON形式
    success INTEGER DEFAULT 1,
    severity TEXT DEFAULT 'info'
);
```

### インデックス

パフォーマンス最適化のため、以下のインデックスが作成されます：

- `idx_audit_logs_timestamp`: タイムスタンプ（降順）
- `idx_audit_logs_user_id`: ユーザーID
- `idx_audit_logs_event_type`: イベントタイプ
- `idx_audit_logs_severity`: 深刻度
- 複合インデックス: user_id+timestamp, event_type+timestamp等

## 使用方法

### 基本的な記録

```python
from modules.audit_log import audit_logger, AuditEventType

# イベント記録
audit_logger.log_event(
    event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
    user_id="user123",
    username="testuser",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0",
    details={"method": "password"},
    success=True,
    severity="info"
)
```

### ヘルパー関数の使用

```python
from modules.audit_log import log_auth_event, log_security_event

# 認証イベント
log_auth_event(
    event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
    user_id="user123",
    username="testuser",
    ip_address=request.remote_addr,
    user_agent=request.headers.get('User-Agent'),
    success=True
)

# セキュリティイベント（常にcritical）
log_security_event(
    event_type=AuditEventType.SECURITY_SUSPICIOUS_ACTIVITY,
    ip_address="192.168.1.100",
    details={"type": "brute_force", "attempts": 10}
)
```

### ログ取得

```python
# 最新50件取得
logs = audit_logger.get_logs(limit=50)

# フィルタ付き取得
logs = audit_logger.get_logs(
    event_type=AuditEventType.AUTH_LOGIN_FAILURE,
    user_id="admin",
    success=False,
    severity="warning",
    limit=100
)

# ページネーション
page1 = audit_logger.get_logs(limit=20, offset=0)
page2 = audit_logger.get_logs(limit=20, offset=20)
```

### 統計情報

```python
stats = audit_logger.get_statistics()

# 返される情報:
# {
#     'total_events': 1000,
#     'failed_events': 50,
#     'success_rate': 95.0,
#     'event_types': {...},
#     'severities': {...},
#     'top_users': {...}
# }
```

### ログのクリーンアップ

```python
# 90日以上古いログを削除
deleted_count = audit_logger.cleanup_old_logs(days=90)
```

### ログのエクスポート

```python
# JSON形式でエクスポート
audit_logger.export_logs(
    output_path="/path/to/export.json",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
    format="json"
)

# CSV形式でエクスポート
audit_logger.export_logs(
    output_path="/path/to/export.csv",
    format="csv"
)
```

## REST API エンドポイント

### ログイン

```http
POST /api/auth/login
Content-Type: application/json

{
    "username": "admin",
    "password": "password123"
}
```

**監査ログ記録内容:**
- イベント: `AUTH_LOGIN_SUCCESS` / `AUTH_LOGIN_FAILURE`
- IPアドレス、User-Agent
- ブルートフォース攻撃検出（5回以上の失敗）

### ログアウト

```http
POST /api/auth/logout
```

**監査ログ記録内容:**
- イベント: `AUTH_LOGOUT`
- ユーザーID、セッションID

### 監査ログ取得（管理者専用）

```http
GET /api/auth/audit/logs?limit=50&offset=0&event_type=auth.login.failure
Authorization: Bearer <token>
```

**レスポンス:**
```json
{
    "logs": [
        {
            "id": 123,
            "event_type": "auth.login.failure",
            "user_id": "user123",
            "username": "testuser",
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "timestamp": "2025-12-07T10:30:00Z",
            "details": {"reason": "invalid_password"},
            "success": false,
            "severity": "warning"
        }
    ],
    "total": 150,
    "limit": 50,
    "offset": 0
}
```

### 統計情報取得（管理者専用）

```http
GET /api/auth/audit/statistics
Authorization: Bearer <token>
```

**レスポンス:**
```json
{
    "total_events": 5000,
    "failed_events": 250,
    "success_rate": 95.0,
    "event_types": {
        "auth.login.success": 2000,
        "auth.logout": 1800,
        "config.update": 500
    },
    "severities": {
        "info": 4500,
        "warning": 400,
        "error": 80,
        "critical": 20
    },
    "top_users": {
        "admin": 1500,
        "user1": 800,
        "user2": 600
    }
}
```

## セキュリティ機能

### ブルートフォース攻撃検出

同一IPアドレスから5回以上のログイン失敗が発生した場合、自動的に検出され、`SECURITY_SUSPICIOUS_ACTIVITY`イベントが記録されます。

```python
# app/routes/auth_audit.py 内の実装
recent_failures = audit_logger.get_logs(
    limit=10,
    event_type=AuditEventType.AUTH_LOGIN_FAILURE,
    ip_address=client_ip
)

if len(recent_failures) >= 5:
    log_security_event(
        event_type=AuditEventType.SECURITY_SUSPICIOUS_ACTIVITY,
        ip_address=client_ip,
        details={"type": "brute_force", "attempts": len(recent_failures)}
    )
```

### 機密情報の保護

パスワードやトークンなどの機密情報は、監査ログに記録されません。

**記録される情報:**
- 認証方法（password, OAuth等）
- イベント結果（成功/失敗）
- IPアドレス、User-Agent

**記録されない情報:**
- パスワード平文
- トークン（アクセストークン、リフレッシュトークン）
- APIキー

## ベストプラクティス

### 1. 適切なイベントタイプの選択

```python
# 良い例
audit_logger.log_event(
    event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
    user_id=user_id,
    details={"method": "oauth"}
)

# 悪い例（汎用的すぎる）
audit_logger.log_event(
    event_type=AuditEventType.API_CALL,  # 具体性に欠ける
    details={"action": "login"}
)
```

### 2. 詳細情報の記録

```python
# 良い例
audit_logger.log_event(
    event_type=AuditEventType.CONFIG_UPDATE,
    user_id="admin",
    details={
        "key": "notification_enabled",
        "old_value": False,
        "new_value": True,
        "reason": "User request"
    }
)

# 悪い例（情報不足）
audit_logger.log_event(
    event_type=AuditEventType.CONFIG_UPDATE,
    user_id="admin"
)
```

### 3. 適切な深刻度の設定

```python
# セキュリティ関連は critical
log_security_event(
    event_type=AuditEventType.SECURITY_BREACH_ATTEMPT,
    severity="critical"
)

# 通常の失敗は warning
log_auth_event(
    event_type=AuditEventType.AUTH_LOGIN_FAILURE,
    success=False,
    severity="warning"
)

# 成功イベントは info
log_auth_event(
    event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
    success=True,
    severity="info"
)
```

### 4. 定期的なクリーンアップ

```python
# cronジョブやスケジューラで定期実行
# 毎月1日に90日以上前のログを削除
from modules.audit_log import audit_logger

deleted = audit_logger.cleanup_old_logs(days=90)
print(f"Cleaned up {deleted} old audit logs")
```

## パフォーマンス最適化

### インデックスの活用

頻繁に使用するクエリパターンに対してインデックスが最適化されています：

```sql
-- タイムスタンプ範囲検索
SELECT * FROM audit_logs
WHERE timestamp BETWEEN ? AND ?
ORDER BY timestamp DESC;
-- → idx_audit_logs_timestamp 使用

-- ユーザー別アクティビティ
SELECT * FROM audit_logs
WHERE user_id = ?
ORDER BY timestamp DESC;
-- → idx_audit_logs_user_timestamp 使用
```

### ページネーション

大量のログを扱う場合、必ずページネーションを使用：

```python
# 良い例
for offset in range(0, total_count, 100):
    logs = audit_logger.get_logs(limit=100, offset=offset)
    process_logs(logs)

# 悪い例
all_logs = audit_logger.get_logs(limit=1000000)  # メモリ枯渇の危険
```

## トラブルシューティング

### ログが記録されない

**原因1: データベース接続エラー**
```bash
# ログファイルを確認
tail -f logs/application.log | grep audit
```

**原因2: パーミッション問題**
```bash
# データベースファイルの権限を確認
ls -l db.sqlite3
chmod 664 db.sqlite3
```

### クエリが遅い

**解決策1: インデックスの確認**
```sql
-- インデックスが作成されているか確認
SELECT name FROM sqlite_master
WHERE type='index' AND tbl_name='audit_logs';
```

**解決策2: 古いログの削除**
```python
audit_logger.cleanup_old_logs(days=30)
```

### ディスク容量不足

**解決策: 定期的なクリーンアップを自動化**
```bash
# crontabに追加
0 2 1 * * python3 -c "from modules.audit_log import audit_logger; audit_logger.cleanup_old_logs(days=90)"
```

## コンプライアンス

### GDPR対応

ユーザーデータの削除要求に対応：

```python
def delete_user_audit_logs(user_id: str):
    """ユーザーの監査ログを削除（GDPR対応）"""
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM audit_logs WHERE user_id = ?",
        (user_id,)
    )

    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted_count
```

### 監査証跡の保持

法令により監査ログの保持期間が定められている場合：

```python
# 重要なイベントは長期保存
CRITICAL_EVENTS = [
    AuditEventType.USER_DELETE,
    AuditEventType.DATA_DELETE,
    AuditEventType.SECURITY_BREACH_ATTEMPT
]

# 一般ログは90日、重要ログは7年保持
audit_logger.cleanup_old_logs(
    days=90,
    exclude_event_types=CRITICAL_EVENTS
)
```

## テスト

```bash
# すべての監査ログテストを実行
pytest tests/test_audit_log.py -v

# カバレッジ付き実行
pytest tests/test_audit_log.py --cov=modules.audit_log --cov-report=html

# 特定のテストクラスのみ実行
pytest tests/test_audit_log.py::TestAuditLogger -v
```

## まとめ

監査ログシステムにより、以下が実現されます：

✅ **完全な監査証跡** - すべての重要なイベントが記録される
✅ **セキュリティ強化** - 不正アクセスや不審なアクティビティを検出
✅ **コンプライアンス対応** - 監査要件を満たす
✅ **トラブルシューティング** - 問題発生時の原因調査が容易
✅ **パフォーマンス最適化** - インデックスとページネーションによる高速化

## 関連ドキュメント

- [認証システム設計](./AUTHENTICATION_SYSTEM.md)
- [セキュリティガイドライン](./technical/security_guidelines.md)
- [API リファレンス](./guides/QUICK_API_REFERENCE.md)

---

**最終更新**: 2025-12-07
**バージョン**: 1.0.0
**担当エージェント**: Backend Developer Agent
