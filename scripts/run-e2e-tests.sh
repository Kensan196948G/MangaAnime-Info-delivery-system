#!/bin/bash

###############################################################################
# E2Eテスト実行スクリプト
# Usage: ./scripts/run-e2e-tests.sh [options]
###############################################################################

set -e

# 色付きログ
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# プロジェクトルート
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
E2E_DIR="${PROJECT_ROOT}/tests/e2e"

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ヘルプメッセージ
show_help() {
    cat << EOF
E2Eテスト実行スクリプト

Usage: $0 [OPTIONS]

OPTIONS:
    -h, --help              ヘルプを表示
    -b, --browser BROWSER   ブラウザ指定 (chromium|firefox|webkit|all)
    -u, --ui                UIモードで実行
    -d, --debug             デバッグモードで実行
    -p, --parallel N        並列実行数を指定
    -t, --test FILE         特定のテストファイルのみ実行
    --headed                ヘッドモードで実行
    --no-setup              セットアップをスキップ
    --report-only           レポートのみ表示

EXAMPLES:
    $0                      # すべてのテストを実行
    $0 -b chromium          # Chromiumのみ
    $0 -u                   # UIモードで実行
    $0 -d -t home.spec.ts   # デバッグモードで特定のテスト
    $0 -p 4                 # 4並列で実行
EOF
}

# デフォルト値
BROWSER="all"
UI_MODE=false
DEBUG_MODE=false
HEADED_MODE=false
PARALLEL=""
TEST_FILE=""
SKIP_SETUP=false
REPORT_ONLY=false

# オプション解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -b|--browser)
            BROWSER="$2"
            shift 2
            ;;
        -u|--ui)
            UI_MODE=true
            shift
            ;;
        -d|--debug)
            DEBUG_MODE=true
            shift
            ;;
        --headed)
            HEADED_MODE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL="--workers=$2"
            shift 2
            ;;
        -t|--test)
            TEST_FILE="$2"
            shift 2
            ;;
        --no-setup)
            SKIP_SETUP=true
            shift
            ;;
        --report-only)
            REPORT_ONLY=true
            shift
            ;;
        *)
            log_error "不明なオプション: $1"
            show_help
            exit 1
            ;;
    esac
done

# レポートのみ表示
if [ "$REPORT_ONLY" = true ]; then
    log_info "テストレポートを表示します..."
    cd "${E2E_DIR}"
    npx playwright show-report
    exit 0
fi

# セットアップ
if [ "$SKIP_SETUP" = false ]; then
    log_info "セットアップを開始します..."

    # Node.js のバージョン確認
    if ! command -v node &> /dev/null; then
        log_error "Node.js がインストールされていません"
        exit 1
    fi

    log_info "Node.js バージョン: $(node --version)"

    # 依存関係のインストール
    cd "${E2E_DIR}"
    if [ ! -d "node_modules" ]; then
        log_info "依存関係をインストールしています..."
        npm install
    fi

    # Playwrightブラウザのインストール確認
    if ! npx playwright --version &> /dev/null; then
        log_info "Playwrightブラウザをインストールしています..."
        npx playwright install --with-deps
    fi

    log_success "セットアップ完了"
fi

# アプリケーションの起動確認
log_info "アプリケーションの起動を確認しています..."

APP_URL="http://localhost:5000"
if curl -s "${APP_URL}/api/health" > /dev/null; then
    log_success "アプリケーションが起動しています"
else
    log_warning "アプリケーションが起動していません"
    log_info "アプリケーションを起動してください: python app/app.py"

    read -p "アプリケーションは起動していますか? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "テストを中止します"
        exit 1
    fi
fi

# テスト実行
cd "${E2E_DIR}"

log_info "E2Eテストを開始します..."
log_info "ブラウザ: ${BROWSER}"
log_info "並列実行: ${PARALLEL:-デフォルト}"
log_info "テストファイル: ${TEST_FILE:-すべて}"

# コマンド構築
COMMAND="npx playwright test"

# ブラウザ指定
if [ "$BROWSER" != "all" ]; then
    COMMAND="${COMMAND} --project=${BROWSER}"
fi

# UIモード
if [ "$UI_MODE" = true ]; then
    COMMAND="${COMMAND} --ui"
fi

# デバッグモード
if [ "$DEBUG_MODE" = true ]; then
    COMMAND="${COMMAND} --debug"
fi

# ヘッドモード
if [ "$HEADED_MODE" = true ]; then
    COMMAND="${COMMAND} --headed"
fi

# 並列実行
if [ -n "$PARALLEL" ]; then
    COMMAND="${COMMAND} ${PARALLEL}"
fi

# テストファイル指定
if [ -n "$TEST_FILE" ]; then
    COMMAND="${COMMAND} specs/${TEST_FILE}"
fi

# 実行
log_info "実行コマンド: ${COMMAND}"
echo ""

if eval "${COMMAND}"; then
    log_success "✅ すべてのテストが成功しました"

    # レポート表示の確認
    read -p "テストレポートを表示しますか? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        npx playwright show-report
    fi

    exit 0
else
    log_error "❌ テストが失敗しました"

    # トレース表示の確認
    log_info "失敗の詳細を確認するには:"
    log_info "  1. レポート表示: npx playwright show-report"
    log_info "  2. トレース表示: npx playwright show-trace test-results/*/trace.zip"

    read -p "今すぐレポートを表示しますか? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        npx playwright show-report
    fi

    exit 1
fi
