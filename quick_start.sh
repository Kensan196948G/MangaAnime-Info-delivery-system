#!/bin/bash

# =============================================================================
# クイックスタート - MangaAnime AI開発環境
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 MangaAnime AI Development - Quick Start${NC}"
echo ""

# 引数チェック
if [ $# -eq 0 ]; then
    echo "使用方法:"
    echo "  ./quick_start.sh claude      # Claude Code (12 SubAgents)"
    echo "  ./quick_start.sh swarm       # Claude-Flow Swarm 並列開発"
    echo "  ./quick_start.sh integrated  # 統合モード (推奨)"
    echo "  ./quick_start.sh context7    # Context7 分析モード"
    echo ""
    echo -e "${GREEN}推奨: ./quick_start.sh integrated${NC}"
    exit 1
fi

# メインスクリプトを引数付きで実行
exec ./start_integrated_ai_development.sh "$1"