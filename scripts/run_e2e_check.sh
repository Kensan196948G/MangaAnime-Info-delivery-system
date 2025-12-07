#!/bin/bash
# E2E全階層エラーチェック実行スクリプト

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "========================================"
echo "🔍 E2E全階層エラーチェック"
echo "========================================"

# Python環境確認
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3が見つかりません"
    exit 1
fi

echo ""
echo "📦 必要なパッケージ確認..."
pip3 list | grep -q "Flask" || pip3 install Flask
pip3 list | grep -q "pytest" || pip3 install pytest

echo ""
echo "1️⃣ E2Eエラーチェック実行..."
python3 tests/test_e2e_comprehensive.py

# エラーが検出された場合
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ エラーが検出されました"
    echo ""
    read -p "🔧 自動修復を実行しますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "2️⃣ エラー自動修復実行..."
        python3 scripts/fix_e2e_errors.py

        echo ""
        echo "3️⃣ 再チェック実行..."
        python3 tests/test_e2e_comprehensive.py

        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ すべてのエラーが修正されました！"
        else
            echo ""
            echo "⚠️  一部エラーが残っています。手動修正が必要です。"
            exit 1
        fi
    else
        echo ""
        echo "ℹ️  自動修復をスキップしました"
        exit 1
    fi
else
    echo ""
    echo "✅ エラーは検出されませんでした！"
fi

echo ""
echo "========================================"
echo "✨ E2Eチェック完了"
echo "========================================"
