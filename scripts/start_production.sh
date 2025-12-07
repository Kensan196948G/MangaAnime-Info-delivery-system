#!/bin/bash
# 本番環境起動スクリプト

set -e

echo "=== MangaAnime情報配信システム - 本番環境起動 ==="

# 環境変数読み込み
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ .env ファイル読み込み完了"
else
    echo "❌ .env ファイルが見つかりません"
    exit 1
fi

# ログディレクトリ作成
mkdir -p logs
echo "✅ ログディレクトリ作成"

# マイグレーション実行
echo "データベースマイグレーション実行中..."
python3 scripts/run_migrations.py --migrations 6 7
echo "✅ マイグレーション完了"

# Gunicorn起動
echo "Gunicornサーバー起動中..."
exec gunicorn -c gunicorn_config.py app.web_app:app
