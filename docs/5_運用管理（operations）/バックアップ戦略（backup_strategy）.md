# データベースバックアップ戦略改善案

## 概要
MangaAnime-Info-delivery-systemのデータベースに対する包括的なバックアップ・リカバリ戦略を定義します。

## 現在の課題
- 自動バックアップ機能なし
- 障害時の復旧手順未定義
- データ整合性チェック機能なし
- バージョン管理なし

## 改善されたバックアップ戦略

### 1. バックアップスケジュール

#### 完全バックアップ（Daily）
```bash
# 毎日午前3時に実行
0 3 * * * /usr/local/bin/backup_database.sh full
```

#### 増分バックアップ（Hourly）
```bash
# 毎時15分に実行（WALファイルバックアップ）
15 * * * * /usr/local/bin/backup_database.sh incremental
```

#### 週次メンテナンス
```bash
# 毎週日曜日午前2時
0 2 * * 0 /usr/local/bin/maintenance_database.sh
```

### 2. バックアップスクリプト実装

#### backup_database.sh
```bash
#!/bin/bash
# データベースバックアップスクリプト

DB_PATH="/path/to/db.sqlite3"
BACKUP_DIR="/backups/mangaanime"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/db_backup.log"

# ディレクトリ作成
mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly,archive}

case "$1" in
    "full")
        # 完全バックアップ
        echo "$(date): Starting full backup" >> "$LOG_FILE"
        
        # SQLite VACUUMとバックアップ
        sqlite3 "$DB_PATH" "VACUUM INTO '$BACKUP_DIR/daily/db_${TIMESTAMP}.sqlite3'"
        
        # 整合性チェック
        sqlite3 "$BACKUP_DIR/daily/db_${TIMESTAMP}.sqlite3" "PRAGMA integrity_check" > "$BACKUP_DIR/daily/integrity_${TIMESTAMP}.log"
        
        # 圧縮
        gzip "$BACKUP_DIR/daily/db_${TIMESTAMP}.sqlite3"
        
        echo "$(date): Full backup completed" >> "$LOG_FILE"
        ;;
        
    "incremental")
        # WALファイルバックアップ
        if [ -f "${DB_PATH}-wal" ]; then
            cp "${DB_PATH}-wal" "$BACKUP_DIR/wal_${TIMESTAMP}.wal"
            echo "$(date): WAL backup created" >> "$LOG_FILE"
        fi
        ;;
        
    "weekly")
        # 週次バックアップ（月別ディレクトリ）
        MONTH_DIR="$BACKUP_DIR/weekly/$(date +%Y-%m)"
        mkdir -p "$MONTH_DIR"
        
        sqlite3 "$DB_PATH" "VACUUM INTO '$MONTH_DIR/db_weekly_${TIMESTAMP}.sqlite3'"
        gzip "$MONTH_DIR/db_weekly_${TIMESTAMP}.sqlite3"
        ;;
        
    "monthly")
        # 月次アーカイブ
        YEAR=$(date +%Y)
        mkdir -p "$BACKUP_DIR/monthly/$YEAR"
        
        sqlite3 "$DB_PATH" "VACUUM INTO '$BACKUP_DIR/monthly/$YEAR/db_monthly_${TIMESTAMP}.sqlite3'"
        gzip "$BACKUP_DIR/monthly/$YEAR/db_monthly_${TIMESTAMP}.sqlite3"
        ;;
esac

# 古いバックアップの削除
find "$BACKUP_DIR/daily" -name "*.gz" -mtime +7 -delete
find "$BACKUP_DIR/wal" -name "*.wal" -mtime +3 -delete
```

#### maintenance_database.sh
```bash
#!/bin/bash
# データベースメンテナンススクリプト

DB_PATH="/path/to/db.sqlite3"
LOG_FILE="/var/log/db_maintenance.log"

echo "$(date): Starting database maintenance" >> "$LOG_FILE"

# 統計情報更新
sqlite3 "$DB_PATH" "PRAGMA optimize;"

# データベース最適化
sqlite3 "$DB_PATH" "VACUUM;"

# 整合性チェック
INTEGRITY_CHECK=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;")
if [ "$INTEGRITY_CHECK" != "ok" ]; then
    echo "$(date): INTEGRITY CHECK FAILED: $INTEGRITY_CHECK" >> "$LOG_FILE"
    # 緊急通知送信
    /usr/local/bin/send_alert.sh "Database integrity check failed"
else
    echo "$(date): Integrity check passed" >> "$LOG_FILE"
fi

# WALファイルクリーンアップ
sqlite3 "$DB_PATH" "PRAGMA wal_checkpoint(TRUNCATE);"

echo "$(date): Database maintenance completed" >> "$LOG_FILE"
```

### 3. 復旧手順

#### Point-in-Time Recovery
```bash
#!/bin/bash
# ポイントインタイム復旧スクリプト

RECOVERY_POINT="$1"  # YYYY-MM-DD HH:MM:SS
BACKUP_DIR="/backups/mangaanime"
RECOVERY_DB="/tmp/recovery_db.sqlite3"

# 1. 最新の完全バックアップを特定
LATEST_BACKUP=$(find "$BACKUP_DIR/daily" -name "*.gz" -newer "$BACKUP_DIR/reference_${RECOVERY_POINT}.tmp" | sort | tail -1)

# 2. バックアップ復元
gunzip -c "$LATEST_BACKUP" > "$RECOVERY_DB"

# 3. WALファイル適用（復旧ポイントまで）
for wal_file in $(find "$BACKUP_DIR" -name "wal_*.wal" -newer "$RECOVERY_DB"); do
    sqlite3 "$RECOVERY_DB" ".restore wal $wal_file"
done

echo "Recovery completed: $RECOVERY_DB"
```

### 4. モニタリング・アラート

#### ヘルスチェックスクリプト
```python
#!/usr/bin/env python3
# db_health_check.py

import sqlite3
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os

def check_database_health():
    db_path = "/path/to/db.sqlite3"
    issues = []
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 1. 整合性チェック
        cursor = conn.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        if integrity != "ok":
            issues.append(f"Integrity check failed: {integrity}")
        
        # 2. データ更新確認
        cursor = conn.execute("SELECT MAX(created_at) FROM releases")
        last_update = cursor.fetchone()[0]
        if last_update:
            last_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            if datetime.now() - last_dt > timedelta(hours=25):
                issues.append(f"No data updates for 25+ hours (last: {last_update})")
        
        # 3. データベースサイズ確認
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        if size_mb > 1000:  # 1GB over
            issues.append(f"Database size is large: {size_mb:.2f}MB")
        
        # 4. 未通知レコード数確認
        cursor = conn.execute("SELECT COUNT(*) FROM releases WHERE notified = 0 AND release_date < date('now', '-1 day')")
        overdue_count = cursor.fetchone()[0]
        if overdue_count > 100:
            issues.append(f"Large number of overdue notifications: {overdue_count}")
        
        conn.close()
        
    except Exception as e:
        issues.append(f"Database connection error: {str(e)}")
    
    return issues

def send_alert(issues):
    if not issues:
        return
    
    msg_body = "Database Health Issues Detected:\\n\\n" + "\\n".join(issues)
    msg = MIMEText(msg_body)
    msg['Subject'] = 'MangaAnime DB Health Alert'
    msg['From'] = 'system@mangaanime.local'
    msg['To'] = 'admin@mangaanime.local'
    
    # SMTP送信処理
    # (実装は環境に応じて調整)

if __name__ == "__main__":
    issues = check_database_health()
    if issues:
        send_alert(issues)
        print(f"Health check completed with {len(issues)} issues")
    else:
        print("Health check passed")
```

### 5. バックアップ設定最適化

#### SQLite設定
```sql
-- WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- Checkpoint optimization
PRAGMA wal_autocheckpoint = 1000;

-- Backup-friendly settings
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
```

### 6. 災害復旧計画（DR）

#### オフサイトバックアップ
```bash
#!/bin/bash
# rsyncでオフサイトバックアップ
rsync -avz --delete /backups/mangaanime/ backup-server:/remote/backups/mangaanime/
```

#### クラウドストレージ同期
```bash
#!/bin/bash
# AWS S3へのバックアップ（例）
aws s3 sync /backups/mangaanime/ s3://mangaanime-backups/$(date +%Y-%m-%d)/
```

### 7. テストと検証

#### 復旧テストスケジュール
- 月次：完全復旧テスト
- 週次：部分復旧テスト
- 随時：整合性チェック

#### 自動テストスクリプト
```python
def test_backup_integrity():
    # バックアップファイルの整合性テスト
    # 復元テスト
    # データ比較テスト
    pass
```

## 実装優先度

1. **高優先度**
   - 日次完全バックアップの実装
   - 整合性チェック機能
   - 基本的な復旧スクリプト

2. **中優先度**
   - WAL増分バックアップ
   - ヘルスチェック機能
   - アラート通知

3. **低優先度**
   - オフサイトバックアップ
   - 高度な復旧機能
   - 災害復旧テスト

## まとめ

この改善されたバックアップ戦略により、以下の効果が期待できます：

- **データ保護**: 定期的な自動バックアップ
- **迅速な復旧**: 整理されたバックアップとスクリプト
- **プロアクティブ管理**: ヘルスチェックとアラート
- **運用効率**: 自動化されたメンテナンス
- **災害対応**: オフサイトバックアップとDR計画