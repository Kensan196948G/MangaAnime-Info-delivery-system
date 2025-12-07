#!/bin/bash

# クイックDevOpsチェックスクリプト
PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"

echo "=== GitHub Actionsワークフロー ==="
if [ -d "$PROJECT_ROOT/.github/workflows" ]; then
    ls -1 "$PROJECT_ROOT/.github/workflows"
    echo "合計: $(ls -1 "$PROJECT_ROOT/.github/workflows" | wc -l) ファイル"
else
    echo ".github/workflows ディレクトリは存在しません"
    echo "作成が必要です"
fi

echo ""
echo "=== Docker設定 ==="
ls -1 "$PROJECT_ROOT" | grep -i docker || echo "Dockerファイルなし"

echo ""
echo "=== Make/スクリプト ==="
[ -f "$PROJECT_ROOT/Makefile" ] && echo "Makefile: 存在" || echo "Makefile: なし"
[ -f "$PROJECT_ROOT/package.json" ] && echo "package.json: 存在" || echo "package.json: なし"
[ -d "$PROJECT_ROOT/scripts" ] && echo "scripts/: 存在 ($(ls -1 "$PROJECT_ROOT/scripts" | wc -l) ファイル)" || echo "scripts/: なし"

echo ""
echo "=== Python設定 ==="
[ -f "$PROJECT_ROOT/requirements.txt" ] && echo "requirements.txt: 存在 ($(wc -l < "$PROJECT_ROOT/requirements.txt") 行)" || echo "requirements.txt: なし"
[ -f "$PROJECT_ROOT/setup.py" ] && echo "setup.py: 存在" || echo "setup.py: なし"

echo ""
echo "=== 環境設定 ==="
ls -1a "$PROJECT_ROOT" | grep "^\.env" || echo "環境変数ファイルなし"

echo ""
echo "=== config/ディレクトリ ==="
if [ -d "$PROJECT_ROOT/config" ]; then
    ls -1 "$PROJECT_ROOT/config" | head -10
    total=$(ls -1 "$PROJECT_ROOT/config" | wc -l)
    [ $total -gt 10 ] && echo "... 他 $((total - 10)) ファイル"
else
    echo "config/ディレクトリは存在しません"
fi
