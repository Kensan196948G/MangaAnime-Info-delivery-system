#!/bin/bash
# テスト環境セットアップスクリプト

set -e

cd "$(dirname "$0")"

echo "=========================================="
echo "テスト環境セットアップ"
echo "=========================================="

# 色設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. スクリプトに実行権限を付与
echo -e "${BLUE}[1/3] スクリプトに実行権限を付与...${NC}"
chmod +x scripts/check_coverage.sh
chmod +x scripts/run_coverage_tests.sh
echo -e "${GREEN}✓ 実行権限付与完了${NC}"
echo ""

# 2. テスト用パッケージのインストール
echo -e "${BLUE}[2/3] テスト用パッケージのインストール...${NC}"
if [ -f "test_requirements.txt" ]; then
    python3 -m pip install -r test_requirements.txt -q
    echo -e "${GREEN}✓ パッケージインストール完了${NC}"
else
    echo "test_requirements.txtが見つかりません"
fi
echo ""

# 3. pytest設定ファイルの配置
echo -e "${BLUE}[3/3] pytest設定ファイルの配置...${NC}"
if [ -f "setup_pytest.ini" ]; then
    cp setup_pytest.ini pytest.ini
    echo -e "${GREEN}✓ pytest.ini配置完了${NC}"
fi
echo ""

echo "=========================================="
echo "セットアップ完了！"
echo ""
echo "次のコマンドでテストを実行してください:"
echo "  bash scripts/run_coverage_tests.sh"
echo "=========================================="
