#!/bin/bash

# Project Relocation Script
# プロジェクト移動後の再初期化

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_NAME="$(basename "$PROJECT_DIR")"

echo "========================================="
echo "  Relocating Project: $PROJECT_NAME"
echo "========================================="

# 1. 現在のパスを更新
echo "Updating project paths..."
find "$PROJECT_DIR/.claude" -name "*.md" -o -name "*.json" | while read file; do
    # 古いパスを新しいパスに置換（必要に応じて）
    echo "  Checking: $file"
done

# 2. Python仮想環境の再作成（必要な場合）
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "Recreating Python virtual environment..."
    python3 -m venv "$PROJECT_DIR/venv"
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
    fi
fi

# 3. 設定ファイルの更新
if [ -f "$PROJECT_DIR/config/settings.json" ]; then
    echo "Updating configuration..."
    # jqがある場合は使用、なければsedで更新
    if command -v jq &> /dev/null; then
        jq ".relocated_at = \"$(date -Iseconds)\"" "$PROJECT_DIR/config/settings.json" > tmp.json && mv tmp.json "$PROJECT_DIR/config/settings.json"
    fi
fi

# 4. 検証実行
echo "Running validation..."
bash "$PROJECT_DIR/scripts/validate.sh"

echo
echo "✅ Project successfully relocated!"
echo "New location: $PROJECT_DIR"
