# 🚀 MangaAnime Info Delivery System - デプロイメントガイド

## 📋 目次
1. [システム要件](#システム要件)
2. [初期セットアップ](#初期セットアップ)
3. [API認証設定](#api認証設定)
4. [データベース初期化](#データベース初期化)
5. [Web UIの起動](#web-uiの起動)
6. [スケジューラー設定](#スケジューラー設定)
7. [本番環境チェックリスト](#本番環境チェックリスト)
8. [トラブルシューティング](#トラブルシューティング)

---

## システム要件

### 最小要件
- **OS**: Ubuntu 20.04+ / Debian 11+
- **Python**: 3.12.0以上
- **メモリ**: 2GB以上
- **ストレージ**: 1GB以上の空き容量
- **ネットワーク**: インターネット接続必須

### 推奨要件
- **CPU**: 2コア以上
- **メモリ**: 4GB以上
- **ストレージ**: SSD 5GB以上

---

## 初期セットアップ

### 1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/MangaAnime-Info-delivery-system.git
cd MangaAnime-Info-delivery-system
```

### 2. Python仮想環境の作成
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows
```

### 3. 依存パッケージのインストール
```bash
pip install -r requirements.txt
npm install  # E2Eテスト用（オプション）
```

### 4. 環境変数の設定
```bash
cp .env.example .env
# .envファイルを編集して必要な情報を設定
```

---

## API認証設定

### Gmail API設定

#### 1. Google Cloud Consoleでのプロジェクト作成
1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新規プロジェクトを作成
3. Gmail APIとGoogle Calendar APIを有効化

#### 2. 認証情報の作成
```bash
# OAuth2認証情報をダウンロードして配置
mv ~/Downloads/credentials.json ./credentials.json

# App Passwordの設定（2段階認証が必要）
echo "your-app-password" > gmail_app_password.txt
chmod 600 gmail_app_password.txt
```

#### 3. トークンの生成
```bash
python create_token.py
# ブラウザが開いてGoogleアカウントの認証を求められます
```

### AniList API設定
```json
// config.jsonで設定
{
  "apis": {
    "anilist": {
      "enabled": true,
      "rate_limit": 90,
      "rate_window": 60
    }
  }
}
```

---

## データベース初期化

### 1. データベースの作成
```bash
# SQLiteデータベースの初期化
python -c "from modules.db import DatabaseManager; db = DatabaseManager('db.sqlite3'); db.initialize()"
```

### 2. 初期データの投入（オプション）
```bash
python init_demo_db.py  # デモデータの投入
```

### 3. データベース最適化
```bash
sqlite3 db.sqlite3 < optimize_database.sql
```

---

## Web UIの起動

### 開発環境での起動
```bash
python web_app.py
# http://localhost:5000 でアクセス可能
```

### 本番環境での起動（systemdサービス）
```bash
# サービスファイルのインストール
sudo cp mangaanime-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mangaanime-web
sudo systemctl start mangaanime-web
```

### Nginxリバースプロキシ設定（推奨）
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## スケジューラー設定

### cronジョブの設定
```bash
# crontabを編集
crontab -e

# 以下を追加
# 毎朝8時に情報収集と通知
0 8 * * * /usr/bin/python3 /path/to/release_notifier.py >> /path/to/logs/cron.log 2>&1

# 毎日3時にバックアップ
0 3 * * * /usr/bin/python3 /path/to/backup_database.py >> /path/to/logs/backup.log 2>&1

# 毎時0分にヘルスチェック
0 * * * * /usr/bin/python3 /path/to/health_check.py >> /path/to/logs/health.log 2>&1
```

---

## 本番環境チェックリスト

### セキュリティ
- [ ] ファイアウォール設定（必要なポートのみ開放）
- [ ] SSL証明書の設定（Let's Encrypt推奨）
- [ ] 認証ファイルのパーミッション確認（600）
- [ ] APIキーの環境変数化
- [ ] デバッグモードの無効化

### パフォーマンス
- [ ] データベースインデックスの作成
- [ ] キャッシュの有効化
- [ ] ログローテーションの設定
- [ ] リソース監視の設定

### バックアップ
- [ ] 自動バックアップの設定
- [ ] バックアップの定期テスト
- [ ] リストア手順の文書化
- [ ] オフサイトバックアップの設定

### 監視
- [ ] エラーログの監視
- [ ] API使用量の監視
- [ ] ディスク容量の監視
- [ ] アラート通知の設定

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. Gmail API認証エラー
```bash
# トークンを再生成
rm token.json
python create_token.py
```

#### 2. データベースロックエラー
```bash
# WALモードを有効化
sqlite3 db.sqlite3 "PRAGMA journal_mode=WAL;"
```

#### 3. メモリ不足エラー
```bash
# スワップファイルの作成
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 4. ポート競合
```bash
# 使用中のポートを確認
sudo lsof -i :5000
# プロセスを終了
sudo kill -9 <PID>
```

### ログファイルの場所
- アプリケーションログ: `./logs/app.log`
- エラーログ: `./logs/error.log`
- APIログ: `./logs/api.log`
- cronログ: `./logs/cron.log`

### サポート
問題が解決しない場合は、以下をご確認ください：
- [プロジェクトWiki](https://github.com/yourusername/MangaAnime-Info-delivery-system/wiki)
- [Issue Tracker](https://github.com/yourusername/MangaAnime-Info-delivery-system/issues)
- [FAQ](./docs/FAQ.md)

---

## 🎉 デプロイ完了！

システムが正常に稼働していることを確認してください：
1. Web UIにアクセス: http://your-domain.com
2. テスト通知の送信: `python test_email_delivery.py`
3. ヘルスチェック: `python health_check.py`

問題がなければ、MangaAnime Info Delivery Systemの運用を開始できます！