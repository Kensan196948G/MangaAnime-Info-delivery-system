# トラブルシューティングガイド

## 目次
1. [概要](#概要)
2. [基本的なトラブルシューティング手順](#基本的なトラブルシューティング手順)
3. [API関連の問題](#api関連の問題)
4. [データベース関連の問題](#データベース関連の問題)
5. [認証関連の問題](#認証関連の問題)
6. [通知・メール関連の問題](#通知メール関連の問題)
7. [カレンダー関連の問題](#カレンダー関連の問題)
8. [スケジューリング関連の問題](#スケジューリング関連の問題)
9. [パフォーマンス関連の問題](#パフォーマンス関連の問題)
10. [システム関連の問題](#システム関連の問題)
11. [よくある質問 (FAQ)](#よくある質問-faq)
12. [ログの読み方](#ログの読み方)
13. [デバッグモードの使い方](#デバッグモードの使い方)

---

## 概要

本ドキュメントは、MangaAnime-Info-delivery-systemで発生する可能性のある問題とその解決方法を記載しています。

### トラブルシューティングの基本原則

1. **ログを確認する**: まず logs/app.log と logs/error.log を確認
2. **エラーメッセージを記録する**: 正確なエラーメッセージをメモ
3. **最近の変更を確認する**: 問題発生前に何か変更したか
4. **段階的に確認する**: 問題を切り分けて確認
5. **バックアップを取る**: 修正前に必ずバックアップ

---

## 基本的なトラブルシューティング手順

### Step 1: ログの確認

```bash
# 最新のエラーログを確認
tail -n 50 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs/error.log

# 本日のログからエラーを抽出
grep "$(date +%Y-%m-%d)" /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs/app.log | grep -i "error\|exception\|failed"

# 特定のエラーを検索
grep "ConnectionError" /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs/error.log
```

### Step 2: システム状態の確認

```bash
# ディスク容量の確認
df -h /mnt/Linux-ExHDD

# メモリ使用量の確認
free -h

# プロセスの確認
ps aux | grep python

# ネットワーク接続の確認
ping -c 3 google.com
```

### Step 3: 設定ファイルの確認

```bash
# .envファイルの存在確認
ls -la /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config/.env

# 必須環境変数の確認
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
source venv/bin/activate
python -c "
from dotenv import load_dotenv
import os
load_dotenv('config/.env')
print('DATABASE_PATH:', os.getenv('DATABASE_PATH'))
print('GOOGLE_CREDENTIALS_PATH:', os.getenv('GOOGLE_CREDENTIALS_PATH'))
print('GMAIL_SENDER:', os.getenv('GMAIL_SENDER'))
"
```

### Step 4: データベースの確認

```bash
# データベースファイルの存在確認
ls -lh /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3

# データベース整合性チェック
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 "PRAGMA integrity_check;"

# テーブルの存在確認
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 ".tables"
```

### Step 5: テスト実行

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
source venv/bin/activate

# ドライラン (実際の通知なし)
python release_notifier.py --dry-run

# デバッグモードで実行
DEBUG_MODE=true python release_notifier.py --limit 1
```

---

## API関連の問題

### 問題1: AniList API接続エラー

#### 症状
```
ERROR: Failed to connect to AniList API
ConnectionError: HTTPSConnectionPool
```

#### 原因
- インターネット接続の問題
- APIレート制限超過 (90リクエスト/分)
- AniList APIのダウンタイム

#### 解決方法

```bash
# 1. ネットワーク接続の確認
ping -c 3 graphql.anilist.co
curl -I https://graphql.anilist.co

# 2. APIレート制限の確認
grep "AniList API" logs/app.log | grep "$(date +%Y-%m-%d)" | wc -l

# 3. 一時的に待機してから再実行
sleep 60
python modules/anime_anilist.py --test

# 4. config/.env でリトライ設定を調整
API_RETRY_COUNT=3
API_RETRY_DELAY=5
```

### 問題2: しょぼいカレンダーAPI接続エラー

#### 症状
```
ERROR: Failed to fetch from Syobocal API
Timeout error
```

#### 原因
- APIサーバーの一時的な不調
- ネットワークタイムアウト

#### 解決方法

```bash
# 1. APIエンドポイントの確認
curl -I https://cal.syoboi.jp/json.php

# 2. タイムアウト設定の調整 (config/.env)
API_TIMEOUT=30

# 3. 手動でテスト実行
python -c "
import requests
response = requests.get('https://cal.syoboi.jp/json.php', timeout=10)
print(f'Status: {response.status_code}')
"
```

### 問題3: RSS取得エラー

#### 症状
```
ERROR: Failed to parse RSS feed
XMLSyntaxError
```

#### 原因
- RSSフィードのフォーマットエラー
- URLの変更
- サーバーダウン

#### 解決方法

```bash
# 1. RSSフィードの確認
curl -L "https://anime.dmkt-sp.jp/animestore/CF/rss/"

# 2. feedparserでのパース確認
python -c "
import feedparser
feed = feedparser.parse('https://anime.dmkt-sp.jp/animestore/CF/rss/')
print(f'Status: {feed.status if hasattr(feed, \"status\") else \"Unknown\"}')
print(f'Entries: {len(feed.entries)}')
"

# 3. URLの更新が必要な場合は config/.env を編集
RSS_FEED_URLS=https://new-url.com/rss/
```

---

## データベース関連の問題

### 問題1: データベースロックエラー

#### 症状
```
sqlite3.OperationalError: database is locked
```

#### 原因
- 複数のプロセスが同時にデータベースにアクセス
- 前回の処理が正常終了していない

#### 解決方法

```bash
# 1. データベースをロックしているプロセスを確認
lsof /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3

# 2. プロセスの強制終了
kill -9 <PID>

# 3. ロックファイルの削除 (注意: プロセスがいないことを確認)
rm -f /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3-journal
rm -f /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3-wal
rm -f /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3-shm

# 4. データベース整合性チェック
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 "PRAGMA integrity_check;"

# 5. タイムアウト設定の調整 (modules/db.py)
# connection.execute("PRAGMA busy_timeout = 30000")
```

### 問題2: データベース破損

#### 症状
```
sqlite3.DatabaseError: database disk image is malformed
PRAGMA integrity_check の結果がエラー
```

#### 原因
- ディスク障害
- システムクラッシュ中の書き込み
- ファイルシステムエラー

#### 解決方法

```bash
# 1. データベースのバックアップを取得
cp /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 \
   /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3.corrupted-$(date +%Y%m%d-%H%M%S)

# 2. SQLiteの修復を試みる
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 ".dump" | \
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db-recovered.sqlite3

# 3. 修復したデータベースを確認
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db-recovered.sqlite3 "PRAGMA integrity_check;"

# 4. データ件数を確認
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db-recovered.sqlite3 \
  "SELECT COUNT(*) FROM works; SELECT COUNT(*) FROM releases;"

# 5. 問題なければリプレース
mv /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 \
   /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3.old
mv /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db-recovered.sqlite3 \
   /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3

# 6. 修復できない場合はバックアップから復元
cp /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/backups/db.sqlite3.backup-YYYYMMDD \
   /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3
```

### 問題3: テーブルが存在しない

#### 症状
```
sqlite3.OperationalError: no such table: works
```

#### 原因
- データベースの初期化が未実施
- スキーマファイルの実行漏れ

#### 解決方法

```bash
# 1. テーブルの存在確認
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 ".tables"

# 2. スキーマファイルの実行
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 < \
  /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/scripts/schema.sql

# 3. または初期化スクリプトの実行
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
source venv/bin/activate
python scripts/init_database.py

# 4. テーブルが作成されたか確認
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 ".schema works"
```

---

## 認証関連の問題

### 問題1: Google API認証エラー

#### 症状
```
google.auth.exceptions.RefreshError: invalid_grant
Token has been expired or revoked
```

#### 原因
- アクセストークンの有効期限切れ
- 認証情報の取り消し
- credentials.json の不備

#### 解決方法

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

# 1. 既存トークンのバックアップ
cp credentials/token.json credentials/token.json.backup-$(date +%Y%m%d-%H%M%S)

# 2. トークンファイルの削除
rm credentials/token.json

# 3. 再認証の実行
source venv/bin/activate
python scripts/authenticate_google.py

# 4. ブラウザで認証フローを完了

# 5. トークンが生成されたか確認
ls -la credentials/token.json

# 6. 権限の設定
chmod 600 credentials/token.json
```

### 問題2: credentials.jsonが見つからない

#### 症状
```
FileNotFoundError: credentials/credentials.json not found
```

#### 原因
- Google Cloud Consoleからのダウンロード漏れ
- ファイルパスの誤り

#### 解決方法

```bash
# 1. ファイルの存在確認
ls -la /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/credentials/credentials.json

# 2. 存在しない場合、Google Cloud Consoleから再ダウンロード
# https://console.cloud.google.com/apis/credentials

# 3. ダウンロードしたファイルを配置
cp ~/Downloads/credentials.json \
   /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/credentials/credentials.json

# 4. 権限の設定
chmod 600 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/credentials/credentials.json

# 5. .envファイルのパス確認
grep GOOGLE_CREDENTIALS_PATH /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config/.env
```

### 問題3: OAuth2スコープ不足

#### 症状
```
google.auth.exceptions.InsufficientScopeError:
Request had insufficient authentication scopes
```

#### 原因
- 必要なAPIスコープが設定されていない
- 認証時のスコープ不足

#### 解決方法

```bash
# 1. 必要なスコープを確認 (scripts/authenticate_google.py)
# SCOPES = [
#     'https://www.googleapis.com/auth/gmail.send',
#     'https://www.googleapis.com/auth/calendar'
# ]

# 2. トークンを削除して再認証
rm /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/credentials/token.json

# 3. 再認証
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
source venv/bin/activate
python scripts/authenticate_google.py

# 4. 認証画面で全ての権限を許可
```

---

## 通知・メール関連の問題

### 問題1: メール送信失敗

#### 症状
```
ERROR: Failed to send email
SMTPException: Authentication failed
```

#### 原因
- Gmail APIの認証エラー
- 送信者メールアドレスの不一致
- APIクォータ超過

#### 解決方法

```bash
# 1. 送信者メールアドレスの確認
grep GMAIL_SENDER /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config/.env

# 2. トークンの再発行
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
source venv/bin/activate
rm credentials/token.json
python scripts/authenticate_google.py

# 3. テストメール送信
python modules/mailer.py --test

# 4. Gmail APIクォータの確認
# https://console.cloud.google.com/apis/api/gmail.googleapis.com/quotas

# 5. ログで詳細確認
grep "Email" logs/app.log | tail -n 20
```

### 問題2: メールが届かない

#### 症状
- エラーは出ないがメールが届かない
- ログには成功と表示される

#### 原因
- スパムフォルダに振り分けられている
- メールアドレスの誤り
- Gmail側のフィルタリング

#### 解決方法

```bash
# 1. 受信者メールアドレスの確認
grep GMAIL_RECIPIENT /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config/.env

# 2. Gmailのスパムフォルダを確認

# 3. 送信履歴の確認 (Gmailの送信済みアイテム)

# 4. テストメールを自分宛に送信
export GMAIL_RECIPIENT="your-email@gmail.com"
python modules/mailer.py --test

# 5. メールヘッダーの確認 (SPF, DKIM設定)
```

### 問題3: HTML形式のメールが正しく表示されない

#### 症状
- メールがテキストのみで表示される
- レイアウトが崩れる

#### 原因
- HTMLタグのエスケープ不足
- MIMEタイプの設定ミス

#### 解決方法

```python
# modules/mailer.py を確認

# 1. MIMEタイプの設定確認
message = MIMEMultipart('alternative')

# 2. HTML部分の設定確認
html_part = MIMEText(html_content, 'html', 'utf-8')
message.attach(html_part)

# 3. テンプレートの確認
cat templates/email_template.html
```

---

## カレンダー関連の問題

### 問題1: カレンダー登録失敗

#### 症状
```
ERROR: Failed to create calendar event
HttpError 403: Forbidden
```

#### 原因
- Calendar APIの権限不足
- カレンダーIDの誤り
- APIクォータ超過

#### 解決方法

```bash
# 1. カレンダーIDの確認
grep CALENDAR_ID /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config/.env

# 2. カレンダーへのアクセス権限確認
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
source venv/bin/activate
python -c "
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file('credentials/token.json')
service = build('calendar', 'v3', credentials=creds)
calendars = service.calendarList().list().execute()
for cal in calendars.get('items', []):
    print(f'{cal[\"summary\"]}: {cal[\"id\"]}')
"

# 3. トークンの再発行
rm credentials/token.json
python scripts/authenticate_google.py

# 4. テストイベント作成
python modules/calendar.py --test

# 5. APIクォータの確認
# https://console.cloud.google.com/apis/api/calendar-json.googleapis.com/quotas
```

### 問題2: イベントが重複登録される

#### 症状
- 同じイベントが複数回登録される
- カレンダーが同じイベントで埋まる

#### 原因
- 重複チェックロジックの不備
- データベースのnotifiedフラグ更新漏れ

#### 解決方法

```bash
# 1. データベースで重複確認
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 "
SELECT work_id, release_type, number, platform, release_date, COUNT(*)
FROM releases
GROUP BY work_id, release_type, number, platform, release_date
HAVING COUNT(*) > 1;"

# 2. 重複レコードの削除
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
source venv/bin/activate
python scripts/remove_duplicates.py

# 3. notifiedフラグの確認
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 "
SELECT COUNT(*) FROM releases WHERE notified = 0;"

# 4. カレンダーの重複イベント削除 (手動)
# Googleカレンダーのウェブインターフェースから削除
```

### 問題3: 日時のタイムゾーンがおかしい

#### 症状
- イベントの時刻が9時間ずれる
- JST以外のタイムゾーンで登録される

#### 原因
- タイムゾーン設定の誤り
- UTCとJSTの変換ミス

#### 解決方法

```bash
# 1. システムのタイムゾーン確認
timedatectl
date

# 2. .envファイルのタイムゾーン設定確認
grep TIMEZONE /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config/.env

# 3. Pythonスクリプトでの確認
python -c "
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz

load_dotenv('config/.env')
tz = pytz.timezone(os.getenv('TIMEZONE', 'Asia/Tokyo'))
now = datetime.now(tz)
print(f'Current time: {now}')
print(f'Timezone: {now.tzinfo}')
"

# 4. modules/calendar.py のタイムゾーン設定を確認・修正
```

---

## スケジューリング関連の問題

### 問題1: cronジョブが実行されない

#### 症状
- 指定時刻になってもスクリプトが実行されない
- ログに実行記録がない

#### 原因
- crontabの設定ミス
- cronサービスの停止
- パス設定の誤り

#### 解決方法

```bash
# 1. crontabの確認
crontab -l

# 2. cronサービスの状態確認
sudo systemctl status cron

# 3. cronサービスの起動
sudo systemctl start cron
sudo systemctl enable cron

# 4. crontabの再設定
crontab -e

# 正しい設定例:
# 0 8 * * * cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system && /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/venv/bin/python /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/release_notifier.py >> /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs/cron.log 2>&1

# 5. cronログの確認
tail -f /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs/cron.log
grep CRON /var/log/syslog | tail -n 20
```

### 問題2: systemdタイマーが動作しない

#### 症状
- タイマーが起動しない
- サービスが実行されない

#### 原因
- サービスファイルの設定ミス
- タイマーが有効化されていない

#### 解決方法

```bash
# 1. サービスの状態確認
sudo systemctl status manga-anime-notifier.service
sudo systemctl status manga-anime-notifier.timer

# 2. タイマー一覧の確認
sudo systemctl list-timers --all | grep manga-anime

# 3. サービスの手動実行テスト
sudo systemctl start manga-anime-notifier.service

# 4. ログの確認
sudo journalctl -u manga-anime-notifier.service -n 50

# 5. タイマーの有効化
sudo systemctl enable manga-anime-notifier.timer
sudo systemctl start manga-anime-notifier.timer

# 6. 設定ファイルの再読み込み
sudo systemctl daemon-reload
```

### 問題3: スクリプトが途中で止まる

#### 症状
- 処理が完了せずに途中で終了する
- タイムアウトエラーが発生する

#### 原因
- API接続のタイムアウト
- メモリ不足
- 処理時間の超過

#### 解決方法

```bash
# 1. ログで停止箇所を特定
grep "$(date +%Y-%m-%d)" /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs/app.log

# 2. メモリ使用量の確認
free -h
ps aux | grep python | awk '{print $6}' # メモリ使用量(KB)

# 3. タイムアウト設定の調整 (config/.env)
API_TIMEOUT=60
SCRIPT_TIMEOUT=3600

# 4. バッチサイズの削減
BATCH_SIZE=50

# 5. デバッグモードで段階的に実行
DEBUG_MODE=true python release_notifier.py --limit 10
```

---

## パフォーマンス関連の問題

### 問題1: 実行時間が長すぎる

#### 症状
- スクリプトの実行に30分以上かかる
- タイムアウトが発生する

#### 原因
- データ量の増加
- 非効率なクエリ
- APIレート制限

#### 解決方法

```bash
# 1. 実行時間の計測
time python /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/release_notifier.py

# 2. ボトルネックの特定 (プロファイリング)
python -m cProfile -o profile.stats /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/release_notifier.py

python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative')
p.print_stats(20)
"

# 3. データベースクエリの最適化
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 "
CREATE INDEX IF NOT EXISTS idx_releases_notified ON releases(notified);
CREATE INDEX IF NOT EXISTS idx_releases_release_date ON releases(release_date);
"

# 4. バッチ処理の調整 (config/.env)
BATCH_SIZE=100
WORKER_THREADS=4

# 5. キャッシュの活用
CACHE_ENABLED=true
CACHE_TIMEOUT=3600
```

### 問題2: メモリ使用量が多い

#### 症状
- メモリ不足エラー
- システムがスワップを使用

#### 原因
- 大量のデータを一度にメモリに読み込む
- メモリリークの可能性

#### 解決方法

```bash
# 1. メモリ使用量の監視
python -c "
import psutil
import os

process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"

# 2. バッチサイズの削減
# config/.env
BATCH_SIZE=50

# 3. ガベージコレクションの強制実行 (スクリプトに追加)
import gc
gc.collect()

# 4. ジェネレータの使用 (大量データの処理)
# for文でデータを1件ずつ処理

# 5. システムメモリの増設を検討
```

### 問題3: データベースが肥大化

#### 症状
- db.sqlite3のサイズが数GB
- クエリが遅い

#### 原因
- 古いデータの蓄積
- VACUUMの未実行

#### 解決方法

```bash
# 1. データベースサイズの確認
du -sh /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3

# 2. レコード数の確認
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 "
SELECT 'works' as table_name, COUNT(*) as count FROM works
UNION ALL
SELECT 'releases', COUNT(*) FROM releases;"

# 3. 古いデータのアーカイブ (6ヶ月以上前)
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
source venv/bin/activate
python scripts/archive_old_data.py --months 6

# 4. VACUUMの実行
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 "VACUUM;"

# 5. サイズの再確認
du -sh /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3
```

---

## システム関連の問題

### 問題1: ディスク容量不足

#### 症状
```
OSError: [Errno 28] No space left on device
```

#### 原因
- ログファイルの肥大化
- バックアップファイルの蓄積
- データベースの肥大化

#### 解決方法

```bash
# 1. ディスク使用量の確認
df -h /mnt/Linux-ExHDD

# 2. 大きなファイルの検索
du -sh /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/* | sort -h

# 3. ログファイルの削除
find /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs -name "*.log" -mtime +30 -delete

# 4. 古いバックアップの削除
find /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/backups -name "*.backup-*" -mtime +90 -delete

# 5. ログローテーションの設定
sudo logrotate -f /etc/logrotate.d/manga-anime-notifier
```

### 問題2: パーミッションエラー

#### 症状
```
PermissionError: [Errno 13] Permission denied
```

#### 原因
- ファイル・ディレクトリの権限不足
- 所有者の不一致

#### 解決方法

```bash
# 1. 現在の権限確認
ls -la /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/

# 2. 所有者の確認
stat /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3

# 3. 権限の修正
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
chmod 755 .
chmod 755 data logs config
chmod 644 data/db.sqlite3
chmod 700 credentials
chmod 600 credentials/*.json
chmod 600 config/.env

# 4. 所有者の変更 (必要な場合)
sudo chown -R your-username:your-username /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
```

### 問題3: Python環境の問題

#### 症状
```
ModuleNotFoundError: No module named 'requests'
```

#### 原因
- 仮想環境が有効化されていない
- パッケージのインストール漏れ

#### 解決方法

```bash
# 1. 仮想環境の確認
which python
python --version

# 2. 仮想環境の有効化
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
source venv/bin/activate

# 3. パッケージのインストール確認
pip list

# 4. 不足パッケージのインストール
pip install -r requirements.txt

# 5. 仮想環境の再作成 (最終手段)
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## よくある質問 (FAQ)

### Q1: メールが毎日同じ内容で送られてくる

**A:** データベースのnotifiedフラグが更新されていない可能性があります。

```bash
# 1. notifiedフラグの確認
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 "
SELECT COUNT(*) FROM releases WHERE notified = 1;"

# 2. 手動でフラグを更新
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3 "
UPDATE releases SET notified = 1 WHERE id IN (
  SELECT id FROM releases ORDER BY created_at DESC LIMIT 100
);"
```

### Q2: 特定の作品を通知から除外したい

**A:** NGキーワードリストに追加します。

```bash
# config/.env を編集
nano /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/config/.env

# NG_KEYWORDSに追加
NG_KEYWORDS=エロ,R18,成人向け,BL,百合,ボーイズラブ,除外したい作品名
```

### Q3: カレンダーに色を付けたい

**A:** modules/calendar.py で colorId を設定します。

```python
# modules/calendar.py
event = {
    'summary': title,
    'start': {'dateTime': start_time, 'timeZone': 'Asia/Tokyo'},
    'end': {'dateTime': end_time, 'timeZone': 'Asia/Tokyo'},
    'colorId': '1',  # 1-11の数字でカラー指定
}
```

### Q4: 実行時刻を変更したい

**A:** crontab または systemd timer を編集します。

```bash
# cronの場合
crontab -e
# 0 8 * * * を 0 20 * * * (20:00) などに変更

# systemdの場合
sudo nano /etc/systemd/system/manga-anime-notifier.timer
# OnCalendar=08:00:00 を OnCalendar=20:00:00 に変更
sudo systemctl daemon-reload
sudo systemctl restart manga-anime-notifier.timer
```

### Q5: テスト実行したい

**A:** --dry-run オプションを使用します。

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
source venv/bin/activate
python release_notifier.py --dry-run --limit 5
```

---

## ログの読み方

### ログレベルの意味

- **DEBUG**: デバッグ情報 (開発時のみ)
- **INFO**: 正常な処理の記録
- **WARNING**: 警告 (処理は継続)
- **ERROR**: エラー (一部機能が失敗)
- **CRITICAL**: 重大なエラー (システム停止の可能性)

### ログの典型的なパターン

#### 正常実行
```
2025-12-08 08:00:01 INFO Starting release notifier
2025-12-08 08:00:05 INFO Fetched 45 works from AniList
2025-12-08 08:00:10 INFO Fetched 234 releases from Syobocal
2025-12-08 08:00:15 INFO Database updated: 279 new releases
2025-12-08 08:00:20 INFO Email sent successfully to user@example.com
2025-12-08 08:00:25 INFO Calendar synced: 279 events created
2025-12-08 08:00:30 INFO Execution completed in 29 seconds
```

#### エラー発生
```
2025-12-08 08:00:01 INFO Starting release notifier
2025-12-08 08:00:05 ERROR Failed to connect to AniList API
2025-12-08 08:00:05 ERROR ConnectionError: HTTPSConnectionPool
2025-12-08 08:00:05 WARNING Retrying in 5 seconds...
2025-12-08 08:00:10 INFO Successfully connected to AniList API
```

---

## デバッグモードの使い方

### デバッグモードの有効化

```bash
# 1. 環境変数で有効化
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
source venv/bin/activate
DEBUG_MODE=true python release_notifier.py

# 2. .envファイルで恒久的に有効化
nano config/.env
# DEBUG_MODE=true に変更

# 3. ログレベルの変更
LOG_LEVEL=DEBUG
```

### デバッグ出力の例

```
2025-12-08 08:00:01 DEBUG Loading environment variables
2025-12-08 08:00:01 DEBUG DATABASE_PATH: /mnt/Linux-ExHDD/...
2025-12-08 08:00:02 DEBUG Connecting to database
2025-12-08 08:00:02 DEBUG Database connection established
2025-12-08 08:00:03 DEBUG Executing query: SELECT * FROM works
2025-12-08 08:00:03 DEBUG Query returned 1234 rows
```

---

## サポートとエスカレーション

### 問題が解決しない場合

1. ログファイルを保存
2. エラーメッセージを記録
3. 実行環境の情報を収集
4. 以下の連絡先に問い合わせ

### システム情報の収集

```bash
# システム情報の収集スクリプト
bash /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/scripts/collect_diagnostic_info.sh

# 生成されたファイルをサポートに送付
# diagnostic-info-YYYYMMDD-HHMMSS.tar.gz
```

### 連絡先

- **技術サポート**: tech-support@example.com
- **緊急連絡先**: emergency@example.com

---

## 関連ドキュメント

- [デプロイガイド](../operations/deployment-guide.md)
- [運用マニュアル](../operations/operation-manual.md)
- [技術仕様書](../technical/system-specification.md)

---

*最終更新: 2025-12-08*
