#!/bin/bash

# 自動修復コミット・プッシュScript (Auto-commit and Push Fixes Script)
#
# 機能:
# - 修復結果の自動コミット
# - インテリジェントなコミットメッセージ生成
# - プルリクエスト作成（オプション）
# - 修復結果のサマリー生成
# - Git操作の安全性確保

set -euo pipefail

# 設定 (Configuration)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="$PROJECT_ROOT/.github/outputs"
LOG_FILE="$OUTPUT_DIR/auto-commit.log"
TIME_LIMIT=300  # 5分制限

# Git設定
BRANCH_NAME="auto-repair/$(date +%Y%m%d-%H%M%S)"
COMMIT_PREFIX="🤖 Auto-repair:"
PR_TITLE="🤖 Automated Fixes from Auto-Repair System"

# ログ関数 (Logging functions)
log_info() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $*" | tee -a "$LOG_FILE"
}

# 初期化 (Initialization)
initialize() {
    mkdir -p "$OUTPUT_DIR"
    echo "📝 自動コミット・プッシュを開始... (Starting Auto-commit & Push...)" | tee "$LOG_FILE"
    
    cd "$PROJECT_ROOT"
    
    # Git設定の確認
    if ! git config user.name >/dev/null 2>&1; then
        git config user.name "Auto-Repair Bot"
        log_info "Git user.nameを設定: Auto-Repair Bot"
    fi
    
    if ! git config user.email >/dev/null 2>&1; then
        git config user.email "auto-repair@github-actions.bot"
        log_info "Git user.emailを設定: auto-repair@github-actions.bot"
    fi
}

# 修復結果の分析 (Analyze repair results)
analyze_repair_results() {
    log_info "🔍 修復結果を分析中..."
    
    local repair_summary=""
    local fixed_issues=()
    local failed_repairs=()
    
    # 各修復結果ファイルを確認
    local result_files=(
        "$OUTPUT_DIR/test-repair-result.json"
        "$OUTPUT_DIR/build-repair-result.json"
        "$OUTPUT_DIR/lint-repair-result.json"
        "$OUTPUT_DIR/error-analysis.json"
    )
    
    for result_file in "${result_files[@]}"; do
        if [[ -f "$result_file" ]]; then
            local status=$(jq -r '.status // "unknown"' "$result_file" 2>/dev/null || echo "unknown")
            local repair_type=$(basename "$result_file" | cut -d'-' -f1)
            
            case "$status" in
                "success")
                    fixed_issues+=("$repair_type")
                    log_success "$repair_type repair succeeded"
                    ;;
                "failed")
                    failed_repairs+=("$repair_type")
                    log_error "$repair_type repair failed"
                    ;;
                *)
                    log_info "$repair_type repair status unknown"
                    ;;
            esac
        fi
    done
    
    # サマリー生成
    if [[ ${#fixed_issues[@]} -gt 0 ]]; then
        repair_summary+="Fixed: ${fixed_issues[*]}"
    fi
    
    if [[ ${#failed_repairs[@]} -gt 0 ]]; then
        repair_summary+=" Failed: ${failed_repairs[*]}"
    fi
    
    if [[ -z "$repair_summary" ]]; then
        repair_summary="No specific repair results found"
    fi
    
    echo "$repair_summary"
}

# インテリジェントなコミットメッセージ生成 (Generate intelligent commit message)
generate_commit_message() {
    local repair_summary="$1"
    local changed_files
    changed_files=$(git diff --name-only 2>/dev/null || echo "")
    
    local commit_message="$COMMIT_PREFIX $repair_summary"
    
    # 変更ファイルの分析
    local file_types=()
    if echo "$changed_files" | grep -q "\.ts\|\.tsx\|\.js\|\.jsx"; then
        file_types+=("TypeScript/JavaScript")
    fi
    if echo "$changed_files" | grep -q "\.py"; then
        file_types+=("Python")
    fi
    if echo "$changed_files" | grep -q "package\.json\|yarn\.lock\|package-lock\.json"; then
        file_types+=("Dependencies")
    fi
    if echo "$changed_files" | grep -q "\.eslintrc\|\.prettierrc\|tsconfig\.json"; then
        file_types+=("Configuration")
    fi
    
    # 詳細なコミットメッセージ作成
    commit_message+=$'\n\n'
    commit_message+="Auto-repair system executed the following fixes:"$'\n'
    
    if [[ ${#file_types[@]} -gt 0 ]]; then
        commit_message+="- File types: ${file_types[*]}"$'\n'
    fi
    
    if [[ -n "$changed_files" ]]; then
        local file_count
        file_count=$(echo "$changed_files" | wc -l)
        commit_message+="- Files changed: $file_count"$'\n'
    fi
    
    commit_message+="- Timestamp: $(date -Iseconds)"$'\n'
    commit_message+="- Auto-repair run ID: ${GITHUB_RUN_ID:-$(date +%s)}"
    
    echo "$commit_message"
}

# 変更の検証と安全性チェック (Verify changes and safety check)
verify_changes() {
    log_info "🔒 変更の安全性をチェック中..."
    
    # 変更があるかチェック
    if ! git diff --quiet; then
        log_info "変更が検出されました"
    else
        log_info "変更はありません。コミットをスキップします。"
        return 1
    fi
    
    # 危険な変更をチェック
    local dangerous_patterns=(
        "password"
        "secret"
        "token"
        "api_key"
        "private_key"
        "credentials"
    )
    
    for pattern in "${dangerous_patterns[@]}"; do
        if git diff | grep -i "$pattern" >/dev/null 2>&1; then
            log_error "危険な変更が検出されました: $pattern"
            return 1
        fi
    done
    
    # ファイルサイズチェック（1MB以下）
    local large_files
    large_files=$(git diff --name-only | xargs ls -la 2>/dev/null | awk '$5 > 1048576 {print $9}' || true)
    
    if [[ -n "$large_files" ]]; then
        log_error "大きなファイルが検出されました: $large_files"
        return 1
    fi
    
    log_success "変更の安全性チェック完了"
    return 0
}

# 新しいブランチの作成 (Create new branch)
create_repair_branch() {
    log_info "🌿 修復用ブランチを作成中: $BRANCH_NAME"
    
    # 現在のブランチを確認
    local current_branch
    current_branch=$(git branch --show-current 2>/dev/null || echo "main")
    
    # 新しいブランチを作成してチェックアウト
    if git checkout -b "$BRANCH_NAME" 2>/dev/null; then
        log_success "ブランチ作成成功: $BRANCH_NAME"
        return 0
    else
        log_error "ブランチ作成に失敗しました"
        return 1
    fi
}

# 変更のコミット (Commit changes)
commit_changes() {
    local commit_message="$1"
    
    log_info "📝 変更をコミット中..."
    
    # 全ての変更をステージング
    git add . || {
        log_error "git addに失敗しました"
        return 1
    }
    
    # コミット実行
    if git commit -m "$commit_message"; then
        log_success "コミット成功"
        return 0
    else
        log_error "コミットに失敗しました"
        return 1
    fi
}

# リモートへのプッシュ (Push to remote)
push_to_remote() {
    log_info "🚀 リモートにプッシュ中..."
    
    # リモートの存在確認
    if ! git remote get-url origin >/dev/null 2>&1; then
        log_error "リモートリポジトリが設定されていません"
        return 1
    fi
    
    # プッシュ実行
    if git push -u origin "$BRANCH_NAME"; then
        log_success "プッシュ成功: $BRANCH_NAME"
        return 0
    else
        log_error "プッシュに失敗しました"
        return 1
    fi
}

# プルリクエストの作成 (Create pull request)
create_pull_request() {
    log_info "🔄 プルリクエストを作成中..."
    
    # GitHub CLIの確認
    if ! command -v gh >/dev/null 2>&1; then
        log_info "GitHub CLIが見つかりません。PRの手動作成が必要です。"
        return 0
    fi
    
    # PRの説明文生成
    local pr_body
    pr_body=$(cat << EOF
## 🤖 自動修復システムによる修正

このプルリクエストは自動修復システムによって生成されました。

### 修復内容
$(analyze_repair_results)

### 変更されたファイル
$(git diff --name-only HEAD~1 | head -10)

### 実行時刻
$(date -Iseconds)

### 注意事項
- この修正は自動生成されたものです
- マージ前にレビューを推奨します
- 必要に応じて追加の手動修正を行ってください

---
Generated by Auto-Repair System
EOF
)
    
    # プルリクエスト作成
    if gh pr create \
        --title "$PR_TITLE" \
        --body "$pr_body" \
        --label "auto-repair" \
        --label "bot" 2>/dev/null; then
        log_success "プルリクエスト作成成功"
        return 0
    else
        log_error "プルリクエスト作成に失敗しました"
        return 1
    fi
}

# 修復サマリーの生成 (Generate repair summary)
generate_summary_report() {
    log_info "📊 修復サマリーレポートを生成中..."
    
    local summary_file="$OUTPUT_DIR/repair-summary.md"
    
    cat > "$summary_file" << EOF
# 🤖 Auto-Repair System Summary

## 実行時刻
$(date -Iseconds)

## 修復結果
$(analyze_repair_results)

## 変更されたファイル
\`\`\`
$(git diff --name-only 2>/dev/null || echo "No changes detected")
\`\`\`

## Git情報
- Branch: $BRANCH_NAME
- Commit: $(git rev-parse HEAD 2>/dev/null || echo "No commit")
- Remote: $(git remote get-url origin 2>/dev/null || echo "No remote")

## 修復ログ
各修復プロセスの詳細ログは以下のファイルを参照してください：
- Test repair: \`$OUTPUT_DIR/test-repair.log\`
- Build repair: \`$OUTPUT_DIR/build-repair.log\`
- Lint repair: \`$OUTPUT_DIR/lint-repair.log\`
- Auto-commit: \`$LOG_FILE\`

---
Generated by Auto-Repair System
EOF
    
    log_success "サマリーレポート生成完了: $summary_file"
}

# クリーンアップ (Cleanup)
cleanup() {
    log_info "🧹 クリーンアップを実行中..."
    
    # 失敗した場合の元ブランチへの復帰
    if [[ $? -ne 0 ]]; then
        git checkout - 2>/dev/null || true
        git branch -D "$BRANCH_NAME" 2>/dev/null || true
    fi
}

# メイン処理 (Main process)
main() {
    local start_time=$(date +%s)
    local exit_code=0
    
    # トラップ設定
    trap 'cleanup; log_error "自動コミット処理が中断されました"; exit 130' INT TERM
    
    initialize
    
    # 修復結果の分析
    local repair_summary
    repair_summary=$(analyze_repair_results)
    log_info "修復サマリー: $repair_summary"
    
    # 変更の検証
    if ! verify_changes; then
        log_info "変更がないか、安全でない変更が検出されました。処理を終了します。"
        exit_code=0
        exit $exit_code
    fi
    
    # 新しいブランチの作成
    if ! create_repair_branch; then
        log_error "ブランチ作成に失敗しました"
        exit_code=1
        exit $exit_code
    fi
    
    # コミットメッセージ生成
    local commit_message
    commit_message=$(generate_commit_message "$repair_summary")
    
    # 変更のコミット
    if ! commit_changes "$commit_message"; then
        log_error "コミットに失敗しました"
        exit_code=1
        exit $exit_code
    fi
    
    # リモートへのプッシュ
    if ! push_to_remote; then
        log_error "プッシュに失敗しました"
        exit_code=1
        exit $exit_code
    fi
    
    # プルリクエストの作成（オプション）
    if [[ "${CREATE_PR:-true}" == "true" ]]; then
        create_pull_request || log_info "PRの作成はスキップされました"
    fi
    
    # サマリーレポート生成
    generate_summary_report
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_success "✅ 自動コミット・プッシュが完了しました"
    log_info "実行時間: ${duration}秒"
    
    # 結果出力
    cat > "$OUTPUT_DIR/auto-commit-result.json" << EOF
{
    "status": "success",
    "branch": "$BRANCH_NAME",
    "commit": "$(git rev-parse HEAD)",
    "duration": $duration,
    "timestamp": "$(date -Iseconds)",
    "summary": "$repair_summary",
    "logFile": "$LOG_FILE"
}
EOF
    
    exit $exit_code
}

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi