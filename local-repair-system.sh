#!/bin/bash

# ========================================
# ローカル自動修復システム
# GitHub Actions制限回避用
# ========================================

echo "🤖 ローカル自動修復システム起動"
echo "================================"

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 設定
MAX_ITERATIONS=10
CURRENT_ITERATION=1
REPAIR_STATE_FILE=".repair-state.json"
LOG_DIR="repair-logs"
INTERVAL_SECONDS=1800  # 30分

# ログディレクトリ作成
mkdir -p "$LOG_DIR"

# 状態ファイル初期化
init_state() {
    echo "{
        \"current_iteration\": $CURRENT_ITERATION,
        \"total_errors\": 0,
        \"fixed_errors\": 0,
        \"start_time\": \"$(date -Iseconds)\",
        \"status\": \"running\"
    }" > "$REPAIR_STATE_FILE"
}

# エラー検知
detect_errors() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} 📍 エラー検知開始..."
    
    # テスト実行でエラー検出
    ERROR_COUNT=0
    
    # Python テスト
    if command -v python3 &> /dev/null && [ -f "pytest.ini" ]; then
        echo "  → Pythonテスト実行中..."
        python3 -m pytest tests/ --tb=no -q > "$LOG_DIR/pytest.log" 2>&1
        if [ $? -ne 0 ]; then
            FAILED_COUNT=$(grep -c "FAILED" "$LOG_DIR/pytest.log" 2>/dev/null)
            if [ -z "$FAILED_COUNT" ]; then
                FAILED_COUNT=0
            fi
            ERROR_COUNT=$((ERROR_COUNT + FAILED_COUNT))
        fi
    fi
    
    # Node.js テスト
    if [ -f "package.json" ] && grep -q "\"test\"" package.json; then
        echo "  → Node.jsテスト実行中..."
        if ! npm test > "$LOG_DIR/npm-test.log" 2>&1; then
            ERROR_COUNT=$((ERROR_COUNT + 1))
        fi
    fi
    
    # Lintチェック
    if [ -f ".eslintrc.json" ] || [ -f ".eslintrc.js" ]; then
        echo "  → ESLintチェック中..."
        npx eslint . > "$LOG_DIR/eslint.log" 2>&1
        if [ $? -ne 0 ]; then
            LINT_ERRORS=$(grep -c "error" "$LOG_DIR/eslint.log" 2>/dev/null)
            if [ -z "$LINT_ERRORS" ]; then
                LINT_ERRORS=0
            fi
            ERROR_COUNT=$((ERROR_COUNT + LINT_ERRORS))
        fi
    fi
    
    echo -e "${YELLOW}  検出されたエラー: $ERROR_COUNT 件${NC}"
    return $ERROR_COUNT
}

# エラー修復
repair_errors() {
    local iteration=$1
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} 🔧 修復処理開始 (イテレーション: $iteration/$MAX_ITERATIONS)"
    
    FIXED_COUNT=0
    
    # 依存関係の修復
    if [ -f "package.json" ]; then
        echo "  → 依存関係修復中..."
        npm install --legacy-peer-deps > "$LOG_DIR/npm-install.log" 2>&1
        npm audit fix --force > "$LOG_DIR/npm-audit.log" 2>&1
        FIXED_COUNT=$((FIXED_COUNT + 1))
    fi
    
    # Pythonパッケージ修復
    if [ -f "requirements.txt" ]; then
        echo "  → Python依存関係修復中..."
        pip install -r requirements.txt --quiet 2>&1
        FIXED_COUNT=$((FIXED_COUNT + 1))
    fi
    
    # Lint自動修正
    if [ -f ".eslintrc.json" ] || [ -f ".eslintrc.js" ]; then
        echo "  → Lint自動修正中..."
        npx eslint . --fix > "$LOG_DIR/eslint-fix.log" 2>&1
        FIXED_COUNT=$((FIXED_COUNT + 1))
    fi
    
    # Python format修正
    if command -v black &> /dev/null; then
        echo "  → Python コードフォーマット中..."
        black . --quiet 2>&1
        FIXED_COUNT=$((FIXED_COUNT + 1))
    fi
    
    echo -e "${GREEN}  修復完了: $FIXED_COUNT 項目${NC}"
    return $FIXED_COUNT
}

# コミット処理
commit_fixes() {
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} 📝 変更をコミット中..."
        
        git add -A
        git commit -m "🤖 Auto-repair: Iteration $CURRENT_ITERATION

- 検出エラー: $1 件
- 修復項目: $2 件
- 実行時刻: $(date '+%Y-%m-%d %H:%M:%S')" > /dev/null 2>&1
        
        echo -e "${GREEN}  ✅ コミット完了${NC}"
        
        # オプション: 自動プッシュ（コメントアウトして安全性確保）
        # git push origin main
    else
        echo "  変更なし - コミットスキップ"
    fi
}

# レポート生成
generate_report() {
    local iteration=$1
    local errors=$2
    local fixes=$3
    
    echo ""
    echo "════════════════════════════════════════"
    echo "📊 修復レポート - イテレーション $iteration"
    echo "════════════════════════════════════════"
    echo "  開始時刻: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "  検出エラー: $errors 件"
    echo "  修復項目: $fixes 件"
    echo "  成功率: $(( fixes * 100 / (errors + 1) ))%"
    echo "  次回実行: $(date -d "+30 minutes" '+%Y-%m-%d %H:%M:%S')"
    echo "════════════════════════════════════════"
    echo ""
}

# メインループ
main() {
    echo "🚀 ローカル自動修復システム"
    echo "設定: 最大 $MAX_ITERATIONS イテレーション / 間隔 $INTERVAL_SECONDS 秒"
    echo ""
    
    init_state
    
    while [ $CURRENT_ITERATION -le $MAX_ITERATIONS ]; do
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}イテレーション $CURRENT_ITERATION / $MAX_ITERATIONS 開始${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        
        # エラー検知
        detect_errors
        ERROR_COUNT=$?
        
        if [ $ERROR_COUNT -eq 0 ]; then
            echo -e "${GREEN}✨ エラーなし！システムは健全です。${NC}"
            break
        fi
        
        # エラー修復
        repair_errors $CURRENT_ITERATION
        FIXED_COUNT=$?
        
        # 変更をコミット
        commit_fixes $ERROR_COUNT $FIXED_COUNT
        
        # レポート生成
        generate_report $CURRENT_ITERATION $ERROR_COUNT $FIXED_COUNT
        
        # 次のイテレーション準備
        CURRENT_ITERATION=$((CURRENT_ITERATION + 1))
        
        if [ $CURRENT_ITERATION -le $MAX_ITERATIONS ]; then
            echo "⏳ 次のイテレーションまで待機中..."
            echo "  (Ctrl+C で中断可能)"
            sleep $INTERVAL_SECONDS
        fi
    done
    
    echo ""
    echo -e "${GREEN}🎉 自動修復ループ完了！${NC}"
    echo "ログファイル: $LOG_DIR/"
    echo "状態ファイル: $REPAIR_STATE_FILE"
}

# トラップ設定（Ctrl+C対応）
trap 'echo -e "\n${RED}⚠️  中断されました${NC}"; exit 1' INT

# 実行
main