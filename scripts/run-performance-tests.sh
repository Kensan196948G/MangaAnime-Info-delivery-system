#!/bin/bash

###############################################################################
# パフォーマンステスト実行スクリプト
# Usage: ./scripts/run-performance-tests.sh [options]
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
PERF_DIR="${PROJECT_ROOT}/tests/performance"
RESULTS_DIR="${PROJECT_ROOT}/performance-results"

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
パフォーマンステスト実行スクリプト

Usage: $0 [OPTIONS]

OPTIONS:
    -h, --help                  ヘルプを表示
    -u, --users N               同時接続ユーザー数 (デフォルト: 100)
    -r, --spawn-rate N          スポーンレート (デフォルト: 10)
    -t, --time DURATION         実行時間 (例: 5m, 1h)
    -s, --scenario SCENARIO     シナリオ指定 (AnimeUser|PowerUser|Admin|Stress)
    --host URL                  ターゲットURL (デフォルト: http://localhost:5000)
    --headless                  ヘッドレスモードで実行
    --web                       Web UIモードで実行
    --csv                       CSV出力を有効化
    --tags TAG                  タグでフィルタリング

EXAMPLES:
    $0                                  # デフォルト設定で実行
    $0 -u 100 -r 10 -t 5m              # 100ユーザー、5分間
    $0 -s StressTestUser -u 500        # ストレステスト
    $0 --web                            # Web UIモード
    $0 --tags homepage --tags works    # 特定機能のみ
EOF
}

# デフォルト値
USERS=100
SPAWN_RATE=10
RUN_TIME="5m"
SCENARIO=""
HOST="http://localhost:5000"
HEADLESS=false
WEB_MODE=false
CSV_OUTPUT=false
TAGS=""

# オプション解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -r|--spawn-rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -t|--time)
            RUN_TIME="$2"
            shift 2
            ;;
        -s|--scenario)
            SCENARIO="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --headless)
            HEADLESS=true
            shift
            ;;
        --web)
            WEB_MODE=true
            shift
            ;;
        --csv)
            CSV_OUTPUT=true
            shift
            ;;
        --tags)
            TAGS="${TAGS} --tags $2"
            shift 2
            ;;
        *)
            log_error "不明なオプション: $1"
            show_help
            exit 1
            ;;
    esac
done

# Locustのインストール確認
if ! command -v locust &> /dev/null; then
    log_error "Locust がインストールされていません"
    log_info "インストール: pip install locust"
    exit 1
fi

# 結果ディレクトリの作成
mkdir -p "${RESULTS_DIR}"

# アプリケーションの起動確認
log_info "アプリケーションの起動を確認しています..."
log_info "ターゲット: ${HOST}"

if curl -s "${HOST}/api/health" > /dev/null; then
    log_success "アプリケーションが起動しています"
else
    log_error "アプリケーションが起動していません: ${HOST}"
    log_info "アプリケーションを起動してください: python app/app.py"
    exit 1
fi

# テスト実行
cd "${PERF_DIR}"

log_info "パフォーマンステストを開始します..."
log_info "ユーザー数: ${USERS}"
log_info "スポーンレート: ${SPAWN_RATE}"
log_info "実行時間: ${RUN_TIME}"
log_info "シナリオ: ${SCENARIO:-すべて}"

# Web UIモード
if [ "$WEB_MODE" = true ]; then
    log_info "Web UIモードで起動します"
    log_info "ブラウザで http://localhost:8089 にアクセスしてください"

    COMMAND="locust -f locustfile.py --host=${HOST}"

    if [ -n "$SCENARIO" ]; then
        COMMAND="${COMMAND} ${SCENARIO}"
    fi

    if [ -n "$TAGS" ]; then
        COMMAND="${COMMAND} ${TAGS}"
    fi

    log_info "実行コマンド: ${COMMAND}"
    eval "${COMMAND}"

    exit 0
fi

# ヘッドレスモード
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_PREFIX="${RESULTS_DIR}/perf_test_${TIMESTAMP}"

COMMAND="locust -f locustfile.py"
COMMAND="${COMMAND} --host=${HOST}"
COMMAND="${COMMAND} --users=${USERS}"
COMMAND="${COMMAND} --spawn-rate=${SPAWN_RATE}"
COMMAND="${COMMAND} --run-time=${RUN_TIME}"

if [ "$HEADLESS" = true ]; then
    COMMAND="${COMMAND} --headless"
fi

if [ "$CSV_OUTPUT" = true ]; then
    COMMAND="${COMMAND} --csv=${OUTPUT_PREFIX}"
fi

if [ -n "$SCENARIO" ]; then
    COMMAND="${COMMAND} ${SCENARIO}"
fi

if [ -n "$TAGS" ]; then
    COMMAND="${COMMAND} ${TAGS}"
fi

# 実行
log_info "実行コマンド: ${COMMAND}"
echo ""

if eval "${COMMAND}"; then
    log_success "✅ パフォーマンステスト完了"

    # 結果の表示
    if [ "$CSV_OUTPUT" = true ]; then
        echo ""
        log_info "結果ファイル:"
        ls -lh "${OUTPUT_PREFIX}"*.csv

        echo ""
        log_info "統計サマリー:"
        if [ -f "${OUTPUT_PREFIX}_stats.csv" ]; then
            head -n 10 "${OUTPUT_PREFIX}_stats.csv"
        fi

        # 失敗したリクエストの確認
        if [ -f "${OUTPUT_PREFIX}_failures.csv" ]; then
            FAILURE_COUNT=$(wc -l < "${OUTPUT_PREFIX}_failures.csv")
            if [ "$FAILURE_COUNT" -gt 1 ]; then
                log_warning "失敗したリクエスト: $((FAILURE_COUNT - 1)) 件"
                echo ""
                log_info "失敗の詳細:"
                head -n 5 "${OUTPUT_PREFIX}_failures.csv"
            else
                log_success "失敗したリクエストはありません"
            fi
        fi
    fi

    echo ""
    log_info "詳細なレポートを生成するには:"
    log_info "  python scripts/generate_perf_report.py ${OUTPUT_PREFIX}_stats.csv"

    exit 0
else
    log_error "❌ パフォーマンステストが失敗しました"
    exit 1
fi
