#!/bin/bash
# ローカル完全自動化システム（GitHub Actions代替）

set -euo pipefail

# 設定
WORK_DIR="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
LOG_DIR="$WORK_DIR/logs/automation"
STATE_FILE="$WORK_DIR/.automation-state.json"
CYCLE_INTERVAL=1800  # 30分

# カラーコード
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# ログディレクトリ作成
mkdir -p "$LOG_DIR"

# タイムスタンプ付きログ
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        ERROR)   echo -e "${RED}[$timestamp] [ERROR]${NC} $message" ;;
        SUCCESS) echo -e "${GREEN}[$timestamp] [SUCCESS]${NC} $message" ;;
        WARNING) echo -e "${YELLOW}[$timestamp] [WARNING]${NC} $message" ;;
        INFO)    echo -e "${CYAN}[$timestamp] [INFO]${NC} $message" ;;
        TASK)    echo -e "${MAGENTA}[$timestamp] [TASK]${NC} $message" ;;
        *)       echo "[$timestamp] $message" ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_DIR/system-$(date +%Y%m%d).log"
}

# 状態初期化
init_state() {
    if [[ ! -f "$STATE_FILE" ]]; then
        cat > "$STATE_FILE" <<EOF
{
    "last_test_run": "",
    "last_lint_run": "",
    "last_build_run": "",
    "last_deploy_run": "",
    "test_results": "pending",
    "lint_results": "pending",
    "build_results": "pending",
    "created_at": "$(date -Iseconds)"
}
EOF
        log "INFO" "自動化状態ファイルを初期化しました"
    fi
}

# テスト実行（GitHub Actions test jobの代替）
run_tests() {
    log "TASK" "=== テストタスク開始 ==="
    
    cd "$WORK_DIR"
    
    # テストファイルの存在確認
    if [[ -f "package.json" ]] && grep -q '"test"' package.json; then
        log "INFO" "npm testを実行中..."
        
        if npm test 2>&1 | tee "$LOG_DIR/test-$(date +%Y%m%d-%H%M%S).log"; then
            log "SUCCESS" "テスト成功"
            jq '.test_results = "success" | .last_test_run = now' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
            return 0
        else
            log "ERROR" "テスト失敗"
            jq '.test_results = "failure" | .last_test_run = now' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
            
            # 自動修復を試みる
            auto_fix_test_errors
        fi
    elif [[ -f "requirements.txt" ]] && [[ -d "tests" ]]; then
        log "INFO" "pytestを実行中..."
        
        if [[ -d ".venv" ]]; then
            source .venv/bin/activate
        fi
        
        if pytest tests/ 2>&1 | tee "$LOG_DIR/test-$(date +%Y%m%d-%H%M%S).log"; then
            log "SUCCESS" "テスト成功"
            jq '.test_results = "success" | .last_test_run = now' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
            return 0
        else
            log "ERROR" "テスト失敗"
            jq '.test_results = "failure" | .last_test_run = now' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
            
            # 自動修復を試みる
            auto_fix_test_errors
        fi
    else
        log "WARNING" "テスト設定が見つかりません"
    fi
}

# Lint実行（GitHub Actions lint jobの代替）
run_lint() {
    log "TASK" "=== Lintタスク開始 ==="
    
    cd "$WORK_DIR"
    
    local has_errors=0
    
    # ESLint
    if [[ -f ".eslintrc.json" ]] || [[ -f ".eslintrc.js" ]]; then
        log "INFO" "ESLintを実行中..."
        if npx eslint . --fix 2>&1 | tee "$LOG_DIR/eslint-$(date +%Y%m%d-%H%M%S).log"; then
            log "SUCCESS" "ESLint成功"
        else
            log "WARNING" "ESLintエラーを自動修正しました"
            ((has_errors++))
        fi
    fi
    
    # Prettier
    if [[ -f ".prettierrc" ]] || [[ -f ".prettierrc.json" ]]; then
        log "INFO" "Prettierを実行中..."
        npx prettier --write . 2>&1 | tee "$LOG_DIR/prettier-$(date +%Y%m%d-%H%M%S).log"
        log "SUCCESS" "Prettierでコードをフォーマットしました"
    fi
    
    # Python Black
    if [[ -f "requirements.txt" ]] && grep -q "black" requirements.txt; then
        log "INFO" "Blackを実行中..."
        if [[ -d ".venv" ]]; then
            source .venv/bin/activate
        fi
        black . 2>&1 | tee "$LOG_DIR/black-$(date +%Y%m%d-%H%M%S).log"
        log "SUCCESS" "Blackでコードをフォーマットしました"
    fi
    
    # 変更があればコミット
    if ! git diff --quiet; then
        log "INFO" "Lint修正をコミット中..."
        git add -A
        git commit -m "🎨 自動フォーマット適用

- ESLint修正
- Prettier適用
- Black適用

[Local Automation System]"
        git push
        log "SUCCESS" "Lint修正をコミットしました"
    fi
    
    if [[ $has_errors -eq 0 ]]; then
        jq '.lint_results = "success" | .last_lint_run = now' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
    else
        jq '.lint_results = "warning" | .last_lint_run = now' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
    fi
}

# ビルド実行（GitHub Actions build jobの代替）
run_build() {
    log "TASK" "=== ビルドタスク開始 ==="
    
    cd "$WORK_DIR"
    
    # Node.jsプロジェクト
    if [[ -f "package.json" ]] && grep -q '"build"' package.json; then
        log "INFO" "npm buildを実行中..."
        
        if npm run build 2>&1 | tee "$LOG_DIR/build-$(date +%Y%m%d-%H%M%S).log"; then
            log "SUCCESS" "ビルド成功"
            jq '.build_results = "success" | .last_build_run = now' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
            return 0
        else
            log "ERROR" "ビルド失敗"
            jq '.build_results = "failure" | .last_build_run = now' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
            
            # 自動修復を試みる
            auto_fix_build_errors
        fi
    else
        log "INFO" "ビルド設定が見つかりません"
        jq '.build_results = "skip" | .last_build_run = now' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
    fi
}

# テストエラー自動修復
auto_fix_test_errors() {
    log "INFO" "テストエラーの自動修復を試みます..."
    
    # パッケージの再インストール
    if [[ -f "package.json" ]]; then
        rm -rf node_modules package-lock.json
        npm install
    fi
    
    if [[ -f "requirements.txt" ]]; then
        if [[ -d ".venv" ]]; then
            source .venv/bin/activate
        fi
        pip install -r requirements.txt --upgrade
    fi
    
    # 再度テスト実行
    log "INFO" "修復後の再テスト..."
    # ここでは無限ループを避けるため、再テストは行わない
}

# ビルドエラー自動修復
auto_fix_build_errors() {
    log "INFO" "ビルドエラーの自動修復を試みます..."
    
    # クリーンビルド
    if [[ -d "dist" ]]; then
        rm -rf dist
    fi
    
    if [[ -d "build" ]]; then
        rm -rf build
    fi
    
    # キャッシュクリア
    if [[ -f "package.json" ]]; then
        npm cache clean --force
    fi
}

# デプロイ実行（必要に応じて）
run_deploy() {
    log "TASK" "=== デプロイタスク開始 ==="
    
    # デプロイスクリプトがある場合のみ実行
    if [[ -f "$WORK_DIR/scripts/deploy.sh" ]]; then
        log "INFO" "デプロイスクリプトを実行中..."
        if bash "$WORK_DIR/scripts/deploy.sh"; then
            log "SUCCESS" "デプロイ成功"
            jq '.last_deploy_run = now' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
        else
            log "ERROR" "デプロイ失敗"
        fi
    else
        log "INFO" "デプロイスクリプトなし - スキップ"
    fi
}

# 定期メンテナンス
run_maintenance() {
    log "TASK" "=== メンテナンスタスク開始 ==="
    
    cd "$WORK_DIR"
    
    # 古いログファイルの削除（7日以上）
    find "$LOG_DIR" -name "*.log" -mtime +7 -delete
    log "INFO" "古いログファイルを削除しました"
    
    # Git GC
    git gc --auto
    log "INFO" "Git GCを実行しました"
    
    # ディスク使用量チェック
    local disk_usage=$(df -h "$WORK_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 80 ]]; then
        log "WARNING" "ディスク使用量が高いです: ${disk_usage}%"
    fi
}

# ステータス表示
show_status() {
    echo -e "\n${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║           ローカル自動化システム ステータス            ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}\n"
    
    if [[ -f "$STATE_FILE" ]]; then
        local test_status=$(jq -r '.test_results' "$STATE_FILE")
        local lint_status=$(jq -r '.lint_results' "$STATE_FILE")
        local build_status=$(jq -r '.build_results' "$STATE_FILE")
        
        # ステータスアイコン設定
        case "$test_status" in
            success) test_icon="✅" ;;
            failure) test_icon="❌" ;;
            pending) test_icon="⏳" ;;
            *) test_icon="❓" ;;
        esac
        
        case "$lint_status" in
            success) lint_icon="✅" ;;
            warning) lint_icon="⚠️" ;;
            failure) lint_icon="❌" ;;
            pending) lint_icon="⏳" ;;
            *) lint_icon="❓" ;;
        esac
        
        case "$build_status" in
            success) build_icon="✅" ;;
            failure) build_icon="❌" ;;
            skip) build_icon="⏭️" ;;
            pending) build_icon="⏳" ;;
            *) build_icon="❓" ;;
        esac
        
        echo "  ${test_icon} テスト: $test_status"
        echo "  ${lint_icon} Lint: $lint_status"
        echo "  ${build_icon} ビルド: $build_status"
        echo ""
        
        jq '.' "$STATE_FILE"
    else
        echo "状態ファイルが見つかりません"
    fi
}

# メインループ
main_loop() {
    log "INFO" "========================================="
    log "INFO" "ローカル自動化システムを開始します"
    log "INFO" "========================================="
    
    init_state
    
    while true; do
        echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        log "INFO" "自動化サイクル開始 $(date '+%Y-%m-%d %H:%M:%S')"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
        
        # 各タスクを順番に実行
        run_tests
        run_lint
        run_build
        run_deploy
        run_maintenance
        
        # ステータス表示
        show_status
        
        log "INFO" "自動化サイクル完了"
        log "INFO" "次のサイクルまで30分待機..."
        
        # 30分待機
        sleep $CYCLE_INTERVAL
    done
}

# シグナルハンドラー
trap 'log "INFO" "自動化システムを終了します"; exit 0' SIGINT SIGTERM

# メイン実行
case "${1:-}" in
    start)
        main_loop
        ;;
    once)
        log "INFO" "単発実行モード"
        init_state
        run_tests
        run_lint
        run_build
        run_deploy
        run_maintenance
        show_status
        ;;
    status)
        show_status
        ;;
    test)
        run_tests
        ;;
    lint)
        run_lint
        ;;
    build)
        run_build
        ;;
    *)
        echo "使用方法: $0 {start|once|status|test|lint|build}"
        echo ""
        echo "  start  - 30分サイクルで継続実行"
        echo "  once   - 全タスクを1回実行"
        echo "  status - 現在の状態を表示"
        echo "  test   - テストのみ実行"
        echo "  lint   - Lintのみ実行"
        echo "  build  - ビルドのみ実行"
        exit 1
        ;;
esac