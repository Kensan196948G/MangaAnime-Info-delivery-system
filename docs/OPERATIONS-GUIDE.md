# 運用手順書 - MangaAnime Info Delivery System

## 目次

1. [日常運用](#日常運用)
2. [定期タスク](#定期タスク)
3. [監視・アラート](#監視アラート)
4. [バックアップ](#バックアップ)
5. [障害対応](#障害対応)
6. [メンテナンス](#メンテナンス)

---

## 日常運用

### システム起動

```bash
# 仮想環境をアクティベート
source venv/bin/activate

# アプリケーション起動
python3 app/start_web_ui.py

# バックグラウンド起動（本番環境）
nohup python3 app/start_web_ui.py > logs/app.log 2>&1 &
```

### システム停止

```bash
# プロセスID確認
pgrep -f "start_web_ui.py"

# 停止
pkill -f "start_web_ui.py"
```

### ログ確認

```bash
# リアルタイムログ
tail -f logs/app.log

# エラーログのみ
grep -i error logs/app.log | tail -50

# 本日のログ
grep "$(date +%Y-%m-%d)" logs/app.log
```

---

## 定期タスク

### cron設定

```bash
# crontab編集
crontab -e
```

### 推奨スケジュール

```cron
# 毎朝8時: 情報収集・通知配信
0 8 * * * /path/to/venv/bin/python3 /path/to/scripts/run_watchlist_notifications.py >> /path/to/logs/cron.log 2>&1

# 毎日深夜1時: データベースバックアップ
0 1 * * * /path/to/venv/bin/python3 /path/to/scripts/db_auto_backup.py >> /path/to/logs/backup.log 2>&1

# 毎週日曜深夜2時: WALチェックポイント
0 2 * * 0 /path/to/venv/bin/python3 /path/to/scripts/db_auto_backup.py --checkpoint >> /path/to/logs/checkpoint.log 2>&1

# 毎月1日: 古いログのクリーンアップ
0 3 1 * * find /path/to/logs -name "*.log" -mtime +30 -delete
```

---

## 監視・アラート

### ヘルスチェック

```bash
# 基本チェック
curl -s http://localhost:5000/health | jq .

# 詳細チェック（認証必要）
curl -s -b cookies.txt http://localhost:5000/health/detailed | jq .
```

### 監視スクリプト

```bash
#!/bin/bash
# health_monitor.sh

HEALTH_URL="http://localhost:5000/health"
ALERT_EMAIL="admin@example.com"

response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$response" != "200" ]; then
    echo "ALERT: Health check failed (HTTP $response)" | mail -s "MangaAnime System Alert" $ALERT_EMAIL
fi
```

### 監視項目

| 項目 | 閾値 | 確認方法 |
|------|------|----------|
| レスポンス時間 | 5秒以上で警告 | `/health` |
| データベースサイズ | 1GB超で警告 | `ls -lh data/db.sqlite3` |
| ログサイズ | 100MB超で警告 | `ls -lh logs/` |
| API呼び出し失敗率 | 10%超で警告 | 監査ログ確認 |

---

## バックアップ

### 自動バックアップ

```bash
# バックアップ実行
python3 scripts/db_auto_backup.py

# オプション付き
python3 scripts/db_auto_backup.py --backup-dir /path/to/backups --keep 30
```

### 手動バックアップ

```bash
# データベースコピー
cp data/db.sqlite3 backups/db_$(date +%Y%m%d_%H%M%S).sqlite3

# 設定ファイル込み
tar -czvf backups/full_backup_$(date +%Y%m%d).tar.gz \
    data/db.sqlite3 \
    config/ \
    .env \
    credentials.json \
    token.json
```

### リストア

```bash
# データベースのリストア
cp backups/db_20251208_120000.sqlite3 data/db.sqlite3

# WALファイルがある場合
rm -f data/db.sqlite3-wal data/db.sqlite3-shm
```

---

## 障害対応

### データベース破損時

```bash
# 1. 破損確認
sqlite3 data/db.sqlite3 "PRAGMA integrity_check;"

# 2. バックアップからリストア
cp backups/latest_backup.sqlite3 data/db.sqlite3

# 3. またはダンプから復旧
sqlite3 data/db.sqlite3.corrupted ".dump" | sqlite3 data/db.sqlite3.new
mv data/db.sqlite3.new data/db.sqlite3
```

### API認証エラー時

```bash
# トークン再生成
rm token.json
python3 create_token.py
```

### メモリ不足時

```bash
# プロセス確認
ps aux | grep python

# メモリ使用量
free -h

# 再起動
pkill -f "start_web_ui.py"
sleep 5
python3 app/start_web_ui.py
```

### ディスク容量不足時

```bash
# 使用量確認
df -h

# 古いログ削除
find logs/ -name "*.log" -mtime +7 -delete

# 古いバックアップ削除
find backups/ -name "*.sqlite3" -mtime +30 -delete

# データベースVACUUM
sqlite3 data/db.sqlite3 "VACUUM;"
```

---

## メンテナンス

### 定期メンテナンス（月次）

1. **ログローテーション**
   ```bash
   logrotate -f /etc/logrotate.d/mangaanime
   ```

2. **データベース最適化**
   ```bash
   sqlite3 data/db.sqlite3 "VACUUM; ANALYZE;"
   ```

3. **依存関係更新確認**
   ```bash
   pip list --outdated
   ```

4. **セキュリティスキャン**
   ```bash
   pip-audit
   bandit -r app/ modules/
   ```

### バージョンアップ手順

```bash
# 1. バックアップ
python3 scripts/db_auto_backup.py

# 2. システム停止
pkill -f "start_web_ui.py"

# 3. コード更新
git pull origin main

# 4. 依存関係更新
pip install -r requirements.txt

# 5. マイグレーション実行
python3 scripts/run_migrations.py

# 6. システム起動
python3 app/start_web_ui.py

# 7. 動作確認
curl http://localhost:5000/health
```

### ロールバック手順

```bash
# 1. システム停止
pkill -f "start_web_ui.py"

# 2. コードをロールバック
git checkout <previous_commit_hash>

# 3. データベースをリストア
cp backups/db_before_update.sqlite3 data/db.sqlite3

# 4. システム起動
python3 app/start_web_ui.py
```

---

## 連絡先・エスカレーション

| 緊急度 | 対応者 | 連絡方法 |
|--------|--------|----------|
| 低 | 運用担当 | GitHub Issues |
| 中 | 開発チーム | Slack #dev-support |
| 高 | 管理者 | 電話連絡 |

---

*最終更新: 2025-12-08*
