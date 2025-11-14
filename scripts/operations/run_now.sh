#!/bin/bash
# MangaAnime Info Delivery System - Manual Run Script

echo "================================================"
echo "MangaAnime Info Delivery System - Manual Run"
echo "================================================"
echo ""

# プロジェクトディレクトリに移動
cd "$(dirname "${BASH_SOURCE[0]}")"

# Pythonバージョンチェック
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $REQUIRED_VERSION or higher is required (found: $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"

# 仮想環境のチェック
if [ -d "venv" ]; then
    echo "✅ Virtual environment found"
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found"
    echo "   Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    # 依存関係のインストール
    echo "   Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# 設定ファイルのチェック
if [ ! -f "config.json" ]; then
    echo "❌ Error: config.json not found"
    echo "   Please create config.json from config.json.template"
    exit 1
fi

# Google認証ファイルのチェック
if [ ! -f "credentials.json" ]; then
    echo "⚠️  Warning: credentials.json not found"
    echo "   Gmail and Calendar features will not work"
    echo "   Please download credentials from Google Cloud Console"
    echo ""
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ログディレクトリの作成
mkdir -p logs

# オプション解析
VERBOSE=""
DRY_RUN=""
TEST_MODE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE="--verbose"
            shift
            ;;
        --dry-run|-d)
            DRY_RUN="--dry-run"
            echo "🔍 Running in DRY RUN mode (no actual notifications)"
            shift
            ;;
        --test|-t)
            TEST_MODE="--test"
            echo "🧪 Running in TEST mode"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --verbose, -v    Enable verbose logging"
            echo "  --dry-run, -d    Run without sending actual notifications"
            echo "  --test, -t       Run in test mode"
            echo "  --help, -h       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo ""
echo "Starting system..."
echo "================================================"
echo ""

# メインスクリプトの実行
python3 release_notifier.py --config config.json $VERBOSE $DRY_RUN $TEST_MODE

EXIT_CODE=$?

echo ""
echo "================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ System completed successfully"
    echo ""
    echo "Check logs at: logs/"
else
    echo "❌ System failed with exit code: $EXIT_CODE"
    echo ""
    echo "Check error logs at: logs/"
fi
echo "================================================"

exit $EXIT_CODE