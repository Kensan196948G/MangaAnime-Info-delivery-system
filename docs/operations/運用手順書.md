# MangaAnime情報配信システム - 運用手順書

## 📋 目次

1. [日常運用](#日常運用)
2. [監視・メンテナンス](#監視メンテナンス)
3. [障害対応](#障害対応)
4. [定期メンテナンス](#定期メンテナンス)
5. [パフォーマンス管理](#パフォーマンス管理)
6. [セキュリティ管理](#セキュリティ管理)
7. [バックアップ・復旧](#バックアップ復旧)

## 日常運用

### 📅 毎日の確認事項

#### 朝（9:00頃）- 自動実行結果確認

```bash
# 最新の実行ログ確認
cd /media/kensan/LinuxHDD/MangaAnime-Info-delivery-system
tail -n 50 logs/app.log

# 実行成功の確認
grep "✅ すべての処理が正常に完了しました" logs/app.log | tail -1

# エラーの確認
grep "ERROR\|❌" logs/app.log | tail -5
```

#### 確認ポイント

✅ **正常な場合の表示例**:
```
2025-08-08 08:00:15 - __main__ - INFO - ✅ すべての処理が正常に完了しました
```

❌ **異常な場合の対応**:
- エラーメッセージを確認
- 後述の[障害対応](#障害対応)を参照
- 必要に応じて手動実行

#### 通知確認

1. **Gmail受信確認**
   - 新しいリリース情報のメール受信
   - メール形式の確認（HTML表示）

2. **Googleカレンダー確認**
   - 新しいイベントの登録確認
   - イベント詳細の正確性確認

### 🔄 週次確認事項

#### 毎週月曜日（10:00頃）

```bash
# 週間統計の確認
grep "📊 実行結果レポート" logs/app.log | tail -7

# データベース状況確認
sqlite3 db.sqlite3 << EOF
SELECT COUNT(*) as total_works FROM works;
SELECT COUNT(*) as total_releases FROM releases;
SELECT COUNT(*) as unnotified_releases FROM releases WHERE notified = 0;
.quit
EOF
```

#### システム健全性チェック

```bash
# ディスク使用量確認
du -sh logs/
du -sh db.sqlite3

# 仮想環境確認
source venv/bin/activate
pip list | grep -E "google|requests|feedparser"
```

## 監視・メンテナンス

### 📊 監視項目

#### 1. システム稼働状況

**確認コマンド:**
```bash
# cron実行状況確認
grep "release_notifier" ./logs/system.log | tail -5

# プロセス確認
ps aux | grep python3 | grep release_notifier
```

**正常値:**
- 毎日8:00の実行が記録されている
- エラー終了していない

#### 2. データベース状況

**確認コマンド:**
```bash
# データベースサイズ確認
ls -lh db.sqlite3

# テーブル状況確認
sqlite3 db.sqlite3 << EOF
.schema
SELECT 
  'works' as table_name, COUNT(*) as count 
FROM works
UNION ALL
SELECT 
  'releases' as table_name, COUNT(*) as count 
FROM releases;
.quit
EOF
```

**正常値:**
- データベースサイズが異常に大きくない（< 100MB）
- データの増加が適切（1日あたり10-100件程度）

#### 3. ログファイル状況

**確認コマンド:**
```bash
# ログファイルサイズ確認
ls -lh logs/

# エラー頻度確認
grep -c "ERROR" logs/app.log
grep -c "WARNING" logs/app.log
```

**正常値:**
- ログファイルサイズが適切（< 10MB/月）
- ERRORが頻発していない（< 5回/日）

### 🔧 定期メンテナンス

#### 月次メンテナンス（毎月1日）

##### 1. ログローテーション

```bash
# 古いログの圧縮・削除
cd logs/
gzip app.log.1 app.log.2 app.log.3 2>/dev/null
find . -name "*.gz" -mtime +90 -delete

# 新しいログファイル作成
touch app.log
```

##### 2. データベース最適化

```bash
# データベース最適化
sqlite3 db.sqlite3 << EOF
VACUUM;
ANALYZE;
.quit
EOF

# 古いリリース情報のクリーンアップ（90日以上前）
sqlite3 db.sqlite3 << EOF
DELETE FROM releases 
WHERE created_at < date('now', '-90 days') 
AND notified = 1;
.quit
EOF
```

##### 3. 依存ライブラリ更新確認

```bash
source venv/bin/activate

# 更新可能なパッケージ確認
pip list --outdated

# セキュリティ更新の確認
pip install --upgrade pip
```

#### 四半期メンテナンス（3ヶ月毎）

##### 1. 設定ファイル見直し

```bash
# 設定ファイルのバックアップ
cp config.json config.json.backup.$(date +%Y%m%d)

# NGキーワードの見直し
# フィルタリング効果の確認
sqlite3 db.sqlite3 << EOF
SELECT COUNT(*) as filtered_count 
FROM releases 
WHERE created_at > date('now', '-90 days');
.quit
EOF
```

##### 2. Google API認証更新

```bash
# トークンの有効期限確認
python3 -c "
import json
from datetime import datetime
with open('token.json', 'r') as f:
    token = json.load(f)
exp = datetime.fromtimestamp(token.get('expiry', 0))
print(f'Token expires: {exp}')
if exp < datetime.now():
    print('⚠️ Token expired - need refresh')
else:
    print('✅ Token valid')
"
```

## 障害対応

### 🚨 障害分類と対応

#### レベル1: 軽微な警告

**症状:**
- WARNING レベルのログ出力
- 一部データソースの取得失敗

**対応手順:**
```bash
# 最新のWARNINGログ確認
grep "WARNING" logs/app.log | tail -10

# 手動実行でテスト
python3 release_notifier.py --dry-run --verbose
```

**対応例:**
- API一時的な障害 → 次回実行で自動復旧
- RSS フィード一時的な障害 → 後で再試行

#### レベル2: 機能障害

**症状:**
- ERROR レベルのログ出力
- メール通知が送信されない
- 特定機能の停止

**対応手順:**

1. **エラー内容確認**
```bash
grep "ERROR" logs/app.log | tail -5
```

2. **認証問題の場合**
```bash
# トークン再生成
rm token.json
python3 create_token_simple.py
# ブラウザで認証後
python3 generate_token.py
```

3. **ネットワーク問題の場合**
```bash
# 外部API接続確認
curl -s "https://graphql.anilist.co" -o /dev/null
echo "AniList API: $?"

# DNS確認
nslookup graphql.anilist.co
```

#### レベル3: システム停止

**症状:**
- 実行自体が失敗
- データベース破損
- 設定ファイル問題

**対応手順:**

1. **緊急復旧**
```bash
# バックアップからの復旧
cp db.sqlite3.backup db.sqlite3
cp config.json.backup config.json
```

2. **完全再初期化**
```bash
# 仮想環境再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# データベース再初期化
rm db.sqlite3
python3 release_notifier.py --dry-run
```

### 📞 エスカレーション

**レベル2以上の障害で解決しない場合:**
1. システムログ全体を確認
2. 設定ファイルの整合性確認
3. 開発者向け技術仕様書を参照

## パフォーマンス管理

### ⚡ パフォーマンス監視

#### 実行時間監視

```bash
# 過去7日間の実行時間確認
grep "実行時間:" logs/app.log | tail -7

# 平均実行時間計算
grep "実行時間:" logs/app.log | tail -30 | \
awk '{print $3}' | sed 's/秒//' | \
awk '{sum+=$1} END {print "平均実行時間:", sum/NR, "秒"}'
```

**正常値:** 10-30秒

#### メモリ使用量監視

```bash
# Python プロセスのメモリ使用量
ps aux | grep python3 | grep release_notifier | \
awk '{print "Memory: " $6/1024 " MB"}'
```

**正常値:** < 100MB

### 🔄 パフォーマンス最適化

#### データベース最適化

```bash
# インデックス確認・作成
sqlite3 db.sqlite3 << EOF
.schema
CREATE INDEX IF NOT EXISTS idx_releases_notified ON releases(notified);
CREATE INDEX IF NOT EXISTS idx_releases_created_at ON releases(created_at);
.quit
EOF
```

#### ログ最適化

```bash
# 設定でログレベル調整（config.json）
# "log_level": "INFO"  # DEBUG → INFO で出力量削減
```

## セキュリティ管理

### 🔒 セキュリティチェック項目

#### 毎月のセキュリティ監査

```bash
# ファイル権限確認
ls -la credentials.json token.json
# 適切: -rw------- (600)

# 設定ファイル内の機密情報確認
grep -i "password\|secret\|key" config.json
```

#### 認証トークンの管理

```bash
# トークンファイルの暗号化（推奨）
gpg --symmetric --cipher-algo AES256 token.json
rm token.json
# 使用時に復号化
```

### 🛡️ セキュリティ強化

#### ファイルシステム権限

```bash
# 適切な権限設定
chmod 700 /path/to/MangaAnime-Info-delivery-system
chmod 600 credentials.json token.json
chmod 644 config.json
```

#### ログファイルの保護

```bash
# ログディレクトリ権限
chmod 750 logs/
chmod 640 logs/*.log
```

## バックアップ・復旧

### 💾 バックアップ手順

#### 日次バックアップ（自動化推奨）

```bash
#!/bin/bash
# backup_daily.sh

BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d)
PROJECT_DIR="/media/kensan/LinuxHDD/MangaAnime-Info-delivery-system"

# バックアップディレクトリ作成
mkdir -p $BACKUP_DIR/$DATE

# 重要ファイルのバックアップ
cp $PROJECT_DIR/db.sqlite3 $BACKUP_DIR/$DATE/
cp $PROJECT_DIR/config.json $BACKUP_DIR/$DATE/
cp $PROJECT_DIR/credentials.json $BACKUP_DIR/$DATE/
cp $PROJECT_DIR/token.json $BACKUP_DIR/$DATE/

# ログファイルのバックアップ
tar -czf $BACKUP_DIR/$DATE/logs.tar.gz $PROJECT_DIR/logs/

# 古いバックアップ削除（30日以上前）
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR/$DATE"
```

#### cron設定例

```bash
# crontab -e に追加
0 2 * * * ./scripts/backup_daily.sh >> ./logs/backup.log 2>&1
```

### 🔧 復旧手順

#### 設定ファイル復旧

```bash
# 最新のバックアップから復旧
LATEST_BACKUP=$(ls -t /path/to/backups/ | head -1)
cp /path/to/backups/$LATEST_BACKUP/config.json ./
cp /path/to/backups/$LATEST_BACKUP/credentials.json ./
```

#### データベース復旧

```bash
# データベース復旧
cp /path/to/backups/$LATEST_BACKUP/db.sqlite3 ./

# 整合性確認
sqlite3 db.sqlite3 << EOF
PRAGMA integrity_check;
.quit
EOF
```

#### 完全システム復旧

```bash
# 1. バックアップからの復旧
cp -r /path/to/backups/$LATEST_BACKUP/* ./

# 2. 仮想環境再構築
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 権限設定
chmod 600 credentials.json token.json
chmod 755 *.py

# 4. テスト実行
python3 release_notifier.py --dry-run

# 5. 通知機能テスト
python3 test_notification.py
```

---

## 📞 緊急時連絡先

**システム管理者**: kensan1969@gmail.com  
**障害報告**: エラーログと実行環境情報を添付  
**定期点検**: 月次レポートの作成・保存

**重要**: 本運用手順書は定期的に見直し、システムの変更に合わせて更新してください。