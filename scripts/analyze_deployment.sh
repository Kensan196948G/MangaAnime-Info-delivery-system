#!/bin/bash

# デプロイメント設定分析スクリプト
# 作成日: 2025-12-06

PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"

echo "========================================="
echo "デプロイメント設定分析"
echo "========================================="
echo ""

# Makefileの確認
echo "--- Makefile確認 ---"
if [ -f "$PROJECT_ROOT/Makefile" ]; then
    echo "Makefileが存在します"
    echo ""
    echo "定義されているターゲット:"
    grep "^[a-zA-Z_-]*:" "$PROJECT_ROOT/Makefile" | sed 's/:.*$//'
    echo ""
else
    echo "Makefileは存在しません"
    echo ""
fi

# package.jsonの確認
echo "--- package.json確認 ---"
if [ -f "$PROJECT_ROOT/package.json" ]; then
    echo "package.jsonが存在します"
    echo ""
    echo "定義されているスクリプト:"
    grep -A 20 '"scripts"' "$PROJECT_ROOT/package.json" | grep '"' | grep -v '"scripts"' | sed 's/^[[:space:]]*//'
    echo ""
else
    echo "package.jsonは存在しません"
    echo ""
fi

# Dockerファイルの確認
echo "--- Docker設定確認 ---"
docker_files=$(find "$PROJECT_ROOT" -maxdepth 2 -name "Dockerfile*" -o -name "docker-compose*.yml")
if [ -n "$docker_files" ]; then
    echo "Dockerファイルが見つかりました:"
    echo "$docker_files" | while read -r file; do
        echo "  - $(basename "$file")"
    done
    echo ""
else
    echo "Dockerファイルは見つかりませんでした"
    echo ""
fi

# cron設定の確認
echo "--- cron設定確認 ---"
if [ -f "/etc/crontab" ]; then
    echo "システムcrontabからプロジェクト関連のエントリを検索:"
    grep -i "mangaanime\|release_notifier" /etc/crontab 2>/dev/null || echo "  該当なし"
    echo ""
fi

if [ -f "$PROJECT_ROOT/crontab" ] || [ -f "$PROJECT_ROOT/config/crontab" ]; then
    echo "プロジェクト内のcrontabファイル:"
    find "$PROJECT_ROOT" -name "crontab" -type f
    echo ""
fi

# スクリプトディレクトリの確認
echo "--- 実行スクリプト確認 ---"
if [ -d "$PROJECT_ROOT/scripts" ]; then
    echo "scripts/ディレクトリ内のスクリプト:"
    ls -lh "$PROJECT_ROOT/scripts"/*.sh 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    echo ""
fi

# 環境変数ファイルの確認
echo "--- 環境変数ファイル確認 ---"
env_files=$(find "$PROJECT_ROOT" -maxdepth 2 -name ".env*" -o -name "*.env")
if [ -n "$env_files" ]; then
    echo "環境変数ファイルが見つかりました:"
    echo "$env_files" | while read -r file; do
        echo "  - $(basename "$file")"
        if [ -f "$file" ]; then
            echo "    変数数: $(grep -c "^[A-Z_]" "$file" 2>/dev/null || echo 0)"
        fi
    done
    echo ""
else
    echo "環境変数ファイルは見つかりませんでした"
    echo ""
fi

# 設定ファイルの確認
echo "--- 設定ファイル確認 ---"
config_files=$(find "$PROJECT_ROOT/config" -type f 2>/dev/null | head -20)
if [ -n "$config_files" ]; then
    echo "config/ディレクトリ内のファイル:"
    echo "$config_files" | while read -r file; do
        echo "  - $(basename "$file")"
    done
    echo ""
fi

# requirements.txtの確認
echo "--- Python依存関係確認 ---"
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    echo "requirements.txtが存在します"
    echo "パッケージ数: $(grep -c "^[a-zA-Z]" "$PROJECT_ROOT/requirements.txt")"
    echo ""
    echo "主要パッケージ:"
    head -20 "$PROJECT_ROOT/requirements.txt"
    echo ""
else
    echo "requirements.txtは存在しません"
    echo ""
fi

echo "========================================="
echo "分析完了"
echo "========================================="
