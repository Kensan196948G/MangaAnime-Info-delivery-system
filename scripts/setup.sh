#!/bin/bash

# Project Setup Script
# 自己完結型セットアップ

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "  Project Setup - $(basename "$PROJECT_DIR")"
echo "========================================="

# 1. Python環境セットアップ
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$PROJECT_DIR/venv"
fi

# 2. 依存関係インストール
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "Installing Python dependencies..."
    "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
fi

# 3. Node.js依存関係（存在する場合）
if [ -f "$PROJECT_DIR/package.json" ]; then
    echo "Installing Node.js dependencies..."
    cd "$PROJECT_DIR" && npm install
fi

# 4. 設定ファイル初期化
if [ ! -f "$PROJECT_DIR/config/settings.json" ]; then
    echo "Initializing configuration..."
    cat > "$PROJECT_DIR/config/settings.json" << EOL
{
    "project": "$(basename "$PROJECT_DIR")",
    "version": "1.0.0",
    "mcp_enabled": true,
    "agents_count": 20,
    "language": "ja"
}
EOL
fi

# 5. ログディレクトリ初期化
mkdir -p "$PROJECT_DIR/logs"
touch "$PROJECT_DIR/logs/setup_$(date +%Y%m%d).log"

echo "✅ Setup completed successfully!"
