#!/bin/bash
# ドキュメント内のパス更新スクリプト
# 実行日: 2025-12-06

PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
cd "$PROJECT_ROOT"

echo "========================================="
echo "ドキュメント内のパス更新"
echo "========================================="
echo ""

# 更新対象ファイルリスト
DOCS=(
    "README.md"
    "QUICKSTART.md"
    "QUICKSTART_CALENDAR.md"
    "docs/CALENDAR_SETUP_GUIDE.md"
    "docs/operations/DEPLOYMENT_GUIDE.md"
)

# パス置換マップ
declare -A PATH_MAP=(
    ["setup_calendar.sh"]="scripts/calendar/setup_calendar.sh"
    ["setup_google_calendar.sh"]="scripts/calendar/setup_google_calendar.sh"
    ["finalize_calendar_setup.sh"]="scripts/calendar/finalize_calendar_setup.sh"
    ["run_calendar_integration_test.sh"]="scripts/calendar/run_calendar_integration_test.sh"
    ["check_calendar_status.py"]="scripts/calendar/check_calendar_status.py"
    ["enable_calendar.py"]="scripts/calendar/enable_calendar.py"
    ["check_structure.sh"]="scripts/setup/check_structure.sh"
    ["make_executable.sh"]="scripts/setup/make_executable.sh"
    ["setup_tests.sh"]="scripts/setup/setup_tests.sh"
    ["config.production.json"]="config/config.production.json"
    ["config.schema.json"]="config/config.schema.json"
    ["env.example"]="config/env.example"
)

echo "📝 パス置換マップ:"
for old in "${!PATH_MAP[@]}"; do
    echo "  $old -> ${PATH_MAP[$old]}"
done
echo ""

# 各ドキュメントで置換
for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "📄 更新中: $doc"

        for old in "${!PATH_MAP[@]}"; do
            new="${PATH_MAP[$old]}"
            # sedで置換（バックアップ作成）
            sed -i.bak "s|bash $old|bash $new|g; s|python3 $old|python3 $new|g; s|\./$old|./$new|g" "$doc"
        done

        echo "  ✓ 完了"
    else
        echo "  ⚠ $doc (存在しません)"
    fi
done

echo ""
echo "✅ パス更新完了"
echo ""
echo "バックアップファイル (*.bak) が作成されています"
echo "確認後、以下で削除できます: find . -name '*.bak' -delete"
