#!/bin/bash

# ユーザー管理機能セットアップスクリプト
# 統合スクリプトを実行し、必要な権限を設定します

set -e

echo "========================================="
echo "ユーザー管理機能セットアップ"
echo "========================================="
echo ""

# プロジェクトルートに移動
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo "📁 プロジェクトルート: $PROJECT_ROOT"
echo ""

# Pythonバージョン確認
echo "🐍 Pythonバージョン確認..."
python3 --version
echo ""

# 統合スクリプトに実行権限付与
echo "🔧 統合スクリプトに実行権限を付与..."
chmod +x scripts/integrate_user_management.py
echo "✅ 完了"
echo ""

# 統合実行
echo "⚙️  ユーザー管理機能を統合中..."
python3 scripts/integrate_user_management.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✅ セットアップ完了!"
    echo "========================================="
    echo ""
    echo "次のコマンドでアプリケーションを起動してください:"
    echo "  python3 app/web_app.py"
    echo ""
    echo "または開発サーバーで起動:"
    echo "  flask --app app.web_app run --debug"
    echo ""
    echo "アクセス後、管理者でログインして「ユーザー管理」を確認してください。"
    echo ""
else
    echo ""
    echo "========================================="
    echo "❌ セットアップに失敗しました"
    echo "========================================="
    echo ""
    echo "詳細なログを確認してください。"
    echo "手動統合が必要な場合は、以下を参照:"
    echo "  docs/USER_MANAGEMENT_INTEGRATION.md"
    echo ""
    exit 1
fi
