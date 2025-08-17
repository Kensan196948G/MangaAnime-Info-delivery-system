#!/bin/bash
# ローカル自動化システム起動スクリプト

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# カラーコード
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${MAGENTA}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║      ローカル完全自動化システム（Actions代替）        ║${NC}"
echo -e "${MAGENTA}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# 既存プロセスチェック
if pgrep -f "local-automation-system.sh start" > /dev/null; then
    echo -e "${YELLOW}⚠️  自動化システムは既に実行中です${NC}"
    echo "停止するには: pkill -f 'local-automation-system.sh'"
    exit 1
fi

echo -e "${CYAN}📋 システム機能:${NC}"
echo "  ✓ 自動テスト実行"
echo "  ✓ コードLint・フォーマット"
echo "  ✓ 自動ビルド"
echo "  ✓ エラー自動修復"
echo "  ✓ 定期メンテナンス"
echo ""

echo -e "${CYAN}🔄 実行サイクル:${NC}"
echo "  • 30分ごとに全タスク実行"
echo "  • エラー検出時は自動修復"
echo "  • 修正内容は自動コミット"
echo ""

# オプション選択
echo -e "${GREEN}実行モードを選択してください:${NC}"
echo "  1) バックグラウンド実行（推奨）"
echo "  2) フォアグラウンド実行（デバッグ用）"
echo "  3) 単発実行（1回のみ）"
echo "  4) ステータス確認"
echo ""

read -p "選択 (1-4): " choice

case $choice in
    1)
        echo -e "${GREEN}バックグラウンドで起動します...${NC}"
        nohup "$SCRIPT_DIR/scripts/local-automation-system.sh" start > "$SCRIPT_DIR/logs/automation/daemon.log" 2>&1 &
        PID=$!
        echo $PID > "$SCRIPT_DIR/.automation-daemon.pid"
        echo ""
        echo -e "${GREEN}✅ 自動化システムを起動しました (PID: $PID)${NC}"
        echo ""
        echo "📋 管理コマンド:"
        echo "  ログ確認: tail -f $SCRIPT_DIR/logs/automation/daemon.log"
        echo "  状態確認: $SCRIPT_DIR/scripts/local-automation-system.sh status"
        echo "  停止: kill $PID"
        ;;
    2)
        echo -e "${GREEN}フォアグラウンドで起動します...${NC}"
        echo "停止するには Ctrl+C を押してください"
        echo ""
        "$SCRIPT_DIR/scripts/local-automation-system.sh" start
        ;;
    3)
        echo -e "${GREEN}単発実行を開始します...${NC}"
        "$SCRIPT_DIR/scripts/local-automation-system.sh" once
        ;;
    4)
        "$SCRIPT_DIR/scripts/local-automation-system.sh" status
        ;;
    *)
        echo -e "${YELLOW}無効な選択です${NC}"
        exit 1
        ;;
esac