#!/bin/bash
# tests/run_tests.sh
# テスト実行スクリプト

set -e

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  テストスイート実行開始${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# プロジェクトルートディレクトリに移動
cd "$(dirname "$0")/.."

# Python環境確認
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python3がインストールされていません${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] Python3検出: $(python3 --version)${NC}"

# 仮想環境確認
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[WARN] 仮想環境が見つかりません。作成しますか？ (y/n)${NC}"
    read -r answer
    if [ "$answer" = "y" ]; then
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    else
        echo -e "${RED}[ERROR] 仮想環境が必要です${NC}"
        exit 1
    fi
else
    source venv/bin/activate
    echo -e "${GREEN}[OK] 仮想環境アクティブ化${NC}"
fi

# 必要なパッケージのインストール確認
echo -e "${BLUE}[INFO] 依存パッケージの確認...${NC}"
pip list | grep pytest > /dev/null || {
    echo -e "${YELLOW}[WARN] pytestがインストールされていません。インストール中...${NC}"
    pip install -r requirements-test.txt
}

# ログディレクトリ作成
mkdir -p tests/logs
mkdir -p htmlcov

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  テスト実行オプション${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo "1. 全テスト実行（カバレッジ付き）"
echo "2. 単体テストのみ"
echo "3. 統合テストのみ"
echo "4. E2Eテストのみ"
echo "5. 高速テスト（単体テストのみ、並列実行）"
echo "6. カバレッジレポート表示"
echo "7. 特定のテストファイルを実行"
echo "8. 終了"
echo ""

read -p "選択してください (1-8): " choice

case $choice in
    1)
        echo -e "${BLUE}[INFO] 全テスト実行中...${NC}"
        pytest tests/ \
            --verbose \
            --cov=app \
            --cov=scripts \
            --cov-report=html:htmlcov \
            --cov-report=term-missing \
            --cov-report=xml:coverage.xml \
            --tb=short \
            --durations=10
        ;;
    2)
        echo -e "${BLUE}[INFO] 単体テスト実行中...${NC}"
        pytest tests/unit/ \
            --verbose \
            --cov=app \
            --cov-report=term-missing \
            -m unit
        ;;
    3)
        echo -e "${BLUE}[INFO] 統合テスト実行中...${NC}"
        pytest tests/integration/ \
            --verbose \
            --cov=app \
            --cov-report=term-missing \
            -m integration
        ;;
    4)
        echo -e "${BLUE}[INFO] E2Eテスト実行中...${NC}"
        pytest tests/e2e/ \
            --verbose \
            -m e2e
        ;;
    5)
        echo -e "${BLUE}[INFO] 高速テスト実行中（並列）...${NC}"
        pytest tests/unit/ \
            --verbose \
            -n auto \
            -m "not slow"
        ;;
    6)
        echo -e "${BLUE}[INFO] カバレッジレポート表示...${NC}"
        if [ -d "htmlcov" ]; then
            if command -v xdg-open &> /dev/null; then
                xdg-open htmlcov/index.html
            elif command -v open &> /dev/null; then
                open htmlcov/index.html
            else
                echo -e "${YELLOW}[WARN] ブラウザを自動で開けません${NC}"
                echo -e "${BLUE}[INFO] htmlcov/index.html を手動で開いてください${NC}"
            fi
        else
            echo -e "${RED}[ERROR] カバレッジレポートが見つかりません${NC}"
            echo -e "${BLUE}[INFO] オプション1で全テストを実行してください${NC}"
        fi
        ;;
    7)
        echo -e "${BLUE}[INFO] テストファイルを指定してください${NC}"
        echo "例: tests/unit/test_collectors/test_anilist.py"
        read -p "ファイルパス: " filepath
        if [ -f "$filepath" ]; then
            pytest "$filepath" --verbose --tb=short
        else
            echo -e "${RED}[ERROR] ファイルが見つかりません: $filepath${NC}"
        fi
        ;;
    8)
        echo -e "${GREEN}[INFO] 終了します${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}[ERROR] 無効な選択です${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  テスト実行完了${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# カバレッジサマリー表示
if [ -f "coverage.xml" ]; then
    echo -e "${GREEN}[OK] カバレッジレポート生成: coverage.xml${NC}"
    echo -e "${GREEN}[OK] HTMLレポート: htmlcov/index.html${NC}"
fi

# テスト結果サマリー
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ すべてのテストが成功しました${NC}"
    exit 0
else
    echo -e "${RED}✗ テストが失敗しました${NC}"
    exit 1
fi
