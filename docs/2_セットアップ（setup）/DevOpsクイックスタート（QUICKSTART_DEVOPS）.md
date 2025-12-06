# DevOps クイックスタートガイド

**MangaAnime Info Delivery System**

このガイドでは、最短でDocker環境をセットアップし、CI/CDパイプラインを稼働させる手順を説明します。

---

## ⚡ 3ステップで開始

### Step 1: リポジトリのクローン

```bash
git clone https://github.com/your-org/MangaAnime-Info-delivery-system.git
cd MangaAnime-Info-delivery-system
```

### Step 2: 環境変数の設定

```bash
# テンプレートをコピー
cp env.example .env

# 必須項目を編集
nano .env
```

最低限必要な設定:
```bash
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
NOTIFICATION_EMAIL=your-email@example.com
```

### Step 3: Docker起動

```bash
# ビルドして起動
docker-compose up -d

# ログ確認
docker-compose logs -f
```

**完了!** アプリケーションが起動しました。

---

## 🐳 Docker コマンド集

### 基本操作

```bash
# ビルド
docker-compose build

# 起動（デタッチモード）
docker-compose up -d

# 起動（ログ表示）
docker-compose up

# 停止
docker-compose down

# 停止（ボリューム削除）
docker-compose down -v

# 再起動
docker-compose restart

# ログ確認
docker-compose logs -f [service_name]

# コンテナ一覧
docker-compose ps

# コンテナに入る
docker-compose exec app bash
```

### よく使うコマンド

```bash
# アプリケーションのみ再起動
docker-compose restart app

# データベースのリセット
docker-compose down -v
docker-compose up -d

# 全コンテナのログ
docker-compose logs --tail=100

# 特定サービスのログ
docker-compose logs -f scheduler
```

---

## 🔧 トラブルシューティング

### コンテナが起動しない

```bash
# ログを確認
docker-compose logs

# コンテナの状態を確認
docker-compose ps

# 強制的に再ビルド
docker-compose up -d --build --force-recreate
```

### ポートが使用中

```bash
# ポート8000を使用しているプロセスを確認
sudo lsof -i :8000

# または
sudo netstat -tulpn | grep 8000

# .envでポートを変更
APP_PORT=8080
```

### 環境変数が反映されない

```bash
# .envファイルを確認
cat .env

# コンテナを完全に再作成
docker-compose down
docker-compose up -d
```

---

## 🚀 GitHub Actions セットアップ

### 1. GitHub Secrets設定

リポジトリの `Settings > Secrets and variables > Actions` で設定:

**必須**:
```
GMAIL_CLIENT_ID
GMAIL_CLIENT_SECRET
CALENDAR_API_KEY
NOTIFICATION_EMAIL
```

**デプロイ用（本番環境がある場合）**:
```
DEPLOY_HOST
DEPLOY_USER
DEPLOY_SSH_KEY
PRODUCTION_URL
```

### 2. ワークフロー有効化

`.github/workflows/`のYAMLファイルがリポジトリにプッシュされていることを確認。

### 3. 動作確認

```bash
# PRを作成してCIが実行されることを確認
git checkout -b test-ci
git commit --allow-empty -m "test: CI実行テスト"
git push origin test-ci

# GitHub Actionsタブで確認
# https://github.com/your-org/MangaAnime-Info-delivery-system/actions
```

---

## 📋 チェックリスト

### 初回セットアップ

- [ ] リポジトリをクローンした
- [ ] .envファイルを作成した
- [ ] Docker/Docker Composeがインストールされている
- [ ] `docker-compose up -d` が成功した
- [ ] `docker-compose ps` で全サービスが "Up" 状態

### GitHub Actions

- [ ] GitHub Secretsを設定した
- [ ] ワークフローファイルが存在する
- [ ] CIが自動実行されることを確認した

### 本番デプロイ

- [ ] 本番サーバーが準備されている
- [ ] SSH鍵が設定されている
- [ ] デプロイ用Secretsが設定されている
- [ ] ステージング環境でテスト済み

---

## 📚 次に読むドキュメント

1. **詳細な設定**: [デプロイメントガイド](./operations/DEPLOYMENT_GUIDE.md)
2. **実装計画**: [実装ロードマップ](./operations/IMPLEMENTATION_ROADMAP.md)
3. **詳細分析**: [DevOps/CI/CD分析レポート](./operations/DEVOPS_CICD_ANALYSIS_REPORT.md)

---

## 🆘 サポート

問題が発生した場合:

1. **ログを確認**: `docker-compose logs`
2. **既知の問題を確認**: [トラブルシューティング](./operations/DEPLOYMENT_GUIDE.md#トラブルシューティング)
3. **Issueを作成**: GitHub Issues
4. **チームに連絡**: Slack #mangaanime-support

---

## ⚙️ 環境別の起動方法

### 開発環境

```bash
docker-compose up
```

### ステージング環境

```bash
docker-compose -f docker-compose.staging.yml up -d
```

### 本番環境

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔄 定期実行タスク

### GitHub Actionsを使用（推奨）

自動的に以下が実行されます:
- 毎日 08:00 JST: 情報収集
- 毎週日曜 02:00 JST: クリーンアップ

### ローカルで手動実行

```bash
# 情報収集
docker-compose exec app python -m modules.anime_anilist
docker-compose exec app python -m modules.manga_rss

# データベースクリーンアップ
docker-compose exec app python -m modules.db cleanup
```

---

## 📊 モニタリング

### ヘルスチェック

```bash
curl http://localhost:8000/health
```

### ログ確認

```bash
# リアルタイムログ
docker-compose logs -f

# 過去100行
docker-compose logs --tail=100

# 特定サービス
docker-compose logs -f app
```

### リソース使用状況

```bash
# Docker統計
docker stats

# コンテナ別
docker-compose top
```

---

**最終更新**: 2025-12-06
**メンテナンス**: DevOps Engineer Agent
