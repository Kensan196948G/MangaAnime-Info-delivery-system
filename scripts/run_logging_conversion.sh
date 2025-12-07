#!/bin/bash
#
# Print文からLoggingモジュールへの完全自動変換スクリプト
#
# このスクリプトは以下を実行します：
# 1. 事前検証（現在のprint文の数を確認）
# 2. バックアップ作成
# 3. print文をloggingに変換
# 4. 変換後の検証
# 5. レポート生成
#

set -e  # エラーで停止

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# プロジェクトルート
PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
SCRIPTS_DIR="${PROJECT_ROOT}/scripts"
REPORTS_DIR="${PROJECT_ROOT}/reports/logging_conversion"

# ディレクトリ作成
mkdir -p "${REPORTS_DIR}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Print to Logging Conversion Tool${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# スクリプトが実行可能か確認
if [ ! -f "${SCRIPTS_DIR}/convert_print_to_logging.py" ]; then
    echo -e "${RED}Error: convert_print_to_logging.py not found${NC}"
    exit 1
fi

if [ ! -f "${SCRIPTS_DIR}/verify_logging_conversion.py" ]; then
    echo -e "${RED}Error: verify_logging_conversion.py not found${NC}"
    exit 1
fi

# Pythonバージョン確認
echo -e "${BLUE}Checking Python version...${NC}"
python3 --version

# ステップ1: 事前検証
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Step 1: Pre-Conversion Verification${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

python3 "${SCRIPTS_DIR}/verify_logging_conversion.py" \
    --project-root "${PROJECT_ROOT}" \
    --save-report \
    > "${REPORTS_DIR}/pre_conversion_report.txt" 2>&1

cat "${REPORTS_DIR}/pre_conversion_report.txt"

# 変換前のprint文の数を取得
PRE_PRINTS=$(grep "Remaining Print Statements:" "${REPORTS_DIR}/pre_conversion_report.txt" | awk '{print $4}')
echo ""
echo -e "${YELLOW}Found ${PRE_PRINTS} print statements to convert${NC}"

# 確認プロンプト
echo ""
read -p "$(echo -e ${YELLOW}Continue with conversion? [y/N]: ${NC})" -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Conversion cancelled${NC}"
    exit 0
fi

# ステップ2: バックアップ確認
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Step 2: Creating Backup${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo -e "${GREEN}Backup will be created automatically during conversion${NC}"

# ステップ3: 変換実行
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Step 3: Converting Print Statements${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

python3 "${SCRIPTS_DIR}/convert_print_to_logging.py" \
    --project-root "${PROJECT_ROOT}" \
    > "${REPORTS_DIR}/conversion_log.txt" 2>&1

cat "${REPORTS_DIR}/conversion_log.txt"

# ステップ4: 事後検証
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Step 4: Post-Conversion Verification${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

python3 "${SCRIPTS_DIR}/verify_logging_conversion.py" \
    --project-root "${PROJECT_ROOT}" \
    --save-report \
    --generate-fix \
    > "${REPORTS_DIR}/post_conversion_report.txt" 2>&1

cat "${REPORTS_DIR}/post_conversion_report.txt"

# 変換後のprint文の数を取得
POST_PRINTS=$(grep "Remaining Print Statements:" "${REPORTS_DIR}/post_conversion_report.txt" | awk '{print $4}')

# ステップ5: サマリー
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Conversion Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Print Statements Before: ${RED}${PRE_PRINTS}${NC}"
echo -e "Print Statements After:  ${GREEN}${POST_PRINTS}${NC}"

if [ "$POST_PRINTS" -eq 0 ]; then
    echo -e "${GREEN}Converted:              ${PRE_PRINTS}${NC}"
    echo ""
    echo -e "${GREEN}✓ SUCCESS: All print statements converted!${NC}"
else
    CONVERTED=$((PRE_PRINTS - POST_PRINTS))
    echo -e "${YELLOW}Converted:              ${CONVERTED}${NC}"
    echo -e "${YELLOW}Remaining:              ${POST_PRINTS}${NC}"
    echo ""
    echo -e "${YELLOW}⚠ WARNING: Some print statements remain${NC}"
    echo -e "${YELLOW}Check the post-conversion report for details${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Reports Location${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Pre-conversion:  ${REPORTS_DIR}/pre_conversion_report.txt"
echo -e "Conversion log:  ${REPORTS_DIR}/conversion_log.txt"
echo -e "Post-conversion: ${REPORTS_DIR}/post_conversion_report.txt"

# バックアップ場所を表示
BACKUP_DIR=$(grep "Backup Location:" "${REPORTS_DIR}/conversion_log.txt" | awk '{print $3}')
if [ -n "$BACKUP_DIR" ]; then
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Backup Information${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "Backup Location: ${BACKUP_DIR}"
    echo ""
    echo -e "${GREEN}To rollback, run:${NC}"
    echo -e "  python3 ${SCRIPTS_DIR}/convert_print_to_logging.py --rollback"
fi

# ロールバック手順を保存
cat > "${REPORTS_DIR}/ROLLBACK_INSTRUCTIONS.txt" << EOF
========================================
Rollback Instructions
========================================

If you need to rollback the conversion, run:

  cd ${PROJECT_ROOT}
  python3 ${SCRIPTS_DIR}/convert_print_to_logging.py --rollback

This will restore all files from the backup located at:
  ${BACKUP_DIR}

========================================
EOF

echo ""
echo -e "${GREEN}Conversion process completed!${NC}"
echo ""
