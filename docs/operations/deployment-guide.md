# デプロイガイド

## 目次
1. [概要](#概要)
2. [前提条件](#前提条件)
3. [環境セットアップ](#環境セットアップ)
4. [依存関係のインストール](#依存関係のインストール)
5. [環境変数の設定](#環境変数の設定)
6. [データベースのセットアップ](#データベースのセットアップ)
7. [Google API認証設定](#google-api認証設定)
8. [デプロイ手順](#デプロイ手順)
9. [動作確認](#動作確認)
10. [ロールバック手順](#ロールバック手順)

---

## 概要

本ドキュメントは、MangaAnime-Info-delivery-systemを開発環境および本番環境にデプロイする手順を記載しています。

### システム要件
- OS: Ubuntu 20.04 LTS以上 / Debian 11以上
- Python: 3.9以上
- ストレージ: 最低5GB以上の空き容量
- メモリ: 最低2GB以上
- ネットワーク: インターネット接続必須

---

## 前提条件

### 必須ソフトウェア
- Python 3.9+
- pip (Python パッケージマネージャ)
- git
- cron (スケジューラ)
- SQLite3

### 必須アカウント
- Googleアカウント (Gmail API、Calendar API用)
- AniList API アクセス (無料)

### 権限要件
- システムのcrontab編集権限
- ファイルシステムの読み書き権限
- ネットワークポート使用権限

---

## 環境セットアップ

### 1. システムパッケージのインストール

```bash
# パッケージリストの更新
sudo apt update && sudo apt upgrade -y

# 必須パッケージのインストール
sudo apt install -y \
  python3 \
  python3-pip \
  python3-venv \
  git \
  sqlite3 \
  cron \
  curl \
  wget
```

### 2. プロジェクトのクローン

```bash
# プロジェクトディレクトリに移動
cd /mnt/Linux-ExHDD

# リポジトリのクローン (既存の場合はスキップ)
git clone https://github.com/yourusername/MangaAnime-Info-delivery-system.git

# プロジェクトディレクトリに移動
cd MangaAnime-Info-delivery-system
```

### 3. ディレクトリ構造の確認

```bash
# 必要なディレクトリの作成
mkdir -p data logs config credentials backups

# 権限の設定
chmod 755 data logs config
chmod 700 credentials
```

---

## 依存関係のインストール

### 1. Python仮想環境の作成

```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate

# pipのアップグレード
pip install --upgrade pip setuptools wheel
```

### 2. Pythonパッケージのインストール

```bash
# requirements.txtからインストール
pip install -r requirements.txt

# 主要パッケージ (requirements.txt例)
# requests==2.31.0
# feedparser==6.0.10
# google-auth==2.23.0
# google-auth-oauthlib==1.1.0
# google-auth-httplib2==0.1.1
# google-api-python-client==2.100.0
# python-dotenv==1.0.0
# schedule==1.2.0
```

### 3. インストール確認

```bash
# インストール済みパッケージの確認
pip list

# バージョン確認
python --version
pip --version
```

---

## 環境変数の設定

### 1. .envファイルの作成

```bash
# サンプルファイルをコピー
cp config/.env.example config/.env

# エディタで編集
nano config/.env
```

### 2. .envファイルの設定内容

```bash
# データベース設定
DATABASE_PATH=/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3

# ログ設定
LOG_LEVEL=INFO
LOG_PATH=/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs

# Google API認証情報
GOOGLE_CREDENTIALS_PATH=/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/credentials/credentials.json
GOOGLE_TOKEN_PATH=/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/credentials/token.json

# Gmail設定
GMAIL_SENDER=your-email@gmail.com
GMAIL_RECIPIENT=recipient-email@gmail.com

# Calendar設定
CALENDAR_ID=primary

# AniList API設定
ANILIST_API_URL=https://graphql.anilist.co

# フィルタリング設定
NG_KEYWORDS=エロ,R18,成人向け,BL,百合,ボーイズラブ

# スケジューラ設定
SCHEDULE_TIME=08:00
TIMEZONE=Asia/Tokyo

# 通知設定
NOTIFICATION_ENABLED=true
CALENDAR_SYNC_ENABLED=true

# デバッグモード
DEBUG_MODE=false
```

### 3. 環境変数の読み込み確認

```bash
# 環境変数の読み込みテスト
python -c "from dotenv import load_dotenv; load_dotenv('config/.env'); import os; print('DATABASE_PATH:', os.getenv('DATABASE_PATH'))"
```

---

## データベースのセットアップ

### 1. データベーススキーマの作成

```bash
# スキーマファイルの実行
sqlite3 data/db.sqlite3 < scripts/schema.sql

# または初期化スクリプトを実行
python scripts/init_database.py
```

### 2. データベース構造の確認

```bash
# テーブル一覧の確認
sqlite3 data/db.sqlite3 ".tables"

# スキーマの確認
sqlite3 data/db.sqlite3 ".schema works"
sqlite3 data/db.sqlite3 ".schema releases"
```

### 3. 初期データの投入 (オプション)

```bash
# テストデータの投入
python scripts/seed_test_data.py
```

---

## Google API認証設定

### 1. Google Cloud Consoleでの設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新規プロジェクトを作成
3. 「APIとサービス」→「ライブラリ」から以下を有効化:
   - Gmail API
   - Google Calendar API
4. 「認証情報」→「認証情報を作成」→「OAuthクライアントID」
5. アプリケーションの種類: デスクトップアプリ
6. `credentials.json` をダウンロード

### 2. 認証情報の配置

```bash
# ダウンロードしたファイルを配置
cp ~/Downloads/credentials.json credentials/credentials.json

# 権限の設定
chmod 600 credentials/credentials.json
```

### 3. OAuth認証の初回実行

```bash
# 認証スクリプトの実行
python scripts/authenticate_google.py

# ブラウザが開き、Googleアカウントでログイン
# 権限を許可すると token.json が生成される
```

### 4. 認証トークンの確認

```bash
# token.jsonの存在確認
ls -la credentials/token.json

# 権限の確認
chmod 600 credentials/token.json
```

---

## デプロイ手順

### 開発環境デプロイ

#### 1. 開発環境の起動

```bash
# 仮想環境の有効化
source venv/bin/activate

# 環境変数の読み込み
export $(cat config/.env | grep -v '#' | xargs)

# 開発モードで起動
DEBUG_MODE=true python app/main.py
```

#### 2. 手動実行テスト

```bash
# 情報収集のテスト
python modules/anime_anilist.py

# メール送信のテスト
python modules/mailer.py --test

# カレンダー登録のテスト
python modules/calendar.py --test
```

#### 3. 統合テストの実行

```bash
# 全体のテスト実行
python -m pytest tests/ -v

# カバレッジレポート付き
python -m pytest tests/ --cov=app --cov=modules
```

### 本番環境デプロイ

#### 1. 本番環境用設定の適用

```bash
# 本番環境用.envファイルの作成
cp config/.env config/.env.production

# 本番設定の編集
nano config/.env.production

# DEBUG_MODE=false に設定
# LOG_LEVEL=WARNING に設定
```

#### 2. デプロイスクリプトの実行

```bash
# デプロイスクリプトに実行権限を付与
chmod +x scripts/deploy.sh

# デプロイの実行
bash scripts/deploy.sh production
```

#### 3. cronジョブの設定

```bash
# crontabの編集
crontab -e

# 以下を追加 (毎朝8:00に実行)
0 8 * * * cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system && /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/venv/bin/python /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/release_notifier.py >> /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs/cron.log 2>&1

# cronサービスの再起動
sudo service cron restart

# cron設定の確認
crontab -l
```

#### 4. systemdサービス化 (推奨)

```bash
# サービスファイルの作成
sudo nano /etc/systemd/system/manga-anime-notifier.service
```

サービスファイルの内容:
```ini
[Unit]
Description=MangaAnime Info Delivery System
After=network.target

[Service]
Type=oneshot
User=your-username
WorkingDirectory=/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
Environment="PATH=/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/venv/bin"
ExecStart=/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/venv/bin/python /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/release_notifier.py
StandardOutput=append:/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs/service.log
StandardError=append:/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/logs/service-error.log

[Install]
WantedBy=multi-user.target
```

サービスの有効化:
```bash
# サービスの再読み込み
sudo systemctl daemon-reload

# サービスの有効化
sudo systemctl enable manga-anime-notifier.service

# 手動実行テスト
sudo systemctl start manga-anime-notifier.service

# ステータス確認
sudo systemctl status manga-anime-notifier.service
```

タイマーの設定 (cronの代替):
```bash
# タイマーファイルの作成
sudo nano /etc/systemd/system/manga-anime-notifier.timer
```

タイマーファイルの内容:
```ini
[Unit]
Description=MangaAnime Info Delivery System Timer
Requires=manga-anime-notifier.service

[Timer]
OnCalendar=daily
OnCalendar=08:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

タイマーの有効化:
```bash
# タイマーの有効化
sudo systemctl enable manga-anime-notifier.timer
sudo systemctl start manga-anime-notifier.timer

# タイマーの確認
sudo systemctl list-timers --all | grep manga-anime
```

---

## 動作確認

### 1. 基本動作確認

```bash
# データベース接続確認
python -c "from modules.db import get_connection; print('DB OK' if get_connection() else 'DB ERROR')"

# Google API接続確認
python scripts/test_google_apis.py

# 情報収集の動作確認
python modules/anime_anilist.py --limit 5
```

### 2. エンドツーエンドテスト

```bash
# 完全なフローのテスト実行
python release_notifier.py --dry-run

# 実際の通知テスト (少量データ)
python release_notifier.py --limit 3
```

### 3. ログの確認

```bash
# 最新のログを確認
tail -f logs/app.log

# エラーログのみ確認
tail -f logs/error.log

# cronログの確認
tail -f logs/cron.log
```

### 4. 監視コマンド

```bash
# プロセスの確認
ps aux | grep release_notifier

# ディスク使用量の確認
du -sh data/ logs/

# データベースサイズの確認
ls -lh data/db.sqlite3
```

---

## ロールバック手順

### 1. バックアップからの復元

```bash
# データベースの復元
cp backups/db.sqlite3.backup-YYYYMMDD data/db.sqlite3

# 設定ファイルの復元
cp backups/config/.env.backup-YYYYMMDD config/.env

# 認証情報の復元 (必要な場合)
cp backups/credentials/token.json.backup-YYYYMMDD credentials/token.json
```

### 2. Gitでの巻き戻し

```bash
# 特定のコミットへの巻き戻し
git log --oneline  # コミットハッシュを確認
git checkout <commit-hash>

# または直前のバージョンへ
git checkout HEAD~1

# 依存関係の再インストール
pip install -r requirements.txt
```

### 3. サービスの再起動

```bash
# cronの場合
sudo service cron restart

# systemdの場合
sudo systemctl restart manga-anime-notifier.service
```

### 4. 動作確認

```bash
# ロールバック後の動作確認
python release_notifier.py --dry-run

# ログの確認
tail -f logs/app.log
```

---

## セキュリティ考慮事項

### ファイル権限の設定

```bash
# 認証情報ディレクトリ
chmod 700 credentials/
chmod 600 credentials/*.json

# 設定ファイル
chmod 600 config/.env*

# ログディレクトリ
chmod 755 logs/
chmod 644 logs/*.log
```

### 定期的なセキュリティ更新

```bash
# システムパッケージの更新
sudo apt update && sudo apt upgrade -y

# Pythonパッケージの更新
pip list --outdated
pip install --upgrade <package-name>
```

---

## チェックリスト

### デプロイ前チェックリスト

- [ ] システム要件を満たしているか
- [ ] 必須ソフトウェアがインストールされているか
- [ ] Google API認証情報が準備されているか
- [ ] .envファイルが正しく設定されているか
- [ ] データベーススキーマが作成されているか
- [ ] テストが全て通過しているか
- [ ] バックアップが取得されているか

### デプロイ後チェックリスト

- [ ] データベース接続が正常か
- [ ] Google API認証が正常か
- [ ] 情報収集が正常に動作するか
- [ ] メール送信が正常に動作するか
- [ ] カレンダー登録が正常に動作するか
- [ ] cronジョブが設定されているか
- [ ] ログが正常に出力されているか
- [ ] エラーが発生していないか

---

## 関連ドキュメント

- [運用マニュアル](operation-manual.md)
- [トラブルシューティングガイド](../troubleshooting/troubleshooting-guide.md)
- [技術仕様書](../technical/system-specification.md)

---

*最終更新: 2025-12-08*
