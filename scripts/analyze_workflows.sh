#!/bin/bash

# GitHub Actionsワークフロー分析スクリプト
# 作成日: 2025-12-06

WORKFLOWS_DIR="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/.github/workflows"
OUTPUT_FILE="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/docs/operations/workflows-inventory.json"

echo "========================================="
echo "GitHub Actionsワークフロー分析"
echo "========================================="
echo ""

# ワークフローディレクトリの確認
if [ ! -d "$WORKFLOWS_DIR" ]; then
    echo "エラー: .github/workflows/ ディレクトリが存在しません"
    exit 1
fi

echo "ワークフローディレクトリ: $WORKFLOWS_DIR"
echo ""

# ファイル数をカウント
WORKFLOW_COUNT=$(find "$WORKFLOWS_DIR" -name "*.yml" -o -name "*.yaml" | wc -l)
echo "検出されたワークフローファイル数: $WORKFLOW_COUNT"
echo ""

# 各ワークフローファイルの詳細を表示
echo "========================================="
echo "ワークフローファイル一覧:"
echo "========================================="

find "$WORKFLOWS_DIR" -name "*.yml" -o -name "*.yaml" | sort | while read -r file; do
    filename=$(basename "$file")
    echo ""
    echo "--- $filename ---"
    echo "パス: $file"

    # nameフィールドを抽出
    name=$(grep -m 1 "^name:" "$file" | sed 's/name: *//' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
    echo "名前: $name"

    # onトリガーを抽出
    echo "トリガー:"
    grep -A 10 "^on:" "$file" | grep -E "^  [a-z_]+:" | sed 's/://' | sed 's/^  /  - /'

    # scheduleがあるか確認
    if grep -q "schedule:" "$file"; then
        echo "  - schedule (cron)"
        grep -A 2 "cron:" "$file" | grep "cron:" | sed 's/.*cron: */    cron: /'
    fi

    # jobsの数をカウント
    jobs_count=$(grep -E "^  [a-z_-]+:" "$file" | grep -v "on:" | grep -v "env:" | wc -l)
    echo "ジョブ数: $jobs_count"

    # ファイルサイズ
    size=$(stat -c%s "$file")
    echo "サイズ: $size bytes"

    echo ""
done

echo ""
echo "========================================="
echo "ワークフロー種別の集計"
echo "========================================="

# トリガー種別の集計
echo ""
echo "トリガー種別:"
echo "  - push: $(grep -l "^  push:" "$WORKFLOWS_DIR"/*.y*ml 2>/dev/null | wc -l) 個"
echo "  - pull_request: $(grep -l "^  pull_request:" "$WORKFLOWS_DIR"/*.y*ml 2>/dev/null | wc -l) 個"
echo "  - schedule: $(grep -l "schedule:" "$WORKFLOWS_DIR"/*.y*ml 2>/dev/null | wc -l) 個"
echo "  - workflow_dispatch: $(grep -l "workflow_dispatch:" "$WORKFLOWS_DIR"/*.y*ml 2>/dev/null | wc -l) 個"
echo "  - workflow_run: $(grep -l "workflow_run:" "$WORKFLOWS_DIR"/*.y*ml 2>/dev/null | wc -l) 個"

echo ""
echo "使用されているActions:"
grep -h "uses:" "$WORKFLOWS_DIR"/*.y*ml 2>/dev/null | sed 's/.*uses: *//' | sort | uniq -c | sort -rn

echo ""
echo "========================================="
echo "分析完了"
echo "========================================="
