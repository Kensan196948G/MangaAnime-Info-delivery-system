# メール配信システム運用マニュアル

## 📖 目次

1. [日常運用](#日常運用)
2. [配信管理](#配信管理)
3. [データベース管理](#データベース管理)
4. [ログ管理](#ログ管理)
5. [バックアップとリストア](#バックアップとリストア)
6. [パフォーマンス監視](#パフォーマンス監視)
7. [緊急時対応](#緊急時対応)

---

## 日常運用

### 📅 日次タスク

#### 1. 配信状況の確認

```bash
# 本日の配信状況を確認
python3 -c "
import sqlite3
from datetime import datetime, date

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# 本日の配信済み件数
cursor.execute('''
    SELECT COUNT(*) FROM releases 
    WHERE notified = 1 
    AND DATE(updated_at) = DATE('now', 'localtime')
''')
today_sent = cursor.fetchone()[0]

# 未配信件数
cursor.execute('SELECT COUNT(*) FROM releases WHERE notified = 0')
pending = cursor.fetchone()[0]

print(f'📊 本日の配信状況 ({date.today()})')
print(f'  ✅ 配信済み: {today_sent} 件')
print(f'  ⏳ 未配信: {pending} 件')
"

# 出力例：
# 📊 本日の配信状況 (2024-08-15)
#   ✅ 配信済み: 45 件
#   ⏳ 未配信: 1041 件
```

#### 2. エラーチェック

```bash
# 本日のエラーを確認
grep "ERROR\|CRITICAL" logs/daily_delivery.log | grep "$(date +%Y-%m-%d)"

# エラー件数をカウント
echo "エラー件数: $(grep ERROR logs/daily_delivery.log | wc -l)"
```

#### 3. スケジュール確認

```bash
# 次回の配信時刻を確認
./scripts/setup_daily_delivery.sh status

# crontabの実行予定を確認
for time in "0 8" "0 12" "0 20"; do
    echo "次回 $time 時の実行まで:"
    python3 -c "
from datetime import datetime, timedelta
now = datetime.now()
hour = int('$time'.split()[1])
next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
if next_run <= now:
    next_run += timedelta(days=1)
diff = next_run - now
hours = int(diff.seconds / 3600)
minutes = int((diff.seconds % 3600) / 60)
print(f'  {hours}時間{minutes}分後 ({next_run.strftime(\"%m/%d %H:%M\")})')
"
done
```

### 📅 週次タスク

#### 1. パフォーマンスレポート

```bash
# 週次レポートスクリプト
cat << 'EOF' > /tmp/weekly_report.py
import sqlite3
from datetime import datetime, timedelta
import json

# 1週間の統計を集計
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

# 配信統計
cursor.execute(f'''
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN notified = 1 THEN 1 ELSE 0 END) as sent,
        SUM(CASE WHEN notified = 0 THEN 1 ELSE 0 END) as pending
    FROM releases
    WHERE created_at >= '{week_ago}'
''')

stats = cursor.fetchone()

print("📊 週次レポート")
print("=" * 50)
print(f"期間: {week_ago} ~ {datetime.now().strftime('%Y-%m-%d')}")
print(f"新規登録: {stats[0]} 件")
print(f"配信済み: {stats[1]} 件")
print(f"未配信: {stats[2]} 件")
print(f"配信率: {stats[1]/stats[0]*100:.1f}%" if stats[0] > 0 else "配信率: N/A")

# プラットフォーム別統計
cursor.execute(f'''
    SELECT platform, COUNT(*) as count
    FROM releases
    WHERE created_at >= '{week_ago}'
    GROUP BY platform
    ORDER BY count DESC
    LIMIT 5
''')

print("\n📱 プラットフォーム別TOP5:")
for platform, count in cursor.fetchall():
    print(f"  {platform}: {count} 件")

conn.close()
EOF

python3 /tmp/weekly_report.py
```

#### 2. ログのアーカイブ

```bash
# 1週間前のログをアーカイブ
cd logs
tar -czf "archive_$(date -d '7 days ago' +%Y%m%d).tar.gz" \
    $(find . -name "*.log" -mtime +7)

# アーカイブ後、古いログを削除
find . -name "*.log" -mtime +7 -delete
```

### 📅 月次タスク

#### 1. データベース最適化

```bash
# データベースの最適化
python3 << EOF
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# バキューム実行（断片化解消）
print("🔧 データベース最適化を開始...")
cursor.execute("VACUUM")

# インデックスの再構築
cursor.execute("REINDEX")

# 統計情報の更新
cursor.execute("ANALYZE")

print("✅ データベース最適化完了")

# データベースサイズを確認
import os
size_mb = os.path.getsize('db.sqlite3') / 1024 / 1024
print(f"📊 DBサイズ: {size_mb:.2f} MB")

conn.close()
EOF
```

---

## 配信管理

### 手動配信

#### 即時配信

```bash
# 通常配信（未通知をすべて送信）
python3 release_notifier.py

# 制限付き配信（最大50件）
python3 release_notifier.py --limit 50

# ドライラン（実際には送信しない）
python3 release_notifier.py --dry-run
```

#### 特定期間の配信

```bash
# 本日分のみ配信
python3 -c "
from release_notifier import ReleaseNotifier
from datetime import date

notifier = ReleaseNotifier()
notifier.send_notifications(date_filter=date.today())
"

# 特定の日付範囲を配信
python3 -c "
from release_notifier import ReleaseNotifier
from datetime import datetime

notifier = ReleaseNotifier()
notifier.send_notifications(
    start_date=datetime(2024, 8, 1),
    end_date=datetime(2024, 8, 15)
)
"
```

### 配信の一時停止と再開

#### 一時停止

```bash
# crontabを一時的に無効化
crontab -l | sed 's/^/#/' | crontab -

echo "⏸️  配信を一時停止しました"
```

#### 再開

```bash
# crontabを再有効化
crontab -l | sed 's/^#//' | crontab -

echo "▶️  配信を再開しました"
```

### 配信リトライ

```bash
# 失敗した配信を再試行
python3 << EOF
import sqlite3
from modules.mailer import GmailNotifier
import json

# 設定読み込み
with open('config.json', 'r') as f:
    config = json.load(f)

# 失敗したメールのリトライ
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# notifiedが2（失敗）のレコードを取得
cursor.execute('''
    SELECT id, work_id, title 
    FROM releases r
    JOIN works w ON r.work_id = w.id
    WHERE r.notified = 2
    LIMIT 10
''')

failed = cursor.fetchall()
print(f"🔄 {len(failed)} 件の失敗配信をリトライします")

notifier = GmailNotifier(config)
for release_id, work_id, title in failed:
    print(f"  リトライ: {title}")
    # リトライ処理
    # ...

conn.close()
EOF
```

---

## データベース管理

### データベース統計

```bash
# テーブル別レコード数
sqlite3 db.sqlite3 << EOF
.headers on
.mode column
SELECT 
    'works' as table_name, 
    COUNT(*) as record_count 
FROM works
UNION ALL
SELECT 
    'releases' as table_name, 
    COUNT(*) as record_count 
FROM releases;
EOF
```

### データクリーンアップ

```bash
# 古い通知済みデータを削除（6ヶ月以上前）
sqlite3 db.sqlite3 << EOF
DELETE FROM releases 
WHERE notified = 1 
AND updated_at < datetime('now', '-6 months');

-- 削除件数を表示
SELECT changes() || ' 件のレコードを削除しました' as result;
EOF
```

### インデックス管理

```sql
-- パフォーマンス向上のためのインデックス作成
CREATE INDEX IF NOT EXISTS idx_releases_notified 
ON releases(notified);

CREATE INDEX IF NOT EXISTS idx_releases_date 
ON releases(release_date);

CREATE INDEX IF NOT EXISTS idx_works_type 
ON works(type);
```

---

## ログ管理

### ログローテーション設定

```bash
# logrotate設定ファイルを作成
sudo tee /etc/logrotate.d/mangaanime << EOF
/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 $(whoami) $(whoami)
    sharedscripts
    postrotate
        # 必要に応じてサービス再起動などを追加
    endscript
}
EOF
```

### ログ分析

```bash
# エラー頻度分析
echo "📊 エラー頻度分析（過去7日間）"
for i in {0..6}; do
    date=$(date -d "$i days ago" +%Y-%m-%d)
    count=$(grep "$date" logs/daily_delivery.log | grep -c ERROR || echo 0)
    printf "%s: %3d errors\n" "$date" "$count"
done

# 配信成功率
total=$(grep "送信開始" logs/daily_delivery.log | wc -l)
success=$(grep "送信成功" logs/daily_delivery.log | wc -l)
if [ $total -gt 0 ]; then
    rate=$((success * 100 / total))
    echo "配信成功率: ${rate}%"
fi
```

---

## バックアップとリストア

### 自動バックアップスクリプト

```bash
#!/bin/bash
# backup.sh - 日次バックアップスクリプト

BACKUP_DIR="/backup/mangaanime"
PROJECT_DIR="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
DATE=$(date +%Y%m%d_%H%M%S)

# バックアップディレクトリ作成
mkdir -p "$BACKUP_DIR"

# データベースバックアップ
sqlite3 "$PROJECT_DIR/db.sqlite3" ".backup '$BACKUP_DIR/db_$DATE.sqlite3'"

# 設定ファイルバックアップ
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    -C "$PROJECT_DIR" \
    config.json \
    .env \
    credentials.json \
    token.json

# 古いバックアップを削除（30日以上）
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.sqlite3" -mtime +30 -delete

echo "✅ バックアップ完了: $BACKUP_DIR/*_$DATE.*"
```

### リストア手順

```bash
# 最新のバックアップからリストア
LATEST_DB=$(ls -t /backup/mangaanime/db_*.sqlite3 | head -1)
LATEST_CONFIG=$(ls -t /backup/mangaanime/config_*.tar.gz | head -1)

# データベースをリストア
cp "$LATEST_DB" db.sqlite3

# 設定ファイルをリストア
tar -xzf "$LATEST_CONFIG"

echo "✅ リストア完了"
```

---

## パフォーマンス監視

### リアルタイム監視

```bash
# 配信速度の監視
tail -f logs/daily_delivery.log | grep --line-buffered "送信" | \
while read line; do
    echo "$(date +%H:%M:%S) $line"
done
```

### パフォーマンス指標

```python
# performance_check.py
import sqlite3
import time
from datetime import datetime, timedelta

def check_performance():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # クエリ実行時間測定
    queries = [
        ("未通知取得", "SELECT COUNT(*) FROM releases WHERE notified = 0"),
        ("本日配信", "SELECT COUNT(*) FROM releases WHERE DATE(updated_at) = DATE('now')"),
        ("JOIN性能", """
            SELECT COUNT(*) FROM releases r 
            JOIN works w ON r.work_id = w.id 
            WHERE r.notified = 0
        """)
    ]
    
    print("🔍 パフォーマンス測定")
    print("-" * 40)
    
    for name, query in queries:
        start = time.time()
        cursor.execute(query)
        result = cursor.fetchone()[0]
        elapsed = (time.time() - start) * 1000
        
        status = "✅" if elapsed < 100 else "⚠️" if elapsed < 500 else "❌"
        print(f"{status} {name}: {elapsed:.2f}ms (結果: {result}件)")
    
    conn.close()

if __name__ == "__main__":
    check_performance()
```

---

## 緊急時対応

### 配信停止

```bash
# 即座に全配信を停止
touch /tmp/mangaanime_stop

# release_notifier.py内でチェック
if [ -f /tmp/mangaanime_stop ]; then
    echo "⛔ 緊急停止フラグが設定されています"
    exit 1
fi
```

### エラー通知設定

```bash
# エラー発生時のSlack通知（例）
cat << 'EOF' > scripts/error_notification.sh
#!/bin/bash

ERROR_COUNT=$(grep -c "ERROR\|CRITICAL" logs/daily_delivery.log)

if [ $ERROR_COUNT -gt 0 ]; then
    # Slack Webhook URL
    WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    
    curl -X POST $WEBHOOK_URL \
        -H 'Content-Type: application/json' \
        -d "{
            \"text\": \"⚠️ MangaAnimeシステムエラー\",
            \"attachments\": [{
                \"color\": \"danger\",
                \"fields\": [{
                    \"title\": \"エラー件数\",
                    \"value\": \"$ERROR_COUNT\",
                    \"short\": true
                }]
            }]
        }"
fi
EOF

chmod +x scripts/error_notification.sh
```

### 緊急リカバリ

```bash
# システム全体のリセット
cat << 'EOF' > scripts/emergency_recovery.sh
#!/bin/bash

echo "🚨 緊急リカバリを開始します"

# 1. 配信を停止
crontab -l | grep -v "MangaAnime" | crontab -

# 2. プロセスを終了
pkill -f release_notifier.py

# 3. 一時ファイルをクリア
rm -f /tmp/mangaanime_*

# 4. データベースを修復
sqlite3 db.sqlite3 "PRAGMA integrity_check;"

# 5. 設定を再読み込み
python3 -c "
import json
with open('config.json', 'r') as f:
    config = json.load(f)
print('✅ 設定ファイル: 正常')
"

# 6. テストモードで動作確認
python3 release_notifier.py --dry-run --limit 1

echo "✅ 緊急リカバリ完了"
EOF

chmod +x scripts/emergency_recovery.sh
```

---

## 運用チェックリスト

### 日次チェック項目

- [ ] 配信ログにエラーがないか
- [ ] 未配信件数が異常に多くないか
- [ ] ディスク容量は十分か
- [ ] cronジョブが正常に実行されているか

### 週次チェック項目

- [ ] パフォーマンスレポートの確認
- [ ] ログファイルのローテーション
- [ ] データベースサイズの確認
- [ ] バックアップの実行確認

### 月次チェック項目

- [ ] データベースの最適化
- [ ] 古いデータのクリーンアップ
- [ ] システムアップデートの確認
- [ ] セキュリティパッチの適用

---

## 関連ドキュメント

- [トラブルシューティング](../troubleshooting/トラブルシューティング.md) - 問題解決ガイド
- [設定ガイド](../setup/設定ガイド.md) - 初期設定手順
- [API仕様書](../technical/API仕様書.md) - 技術仕様

---

*最終更新: 2024年8月*