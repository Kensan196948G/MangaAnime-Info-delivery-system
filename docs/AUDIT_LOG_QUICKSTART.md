# 監査ログシステム クイックスタート

5分で始める監査ログシステム

## ステップ1: マイグレーション実行（1分）

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 scripts/run_audit_migration.py
```

**期待される出力:**
```
============================================================
監査ログマイグレーション実行
============================================================
データベース: /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/db.sqlite3
マイグレーション: /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/migrations/006_audit_logs.sql

📊 マイグレーション実行中...
✅ audit_logs テーブルが作成されました
   サンプルデータ: 3 件
   インデックス: 11 個
   ビュー: 4 個

============================================================
✅ マイグレーション完了
============================================================
```

## ステップ2: 基本的な使い方（2分）

### 2.1 Pythonスクリプトで使用

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
    success=True
)

# ログ取得
logs = audit_logger.get_logs(limit=10)
for log in logs:
    print(f"{log.timestamp} - {log.event_type.value} - {log.username}")

# 統計情報
stats = audit_logger.get_statistics()
print(f"Total: {stats['total_events']}, Success Rate: {stats['success_rate']:.1f}%")
```

### 2.2 Flaskアプリケーションで使用

```python
from flask import Flask, request
from modules.audit_log import log_auth_event, AuditEventType

app = Flask(__name__)

@app.route('/api/auth/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    if authenticate(username, password):
        # ログイン成功を記録
        log_auth_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            user_id=username,
            username=username,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            success=True
        )
        return {'message': 'Login successful'}, 200
    else:
        # ログイン失敗を記録
        log_auth_event(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            username=username,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            success=False,
            details={'reason': 'invalid_credentials'}
        )
        return {'error': 'Invalid credentials'}, 401
```

## ステップ3: REST API テスト（2分）

### 3.1 Webアプリケーション起動

```bash
python3 app/web_app.py
```

### 3.2 APIリクエスト

#### ログイン
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

**レスポンス:**
```json
{
  "message": "Login successful",
  "user": {
    "id": "admin",
    "username": "admin"
  }
}
```

#### 監査ログ取得（管理者専用）
```bash
curl http://localhost:5000/api/auth/audit/logs?limit=5 \
  -H "Cookie: session=..."
```

**レスポンス:**
```json
{
  "logs": [
    {
      "id": 1,
      "event_type": "auth.login.success",
      "user_id": "admin",
      "username": "admin",
      "ip_address": "127.0.0.1",
      "timestamp": "2025-12-07T10:30:00Z",
      "success": true,
      "severity": "info"
    }
  ],
  "total": 10,
  "limit": 5,
  "offset": 0
}
```

#### 統計情報取得
```bash
curl http://localhost:5000/api/auth/audit/statistics \
  -H "Cookie: session=..."
```

**レスポンス:**
```json
{
  "total_events": 100,
  "failed_events": 5,
  "success_rate": 95.0,
  "event_types": {
    "auth.login.success": 40,
    "auth.logout": 35,
    "config.update": 20
  },
  "top_users": {
    "admin": 50,
    "user1": 30,
    "user2": 20
  }
}
```

## よく使うコマンド

### ログのフィルタリング
```python
# ログイン失敗のみ取得
failures = audit_logger.get_logs(
    event_type=AuditEventType.AUTH_LOGIN_FAILURE,
    success=False
)

# 特定ユーザーのアクティビティ
user_logs = audit_logger.get_logs(
    user_id="admin",
    limit=50
)

# 深刻度別
critical_logs = audit_logger.get_logs(
    severity="critical"
)
```

### 古いログの削除
```python
# 90日以上前のログを削除
deleted = audit_logger.cleanup_old_logs(days=90)
print(f"Deleted {deleted} old logs")
```

### ログのエクスポート
```python
# JSON形式
audit_logger.export_logs(
    output_path="audit_logs_2025.json",
    format="json"
)

# CSV形式
audit_logger.export_logs(
    output_path="audit_logs_2025.csv",
    format="csv"
)
```

## セキュリティアラート例

### ブルートフォース攻撃検出
```python
# 同一IPから5回以上の失敗を検出
recent_failures = audit_logger.get_logs(
    limit=10,
    event_type=AuditEventType.AUTH_LOGIN_FAILURE,
    ip_address="192.168.1.100"
)

if len(recent_failures) >= 5:
    print(f"⚠️  Brute force attack detected from {ip_address}")
    # アラート通知、IPブロック等の処理
```

### 不審なアクティビティ検出
```python
# Critical イベントを監視
critical_events = audit_logger.get_logs(
    severity="critical",
    limit=100
)

for event in critical_events:
    print(f"🚨 {event.event_type.value} from {event.ip_address}")
```

## トラブルシューティング

### エラー: テーブルが見つからない
```bash
# マイグレーションを再実行
python3 scripts/run_audit_migration.py
```

### エラー: パーミッション拒否
```bash
# データベースファイルの権限を確認
ls -l db.sqlite3
chmod 664 db.sqlite3
```

### エラー: モジュールが見つからない
```bash
# Pythonパスを確認
export PYTHONPATH=/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system:$PYTHONPATH
```

## 次のステップ

1. **詳細ドキュメント**: `docs/AUDIT_LOG_SYSTEM.md`
2. **実装レポート**: `docs/AUDIT_LOG_IMPLEMENTATION_REPORT.md`
3. **テスト実行**: `pytest tests/test_audit_log.py -v`

## サポート

問題が発生した場合:
1. ログファイルを確認: `logs/application.log`
2. テストを実行: `pytest tests/test_audit_log.py -v`
3. データベースを確認: `sqlite3 db.sqlite3 "SELECT * FROM audit_logs LIMIT 5;"`

---

**所要時間**: 5分
**難易度**: 初級
**最終更新**: 2025-12-07
