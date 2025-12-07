#!/bin/bash
# プロジェクトファイル整理スクリプト
# 実行日: 2025-12-06

set -e

PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
cd "$PROJECT_ROOT"

echo "========================================="
echo "プロジェクトファイル整理開始"
echo "========================================="
echo ""

# 処理したファイルを記録
MOVED_FILES=()
DELETED_FILES=()

# 1. scripts/calendar/ フォルダを作成
echo "📁 [1/7] scripts/calendar/ フォルダ作成中..."
mkdir -p scripts/calendar
echo "✅ scripts/calendar/ 作成完了"
echo ""

# 2. カレンダー関連ファイルを scripts/calendar/ に移動
echo "📦 [2/7] カレンダー関連ファイルを scripts/calendar/ に移動中..."
CALENDAR_FILES=(
    "setup_calendar.sh"
    "setup_google_calendar.sh"
    "finalize_calendar_setup.sh"
    "run_calendar_integration_test.sh"
    "check_calendar_status.py"
    "enable_calendar.py"
    "investigate_calendar.py"
    "test_calendar_dry_run.py"
    "test_calendar_dryrun.py"
)

for file in "${CALENDAR_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "scripts/calendar/"
        MOVED_FILES+=("$file -> scripts/calendar/")
        echo "  ✓ $file"
    else
        echo "  ⚠ $file (存在しません)"
    fi
done
echo ""

# 3. scripts/setup/ フォルダを作成
echo "📁 [3/7] scripts/setup/ フォルダ作成中..."
mkdir -p scripts/setup
echo "✅ scripts/setup/ 作成完了"
echo ""

# 4. セットアップ関連ファイルを scripts/setup/ に移動
echo "📦 [4/7] セットアップ関連ファイルを scripts/setup/ に移動中..."
SETUP_FILES=(
    "check_structure.sh"
    "make_executable.sh"
    "setup_pytest.ini"
    "setup_tests.sh"
)

for file in "${SETUP_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "scripts/setup/"
        MOVED_FILES+=("$file -> scripts/setup/")
        echo "  ✓ $file"
    else
        echo "  ⚠ $file (存在しません)"
    fi
done
echo ""

# 5. config/ フォルダに設定ファイルを移動
echo "📦 [5/7] 設定ファイルを config/ に移動中..."
mkdir -p config

CONFIG_FILES=(
    "config.production.json"
    "config.schema.json"
    "env.example"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "config/"
        MOVED_FILES+=("$file -> config/")
        echo "  ✓ $file"
    else
        echo "  ⚠ $file (存在しません)"
    fi
done
echo ""

# 6. テストスクリプトを tests/ に移動
echo "📦 [6/7] テストスクリプトを tests/ に移動中..."
TEST_FILES=(
    "test_new_api_sources.py"
    "test_notification_history.py"
    "test_requirements.txt"
)

for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        # test_requirements.txtが既に存在する場合は統合
        if [ "$file" = "test_requirements.txt" ] && [ -f "tests/test_requirements.txt" ]; then
            echo "  ⚠ tests/test_requirements.txt は既に存在します（スキップ）"
            DELETED_FILES+=("$file (tests/に既存)")
            rm -f "$file"
        else
            mv "$file" "tests/"
            MOVED_FILES+=("$file -> tests/")
            echo "  ✓ $file"
        fi
    else
        echo "  ⚠ $file (存在しません)"
    fi
done
echo ""

# 7. 不要ファイル削除
echo "🗑️  [7/7] 不要ファイル削除中..."
CLEANUP_FILES=(
    ".gitignore_calendar"
    ".investigation_script.sh"
    ".run_investigation.sh"
)

for file in "${CLEANUP_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm -f "$file"
        DELETED_FILES+=("$file")
        echo "  ✓ $file 削除"
    else
        echo "  ⚠ $file (存在しません)"
    fi
done
echo ""

# スクリプトに実行権限を付与
echo "🔧 スクリプトに実行権限付与中..."
find scripts/ -type f -name "*.sh" -exec chmod +x {} \;
echo "✅ 実行権限付与完了"
echo ""

# 結果レポート
echo "========================================="
echo "📊 整理結果レポート"
echo "========================================="
echo ""
echo "✅ 移動されたファイル (${#MOVED_FILES[@]}個):"
for item in "${MOVED_FILES[@]}"; do
    echo "  - $item"
done
echo ""

if [ ${#DELETED_FILES[@]} -gt 0 ]; then
    echo "🗑️  削除されたファイル (${#DELETED_FILES[@]}個):"
    for item in "${DELETED_FILES[@]}"; do
        echo "  - $item"
    done
    echo ""
fi

echo "========================================="
echo "✅ プロジェクトファイル整理完了"
echo "========================================="
echo ""

# 新しいディレクトリ構造を表示
echo "📁 新しいディレクトリ構造:"
echo ""
tree -L 2 -d scripts/ config/ 2>/dev/null || {
    echo "scripts/"
    ls -la scripts/ | grep "^d" | awk '{print "  " $9}'
    echo ""
    echo "config/"
    ls -la config/ 2>/dev/null | grep -v "^total" | grep -v "^\." | awk '{print "  " $9}'
}

echo ""
echo "✅ 整理完了しました！"
