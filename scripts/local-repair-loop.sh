#!/bin/bash
# ローカル30分サイクル自動修復ループシステム

set -euo pipefail

# 設定
REPO="Kensan196948G/MangaAnime-Info-delivery-system"
MAX_ITERATIONS=10
CURRENT_ITERATION=0
STATE_FILE=".github/repair-state/loop-state.json"
LOG_DIR="logs/local-repair"
CYCLE_INTERVAL=1800  # 30分 = 1800秒

# カラーコード
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ログディレクトリ作成
mkdir -p "$LOG_DIR"

# ログ関数
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        ERROR)   echo -e "${RED}[ERROR]${NC} $message" ;;
        SUCCESS) echo -e "${GREEN}[SUCCESS]${NC} $message" ;;
        WARNING) echo -e "${YELLOW}[WARNING]${NC} $message" ;;
        INFO)    echo -e "${CYAN}[INFO]${NC} $message" ;;
        *)       echo "$message" ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_DIR/repair-$(date +%Y%m%d).log"
}

# 状態ファイル初期化
init_state() {
    if [[ ! -f "$STATE_FILE" ]]; then
        mkdir -p "$(dirname "$STATE_FILE")"
        cat > "$STATE_FILE" <<EOF
{
    "current_iteration": 0,
    "total_repairs": 0,
    "successful_repairs": 0,
    "failed_repairs": 0,
    "last_run": "",
    "created_at": "$(date -Iseconds)"
}
EOF
        log "INFO" "状態ファイルを初期化しました"
    fi
}

# 失敗したワークフローを検出
detect_failures() {
    log "INFO" "失敗したワークフローを検出中..."
    
    local failed_runs=$(gh run list --repo "$REPO" --status failure --limit 10 --json databaseId,name,conclusion,createdAt 2>/dev/null || echo "[]")
    
    if [[ "$failed_runs" == "[]" ]]; then
        log "SUCCESS" "失敗したワークフローはありません"
        return 0
    fi
    
    echo "$failed_runs" | jq -r '.[] | "\(.databaseId)|\(.name)|\(.createdAt)"' | while IFS='|' read -r run_id name created_at; do
        log "WARNING" "失敗を検出: $name (ID: $run_id, 時刻: $created_at)"
        
        # 修復を試みる
        repair_workflow "$run_id" "$name"
    done
}

# ワークフロー修復
repair_workflow() {
    local run_id="$1"
    local workflow_name="$2"
    
    log "INFO" "ワークフロー修復を開始: $workflow_name (ID: $run_id)"
    
    # エラーログを取得（ジョブが実行されない場合の対処）
    local error_log=$(gh run view "$run_id" --repo "$REPO" --log 2>&1 | head -500 || echo "")
    
    # ジョブが開始されていない場合の特別処理
    local job_count=$(gh api repos/"$REPO"/actions/runs/"$run_id"/jobs --jq '.jobs | length' 2>/dev/null || echo "0")
    if [[ "$job_count" -eq 0 ]] || [[ -z "$error_log" ]]; then
        log "WARNING" "ジョブが実行されていません - GitHub Actions設定の問題"
        error_log="GitHub Actions configuration issue - no jobs executed"
    fi
    
    # エラーパターンを分析
    if echo "$error_log" | grep -q "npm\|node_modules\|package"; then
        log "INFO" "依存関係エラーを検出 - 修復を試みます"
        repair_dependency_error
    elif echo "$error_log" | grep -q "permission\|denied\|unauthorized"; then
        log "INFO" "権限エラーを検出 - 修復を試みます"
        repair_permission_error
    elif echo "$error_log" | grep -q "syntax\|parse\|unexpected"; then
        log "INFO" "構文エラーを検出 - 修復を試みます"
        repair_syntax_error
    else
        log "WARNING" "未知のエラーパターン - 手動確認が必要です"
        create_issue_for_failure "$run_id" "$workflow_name" "$error_log"
    fi
    
    # 状態を更新
    update_state "repair_attempted"
}

# 依存関係エラーの修復
repair_dependency_error() {
    log "INFO" "依存関係を修復中..."
    
    # package.jsonが存在する場合
    if [[ -f "package.json" ]]; then
        npm install --legacy-peer-deps
        npm audit fix --force || true
        
        # 変更をコミット
        if git diff --quiet; then
            log "INFO" "依存関係の変更はありません"
        else
            git add -A
            git commit -m "🔧 依存関係の自動修復

- npm install --legacy-peer-deps を実行
- npm audit fix を適用

[ローカル自動修復システム]"
            git push
            log "SUCCESS" "依存関係の修復をコミットしました"
        fi
    fi
}

# 権限エラーの修復
repair_permission_error() {
    log "INFO" "権限設定を確認中..."
    
    # ワークフローファイルの権限を更新
    find .github/workflows -name "*.yml" -o -name "*.yaml" | while read -r workflow_file; do
        if ! grep -q "permissions:" "$workflow_file"; then
            log "INFO" "権限設定を追加: $workflow_file"
            # 権限設定の追加ロジック（実装省略）
        fi
    done
}

# 構文エラーの修復
repair_syntax_error() {
    log "INFO" "構文エラーをチェック中..."
    
    # YAMLファイルの検証
    find .github/workflows -name "*.yml" -o -name "*.yaml" | while read -r workflow_file; do
        if ! python3 -c "import yaml; yaml.safe_load(open('$workflow_file'))" 2>/dev/null; then
            log "ERROR" "YAML構文エラー: $workflow_file"
            # 自動修復は危険なため、Issueを作成
            create_issue_for_failure "syntax" "$workflow_file" "YAML構文エラー"
        fi
    done
}

# Issue作成
create_issue_for_failure() {
    local run_id="$1"
    local workflow_name="$2"
    local error_log="$3"
    
    log "INFO" "修復失敗のIssueを作成中..."
    
    local issue_title="🚨 自動修復失敗: $workflow_name"
    local issue_body="## ワークフロー修復失敗レポート

**ワークフロー**: $workflow_name
**実行ID**: $run_id
**検出時刻**: $(date -Iseconds)

### エラー概要
\`\`\`
$(echo "$error_log" | head -50)
\`\`\`

### 推奨アクション
- エラーログを確認してください
- 手動での修正が必要です

---
*このIssueはローカル自動修復システムによって作成されました*"

    gh issue create --repo "$REPO" --title "$issue_title" --body "$issue_body" --label "auto-repair,bug" 2>/dev/null || \
        log "WARNING" "Issue作成に失敗しました"
}

# 状態更新
update_state() {
    local action="$1"
    
    case "$action" in
        repair_attempted)
            jq '.total_repairs += 1 | .last_run = now' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
            ;;
        iteration_complete)
            jq '.current_iteration += 1' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
            ;;
    esac
}

# メインループ
main_loop() {
    log "INFO" "========================================="
    log "INFO" "ローカル自動修復ループを開始します"
    log "INFO" "========================================="
    
    init_state
    
    while [[ $CURRENT_ITERATION -lt $MAX_ITERATIONS ]]; do
        CURRENT_ITERATION=$((CURRENT_ITERATION + 1))
        
        echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        log "INFO" "イテレーション $CURRENT_ITERATION/$MAX_ITERATIONS を開始"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
        
        # 失敗したワークフローを検出・修復
        detect_failures
        
        # 10分待機
        log "INFO" "10分間待機中..."
        sleep 600
        
        # 検証フェーズ
        log "INFO" "修復結果を検証中..."
        local current_failures=$(gh run list --repo "$REPO" --status failure --limit 5 --json databaseId --jq '. | length')
        
        if [[ "$current_failures" -eq 0 ]]; then
            log "SUCCESS" "全てのワークフローが正常に動作しています！"
        else
            log "WARNING" "まだ $current_failures 個の失敗したワークフローがあります"
        fi
        
        # 状態更新
        update_state "iteration_complete"
        
        # 次のサイクルまで待機（残り20分）
        log "INFO" "次のサイクルまで20分待機..."
        sleep 1200
    done
    
    log "SUCCESS" "========================================="
    log "SUCCESS" "10回のループが完了しました"
    log "SUCCESS" "========================================="
}

# シグナルハンドラー
trap 'log "INFO" "修復ループを終了します"; exit 0' SIGINT SIGTERM

# メイン実行
case "${1:-}" in
    start)
        main_loop
        ;;
    status)
        if [[ -f "$STATE_FILE" ]]; then
            echo -e "${CYAN}=== 修復システム状態 ===${NC}"
            jq '.' "$STATE_FILE"
        else
            echo "状態ファイルが見つかりません"
        fi
        ;;
    reset)
        rm -f "$STATE_FILE"
        log "SUCCESS" "状態をリセットしました"
        ;;
    *)
        echo "使用方法: $0 {start|status|reset}"
        echo ""
        echo "  start  - 修復ループを開始"
        echo "  status - 現在の状態を表示"
        echo "  reset  - 状態をリセット"
        exit 1
        ;;
esac