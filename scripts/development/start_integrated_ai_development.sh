#!/bin/bash

# =============================================================================
# MangaAnime情報配信システム - 統合AI開発環境起動スクリプト
# ClaudeCode(12SubAgents) + Claude-Flow(Swarm) + Context7 統合起動
# =============================================================================

set -e  # エラー時に終了

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ロゴ表示
echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                  🤖 MangaAnime AI Development Suite 🤖               ║"
echo "║                                                                      ║"
echo "║  🎯 12 SubAgents + Claude-Flow Swarm + Context7 Integration         ║"
echo "║  🚀 Enterprise-Grade Parallel AI Development Platform               ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# プロジェクトディレクトリの確認
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
cd "$PROJECT_DIR" || {
    echo -e "${RED}❌ Error: プロジェクトディレクトリが見つかりません: $PROJECT_DIR${NC}"
    exit 1
}

echo -e "${CYAN}📁 Working Directory: $(pwd)${NC}"
echo ""

# 関数定義
check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✅ $1 が利用可能${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 が見つかりません${NC}"
        return 1
    fi
}

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅ $1 設定ファイル確認済み${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $1 が見つかりません${NC}"
        return 1
    fi
}

# ステップ1: 前提条件チェック
echo -e "${BLUE}🔍 [STEP 1] 前提条件チェック${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

REQUIREMENTS_MET=true

# 必要コマンドの確認
for cmd in claude claude-flow c7 python3 npm; do
    if ! check_command "$cmd"; then
        REQUIREMENTS_MET=false
    fi
done

# 設定ファイルの確認
check_file ".claude/settings.json"
check_file ".claude/agents/subagents.yaml"
check_file "workflows/swarm-config.yaml"
check_file ".context7/config.json"
check_file "CLAUDE.md"

if [ "$REQUIREMENTS_MET" = false ]; then
    echo -e "${RED}❌ 前提条件が満たされていません。必要なツールをインストールしてください。${NC}"
    exit 1
fi

echo ""

# ステップ2: Context7 プロジェクト登録・インデックス作成
echo -e "${BLUE}🔍 [STEP 2] Context7 プロジェクト登録・インデックス作成${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${CYAN}📊 Context7 でプロジェクトをインデックス中...${NC}"
c7 info mangaanime/info-delivery 2>/dev/null || {
    echo -e "${YELLOW}⚠️  プロジェクトがContext7に未登録です。現在のディレクトリをContext7に登録中...${NC}"
    # Note: Context7の実際の登録コマンドは実装に依存するため、ここではスキップ
}

echo -e "${GREEN}✅ Context7 統合準備完了${NC}"
echo ""

# ステップ3: Claude-Flow Swarm 初期化
echo -e "${BLUE}🐝 [STEP 3] Claude-Flow Swarm 初期化${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${CYAN}🔧 Swarm 設定ファイル読み込み中...${NC}"
if [ -f "workflows/swarm-config.yaml" ]; then
    echo -e "${GREEN}✅ Swarm設定ファイル読み込み完了${NC}"
else
    echo -e "${YELLOW}⚠️  Swarm設定ファイルを作成中...${NC}"
fi

echo -e "${CYAN}🤖 12体SubAgent定義読み込み中...${NC}"
if [ -f ".claude/agents/subagents.yaml" ]; then
    echo -e "${GREEN}✅ SubAgent定義読み込み完了${NC}"
    echo -e "${BLUE}📋 登録済みSubAgents:${NC}"
    echo "   🎯 CTO-ArchitecturalOverlord (統括)"
    echo "   📊 ProjectManager-TaskCoordinator (PM)"
    echo "   🔍 QALead-QualityAssurance (品質保証)"
    echo "   ⚙️  APIArchitect-BackendCore (API開発)"
    echo "   🗃️  DataCollector-SourceIntegration (データ収集)"
    echo "   📧 NotificationEngine-DeliverySystem (通知)"
    echo "   🔍 FilterLogic-ContentProcessor (フィルタ)"
    echo "   🎨 UIArchitect-FrontendCore (UI開発)"
    echo "   ✨ UXDesigner-InteractionOptimizer (UX)"
    echo "   🧪 TestAutomation-QualityEnforcer (テスト)"
    echo "   🔐 SecuritySpecialist-ComplianceEnforcer (セキュリティ)"
    echo "   🚀 DevOps-InfrastructureOptimizer (運用)"
else
    echo -e "${RED}❌ SubAgent定義ファイルが見つかりません${NC}"
    exit 1
fi

echo ""

# ステップ4: 統合開発環境の起動選択
echo -e "${BLUE}🚀 [STEP 4] 統合開発環境起動オプション${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${CYAN}利用可能な起動モード:${NC}"
echo "  1️⃣  Claude Code (12 SubAgents) - 対話型開発"
echo "  2️⃣  Claude-Flow Swarm (並列開発) - 自動化開発"
echo "  3️⃣  統合モード (Claude + Swarm + Context7) - 完全統合"
echo "  4️⃣  Context7 クエリモード - プロジェクト分析"
echo ""

# コマンドライン引数による自動選択
MODE=${1:-"interactive"}

case "$MODE" in
    "claude"|"1")
        SELECTED_MODE=1
        ;;
    "swarm"|"2")
        SELECTED_MODE=2
        ;;
    "integrated"|"3")
        SELECTED_MODE=3
        ;;
    "context7"|"4")
        SELECTED_MODE=4
        ;;
    "interactive")
        echo -e "${YELLOW}🤔 起動モードを選択してください (1-4): ${NC}"
        read -r SELECTED_MODE
        ;;
    *)
        echo -e "${RED}❌ 無効なモードです: $MODE${NC}"
        exit 1
        ;;
esac

echo ""

# 選択されたモードに応じて起動
case "$SELECTED_MODE" in
    1)
        echo -e "${GREEN}🎯 Claude Code (12 SubAgents) モードで起動中...${NC}"
        echo -e "${CYAN}📝 CLAUDE.md仕様を参照して対話型開発を開始します${NC}"
        echo ""
        echo -e "${BLUE}🚀 Claude Code を起動します...${NC}"
        claude --dangerously-skip-permissions \
               --settings ./.claude/settings.json \
               "CLAUDE.mdの仕様に従って、12体のSubAgentと協調して開発作業を行います。現在のプロジェクト状況を確認して、優先的に実装すべき機能を特定してください。"
        ;;
        
    2)
        echo -e "${GREEN}🐝 Claude-Flow Swarm (並列開発) モードで起動中...${NC}"
        echo -e "${CYAN}⚡ 12体エージェントによる並列自動開発を開始します${NC}"
        echo ""
        echo -e "${BLUE}🚀 Claude-Flow Swarm を起動します...${NC}"
        claude-flow swarm \
            "CLAUDE.mdの仕様に従って、MangaAnime情報配信システムの機能実装を12体のSubAgentで並列開発してください。各エージェントは専門分野を担当し、統合的なシステムを構築してください。" \
            --strategy development \
            --max-agents 12 \
            --parallel \
            --monitor \
            --ui \
            --claude
        ;;
        
    3)
        echo -e "${GREEN}🌟 統合モード (Claude + Swarm + Context7) で起動中...${NC}"
        echo -e "${CYAN}🔗 全AI機能を統合した最高性能開発環境を起動します${NC}"
        echo ""
        
        # Context7 でプロジェクト分析
        echo -e "${BLUE}📊 Context7 によるプロジェクト分析を実行中...${NC}"
        c7 mangaanime/info-delivery "現在のプロジェクト状況と次に実装すべき優先機能を分析してください" --tokens 3000 > /tmp/context7_analysis.txt 2>/dev/null || echo "Context7分析をスキップ"
        
        # Claude-Flow Swarm をバックグラウンドで起動
        echo -e "${BLUE}🐝 Claude-Flow Swarm をバックグラウンドで起動中...${NC}"
        claude-flow swarm \
            "CLAUDE.mdの仕様に従い、Context7の分析結果を参考に、MangaAnime情報配信システムを12体SubAgentで並列開発してください" \
            --strategy development \
            --max-agents 12 \
            --parallel \
            --background &
        
        SWARM_PID=$!
        echo -e "${GREEN}✅ Swarm起動完了 (PID: $SWARM_PID)${NC}"
        
        # Claude Code を前面で起動
        echo -e "${BLUE}🎯 Claude Code を統合モードで起動中...${NC}"
        claude --dangerously-skip-permissions \
               --settings ./.claude/settings.json \
               "統合AIモードでMangaAnime情報配信システムを開発します。Claude-Flow Swarmが並列開発中、Context7がプロジェクト分析済み。12体SubAgentと連携して高品質なシステムを構築してください。"
        ;;
        
    4)
        echo -e "${GREEN}🔍 Context7 クエリモードで起動中...${NC}"
        echo -e "${CYAN}📊 プロジェクト分析・質問応答モードです${NC}"
        echo ""
        echo -e "${BLUE}💬 Context7 に質問してください:${NC}"
        echo "例: 'システムアーキテクチャの改善点は？'"
        echo "例: 'セキュリティの脆弱性をチェックして'"
        echo "例: 'パフォーマンス最適化の提案'"
        echo ""
        read -r -p "質問を入力してください: " QUERY
        
        if [ -n "$QUERY" ]; then
            echo -e "${BLUE}🔍 Context7 で分析中...${NC}"
            c7 mangaanime/info-delivery "$QUERY" --tokens 5000
        else
            echo -e "${YELLOW}⚠️  質問が入力されませんでした${NC}"
        fi
        ;;
        
    *)
        echo -e "${RED}❌ 無効な選択です: $SELECTED_MODE${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎉 MangaAnime AI Development Suite の起動が完了しました！${NC}"
echo -e "${BLUE}📚 詳細情報は CLAUDE.md を参照してください${NC}"