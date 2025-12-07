#!/bin/bash
###############################################################################
# セキュリティツールセットアップスクリプト
#
# 目的: SQLインジェクション対策ツールを設定
# 作成日: 2025-12-07
# 作成者: Database Designer Agent
###############################################################################

set -e  # エラー時に停止

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ロゴ表示
echo -e "${BLUE}"
cat << "EOF"
  ____  _____ ____ _   _ ____  ___ _______   __
 / ___|| ____/ ___| | | |  _ \|_ _|_   _\ \ / /
 \___ \|  _|| |   | | | | |_) || |  | |  \ V /
  ___) | |__| |___| |_| |  _ < | |  | |   | |
 |____/|_____\____|\___/|_| \_\___| |_|   |_|

 _____ ___   ___  _     ____
|_   _/ _ \ / _ \| |   / ___|
  | || | | | | | | |   \___ \
  | || |_| | |_| | |___ ___) |
  |_| \___/ \___/|_____|____/

  SQL Injection Protection Tools Setup
EOF
echo -e "${NC}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}セキュリティツールセットアップ${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""
echo -e "📂 プロジェクトルート: ${GREEN}$PROJECT_ROOT${NC}"
echo ""

# 1. 実行権限の付与
echo -e "${YELLOW}[1/5] スクリプトに実行権限を付与...${NC}"

chmod +x scripts/scan_sql_vulnerabilities.py
chmod +x scripts/analyze_database_secure.py

echo -e "${GREEN}✓ 実行権限の付与完了${NC}"
echo ""

# 2. Pythonモジュールの確認
echo -e "${YELLOW}[2/5] Pythonモジュールの確認...${NC}"

PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3が見つかりません${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
echo -e "  Python バージョン: ${GREEN}$PYTHON_VERSION${NC}"

# 必要なモジュールのチェック
REQUIRED_MODULES=("sqlite3" "pathlib" "argparse" "re")
MISSING_MODULES=()

for module in "${REQUIRED_MODULES[@]}"; do
    if ! $PYTHON_CMD -c "import $module" 2>/dev/null; then
        MISSING_MODULES+=("$module")
    fi
done

if [ ${#MISSING_MODULES[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ 必要なモジュールがすべて利用可能です${NC}"
else
    echo -e "${RED}✗ 不足しているモジュール: ${MISSING_MODULES[*]}${NC}"
    exit 1
fi
echo ""

# 3. セキュリティツールのインストール（オプション）
echo -e "${YELLOW}[3/5] セキュリティツールのインストール確認...${NC}"

INSTALL_TOOLS=false
if command -v pip3 &> /dev/null; then
    read -p "追加のセキュリティツール（bandit, sqlfluff）をインストールしますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        INSTALL_TOOLS=true
    fi
fi

if [ "$INSTALL_TOOLS" = true ]; then
    echo "  bandit をインストール中..."
    pip3 install bandit --quiet || echo -e "${YELLOW}  ⚠ bandit のインストールに失敗しました${NC}"

    echo "  sqlfluff をインストール中..."
    pip3 install sqlfluff --quiet || echo -e "${YELLOW}  ⚠ sqlfluff のインストールに失敗しました${NC}"

    echo -e "${GREEN}✓ セキュリティツールのインストール完了${NC}"
else
    echo -e "${BLUE}ℹ セキュリティツールのインストールをスキップしました${NC}"
fi
echo ""

# 4. ディレクトリ構造の確認
echo -e "${YELLOW}[4/5] ディレクトリ構造の確認...${NC}"

REQUIRED_DIRS=("scripts" "docs" "modules" "tests")
MISSING_DIRS=()

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        MISSING_DIRS+=("$dir")
    fi
done

if [ ${#MISSING_DIRS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ 必要なディレクトリがすべて存在します${NC}"
else
    echo -e "${YELLOW}⚠ 不足しているディレクトリ: ${MISSING_DIRS[*]}${NC}"
    echo "  必要に応じて作成してください"
fi
echo ""

# 5. テスト実行
echo -e "${YELLOW}[5/5] スキャンツールのテスト実行...${NC}"

# ヘルプの表示
echo "  脆弱性スキャンツール:"
$PYTHON_CMD scripts/scan_sql_vulnerabilities.py --help | head -n 5

echo ""
echo "  データベース分析ツール:"
$PYTHON_CMD scripts/analyze_database_secure.py --help | head -n 5

echo ""
echo -e "${GREEN}✓ ツールのテスト実行完了${NC}"
echo ""

# セットアップ完了
echo -e "${BLUE}=================================================${NC}"
echo -e "${GREEN}✓ セットアップが正常に完了しました！${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

# 使用方法の表示
echo -e "${YELLOW}📚 使用方法:${NC}"
echo ""
echo -e "${BLUE}1. SQLインジェクション脆弱性スキャン${NC}"
echo "   $ python3 scripts/scan_sql_vulnerabilities.py"
echo ""
echo -e "${BLUE}2. データベース分析（セキュア版）${NC}"
echo "   $ python3 scripts/analyze_database_secure.py"
echo "   $ python3 scripts/analyze_database_secure.py --recommendations"
echo ""
echo -e "${BLUE}3. Banditセキュリティスキャン（インストール済みの場合）${NC}"
echo "   $ bandit -r . -f json -o security_report.json"
echo ""
echo -e "${BLUE}4. CI/CD統合${NC}"
echo "   GitHub Actionsワークフローは以下に配置されています："
echo "   .github/workflows/sql-security-scan.yml"
echo ""

# ドキュメントの案内
echo -e "${YELLOW}📖 ドキュメント:${NC}"
echo ""
echo "  - セキュリティガイドライン:"
echo "    docs/DATABASE_SECURITY_GUIDELINES.md"
echo ""
echo "  - 修正サマリー:"
echo "    docs/SQL_INJECTION_FIX_SUMMARY.md"
echo ""
echo "  - 実装完了レポート:"
echo "    docs/SQL_INJECTION_FIX_IMPLEMENTATION_REPORT.md"
echo ""

# 次のステップ
echo -e "${YELLOW}🚀 次のステップ:${NC}"
echo ""
echo "  1. 脆弱性スキャンを実行してプロジェクトの現状を確認"
echo "  2. 検出された脆弱性を修正"
echo "  3. ユニットテストでセキュリティを検証"
echo "  4. CI/CDパイプラインを有効化"
echo ""

echo -e "${GREEN}Happy Secure Coding! 🔒${NC}"
