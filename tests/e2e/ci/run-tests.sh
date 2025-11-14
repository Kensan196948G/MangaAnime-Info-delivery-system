#!/bin/bash

# E2Eテスト実行スクリプト（CI/CD用）
# 
# このスクリプトはCI/CD環境でPlaywrightのE2Eテストを実行します

set -e

# 色付きログ出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ出力関数
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

# 設定
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
TEST_RESULTS_DIR="$PROJECT_ROOT/tests/e2e/reports"
BROWSER_LIST="chromium firefox webkit"

# デフォルト値
HEADLESS=true
BROWSER=""
TEST_PATTERN=""
WORKERS=1
TIMEOUT=60000
RETRIES=2

# 使用方法表示
usage() {
    cat << EOF
使用方法: $0 [オプション]

オプション:
  -h, --help              このヘルプメッセージを表示
  -b, --browser BROWSER   テスト対象ブラウザ (chromium|firefox|webkit|all)
  -p, --pattern PATTERN   テストファイルのパターン (例: "*navigation*")
  -w, --workers COUNT     並列ワーカー数 (デフォルト: 1)
  -t, --timeout MS        テストタイムアウト (デフォルト: 60000ms)
  -r, --retries COUNT     再試行回数 (デフォルト: 2)
  --headed                ヘッドレスモード無効化（デバッグ用）
  --debug                 デバッグモード有効化
  --smoke                 スモークテストのみ実行
  --full                  全テスト実行（デフォルト）

例:
  $0                      # 全テストをヘッドレスで実行
  $0 --headed -b chromium # Chromiumで画面表示しながらテスト実行
  $0 --smoke              # スモークテストのみ実行
  $0 -p "*config*"        # 設定関連テストのみ実行

EOF
}

# コマンドライン引数処理
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -b|--browser)
            BROWSER="$2"
            shift 2
            ;;
        -p|--pattern)
            TEST_PATTERN="$2"
            shift 2
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -r|--retries)
            RETRIES="$2"
            shift 2
            ;;
        --headed)
            HEADLESS=false
            shift
            ;;
        --debug)
            DEBUG=true
            HEADLESS=false
            WORKERS=1
            shift
            ;;
        --smoke)
            TEST_PATTERN="*navigation*"
            TIMEOUT=30000
            shift
            ;;
        --full)
            TEST_PATTERN=""
            shift
            ;;
        *)
            log_error "不明なオプション: $1"
            usage
            exit 1
            ;;
    esac
done

# プロジェクトディレクトリへ移動
cd "$PROJECT_ROOT"

log_info "MangaAnime E2Eテスト実行を開始します..."
log_info "プロジェクトディレクトリ: $PROJECT_ROOT"

# 前提条件チェック
log_info "前提条件をチェックしています..."

# Node.jsの確認
if ! command -v node &> /dev/null; then
    log_error "Node.jsがインストールされていません"
    exit 1
fi

# npmの確認
if ! command -v npm &> /dev/null; then
    log_error "npmがインストールされていません"
    exit 1
fi

# package.jsonの確認
if [[ ! -f "package.json" ]]; then
    log_error "package.jsonが見つかりません"
    exit 1
fi

# Playwrightの確認
if [[ ! -f "playwright.config.ts" ]]; then
    log_error "playwright.config.tsが見つかりません"
    exit 1
fi

log_success "前提条件チェック完了"

# 依存関係インストール
log_info "依存関係をインストールしています..."
npm install || {
    log_error "npm installに失敗しました"
    exit 1
}

# Playwrightブラウザインストール
log_info "Playwrightブラウザをインストールしています..."
npx playwright install || {
    log_error "Playwrightブラウザのインストールに失敗しました"
    exit 1
}

# テスト結果ディレクトリの準備
log_info "テスト結果ディレクトリを準備しています..."
rm -rf "$TEST_RESULTS_DIR"
mkdir -p "$TEST_RESULTS_DIR"

# 環境変数設定
export TESTING=true
export CI=true
export NODE_ENV=test
export DATABASE_URL="test_e2e_ci.db"

# アプリケーションサーバー起動チェック
log_info "アプリケーションサーバーの状態をチェックしています..."

check_server() {
    local url="$1"
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
            return 0
        fi
        ((attempt++))
        sleep 2
        echo -n "."
    done
    return 1
}

# サーバーの起動確認
if ! check_server "http://127.0.0.1:3033"; then
    log_warning "アプリケーションサーバーが起動していません。起動を試行します..."
    
    # バックグラウンドでサーバー起動
    python3 web_app.py > server.log 2>&1 &
    SERVER_PID=$!
    
    log_info "サーバー起動中... (PID: $SERVER_PID)"
    sleep 10
    
    if ! check_server "http://127.0.0.1:3033"; then
        log_error "アプリケーションサーバーの起動に失敗しました"
        if [[ -n "$SERVER_PID" ]]; then
            kill "$SERVER_PID" 2>/dev/null || true
        fi
        exit 1
    fi
else
    log_success "アプリケーションサーバーは既に起動しています"
fi

# Playwrightテスト実行
log_info "E2Eテストを実行しています..."

# テスト実行コマンド構築
PLAYWRIGHT_CMD="npx playwright test"

if [[ "$HEADLESS" == "false" ]]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --headed"
fi

if [[ -n "$BROWSER" && "$BROWSER" != "all" ]]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --project=$BROWSER"
fi

if [[ -n "$TEST_PATTERN" ]]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD $TEST_PATTERN"
fi

PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --workers=$WORKERS"
PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --timeout=$TIMEOUT"
PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --retries=$RETRIES"

if [[ "$DEBUG" == "true" ]]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --debug"
fi

log_info "実行コマンド: $PLAYWRIGHT_CMD"

# テスト実行
START_TIME=$(date +%s)

if $PLAYWRIGHT_CMD; then
    TEST_RESULT="SUCCESS"
    EXIT_CODE=0
    log_success "E2Eテストが正常に完了しました"
else
    TEST_RESULT="FAILED"
    EXIT_CODE=1
    log_error "E2Eテストが失敗しました"
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# テスト結果サマリー生成
log_info "テスト結果を生成しています..."

# HTMLレポートの確認
if [[ -f "$TEST_RESULTS_DIR/html/index.html" ]]; then
    log_success "HTMLレポートが生成されました: $TEST_RESULTS_DIR/html/index.html"
fi

# JUnitレポートの確認
if [[ -f "$TEST_RESULTS_DIR/junit.xml" ]]; then
    log_success "JUnitレポートが生成されました: $TEST_RESULTS_DIR/junit.xml"
fi

# JSONレポートの確認
if [[ -f "$TEST_RESULTS_DIR/test-results.json" ]]; then
    log_success "JSONレポートが生成されました: $TEST_RESULTS_DIR/test-results.json"
    
    # テスト統計の表示
    if command -v jq &> /dev/null; then
        log_info "テスト統計:"
        cat "$TEST_RESULTS_DIR/test-results.json" | jq -r '
            "  合計テスト数: " + (.stats.total // 0 | tostring) +
            "\n  成功: " + (.stats.passed // 0 | tostring) +
            "\n  失敗: " + (.stats.failed // 0 | tostring) +
            "\n  スキップ: " + (.stats.skipped // 0 | tostring) +
            "\n  実行時間: " + ((.stats.duration // 0) / 1000 | tostring) + "秒"
        '
    fi
fi

# スクリーンショット・ビデオの確認
SCREENSHOT_DIR="$TEST_RESULTS_DIR/screenshots"
VIDEO_DIR="$TEST_RESULTS_DIR/videos"

if [[ -d "$SCREENSHOT_DIR" ]] && [[ -n "$(ls -A "$SCREENSHOT_DIR" 2>/dev/null)" ]]; then
    log_info "スクリーンショットが保存されました: $SCREENSHOT_DIR"
fi

if [[ -d "$VIDEO_DIR" ]] && [[ -n "$(ls -A "$VIDEO_DIR" 2>/dev/null)" ]]; then
    log_info "テスト実行ビデオが保存されました: $VIDEO_DIR"
fi

# ログファイルの整理
if [[ -f "server.log" ]]; then
    mv server.log "$TEST_RESULTS_DIR/server.log"
    log_info "サーバーログを保存しました: $TEST_RESULTS_DIR/server.log"
fi

# 最終サマリー
log_info "======================================"
log_info "テスト実行完了"
log_info "======================================"
log_info "結果: $TEST_RESULT"
log_info "実行時間: ${DURATION}秒"
log_info "レポート場所: $TEST_RESULTS_DIR"

if [[ "$TEST_RESULT" == "SUCCESS" ]]; then
    log_success "全てのE2Eテストが正常に完了しました"
else
    log_error "一部またはすべてのE2Eテストが失敗しました"
    log_error "詳細は $TEST_RESULTS_DIR のレポートを確認してください"
fi

# クリーンアップ
if [[ -n "$SERVER_PID" ]]; then
    log_info "サーバープロセスを終了します (PID: $SERVER_PID)"
    kill "$SERVER_PID" 2>/dev/null || true
fi

# テスト用データベースのクリーンアップ
if [[ -f "test_e2e_ci.db" ]]; then
    rm -f "test_e2e_ci.db"
fi

log_info "E2Eテスト実行スクリプトが完了しました"

exit $EXIT_CODE