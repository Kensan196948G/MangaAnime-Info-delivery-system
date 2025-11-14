#!/bin/bash

################################################################################
# Web UI Server Startup Script
# アニメ・マンガ情報配信システム
################################################################################

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${BLUE}======================================================================${NC}"
    echo -e "${BLUE}     $1${NC}"
    echo -e "${BLUE}======================================================================${NC}"
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_header "環境チェック"

    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_info "Python: $PYTHON_VERSION"
    else
        print_error "Python3が見つかりません"
        exit 1
    fi

    # Check required files
    if [ ! -f "app/start_web_ui.py" ]; then
        print_error "start_web_ui.pyが見つかりません"
        exit 1
    fi

    if [ ! -f "app/web_app.py" ]; then
        print_error "web_app.pyが見つかりません"
        exit 1
    fi

    # Check optional files
    if [ ! -f "config.json" ]; then
        print_warning "config.jsonが見つかりません (自動生成されます)"
    fi

    if [ ! -f "db.sqlite3" ]; then
        print_warning "db.sqlite3が見つかりません (初回起動時に作成されます)"
    fi

    # Check Python packages
    print_info "必要なPythonパッケージを確認中..."

    if ! python3 -c "import flask" 2>/dev/null; then
        print_error "Flaskがインストールされていません"
        echo ""
        echo "インストール方法:"
        echo "  pip3 install -r requirements.txt"
        exit 1
    fi

    print_info "環境チェック完了"
    echo ""
}

load_env_file() {
    if [ -f ".env" ]; then
        print_info ".envファイルを読み込んでいます..."
        set -a
        source .env
        set +a
        print_info "環境変数を読み込みました"
    fi
}

show_help() {
    cat << EOF
使用方法: $0 [OPTIONS]

オプション:
  -h, --help              このヘルプメッセージを表示
  -p, --port PORT         ポート番号を指定 (デフォルト: 5000)
  -H, --host HOST         ホストアドレスを指定 (デフォルト: 0.0.0.0)
  -d, --debug             デバッグモードで起動
  -l, --localhost         ローカルホストのみでバインド (127.0.0.1)
  --no-reload             自動リロードを無効化
  --check                 環境チェックのみ実行

環境変数:
  SERVER_HOST             サーバーホスト (例: 0.0.0.0)
  SERVER_PORT             サーバーポート (例: 5000)
  DEBUG_MODE              デバッグモード (true/false)
  SECRET_KEY              Flaskシークレットキー

例:
  # デフォルト設定で起動
  $0

  # カスタムポートで起動
  $0 --port 8080

  # デバッグモードで起動
  $0 --debug

  # ローカルホストのみ
  $0 --localhost --port 3000

  # 環境変数を使用
  SERVER_PORT=8080 DEBUG_MODE=true $0

EOF
}

################################################################################
# Main
################################################################################

# Parse arguments
HOST=""
PORT=""
DEBUG=""
LOCALHOST=""
NO_RELOAD=""
CHECK_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -H|--host)
            HOST="$2"
            shift 2
            ;;
        -d|--debug)
            DEBUG="--debug"
            shift
            ;;
        -l|--localhost)
            LOCALHOST="--localhost-only"
            shift
            ;;
        --no-reload)
            NO_RELOAD="--no-auto-reload"
            shift
            ;;
        --check)
            CHECK_ONLY=true
            shift
            ;;
        *)
            print_error "不明なオプション: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
done

# Check requirements
check_requirements

if [ "$CHECK_ONLY" = true ]; then
    print_info "環境チェックのみを実行しました"
    exit 0
fi

# Load .env file if exists
load_env_file

# Build command
CMD="python3 app/start_web_ui.py"

if [ -n "$HOST" ]; then
    CMD="$CMD --host $HOST"
fi

if [ -n "$PORT" ]; then
    CMD="$CMD --port $PORT"
fi

if [ -n "$DEBUG" ]; then
    CMD="$CMD $DEBUG"
fi

if [ -n "$LOCALHOST" ]; then
    CMD="$CMD $LOCALHOST"
fi

if [ -n "$NO_RELOAD" ]; then
    CMD="$CMD $NO_RELOAD"
fi

# Start server
print_header "サーバーを起動しています"
echo ""

exec $CMD
