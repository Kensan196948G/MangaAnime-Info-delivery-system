#!/bin/bash
# WebUI起動スクリプト

set -e

echo "=== MangaAnime情報配信システム - WebUI起動 ==="

# プロジェクトディレクトリに移動
cd "$(dirname "$0")/.."

# IPアドレス取得
IP_ADDRESS=$(hostname -I | awk '{print $1}')
PORT=3030

echo ""
echo "📡 起動設定:"
echo "  - IPアドレス: ${IP_ADDRESS}"
echo "  - ポート: ${PORT}"
echo "  - アクセスURL: http://${IP_ADDRESS}:${PORT}"
echo ""

# 環境変数設定
export FLASK_ENV=development
export USE_DB_STORE=true
export USE_DB_AUDIT_LOG=true

# データベースパス確認
if [ ! -f "data/db.sqlite3" ]; then
    echo "⚠️  データベースが見つかりません"
    echo "   data/db.sqlite3 を作成します..."
    mkdir -p data
    touch data/db.sqlite3
    
    # マイグレーション実行
    echo "   マイグレーション実行中..."
    python3 scripts/run_migrations.py --migrations 6 7 8 9
fi

echo "🚀 WebUIを起動しています..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  アクセスURL: http://${IP_ADDRESS}:${PORT}"
echo "  ログイン: admin / changeme123"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "停止: Ctrl+C"
echo ""

# Flask起動
python3 app/web_app.py
