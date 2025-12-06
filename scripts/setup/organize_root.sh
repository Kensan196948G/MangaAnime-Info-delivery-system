#!/bin/bash

# プロジェクトルート整理スクリプト
# 実行日: 2025-12-06

set -e

PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "プロジェクトルート整理開始"
echo "=========================================="

# 1. バックアップフォルダの作成（存在しない場合）
if [ ! -d "backups" ]; then
    mkdir -p backups
    echo "✓ backups/ フォルダを作成しました"
fi

# 2. データフォルダの作成（存在しない場合）
if [ ! -d "data" ]; then
    mkdir -p data
    echo "✓ data/ フォルダを作成しました"
fi

# 3. ツールフォルダの作成（存在しない場合）
if [ ! -d "tools" ]; then
    mkdir -p tools
    echo "✓ tools/ フォルダを作成しました"
fi

echo ""
echo "=========================================="
echo "ファイル移動・削除処理"
echo "=========================================="

# 4. db.sqlite3.backup_* ファイルを backups/ に移動
echo ""
echo "[1] SQLiteバックアップファイルの移動:"
for backup_file in db.sqlite3.backup_*; do
    if [ -f "$backup_file" ]; then
        mv "$backup_file" backups/
        echo "  ✓ $backup_file → backups/"
    fi
done

# 5. 調査用一時ファイルを削除
echo ""
echo "[2] 調査用一時ファイルの削除:"
for temp_file in .investigation_script.sh .run_investigation.sh; do
    if [ -f "$temp_file" ]; then
        rm "$temp_file"
        echo "  ✓ $temp_file を削除"
    fi
done

# 6. config.json.bak を backups/ に移動
echo ""
echo "[3] 設定バックアップファイルの移動:"
if [ -f "config.json.bak" ]; then
    mv config.json.bak backups/
    echo "  ✓ config.json.bak → backups/"
fi

# 7. テストDBファイルを data/ に移動
echo ""
echo "[4] テストDBファイルの移動:"
for test_db in test_history.db test_notification.db; do
    if [ -f "$test_db" ]; then
        mv "$test_db" data/
        echo "  ✓ $test_db → data/"
    fi
done

# 8. actionlint バイナリを tools/ に移動
echo ""
echo "[5] actionlintバイナリの移動:"
if [ -f "actionlint" ]; then
    mv actionlint tools/
    chmod +x tools/actionlint
    echo "  ✓ actionlint → tools/"
fi

echo ""
echo "=========================================="
echo "整理完了サマリ"
echo "=========================================="
echo ""
echo "移動先フォルダの内容:"
echo ""
echo "backups/:"
ls -lh backups/ 2>/dev/null || echo "  (ファイルなし)"
echo ""
echo "data/:"
ls -lh data/ 2>/dev/null || echo "  (ファイルなし)"
echo ""
echo "tools/:"
ls -lh tools/ 2>/dev/null || echo "  (ファイルなし)"
echo ""
echo "=========================================="
echo "✓ プロジェクトルート整理が完了しました"
echo "=========================================="
