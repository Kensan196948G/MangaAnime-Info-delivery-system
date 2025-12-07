#!/bin/bash
# E2E全階層テスト実行スクリプト（スタンドアロン版）

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "========================================"
echo "🧪 E2E全階層テスト実行"
echo "========================================"
echo ""

# Python環境確認
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3が見つかりません"
    exit 1
fi

# 実行権限付与
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true
chmod +x tests/*.py 2>/dev/null || true

echo "📋 テストメニュー:"
echo "  1) 基本E2Eチェック"
echo "  2) 完全E2Eテストスイート"
echo "  3) 自動修復付きチェック"
echo "  4) Playwrightブラウザテスト"
echo "  5) HTMLレポート生成のみ"
echo "  6) すべて実行"
echo ""
read -p "選択してください (1-6): " choice

case $choice in
    1)
        echo ""
        echo "1️⃣ 基本E2Eチェック実行..."
        python3 tests/test_e2e_comprehensive.py
        ;;
    2)
        echo ""
        echo "2️⃣ 完全E2Eテストスイート実行..."
        python3 tests/test_e2e_complete.py
        ;;
    3)
        echo ""
        echo "3️⃣ 自動修復付きチェック実行..."
        bash scripts/run_e2e_check.sh
        ;;
    4)
        echo ""
        echo "4️⃣ Playwrightブラウザテスト実行..."
        if ! pip3 list | grep -q playwright; then
            echo "📦 Playwrightをインストールしています..."
            pip3 install playwright
            playwright install chromium
        fi
        pytest tests/test_e2e_playwright.py -v
        ;;
    5)
        echo ""
        echo "5️⃣ HTMLレポート生成..."
        python3 scripts/generate_e2e_report.py
        ;;
    6)
        echo ""
        echo "6️⃣ すべてのテスト実行..."
        echo ""
        echo "▶ 基本E2Eチェック"
        python3 tests/test_e2e_comprehensive.py
        echo ""
        echo "▶ 完全E2Eテストスイート"
        python3 tests/test_e2e_complete.py
        echo ""
        echo "▶ HTMLレポート生成"
        python3 scripts/generate_e2e_report.py
        ;;
    *)
        echo "❌ 無効な選択です"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "✨ E2Eテスト完了"
echo "========================================"
