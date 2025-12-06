# デプロイメントガイド

**対象システム**: MangaAnime Info Delivery System
**最終更新**: 2025-12-06
**作成者**: DevOps Engineer Agent

---

## 目次

1. [前提条件](#前提条件)
2. [初回セットアップ](#初回セットアップ)
3. [デプロイ手順](#デプロイ手順)
4. [ロールバック手順](#ロールバック手順)
5. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

### サーバー要件

- **OS**: Ubuntu 20.04 LTS以上
- **CPU**: 2コア以上
- **メモリ**: 4GB以上
- **ディスク**: 20GB以上の空き容量

### 必要なソフトウェア

```bash
# Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Git
sudo apt-get install git

# その他
sudo apt-get install curl wget
```

### 必要な認証情報

- GitHub Personal Access Token（プライベートリポジトリの場合）
- Google API認証情報（Gmail、Calendar）
- SSH鍵（本番サーバーアクセス用）

---

## 初回セットアップ

### 1. プロジェクトのクローン

```bash
# プロジェクトディレクトリの作成
sudo mkdir -p /opt/mangaanime-system
sudo chown $USER:$USER /opt/mangaanime-system

# Gitクローン
cd /opt
git clone https://github.com/your-org/MangaAnime-Info-delivery-system.git mangaanime-system
cd mangaanime-system
```

### 2. 環境変数の設定

```bash
# .envファイルの作成
cp env.example .env

# .envファイルを編集
nano .env
```

**必須設定項目**:

```bash
ENVIRONMENT=production
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
CALENDAR_API_KEY=your_api_key
NOTIFICATION_EMAIL=your-email@example.com
SECRET_KEY=generate_strong_random_key_here
```

### 3. Google API認証設定

```bash
# 認証情報ファイルの配置
mkdir -p config
cp /path/to/gmail_credentials.json config/
cp /path/to/calendar_credentials.json config/

# 権限設定
chmod 600 config/*.json
```

### 4. ディレクトリ構造の準備

```bash
# 必要なディレクトリを作成
mkdir -p data logs config

# 権限設定
chmod 755 data logs
chmod 700 config
```

### 5. 初回ビルドと起動

```bash
# Dockerイメージのビルド
docker-compose -f docker-compose.prod.yml build

# サービスの起動
docker-compose -f docker-compose.prod.yml up -d

# ログ確認
docker-compose -f docker-compose.prod.yml logs -f
```

### 6. 動作確認

```bash
# コンテナの状態確認
docker-compose -f docker-compose.prod.yml ps

# ヘルスチェック
curl http://localhost:8000/health

# ログ確認
tail -f logs/app.log
```

---

## デプロイ手順

### 方法1: GitHub Actionsによる自動デプロイ（推奨）

#### ステップ1: GitHub Secretsの設定

リポジトリの `Settings > Secrets and variables > Actions` で以下を設定：

```
DEPLOY_HOST=your-server.example.com
DEPLOY_USER=deploy
DEPLOY_SSH_KEY=<SSH秘密鍵の内容>
DEPLOY_PORT=22
GMAIL_CLIENT_ID=<値>
GMAIL_CLIENT_SECRET=<値>
CALENDAR_API_KEY=<値>
NOTIFICATION_EMAIL=<値>
PRODUCTION_URL=https://your-production-url.com
SLACK_WEBHOOK=<Slack Webhook URL（任意）>
```

#### ステップ2: タグを作成してプッシュ

```bash
# バージョンタグを作成
git tag v1.0.0

# タグをプッシュ（これで自動デプロイが開始）
git push origin v1.0.0
```

#### ステップ3: デプロイの監視

GitHub Actionsのページでワークフローの進行状況を確認：

```
https://github.com/your-org/MangaAnime-Info-delivery-system/actions
```

### 方法2: 手動デプロイ

#### サーバーにSSH接続

```bash
ssh user@your-server.example.com
cd /opt/mangaanime-system
```

#### デプロイスクリプトの実行

```bash
# スクリプトに実行権限を付与
chmod +x scripts/deploy.sh

# デプロイ実行
sudo ./scripts/deploy.sh
```

#### デプロイの流れ

1. 現在の状態をバックアップ
2. サービス停止
3. 最新Dockerイメージをプル
4. サービス起動
5. ヘルスチェック
6. クリーンアップ

---

## ロールバック手順

### 自動ロールバック

デプロイスクリプトは、ヘルスチェック失敗時に自動的にロールバックします。

### 手動ロールバック

#### 利用可能なバックアップの確認

```bash
sudo ./scripts/rollback.sh
```

出力例：
```
Available backups:
1. backup-20251206-143022 (Dec 6 14:30)
2. backup-20251205-083015 (Dec 5 08:30)
3. backup-20251204-083012 (Dec 4 08:30)
```

#### バックアップからの復元

```bash
# インタラクティブモード
sudo ./scripts/rollback.sh

# 直接指定
sudo ./scripts/rollback.sh backup-20251206-143022
```

#### 手動でのロールバック

```bash
cd /opt/mangaanime-system

# 現在のコンテナを停止
docker-compose -f docker-compose.prod.yml down

# 特定のバージョンに戻す
git checkout v1.0.0

# 再ビルドと起動
docker-compose -f docker-compose.prod.yml up -d --build

# ヘルスチェック
curl http://localhost:8000/health
```

---

## トラブルシューティング

### 問題1: コンテナが起動しない

**症状**:
```bash
docker-compose ps
# コンテナが "Exited" 状態
```

**解決方法**:

```bash
# ログを確認
docker-compose -f docker-compose.prod.yml logs app

# 一般的な原因
# 1. 環境変数の設定ミス
nano .env

# 2. ポートの競合
sudo netstat -tulpn | grep 8000

# 3. 権限の問題
sudo chown -R $USER:$USER data/ logs/
```

### 問題2: データベース接続エラー

**症状**:
```
sqlite3.OperationalError: unable to open database file
```

**解決方法**:

```bash
# ディレクトリの確認
ls -la data/

# ディレクトリの作成
mkdir -p data

# 権限の設定
chmod 755 data/

# コンテナの再起動
docker-compose -f docker-compose.prod.yml restart
```

### 問題3: Gmail/Calendar API認証エラー

**症状**:
```
google.auth.exceptions.RefreshError
```

**解決方法**:

```bash
# 認証情報ファイルの確認
ls -la config/*.json

# ファイルのパーミッション
chmod 600 config/*.json

# 認証トークンの再生成
rm config/gmail_token.json config/calendar_token.json

# アプリケーションを再起動して再認証
docker-compose -f docker-compose.prod.yml restart
```

### 問題4: メモリ不足

**症状**:
```
docker: Error response from daemon: OOM command not allowed
```

**解決方法**:

```bash
# メモリ使用状況の確認
free -h
docker stats

# 不要なコンテナ・イメージの削除
docker system prune -a

# スワップの追加（必要に応じて）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 問題5: デプロイ後にサービスが応答しない

**チェックリスト**:

```bash
# 1. コンテナの状態
docker-compose -f docker-compose.prod.yml ps

# 2. ログの確認
docker-compose -f docker-compose.prod.yml logs --tail=100

# 3. ポートのリスニング状態
sudo netstat -tulpn | grep 8000

# 4. ファイアウォールの確認
sudo ufw status

# 5. ヘルスチェックエンドポイント
curl -v http://localhost:8000/health
```

---

## ベストプラクティス

### デプロイ前

- [ ] 全てのテストがパスしていることを確認
- [ ] ステージング環境でテスト済み
- [ ] データベースのバックアップを取得
- [ ] ロールバック手順を確認

### デプロイ中

- [ ] デプロイ通知をチームに送信
- [ ] ログをリアルタイムで監視
- [ ] ヘルスチェックの結果を確認

### デプロイ後

- [ ] 主要機能の動作確認
- [ ] エラーログのチェック
- [ ] パフォーマンスメトリクスの確認
- [ ] デプロイ完了通知

---

## 緊急時の連絡先

- **システム管理者**: admin@example.com
- **開発チーム**: dev-team@example.com
- **Slack**: #mangaanime-alerts

---

## 関連ドキュメント

- [運用マニュアル](./OPERATIONS_MANUAL.md)
- [セキュリティガイドライン](./SECURITY_GUIDELINES.md)
- [モニタリング設定](./MONITORING_SETUP.md)

---

**注意**: このガイドは定期的に更新してください。変更があった場合は必ず文書化してください。
