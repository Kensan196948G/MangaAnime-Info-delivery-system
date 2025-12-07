# 監査ログDB版 クイックスタートガイド

5分で監査ログDB永続化を始めるための最速ガイド

## ステップ1: マイグレーション実行（30秒）

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python scripts/migrate_audit_logs.py --verify
```

**期待される出力:**
```
============================================================
🔄 監査ログマイグレーション開始
============================================================
📄 マイグレーションファイル: migrations/006_audit_logs_complete.sql
✅ マイグレーション完了

📊 テーブル構造確認:
  ✓ audit_logs テーブル: 存在
  ✓ カラム数: 17
  ✓ インデックス数: 8
  ✓ 現在のログ件数: 1

============================================================
✅ マイグレーション処理完了
============================================================
```

## ステップ2: 基本的な使い方（1分）

### ログ記録

```python
from modules.audit_log_db import AuditLoggerDB

logger = AuditLoggerDB()

# ログインイベント記録
logger.log_event(
    event_type="login_success",
    user_id="user123",
    username="山田太郎",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0..."
)
```

### ログ取得

```python
# 最新100件取得
logs = logger.get_logs(limit=100)

for log in logs:
    print(f"{log['timestamp']}: {log['event_type']} - {log['username']}")
```

### 統計情報

```python
stats = logger.get_statistics()
print(f"総ログ数: {stats['total_logs']}")
print(f"成功率: {stats.get('success_rate', 0):.1f}%")
```

## ステップ3: 統合（2分）

### 既存コードの更新

**Before:**
```python
from modules.audit_log import audit_logger
```

**After:**
```python
from modules.audit_log_db import audit_logger
```

### 環境変数設定（オプション）

```bash
# .envファイルに追加
echo "USE_DB_AUDIT_LOG=true" >> .env
```

## ステップ4: 検証（1分）

```bash
# テスト実行
python tests/test_audit_log_db.py
```

**期待される出力:**
```
============================================================
監査ログDB版 テストスイート
============================================================

[TEST] 基本的なログ記録...
  ✓ ログID: 1
  ✓ ログ取得成功: test_event

[TEST] フィルタリング...
  ✓ 成功ログ: 3 件
  ✓ 失敗ログ: 2 件

...

============================================================
✅ すべてのテストが成功しました！
============================================================
```

## よく使うコマンド

### 統計確認

```bash
python -c "
from modules.audit_log_db import AuditLoggerDB
logger = AuditLoggerDB()
stats = logger.get_statistics()
print('総ログ数:', stats['total_logs'])
print('過去24h失敗:', stats.get('recent_failures_24h', 0))
"
```

### セキュリティアラート確認

```bash
python -c "
from modules.audit_log_db import AuditLoggerDB
logger = AuditLoggerDB()
alerts = logger.get_security_alerts(threshold=5, hours=24)
print(f'アラート: {len(alerts)} 件')
for alert in alerts:
    print(f'  - IP {alert[\"ip_address\"]}: {alert[\"failure_count\"]}回失敗')
"
```

### ログのクリーンアップ

```bash
python -c "
from modules.audit_log_db import AuditLoggerDB
logger = AuditLoggerDB()
deleted = logger.cleanup_old_logs(days=90, keep_critical=True)
print(f'{deleted}件のログを削除しました')
"
```

## 実用例

### ログイン処理での使用

```python
from modules.audit_log_db import audit_logger

def login(username, password, request):
    try:
        user = authenticate(username, password)

        # 成功ログ
        audit_logger.log_event(
            event_type="login_success",
            user_id=user.id,
            username=username,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            success=True
        )

        return user

    except AuthenticationError as e:
        # 失敗ログ
        audit_logger.log_event(
            event_type="login_failure",
            username=username,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            error_message=str(e),
            success=False
        )

        raise
```

### API呼び出しの記録

```python
from modules.audit_log_db import audit_logger
import time

def api_endpoint(request):
    start_time = time.time()

    try:
        # 処理実行
        result = process_request(request)

        # 成功ログ
        audit_logger.log_event(
            event_type="api_request",
            user_id=request.user.id,
            endpoint=request.path,
            method=request.method,
            status_code=200,
            response_time_ms=int((time.time() - start_time) * 1000),
            details={"action": "success"}
        )

        return result

    except Exception as e:
        # エラーログ
        audit_logger.log_event(
            event_type="api_error",
            user_id=request.user.id,
            endpoint=request.path,
            method=request.method,
            status_code=500,
            response_time_ms=int((time.time() - start_time) * 1000),
            error_message=str(e),
            success=False
        )

        raise
```

### データ変更の監査

```python
from modules.audit_log_db import audit_logger

def update_article(article_id, changes, user):
    # 変更前のデータ取得
    old_data = get_article(article_id)

    # 更新処理
    article = perform_update(article_id, changes)

    # 監査ログ記録
    audit_logger.log_event(
        event_type="data_update",
        user_id=user.id,
        username=user.name,
        resource_type="article",
        resource_id=str(article_id),
        details={
            "changes": changes,
            "old_values": old_data,
            "new_values": article
        }
    )

    return article
```

## トラブルシューティング

### エラー: `table audit_logs already exists`

```bash
# テーブルを再作成
sqlite3 db.sqlite3 "DROP TABLE IF EXISTS audit_logs;"
python scripts/migrate_audit_logs.py
```

### エラー: `no such table: audit_logs`

```bash
# マイグレーション実行
python scripts/migrate_audit_logs.py
```

### パフォーマンスが遅い

```bash
# インデックス再構築
sqlite3 db.sqlite3 "REINDEX; ANALYZE;"
```

## 次に読むべきドキュメント

- 詳細ガイド: `/docs/AUDIT_LOG_DB_MIGRATION.md`
- 実装レポート: `/AUDIT_LOG_DB_IMPLEMENTATION.md`
- テストコード: `/tests/test_audit_log_db.py`

## サポート

問題が発生した場合:
1. `/docs/AUDIT_LOG_DB_MIGRATION.md` のトラブルシューティングを確認
2. テストを実行: `python tests/test_audit_log_db.py`
3. ログを確認: `tail -f logs/app.log`

---

**所要時間**: 5分
**難易度**: 初級
**前提知識**: Python基礎、SQLite基礎
