#!/bin/bash

# GitHub Actions 自動修復システム用ラベル作成スクリプト
# このスクリプトは必要なGitHubラベルを一括作成します

set -e

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GitHub Actions 自動修復システム${NC}"
echo -e "${GREEN}ラベル作成スクリプト${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# GitHub CLIがインストールされているか確認
if ! command -v gh &> /dev/null; then
    echo -e "${RED}エラー: GitHub CLI (gh) がインストールされていません${NC}"
    echo "インストール方法: https://cli.github.com/"
    exit 1
fi

# GitHub認証確認
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}GitHub認証が必要です${NC}"
    gh auth login
fi

echo -e "${GREEN}✓ GitHub CLI認証確認完了${NC}"
echo ""

# リポジトリ情報取得
REPO_OWNER=$(gh repo view --json owner --jq '.owner.login')
REPO_NAME=$(gh repo view --json name --jq '.name')

echo -e "リポジトリ: ${GREEN}${REPO_OWNER}/${REPO_NAME}${NC}"
echo ""

# ラベル定義（名前、色、説明）
declare -A LABELS=(
    ["auto-repair"]="0E8A16|自動修復システム関連Issue"
    ["repair-in-progress"]="FBCA04|修復実行中"
    ["repair-completed"]="0E8A16|修復完了"
    ["repair-failed"]="D73A4A|修復失敗"
    ["critical"]="B60205|クリティカルエラー"
    ["auto-closed-stale"]="CCCCCC|30日間更新なしで自動クローズ"
)

# ラベル作成関数
create_label() {
    local name=$1
    local color=$2
    local description=$3

    # 既存ラベルチェック
    if gh label list --json name --jq '.[].name' | grep -q "^${name}$"; then
        echo -e "${YELLOW}⚠ ラベル '${name}' は既に存在します (スキップ)${NC}"
        return 0
    fi

    # ラベル作成
    if gh label create "${name}" --color "${color}" --description "${description}" 2>/dev/null; then
        echo -e "${GREEN}✓ ラベル '${name}' を作成しました${NC}"
    else
        echo -e "${RED}✗ ラベル '${name}' の作成に失敗しました${NC}"
        return 1
    fi
}

# 全ラベル作成
echo -e "${GREEN}ラベル作成を開始します...${NC}"
echo ""

SUCCESS_COUNT=0
SKIP_COUNT=0
FAIL_COUNT=0

for label_name in "${!LABELS[@]}"; do
    IFS='|' read -r color description <<< "${LABELS[$label_name]}"

    if create_label "${label_name}" "${color}" "${description}"; then
        if gh label list --json name --jq '.[].name' | grep -q "^${label_name}$"; then
            if [[ $(gh label list --json name,color,description --jq ".[] | select(.name==\"${label_name}\")") ]]; then
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            else
                SKIP_COUNT=$((SKIP_COUNT + 1))
            fi
        fi
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi

    sleep 0.5  # API レート制限対策
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ラベル作成完了${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "成功: ${GREEN}${SUCCESS_COUNT}${NC} 個"
echo -e "スキップ: ${YELLOW}${SKIP_COUNT}${NC} 個 (既存)"
echo -e "失敗: ${RED}${FAIL_COUNT}${NC} 個"
echo ""

# 作成されたラベル一覧表示
echo -e "${GREEN}作成されたラベル一覧:${NC}"
echo ""
gh label list | grep -E "(auto-repair|repair-|critical)" || echo "該当ラベルなし"
echo ""

# 次のステップ案内
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}次のステップ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "1. ワークフローファイルを確認:"
echo "   ls -la .github/workflows/auto-repair-unified.yml"
echo ""
echo "2. 権限設定を確認:"
echo "   リポジトリ Settings > Actions > General"
echo "   > Workflow permissions: 'Read and write permissions'"
echo ""
echo "3. テスト実行:"
echo "   gh workflow run auto-repair-unified.yml --field dry_run=true"
echo ""
echo "詳細は以下のドキュメントを参照してください:"
echo "  - docs/setup/AUTO_REPAIR_ACTIVATION_GUIDE.md"
echo "  - docs/setup/AUTO_REPAIR_TESTING.md"
echo ""

exit 0
