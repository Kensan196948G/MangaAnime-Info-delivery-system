# 運用マニュアル

## 目次
1. [概要](#概要)
2. [日次運用](#日次運用)
3. [週次運用](#週次運用)
4. [月次運用](#月次運用)
5. [バックアップとリストア](#バックアップとリストア)
6. [監視とログ管理](#監視とログ管理)
7. [メンテナンス](#メンテナンス)
8. [アラート対応](#アラート対応)
9. [データ管理](#データ管理)
10. [パフォーマンス最適化](#パフォーマンス最適化)

---

## 概要

本ドキュメントは、MangaAnime-Info-delivery-systemの日常的な運用手順を記載しています。

### 運用体制
- **運用時間**: 24時間365日自動運用
- **バッチ実行時刻**: 毎朝08:00 (JST)
- **監視頻度**: 日次
- **バックアップ**: 日次 (自動)

---

## 日次運用

### 1. 朝の動作確認 (08:30頃)

バッチ実行後の確認作業:

```bash
# プロジェクトディレクトリに移動
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

# 最新のログを確認
tail -n 100 logs/app.log

# エラーの有無を確認
grep -i "error\|exception\|failed" logs/app.log | tail -n 20

# 本日の実行ステータスを確認
grep "$(date +%Y-%m-%d)" logs/app.log | grep -i "completed\|success"
```

### 2. 通知メールの確認

```bash
# 送信されたメールの件数確認
grep "Email sent successfully" logs/app.log | grep "$(date +%Y-%m-%d)" | wc -l

# 送信失敗があれば確認
grep "Email failed" logs/app.log | grep "$(date +%Y-%m-%d)"
```

### 3. カレンダー同期の確認

```bash
# カレンダー登録の件数確認
grep "Calendar event created" logs/app.log | grep "$(date +%Y-%m-%d)" | wc -l

# 同期失敗があれば確認
grep "Calendar sync failed" logs/app.log | grep "$(date +%Y-%m-%d)"
```

### 4. データベース状態の確認

```bash
# 本日追加されたレコード数を確認
sqlite3 data/db.sqlite3 "SELECT COUNT(*) FROM releases WHERE DATE(created_at) = DATE('now');"

# 通知済みレコード数を確認
sqlite3 data/db.sqlite3 "SELECT COUNT(*) FROM releases WHERE notified = 1 AND DATE(created_at) = DATE('now');"
```

### 5. ディスク使用量の確認

```bash
# ログファイルのサイズ確認
du -sh logs/

# データベースのサイズ確認
du -sh data/

# 5GB以上になっている場合は古いログの削除を検討
```

---

## 週次運用

### 1. ログのローテーション (毎週日曜日)

```bash
# ログディレクトリに移動
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs

# 古いログのアーカイブ
tar -czf app-$(date +%Y%m%d).tar.gz app.log error.log cron.log

# アーカイブを別ディレクトリに移動
mkdir -p archives
mv app-*.tar.gz archives/

# ログファイルのクリア (必要に応じて)
> app.log
> error.log
> cron.log

# または logrotate を使用
sudo logrotate -f /etc/logrotate.d/manga-anime-notifier
```

### 2. データベースの最適化

```bash
# SQLiteデータベースの最適化
sqlite3 data/db.sqlite3 "VACUUM;"

# インデックスの再構築
sqlite3 data/db.sqlite3 "REINDEX;"

# データベースの整合性チェック
sqlite3 data/db.sqlite3 "PRAGMA integrity_check;"
```

### 3. API制限の確認

```bash
# AniList APIの呼び出し回数を確認
grep "AniList API" logs/app.log | grep "$(date +%Y-%m-%d -d '7 days ago')" | wc -l

# Gmail APIの使用量を確認
grep "Gmail API" logs/app.log | grep "$(date +%Y-%m-%d -d '7 days ago')" | wc -l

# Calendar APIの使用量を確認
grep "Calendar API" logs/app.log | grep "$(date +%Y-%m-%d -d '7 days ago')" | wc -l
```

### 4. 週次レポートの生成

```bash
# 週次統計レポートの生成
python scripts/generate_weekly_report.py

# レポートの確認
cat reports/weekly-report-$(date +%Y-W%U).txt
```

レポート内容例:
```
週次運用レポート (2025-W49)
============================
実行回数: 7回
成功率: 100%
新規作品数: 45件
新規エピソード数: 234件
メール送信数: 279件
カレンダー登録数: 279件
エラー発生数: 0件
平均実行時間: 2分34秒
```

---

## 月次運用

### 1. 月次バックアップの確認

```bash
# バックアップディレクトリの確認
ls -lh backups/monthly/

# 最新の月次バックアップの確認
ls -lt backups/monthly/ | head -n 5

# バックアップサイズの確認
du -sh backups/monthly/
```

### 2. 古いデータのアーカイブ

```bash
# 6ヶ月以上前のデータをアーカイブテーブルに移動
python scripts/archive_old_data.py --months 6

# アーカイブ後のデータベースサイズ確認
du -sh data/db.sqlite3
```

### 3. システムアップデートの確認

```bash
# Pythonパッケージの更新確認
source venv/bin/activate
pip list --outdated

# セキュリティアップデートの確認
pip-audit

# 更新が必要な場合
pip install --upgrade <package-name>
pip freeze > requirements.txt
```

### 4. 月次レポートの生成と送付

```bash
# 月次統計レポートの生成
python scripts/generate_monthly_report.py

# レポートの確認
cat reports/monthly-report-$(date +%Y-%m).txt

# レポートをメールで送信
python scripts/send_monthly_report.py
```

### 5. Google API認証トークンの更新確認

```bash
# トークンの有効期限確認
python scripts/check_token_expiry.py

# 有効期限が近い場合は再認証
python scripts/authenticate_google.py
```

---

## バックアップとリストア

### バックアップ手順

#### 1. 自動バックアップの確認

```bash
# 自動バックアップスクリプトの実行状況確認
crontab -l | grep backup

# 最新のバックアップ確認
ls -lt backups/ | head -n 5
```

#### 2. 手動バックアップの実行

```bash
# 完全バックアップスクリプトの実行
bash scripts/backup.sh

# または個別にバックアップ
# データベース
cp data/db.sqlite3 backups/db.sqlite3.backup-$(date +%Y%m%d-%H%M%S)

# 設定ファイル
cp config/.env backups/config/.env.backup-$(date +%Y%m%d-%H%M%S)

# 認証情報
cp credentials/token.json backups/credentials/token.json.backup-$(date +%Y%m%d-%H%M%S)

# ログファイル
tar -czf backups/logs-$(date +%Y%m%d-%H%M%S).tar.gz logs/
```

#### 3. バックアップの検証

```bash
# データベースバックアップの整合性確認
sqlite3 backups/db.sqlite3.backup-YYYYMMDD "PRAGMA integrity_check;"

# バックアップファイルのサイズ確認
ls -lh backups/db.sqlite3.backup-*
```

### リストア手順

#### 1. サービスの停止

```bash
# systemdサービスの停止
sudo systemctl stop manga-anime-notifier.service
sudo systemctl stop manga-anime-notifier.timer

# またはcronを無効化
crontab -e  # 該当行をコメントアウト
```

#### 2. 現在のデータのバックアップ

```bash
# 万が一に備えて現在の状態を保存
cp data/db.sqlite3 data/db.sqlite3.before-restore-$(date +%Y%m%d-%H%M%S)
```

#### 3. データのリストア

```bash
# バックアップからリストア
cp backups/db.sqlite3.backup-YYYYMMDD data/db.sqlite3

# 設定ファイルのリストア (必要な場合)
cp backups/config/.env.backup-YYYYMMDD config/.env

# 認証情報のリストア (必要な場合)
cp backups/credentials/token.json.backup-YYYYMMDD credentials/token.json

# 権限の設定
chmod 644 data/db.sqlite3
chmod 600 config/.env
chmod 600 credentials/token.json
```

#### 4. 整合性チェック

```bash
# データベースの整合性確認
sqlite3 data/db.sqlite3 "PRAGMA integrity_check;"

# テストデータの確認
sqlite3 data/db.sqlite3 "SELECT COUNT(*) FROM works; SELECT COUNT(*) FROM releases;"
```

#### 5. サービスの再開

```bash
# systemdサービスの再開
sudo systemctl start manga-anime-notifier.service
sudo systemctl start manga-anime-notifier.timer

# またはcronを有効化
crontab -e  # コメントアウトを解除
```

#### 6. 動作確認

```bash
# テスト実行
python release_notifier.py --dry-run

# ログの確認
tail -f logs/app.log
```

---

## 監視とログ管理

### 1. ログファイルの種類と場所

| ログファイル | 場所 | 内容 |
|---------|------|------|
| app.log | logs/app.log | アプリケーション全般のログ |
| error.log | logs/error.log | エラーログのみ |
| cron.log | logs/cron.log | cronジョブの実行ログ |
| service.log | logs/service.log | systemdサービスのログ |

### 2. ログのリアルタイム監視

```bash
# アプリケーションログの監視
tail -f logs/app.log

# エラーログの監視
tail -f logs/error.log

# 複数ログの同時監視
tail -f logs/app.log logs/error.log logs/cron.log

# エラーのみをフィルタリング
tail -f logs/app.log | grep -i "error\|exception\|failed"
```

### 3. ログの検索と分析

```bash
# 特定の日付のログを検索
grep "2025-12-08" logs/app.log

# エラー数のカウント
grep -c "ERROR" logs/app.log

# 特定のエラーの抽出
grep "ConnectionError" logs/error.log

# 実行時間の統計
grep "Execution completed" logs/app.log | awk '{print $NF}' | sort -n
```

### 4. ログローテーションの設定

/etc/logrotate.d/manga-anime-notifier を作成:

```bash
/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    create 0644 your-username your-username
    sharedscripts
    postrotate
        # 必要に応じて処理
    endscript
}
```

### 5. 監視スクリプトの作成

monitor.sh:
```bash
#!/bin/bash

LOG_FILE="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs/app.log"
ERROR_THRESHOLD=5
ALERT_EMAIL="admin@example.com"

# 直近1時間のエラー数をカウント
ERROR_COUNT=$(grep "$(date +%Y-%m-%d)" "$LOG_FILE" | grep -c "ERROR")

if [ "$ERROR_COUNT" -gt "$ERROR_THRESHOLD" ]; then
    echo "Alert: $ERROR_COUNT errors detected in the last hour" | \
    mail -s "MangaAnime System Alert" "$ALERT_EMAIL"
fi
```

---

## メンテナンス

### 1. 定期メンテナンス項目

#### 日次メンテナンス
- [ ] ログファイルの確認
- [ ] エラーの有無確認
- [ ] ディスク使用量確認

#### 週次メンテナンス
- [ ] ログのローテーション
- [ ] データベースの最適化
- [ ] API使用量の確認

#### 月次メンテナンス
- [ ] システムアップデート確認
- [ ] 古いデータのアーカイブ
- [ ] 月次レポートの作成

#### 四半期メンテナンス
- [ ] 設定の見直し
- [ ] パフォーマンス分析
- [ ] セキュリティ監査

### 2. データベースメンテナンス

```bash
# データベースの分析
sqlite3 data/db.sqlite3 "ANALYZE;"

# テーブルサイズの確認
sqlite3 data/db.sqlite3 "
SELECT
    name,
    COUNT(*) as record_count,
    (SELECT COUNT(*) FROM pragma_table_info(name)) as column_count
FROM sqlite_master
WHERE type='table'
GROUP BY name;"

# 古いレコードの削除 (6ヶ月以上前)
sqlite3 data/db.sqlite3 "
DELETE FROM releases
WHERE created_at < datetime('now', '-6 months');"

# VACUUMで領域を回収
sqlite3 data/db.sqlite3 "VACUUM;"
```

### 3. 認証情報のメンテナンス

```bash
# トークンの有効期限確認
python -c "
import json
from datetime import datetime
with open('credentials/token.json', 'r') as f:
    token = json.load(f)
    if 'expiry' in token:
        expiry = datetime.fromisoformat(token['expiry'].replace('Z', '+00:00'))
        print(f'Token expires: {expiry}')
        if (expiry - datetime.now()).days < 7:
            print('WARNING: Token expires within 7 days!')
"

# トークンの再発行 (必要な場合)
python scripts/authenticate_google.py
```

### 4. システム最適化

```bash
# Pythonキャッシュのクリア
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 不要な仮想環境の削除と再作成 (必要な場合)
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## アラート対応

### 1. アラートの種類と対応

#### Level 1: 情報 (INFO)
- **内容**: 正常な処理の完了通知
- **対応**: 特になし、記録のみ

#### Level 2: 警告 (WARNING)
- **内容**: 一時的なエラーや遅延
- **対応**: 次回実行時に自動回復を確認

#### Level 3: エラー (ERROR)
- **内容**: API接続失敗、メール送信失敗など
- **対応**: 即座に確認し、必要に応じて手動実行

#### Level 4: 重大 (CRITICAL)
- **内容**: データベース破損、認証失敗など
- **対応**: 緊急対応、バックアップからの復旧検討

### 2. よくあるアラートと対処法

#### Gmail API接続エラー
```bash
# エラー内容の確認
grep "Gmail API" logs/error.log | tail -n 10

# トークンの再発行
python scripts/authenticate_google.py

# 手動でメール送信テスト
python modules/mailer.py --test
```

#### Calendar API接続エラー
```bash
# エラー内容の確認
grep "Calendar API" logs/error.log | tail -n 10

# 手動でカレンダー登録テスト
python modules/calendar.py --test
```

#### データベースロックエラー
```bash
# データベースロックの確認
lsof data/db.sqlite3

# ロックしているプロセスの終了
kill -9 <PID>

# データベース整合性チェック
sqlite3 data/db.sqlite3 "PRAGMA integrity_check;"
```

#### ディスク容量不足
```bash
# ディスク使用量の確認
df -h /mnt/Linux-ExHDD

# 古いログの削除
find logs/ -name "*.log" -mtime +30 -delete

# 古いバックアップの削除
find backups/ -name "*.backup-*" -mtime +90 -delete
```

---

## データ管理

### 1. データのエクスポート

```bash
# 全データをCSVエクスポート
sqlite3 -header -csv data/db.sqlite3 "SELECT * FROM works;" > exports/works.csv
sqlite3 -header -csv data/db.sqlite3 "SELECT * FROM releases;" > exports/releases.csv

# 特定期間のデータをエクスポート
sqlite3 -header -csv data/db.sqlite3 "
SELECT * FROM releases
WHERE release_date BETWEEN '2025-01-01' AND '2025-12-31';" > exports/releases-2025.csv
```

### 2. データのインポート

```bash
# CSVからインポート
sqlite3 data/db.sqlite3 <<EOF
.mode csv
.import exports/works.csv works
.import exports/releases.csv releases
EOF
```

### 3. データのクリーンアップ

```bash
# 重複レコードの確認
sqlite3 data/db.sqlite3 "
SELECT work_id, release_type, number, platform, release_date, COUNT(*)
FROM releases
GROUP BY work_id, release_type, number, platform, release_date
HAVING COUNT(*) > 1;"

# 重複レコードの削除
python scripts/remove_duplicates.py

# 孤立レコードの削除
sqlite3 data/db.sqlite3 "
DELETE FROM releases
WHERE work_id NOT IN (SELECT id FROM works);"
```

---

## パフォーマンス最適化

### 1. データベースインデックスの追加

```sql
-- 頻繁に検索されるカラムにインデックスを追加
CREATE INDEX IF NOT EXISTS idx_releases_work_id ON releases(work_id);
CREATE INDEX IF NOT EXISTS idx_releases_release_date ON releases(release_date);
CREATE INDEX IF NOT EXISTS idx_releases_notified ON releases(notified);
CREATE INDEX IF NOT EXISTS idx_works_type ON works(type);
```

### 2. クエリの最適化

```bash
# スロークエリの特定
sqlite3 data/db.sqlite3 "EXPLAIN QUERY PLAN SELECT * FROM releases WHERE notified = 0;"

# インデックスの使用状況確認
sqlite3 data/db.sqlite3 "PRAGMA index_list('releases');"
sqlite3 data/db.sqlite3 "PRAGMA index_info('idx_releases_work_id');"
```

### 3. バッチ処理の最適化

```python
# config/.env で調整可能なパラメータ
BATCH_SIZE=100           # 一度に処理するレコード数
API_RATE_LIMIT=90        # APIレート制限
WORKER_THREADS=4         # 並列処理スレッド数
CACHE_TIMEOUT=3600       # キャッシュ有効期限 (秒)
```

### 4. 実行時間の監視

```bash
# 実行時間の記録
time python release_notifier.py

# 実行時間の推移を確認
grep "Execution time" logs/app.log | tail -n 30

# 平均実行時間の算出
grep "Execution time" logs/app.log | awk '{sum+=$NF; count++} END {print sum/count}'
```

---

## 緊急時の連絡先

### システム管理者
- **名前**: [管理者名]
- **メール**: admin@example.com
- **電話**: 000-0000-0000

### エスカレーション先
- **技術責任者**: tech-lead@example.com
- **運用責任者**: ops-lead@example.com

---

## 関連ドキュメント

- [デプロイガイド](deployment-guide.md)
- [トラブルシューティングガイド](../troubleshooting/troubleshooting-guide.md)
- [技術仕様書](../technical/system-specification.md)

---

## 改訂履歴

| 日付 | バージョン | 変更内容 | 担当者 |
|------|-----------|---------|--------|
| 2025-12-08 | 1.0.0 | 初版作成 | Documentation Manager |

---

*最終更新: 2025-12-08*
