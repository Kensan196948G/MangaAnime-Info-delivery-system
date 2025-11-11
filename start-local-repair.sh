#!/bin/bash
# ローカル修復システム起動スクリプト

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/local-repair/daemon.log"

# カラーコード
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ログディレクトリ作成
mkdir -p "$SCRIPT_DIR/logs/local-repair"

# 既存プロセスチェック
if pgrep -f "local-repair-loop.sh start" > /dev/null; then
    echo -e "${YELLOW}⚠️  修復システムは既に実行中です${NC}"
    echo "停止するには: pkill -f 'local-repair-loop.sh'"
    exit 1
fi

echo -e "${CYAN}🔄 ローカル30分サイクル自動修復システムを起動します${NC}"
echo ""
echo "=================================="
echo "  動作モード: バックグラウンド"
echo "  サイクル: 30分ごと"
echo "  最大ループ: 10回（5時間）"
echo "=================================="
echo ""

# バックグラウンドで実行
nohup "$SCRIPT_DIR/scripts/local-repair-loop.sh" start > "$LOG_FILE" 2>&1 &
PID=$!

echo -e "${GREEN}✅ 修復システムを起動しました (PID: $PID)${NC}"
echo ""
echo "📋 コマンド一覧:"
echo "  状態確認: ./scripts/monitor-30min-loop.sh"
echo "  ログ確認: tail -f $LOG_FILE"
echo "  停止: kill $PID"
echo ""
echo -e "${CYAN}ℹ️  システムは自動的に以下を実行します:${NC}"
echo "  1. 30分ごとにGitHubワークフローの失敗を検出"
echo "  2. エラーパターンを分析して自動修復"
echo "  3. 修復不可能な場合はIssueを作成"
echo "  4. 10分後に結果を検証"
echo "  5. 20分待機して次のサイクルへ"

# PIDをファイルに保存
echo $PID > "$SCRIPT_DIR/.repair-daemon.pid"

echo ""
echo -e "${GREEN}修復システムが正常に起動しました！${NC}"