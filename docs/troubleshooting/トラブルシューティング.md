# メール配信システム トラブルシューティングガイド

## 🔍 目次

1. [よくある問題と解決方法](#よくある問題と解決方法)
2. [エラーメッセージ別対処法](#エラーメッセージ別対処法)
3. [症状別診断フローチャート](#症状別診断フローチャート)
4. [デバッグ方法](#デバッグ方法)
5. [ログ分析](#ログ分析)
6. [パフォーマンス問題](#パフォーマンス問題)
7. [データ整合性チェック](#データ整合性チェック)
8. [緊急時の対処](#緊急時の対処)

---

## よくある問題と解決方法

### 1. メールが送信されない

#### 症状
- cronジョブは実行されているがメールが届かない
- ログに送信記録がない

#### 診断コマンド
```bash
# Gmail認証状態を確認
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

password = os.getenv('GMAIL_APP_PASSWORD')
if not password:
    print('❌ Gmail App Passwordが設定されていません')
elif password == 'sxsgmzbvubsajtok':
    print('✅ Gmail App Password設定済み')
else:
    print('⚠️ Gmail App Passwordが異なります')

# トークンファイルの確認
if os.path.exists('token.json'):
    print('✅ OAuth2トークンファイル存在')
else:
    print('❌ OAuth2トークンファイルが見つかりません')
"
```

#### 解決方法

**Step 1: Gmail認証の再設定**
```bash
# App Passwordを再生成
echo "1. https://myaccount.google.com/apppasswords にアクセス"
echo "2. 新しいApp Passwordを生成"
echo "3. 以下のコマンドで設定:"

# .envファイルを更新
read -p "新しいApp Password (スペースなし): " NEW_PASSWORD
echo "GMAIL_APP_PASSWORD=$NEW_PASSWORD" > .env
echo "GMAIL_SENDER_EMAIL=kensan1969@gmail.com" >> .env
```

**Step 2: OAuth2トークンの再生成**
```bash
# 既存トークンを削除
rm -f token.json

# 再認証を実行
python3 -c "
from modules.mailer import GmailNotifier
import json

with open('config.json', 'r') as f:
    config = json.load(f)

notifier = GmailNotifier(config)
if notifier.authenticate():
    print('✅ 認証成功')
else:
    print('❌ 認証失敗')
"
```

**Step 3: テストメール送信**
```bash
python3 scripts/test_email.py
```

---

### 2. 大量の未通知が溜まっている

#### 症状
- 1000件以上の未通知が存在
- 配信が遅れている

#### 診断コマンド
```bash
# 未通知件数の確認
sqlite3 db.sqlite3 "SELECT COUNT(*) as '未通知件数' FROM releases WHERE notified = 0;"

# 日付別の分布を確認
sqlite3 db.sqlite3 "
SELECT 
    DATE(release_date) as date,
    COUNT(*) as count
FROM releases 
WHERE notified = 0
GROUP BY DATE(release_date)
ORDER BY date DESC
LIMIT 10;
"
```

#### 解決方法

**バッチ配信スクリプトの実行**
```python
# batch_send.py - 大量配信用スクリプト
import time
import sqlite3
from modules.mailer import GmailNotifier
from modules.email_scheduler import EmailScheduler
import json

def batch_send_notifications():
    """大量の未通知を段階的に配信"""
    
    # 設定読み込み
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # 未通知件数を確認
    cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 0")
    total = cursor.fetchone()[0]
    
    print(f"📊 未通知総数: {total} 件")
    
    if total > 100:
        print("⚠️ 大量配信モードで実行します")
        batch_size = 50
        batches = (total + batch_size - 1) // batch_size
        
        for i in range(min(batches, 10)):  # 最大10バッチ
            print(f"\n📤 バッチ {i+1}/{min(batches, 10)} を送信中...")
            
            # バッチ取得
            cursor.execute("""
                SELECT r.*, w.title, w.type 
                FROM releases r
                JOIN works w ON r.work_id = w.id
                WHERE r.notified = 0
                LIMIT ?
            """, (batch_size,))
            
            releases = cursor.fetchall()
            
            # 配信処理
            notifier = GmailNotifier(config)
            success_count = 0
            
            for release in releases:
                # 配信処理（実装省略）
                success_count += 1
                
                # レート制限対策
                time.sleep(0.5)
            
            print(f"✅ {success_count} 件送信完了")
            
            # バッチ間の待機
            if i < min(batches, 10) - 1:
                print("⏳ 30秒待機中...")
                time.sleep(30)
    
    conn.close()
    print("\n✅ バッチ配信完了")

if __name__ == "__main__":
    batch_send_notifications()
```

---

### 3. cronジョブが実行されない

#### 症状
- 指定時刻になってもメールが送信されない
- ログファイルが更新されない

#### 診断コマンド
```bash
# crontabの確認
crontab -l | grep MangaAnime

# cronサービスの状態確認
systemctl status cron

# 最後のcron実行を確認
grep CRON /var/log/syslog | tail -20
```

#### 解決方法

**Step 1: cronサービスの再起動**
```bash
sudo systemctl restart cron
# または
sudo service cron restart
```

**Step 2: crontabの再設定**
```bash
# 既存設定をバックアップ
crontab -l > crontab_backup.txt

# 再インストール
./scripts/setup_daily_delivery.sh remove
./scripts/setup_daily_delivery.sh install
```

**Step 3: 権限の確認**
```bash
# スクリプトの実行権限
chmod +x release_notifier.py
chmod +x scripts/*.sh

# ログディレクトリの権限
chmod 755 logs
```

---

## エラーメッセージ別対処法

### Gmail API エラー

#### `Error 401: Invalid Credentials`

```bash
# トークンをリフレッシュ
rm -f token.json
python3 -c "
from modules.mailer import GmailNotifier
import json
with open('config.json', 'r') as f:
    config = json.load(f)
notifier = GmailNotifier(config)
notifier.authenticate()
"
```

#### `Error 403: Rate Limit Exceeded`

```python
# レート制限回避設定
config = {
    "notification": {
        "batch_size": 20,  # バッチサイズを小さく
        "delay_between_batches": 5,  # 待機時間を長く
        "max_requests_per_minute": 50  # 制限を設定
    }
}
```

#### `Error 535: Authentication failed`

```bash
# SMTPパスワードの確認
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

password = os.getenv('GMAIL_APP_PASSWORD')
print(f'現在のパスワード長: {len(password) if password else 0} 文字')

# 正しい形式か確認（16文字、スペースなし）
if password and len(password) == 16 and ' ' not in password:
    print('✅ パスワード形式正常')
else:
    print('❌ パスワード形式異常')
"
```

### データベースエラー

#### `sqlite3.OperationalError: database is locked`

```bash
# ロックを解除
fuser db.sqlite3
# プロセスIDが表示されたら
kill -9 [PID]

# データベースの整合性チェック
sqlite3 db.sqlite3 "PRAGMA integrity_check;"
```

#### `sqlite3.IntegrityError: UNIQUE constraint failed`

```sql
-- 重複データの確認と削除
DELETE FROM releases
WHERE rowid NOT IN (
    SELECT MIN(rowid)
    FROM releases
    GROUP BY work_id, release_type, number, platform, release_date
);
```

---

## 症状別診断フローチャート

```
メールが届かない
│
├─ cronは動いている？
│  │
│  ├─ YES → ログにエラーは？
│  │         │
│  │         ├─ YES → エラーメッセージを確認
│  │         │        └─ 該当セクションへ
│  │         │
│  │         └─ NO → Gmail認証を確認
│  │                  └─ 認証設定セクションへ
│  │
│  └─ NO → cron設定を確認
│           └─ cron設定セクションへ
│
└─ 部分的に届く？
   │
   ├─ YES → レート制限の可能性
   │        └─ バッチサイズを調整
   │
   └─ NO → ネットワーク接続を確認
            └─ DNS/ファイアウォール設定
```

---

## デバッグ方法

### 詳細ログの有効化

```bash
# 環境変数でデバッグモードを有効化
export DEBUG=1
export LOG_LEVEL=DEBUG

# 詳細ログ付きで実行
python3 release_notifier.py --verbose --dry-run
```

### ステップ実行デバッグ

```python
# debug_notifier.py
import pdb
from release_notifier import ReleaseNotifier

def debug_notification():
    notifier = ReleaseNotifier()
    
    # ブレークポイント設定
    pdb.set_trace()
    
    # ステップ実行
    notifier.load_config()
    notifier.connect_database()
    notifier.fetch_pending_releases()
    
    print("デバッグ完了")

if __name__ == "__main__":
    debug_notification()
```

### SQL クエリログ

```bash
# SQLite のクエリログを有効化
sqlite3 db.sqlite3 << EOF
.trace stdout
SELECT * FROM releases WHERE notified = 0 LIMIT 5;
EOF
```

---

## ログ分析

### エラーパターンの抽出

```bash
# エラーの種類と頻度
grep ERROR logs/daily_delivery.log | \
    sed 's/.*ERROR/ERROR/' | \
    cut -d: -f1-2 | \
    sort | uniq -c | sort -rn

# 時間帯別エラー分布
grep ERROR logs/daily_delivery.log | \
    cut -d' ' -f2 | cut -d: -f1 | \
    sort | uniq -c | sort -n
```

### 配信成功率の計算

```python
# analyze_logs.py
import re
from collections import defaultdict

def analyze_delivery_logs():
    success = 0
    failure = 0
    errors = defaultdict(int)
    
    with open('logs/daily_delivery.log', 'r') as f:
        for line in f:
            if '送信成功' in line:
                success += 1
            elif 'ERROR' in line:
                failure += 1
                # エラー種別を抽出
                match = re.search(r'ERROR.*?: (.*?):', line)
                if match:
                    errors[match.group(1)] += 1
    
    total = success + failure
    if total > 0:
        rate = (success / total) * 100
        print(f"📊 配信統計")
        print(f"  成功: {success} 件")
        print(f"  失敗: {failure} 件")
        print(f"  成功率: {rate:.1f}%")
        
        if errors:
            print("\n📋 エラー内訳:")
            for error_type, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
                print(f"  {error_type}: {count} 件")

if __name__ == "__main__":
    analyze_delivery_logs()
```

---

## パフォーマンス問題

### 配信が遅い

#### 診断
```bash
# 配信速度の測定
time python3 -c "
from release_notifier import ReleaseNotifier
notifier = ReleaseNotifier()
notifier.send_single_notification(test=True)
"
```

#### 最適化方法

1. **バッチサイズの調整**
```json
{
  "notification": {
    "batch_size": 30,  // 小さくして安定性重視
    "parallel_workers": 3  // 並列処理
  }
}
```

2. **データベースインデックスの追加**
```sql
CREATE INDEX idx_releases_notified_date 
ON releases(notified, release_date);

ANALYZE;  -- 統計情報を更新
```

3. **接続プーリング**
```python
from contextlib import contextmanager
import sqlite3

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('db.sqlite3', timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```

---

## データ整合性チェック

### 整合性検証スクリプト

```python
# check_integrity.py
import sqlite3

def check_data_integrity():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    checks = []
    
    # 1. 孤立したreleasesレコード
    cursor.execute("""
        SELECT COUNT(*) FROM releases r
        LEFT JOIN works w ON r.work_id = w.id
        WHERE w.id IS NULL
    """)
    orphaned = cursor.fetchone()[0]
    checks.append(('孤立レコード', orphaned, orphaned == 0))
    
    # 2. 重複レコード
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT work_id, release_type, number, platform, release_date, COUNT(*) as cnt
            FROM releases
            GROUP BY work_id, release_type, number, platform, release_date
            HAVING cnt > 1
        )
    """)
    duplicates = cursor.fetchone()[0]
    checks.append(('重複レコード', duplicates, duplicates == 0))
    
    # 3. 未来の日付
    cursor.execute("""
        SELECT COUNT(*) FROM releases
        WHERE release_date > DATE('now', '+1 year')
    """)
    future = cursor.fetchone()[0]
    checks.append(('異常な未来日付', future, future < 100))
    
    # 結果表示
    print("🔍 データ整合性チェック")
    print("-" * 40)
    
    all_ok = True
    for check_name, value, is_ok in checks:
        status = "✅" if is_ok else "❌"
        print(f"{status} {check_name}: {value}")
        if not is_ok:
            all_ok = False
    
    if all_ok:
        print("\n✅ すべてのチェック項目が正常です")
    else:
        print("\n⚠️ 問題が検出されました。修復が必要です")
    
    conn.close()
    return all_ok

if __name__ == "__main__":
    check_data_integrity()
```

### データ修復

```bash
# バックアップを作成
cp db.sqlite3 db.sqlite3.backup

# 修復スクリプト
sqlite3 db.sqlite3 << EOF
-- 孤立レコードを削除
DELETE FROM releases 
WHERE work_id NOT IN (SELECT id FROM works);

-- 重複を削除（最新のみ残す）
DELETE FROM releases
WHERE rowid NOT IN (
    SELECT MAX(rowid)
    FROM releases
    GROUP BY work_id, release_type, number, platform, release_date
);

-- データベースを最適化
VACUUM;
REINDEX;
ANALYZE;
EOF

echo "✅ データ修復完了"
```

---

## 緊急時の対処

### システム完全停止

```bash
#!/bin/bash
# emergency_stop.sh

echo "🚨 緊急停止を実行します"

# 1. cronジョブを無効化
crontab -l | grep -v MangaAnime | crontab -

# 2. 実行中のプロセスを終了
pkill -f release_notifier.py
pkill -f python3.*mailer

# 3. ロックファイルを作成
touch /tmp/MANGAANIME_EMERGENCY_STOP

echo "⛔ システムを停止しました"
echo "再開するには: rm /tmp/MANGAANIME_EMERGENCY_STOP"
```

### 緊急復旧手順

```bash
#!/bin/bash
# emergency_recovery.sh

echo "🔧 緊急復旧を開始"

# 1. 停止フラグを削除
rm -f /tmp/MANGAANIME_EMERGENCY_STOP

# 2. データベースチェック
if ! sqlite3 db.sqlite3 "PRAGMA integrity_check;" | grep -q "ok"; then
    echo "❌ データベース破損を検出"
    echo "バックアップからの復旧を推奨"
    exit 1
fi

# 3. 設定ファイルの検証
python3 -c "
import json
try:
    with open('config.json', 'r') as f:
        json.load(f)
    print('✅ 設定ファイル正常')
except:
    print('❌ 設定ファイル異常')
    exit(1)
"

# 4. 最小構成でテスト
python3 release_notifier.py --dry-run --limit 1

# 5. cronを再設定
./scripts/setup_daily_delivery.sh install

echo "✅ 緊急復旧完了"
```

---

## サポート用診断情報収集

```bash
#!/bin/bash
# collect_diagnostics.sh

OUTPUT="diagnostics_$(date +%Y%m%d_%H%M%S).txt"

{
    echo "=== MangaAnime診断情報 ==="
    echo "生成日時: $(date)"
    echo ""
    
    echo "=== システム情報 ==="
    uname -a
    python3 --version
    
    echo ""
    echo "=== データベース状態 ==="
    sqlite3 db.sqlite3 "SELECT COUNT(*) as '総レコード数' FROM releases;"
    sqlite3 db.sqlite3 "SELECT COUNT(*) as '未通知数' FROM releases WHERE notified = 0;"
    
    echo ""
    echo "=== 最新エラー（10件） ==="
    grep ERROR logs/daily_delivery.log | tail -10
    
    echo ""
    echo "=== cron設定 ==="
    crontab -l | grep MangaAnime
    
    echo ""
    echo "=== ディスク使用状況 ==="
    df -h .
    du -sh db.sqlite3 logs/
    
} > "$OUTPUT"

echo "📋 診断情報を $OUTPUT に保存しました"
```

---

## 問い合わせ先

解決できない問題が発生した場合：

1. 診断情報を収集（上記スクリプト使用）
2. [GitHub Issues](https://github.com/yourusername/MangaAnime-Info-delivery-system/issues)に報告
3. ログファイルとエラーメッセージを添付

---

*最終更新: 2024年8月*