# セットアップガイド - MangaAnime Info Delivery System

## 目次

1. [システム要件](#システム要件)
2. [クイックスタート](#クイックスタート)
3. [詳細インストール](#詳細インストール)
4. [Google API設定](#google-api設定)
5. [環境変数設定](#環境変数設定)
6. [データベース初期化](#データベース初期化)
7. [動作確認](#動作確認)
8. [トラブルシューティング](#トラブルシューティング)

---

## システム要件

### 必須
- Python 3.9以上
- SQLite 3.x
- pip (Pythonパッケージマネージャー)

### 推奨
- Linux (Ubuntu 20.04以上) または macOS
- 4GB RAM以上
- 10GB ディスク空き容量

---

## クイックスタート

```bash
# 1. リポジトリをクローン
git clone https://github.com/Kensan196948G/MangaAnime-Info-delivery-system.git
cd MangaAnime-Info-delivery-system

# 2. 仮想環境を作成
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# または: venv\Scripts\activate  # Windows

# 3. 依存関係をインストール
pip install -r requirements.txt

# 4. 環境変数を設定
cp .env.example .env
# .envファイルを編集して必要な値を設定

# 5. データベースを初期化
python3 -c "from modules.db import init_db; init_db()"

# 6. アプリケーションを起動
python3 app/start_web_ui.py
```

ブラウザで http://localhost:5000 にアクセス

---

## 詳細インストール

### 1. Python環境の準備

```bash
# Pythonバージョン確認
python3 --version  # 3.9以上が必要

# pipの更新
pip install --upgrade pip
```

### 2. 仮想環境の作成（推奨）

```bash
# 仮想環境を作成
python3 -m venv venv

# アクティベート
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate      # Windows PowerShell
```

### 3. 依存関係のインストール

```bash
# 本番用
pip install -r requirements.txt

# 開発用（テストツール含む）
pip install -r requirements-dev.txt
pip install -r requirements-test.txt
```

---

## Google API設定

### 1. Google Cloud Consoleでプロジェクト作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成
3. 以下のAPIを有効化:
   - Gmail API
   - Google Calendar API

### 2. OAuth 2.0 認証情報の作成

1. 「認証情報」→「認証情報を作成」→「OAuth クライアント ID」
2. アプリケーションの種類: 「デスクトップアプリ」
3. `credentials.json` をダウンロード
4. プロジェクトルートに配置

### 3. 初回認証

```bash
python3 create_token.py
```

ブラウザが開くので、Googleアカウントで認証を完了してください。
`token.json` が生成されます。

---

## 環境変数設定

### .env ファイルの作成

```bash
cp .env.example .env
```

### 必須設定

```env
# 管理者認証（必須）
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=your_secure_password_here

# Gmail設定
MANGA_ANIME_GMAIL_FROM=your-email@gmail.com
MANGA_ANIME_GMAIL_TO=recipient@gmail.com

# データベース
MANGA_ANIME_DB_PATH=./data/db.sqlite3

# セキュリティ
MANGA_ANIME_SECRET_KEY=your_random_secret_key_here
```

### オプション設定

```env
# 環境
MANGA_ANIME_ENVIRONMENT=development  # production, testing
MANGA_ANIME_LOG_LEVEL=INFO

# カレンダー
MANGA_ANIME_CALENDAR_ID=primary

# APIファイル
MANGA_ANIME_CREDENTIALS_FILE=credentials.json
MANGA_ANIME_TOKEN_FILE=token.json

# DBストア切り替え
USE_DB_STORE=true
```

---

## データベース初期化

### 自動初期化

```bash
python3 -c "from modules.db import init_db; init_db()"
```

### 手動マイグレーション

```bash
# マイグレーションを実行
python3 scripts/run_migrations.py

# 監査ログテーブルを追加
python3 scripts/migrate_audit_logs.py
```

### データベースの場所

デフォルト: `./data/db.sqlite3`

---

## 動作確認

### 1. ヘルスチェック

```bash
curl http://localhost:5000/health
```

期待される応答:
```json
{"status": "healthy", "timestamp": "..."}
```

### 2. テスト実行

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ付き
pytest tests/ --cov=modules --cov=app --cov-report=term-missing
```

### 3. Web UIアクセス

1. http://localhost:5000 にアクセス
2. 管理者アカウントでログイン
3. ダッシュボードを確認

---

## トラブルシューティング

### 「DEFAULT_ADMIN_PASSWORD must be set」エラー

**原因**: 環境変数が設定されていない

**解決策**:
```bash
export DEFAULT_ADMIN_PASSWORD="your_secure_password"
# または .env ファイルに追加
```

### 「ModuleNotFoundError」エラー

**原因**: 依存関係が不足

**解決策**:
```bash
pip install -r requirements.txt
```

### データベース接続エラー

**原因**: データベースファイルがない、または破損

**解決策**:
```bash
# 新規作成
python3 -c "from modules.db import init_db; init_db()"

# WALチェックポイント（破損時）
python3 scripts/db_auto_backup.py --checkpoint
```

### Google API認証エラー

**原因**: トークンの期限切れ

**解決策**:
```bash
rm token.json
python3 create_token.py
```

### ポート5000が使用中

**解決策**:
```bash
# 別のポートで起動
python3 app/start_web_ui.py --port 8080
```

---

## 次のステップ

1. [API ガイド](api/API-GUIDE.md) を参照
2. [運用手順書](OPERATIONS-GUIDE.md) を確認
3. cronジョブの設定（自動実行）

---

## サポート

問題が発生した場合:
1. GitHubのIssuesを確認
2. ログファイル (`logs/app.log`) を確認
3. 新しいIssueを作成

---

*最終更新: 2025-12-08*
