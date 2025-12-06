#!/bin/bash

# ドキュメント整理スクリプト
# プロジェクトルートの .md ファイルを適切なディレクトリに移動

set -e

PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
cd "$PROJECT_ROOT"

echo "📁 ドキュメント整理を開始します..."

# 1. 必要なディレクトリを作成
echo "✅ ディレクトリ作成中..."
mkdir -p docs/reports
mkdir -p docs/setup

# 2. reports/ に移動するファイル
echo "📋 レポートファイルを移動中..."
REPORT_FILES=(
    "CALENDAR_INTEGRATION_REPORT.md"
    "CALENDAR_INVESTIGATION_REPORT.md"
    "CALENDAR_SETUP_SUMMARY.md"
    "CONFIGURATION_FIX_SUMMARY.md"
    "COVERAGE_IMPROVEMENT_SUMMARY.md"
    "IMPLEMENTATION_SUMMARY.md"
    "DEVOPS_FILES_INDEX.md"
)

for file in "${REPORT_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" docs/reports/
        echo "  ✓ $file → docs/reports/"
    else
        echo "  ⚠ $file が見つかりません（スキップ）"
    fi
done

# 3. setup/ に移動するファイル
echo "📚 セットアップガイドを移動中..."
SETUP_FILES=(
    "CALENDAR_QUICKSTART.md"
    "QUICKSTART.md"
    "QUICKSTART_CALENDAR.md"
    "README_CALENDAR.md"
    "README_DEVOPS.md"
    "TESTING_GUIDE.md"
)

for file in "${SETUP_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" docs/setup/
        echo "  ✓ $file → docs/setup/"
    else
        echo "  ⚠ $file が見つかりません（スキップ）"
    fi
done

# 4. ルートに残すファイル確認
echo ""
echo "🏠 ルートに残るドキュメント:"
ls -1 *.md 2>/dev/null || echo "  （.mdファイルなし、または移動済み）"

# 5. 移動完了レポート
echo ""
echo "✅ ドキュメント整理が完了しました"
echo ""
echo "📊 移動結果サマリー:"
echo "  - docs/reports/ : $(ls -1 docs/reports/*.md 2>/dev/null | wc -l) ファイル"
echo "  - docs/setup/   : $(ls -1 docs/setup/*.md 2>/dev/null | wc -l) ファイル"
echo ""
echo "🔍 詳細:"
echo ""
echo "docs/reports/:"
ls -1 docs/reports/*.md 2>/dev/null | sed 's/^/  - /'
echo ""
echo "docs/setup/:"
ls -1 docs/setup/*.md 2>/dev/null | sed 's/^/  - /'
echo ""
echo "ルート .md ファイル:"
ls -1 *.md 2>/dev/null | sed 's/^/  - /' || echo "  （なし）"
