#!/bin/bash
# プロジェクトファイル整理実行スクリプト
# 実行日: 2025-12-06

set -e

PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
cd "$PROJECT_ROOT"

echo "========================================="
echo "プロジェクトファイル整理実行"
echo "========================================="
echo ""

# 処理結果を記録
REPORT_FILE="file_reorganization_results.txt"
echo "実行日時: $(date)" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 1. ディレクトリ作成
echo "📁 ディレクトリ作成中..."
mkdir -p scripts/calendar
mkdir -p scripts/setup
mkdir -p config
echo "✅ ディレクトリ作成完了" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# 2. カレンダー関連ファイル移動
echo "📦 カレンダー関連ファイル移動中..." | tee -a "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "[scripts/calendar/ に移動]" >> "$REPORT_FILE"

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

CALENDAR_MOVED=0
for file in "${CALENDAR_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "scripts/calendar/"
        echo "  ✓ $file" | tee -a "$REPORT_FILE"
        ((CALENDAR_MOVED++))
    fi
done
echo "  合計: ${CALENDAR_MOVED}個移動" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# 3. セットアップ関連ファイル移動
echo "📦 セットアップ関連ファイル移動中..." | tee -a "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "[scripts/setup/ に移動]" >> "$REPORT_FILE"

SETUP_FILES=(
    "check_structure.sh"
    "make_executable.sh"
    "setup_pytest.ini"
    "setup_tests.sh"
)

SETUP_MOVED=0
for file in "${SETUP_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "scripts/setup/"
        echo "  ✓ $file" | tee -a "$REPORT_FILE"
        ((SETUP_MOVED++))
    fi
done
echo "  合計: ${SETUP_MOVED}個移動" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# 4. 設定ファイル移動
echo "📦 設定ファイル移動中..." | tee -a "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "[config/ に移動]" >> "$REPORT_FILE"

CONFIG_FILES=(
    "config.production.json"
    "config.schema.json"
    "env.example"
)

CONFIG_MOVED=0
for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" "config/"
        echo "  ✓ $file" | tee -a "$REPORT_FILE"
        ((CONFIG_MOVED++))
    fi
done
echo "  合計: ${CONFIG_MOVED}個移動" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# 5. テストファイル移動
echo "📦 テストファイル移動中..." | tee -a "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "[tests/ に移動]" >> "$REPORT_FILE"

TEST_MOVED=0

# test_new_api_sources.py
if [ -f "test_new_api_sources.py" ]; then
    mv "test_new_api_sources.py" "tests/"
    echo "  ✓ test_new_api_sources.py" | tee -a "$REPORT_FILE"
    ((TEST_MOVED++))
fi

# test_notification_history.py
if [ -f "test_notification_history.py" ]; then
    mv "test_notification_history.py" "tests/"
    echo "  ✓ test_notification_history.py" | tee -a "$REPORT_FILE"
    ((TEST_MOVED++))
fi

# test_requirements.txt (重複チェック)
if [ -f "test_requirements.txt" ]; then
    if [ -f "tests/test_requirements.txt" ]; then
        echo "  ⚠ test_requirements.txt (tests/に既存のため削除)" | tee -a "$REPORT_FILE"
        rm -f "test_requirements.txt"
    else
        mv "test_requirements.txt" "tests/"
        echo "  ✓ test_requirements.txt" | tee -a "$REPORT_FILE"
        ((TEST_MOVED++))
    fi
fi

echo "  合計: ${TEST_MOVED}個移動" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# 6. 不要ファイル削除
echo "🗑️  不要ファイル削除中..." | tee -a "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "[削除されたファイル]" >> "$REPORT_FILE"

CLEANUP_FILES=(
    ".gitignore_calendar"
    ".investigation_script.sh"
    ".run_investigation.sh"
)

DELETED=0
for file in "${CLEANUP_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "  ✓ $file" | tee -a "$REPORT_FILE"
        ((DELETED++))
    fi
done
echo "  合計: ${DELETED}個削除" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# 7. 実行権限付与
echo "🔧 スクリプトに実行権限付与中..." | tee -a "$REPORT_FILE"
find scripts/ -type f -name "*.sh" -exec chmod +x {} \;
echo "✅ 実行権限付与完了" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# サマリー
echo "=========================================" | tee -a "$REPORT_FILE"
echo "📊 整理結果サマリー" | tee -a "$REPORT_FILE"
echo "=========================================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"
echo "移動されたファイル:" | tee -a "$REPORT_FILE"
echo "  - カレンダー関連: ${CALENDAR_MOVED}個 → scripts/calendar/" | tee -a "$REPORT_FILE"
echo "  - セットアップ関連: ${SETUP_MOVED}個 → scripts/setup/" | tee -a "$REPORT_FILE"
echo "  - 設定ファイル: ${CONFIG_MOVED}個 → config/" | tee -a "$REPORT_FILE"
echo "  - テストファイル: ${TEST_MOVED}個 → tests/" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"
echo "削除されたファイル: ${DELETED}個" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

TOTAL_MOVED=$((CALENDAR_MOVED + SETUP_MOVED + CONFIG_MOVED + TEST_MOVED))
echo "合計処理: ${TOTAL_MOVED}個移動, ${DELETED}個削除" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# 新しい構造を表示
echo "=========================================" | tee -a "$REPORT_FILE"
echo "📁 新しいディレクトリ構造" | tee -a "$REPORT_FILE"
echo "=========================================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

echo "scripts/calendar/:" | tee -a "$REPORT_FILE"
ls -1 scripts/calendar/ 2>/dev/null | sed 's/^/  - /' | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

echo "scripts/setup/:" | tee -a "$REPORT_FILE"
ls -1 scripts/setup/ 2>/dev/null | sed 's/^/  - /' | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

echo "config/:" | tee -a "$REPORT_FILE"
ls -1 config/ 2>/dev/null | sed 's/^/  - /' | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

echo "=========================================" | tee -a "$REPORT_FILE"
echo "✅ プロジェクトファイル整理完了" | tee -a "$REPORT_FILE"
echo "=========================================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"
echo "詳細レポート: $REPORT_FILE" | tee -a "$REPORT_FILE"

echo ""
echo "次のステップ:"
echo "1. ドキュメント内のパスを更新"
echo "2. CI/CDワークフローのパスを更新"
echo "3. Makefileのパスを更新"
echo "4. 変更をコミット: git add . && git commit -m '[リファクタリング] プロジェクトファイル構造の整理'"
