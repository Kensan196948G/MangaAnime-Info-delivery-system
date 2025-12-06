#!/bin/bash
# データ収集タスク実行スクリプト（統合版）
# 作成日: 2025-12-06
# 目的: 収集前確認→収集実行→検証→レポート生成を一括実行

set -e  # エラー時に停止

PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
cd "$PROJECT_ROOT"

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}データ収集タスク統合実行${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo "プロジェクトルート: $PROJECT_ROOT"
echo "実行日時: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ステップ1: 環境確認
echo -e "${YELLOW}[1/5] 環境確認中...${NC}"
echo ""

# Python確認
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Python: $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python3が見つかりません"
    exit 1
fi

# SQLite確認
if command -v sqlite3 &> /dev/null; then
    SQLITE_VERSION=$(sqlite3 --version | awk '{print $1}')
    echo -e "${GREEN}✓${NC} SQLite: $SQLITE_VERSION"
else
    echo -e "${RED}✗${NC} SQLite3が見つかりません"
    exit 1
fi

# データベースファイル確認
if [ -f "db.sqlite3" ]; then
    DB_SIZE=$(du -h db.sqlite3 | awk '{print $1}')
    echo -e "${GREEN}✓${NC} データベース: db.sqlite3 ($DB_SIZE)"
else
    echo -e "${YELLOW}⚠${NC} データベースファイルが見つかりません（初回実行時は正常）"
fi

# config.json確認
if [ -f "config.json" ]; then
    echo -e "${GREEN}✓${NC} 設定ファイル: config.json"
else
    echo -e "${RED}✗${NC} config.jsonが見つかりません"
    exit 1
fi

echo ""

# ステップ2: 収集前データ件数確認
echo -e "${YELLOW}[2/5] 収集前データ件数確認...${NC}"
echo ""

if [ -f "db.sqlite3" ]; then
    WORKS_BEFORE=$(sqlite3 db.sqlite3 "SELECT COUNT(*) FROM works;" 2>/dev/null || echo "0")
    RELEASES_BEFORE=$(sqlite3 db.sqlite3 "SELECT COUNT(*) FROM releases;" 2>/dev/null || echo "0")
    echo "  作品数: $WORKS_BEFORE"
    echo "  リリース数: $RELEASES_BEFORE"
else
    WORKS_BEFORE=0
    RELEASES_BEFORE=0
    echo "  データベース未作成（初回実行）"
fi

echo ""

# ステップ3: データ収集実行
echo -e "${YELLOW}[3/5] データ収集実行中...${NC}"
echo ""

# データベースバックアップ（既存の場合）
if [ -f "db.sqlite3" ] && [ "$WORKS_BEFORE" -gt 0 ]; then
    mkdir -p backups
    BACKUP_FILE="backups/db_backup_$(date '+%Y%m%d_%H%M%S').sqlite3"
    cp db.sqlite3 "$BACKUP_FILE"
    echo -e "${GREEN}✓${NC} バックアップ作成: $BACKUP_FILE"
    echo ""
fi

# 収集スクリプト実行
chmod +x scripts/collect_all_data.py

echo "収集開始..."
if python3 scripts/collect_all_data.py; then
    echo -e "${GREEN}✓${NC} データ収集完了"
else
    echo -e "${RED}✗${NC} データ収集中にエラーが発生しました"
    echo "詳細はログファイルを確認してください: logs/"
    exit 1
fi

echo ""

# ステップ4: 収集後データ件数確認
echo -e "${YELLOW}[4/5] 収集後データ件数確認...${NC}"
echo ""

if [ -f "db.sqlite3" ]; then
    WORKS_AFTER=$(sqlite3 db.sqlite3 "SELECT COUNT(*) FROM works;" 2>/dev/null || echo "0")
    RELEASES_AFTER=$(sqlite3 db.sqlite3 "SELECT COUNT(*) FROM releases;" 2>/dev/null || echo "0")

    WORKS_DIFF=$((WORKS_AFTER - WORKS_BEFORE))
    RELEASES_DIFF=$((RELEASES_AFTER - RELEASES_BEFORE))

    echo "  作品数: $WORKS_AFTER (+$WORKS_DIFF)"
    echo "  リリース数: $RELEASES_AFTER (+$RELEASES_DIFF)"

    if [ "$WORKS_DIFF" -gt 0 ] || [ "$RELEASES_DIFF" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} 新規データが追加されました"
    else
        echo -e "${YELLOW}⚠${NC} 新規データが追加されませんでした"
    fi
else
    echo -e "${RED}✗${NC} データベースが見つかりません"
    exit 1
fi

echo ""

# ステップ5: データ検証実行
echo -e "${YELLOW}[5/5] データ検証実行中...${NC}"
echo ""

chmod +x scripts/verify_data_collection.py

if python3 scripts/verify_data_collection.py; then
    echo -e "${GREEN}✓${NC} データ検証完了"
else
    echo -e "${YELLOW}⚠${NC} データ検証中に警告が発生しました"
fi

echo ""

# 完了サマリー
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}データ収集タスク完了サマリー${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo "【収集結果】"
echo "  追加作品数: $WORKS_DIFF"
echo "  追加リリース数: $RELEASES_DIFF"
echo ""
echo "【現在のデータ総数】"
echo "  総作品数: $WORKS_AFTER"
echo "  総リリース数: $RELEASES_AFTER"
echo ""
echo "【出力ファイル】"
echo "  検証レポート: logs/data_collection_report.json"
echo "  実行ログ: logs/data_collection_*.log"
if [ -f "$BACKUP_FILE" ]; then
    echo "  バックアップ: $BACKUP_FILE"
fi
echo ""
echo "【次のステップ】"
echo "  1. レポート確認: cat logs/data_collection_report.json | jq"
echo "  2. データ確認: sqlite3 db.sqlite3 'SELECT * FROM works LIMIT 10;'"
echo "  3. Web UI起動: python3 app/app.py"
echo ""
echo -e "${GREEN}タスク完了: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${BLUE}=========================================${NC}"
