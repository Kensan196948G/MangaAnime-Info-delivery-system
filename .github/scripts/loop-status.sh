#!/bin/bash
# Loop Status Tracker for Auto-Repair System
# アニメ・マンガ情報配信システム - ループ状態トラッカー

set -e

# Default values
ITERATION=1
STATUS="unknown"
LOOP_ID=""
STATE_FILE=".github/state/loop-state.json"
REPORTS_DIR="reports"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --iteration)
      ITERATION="$2"
      shift 2
      ;;
    --status)
      STATUS="$2"
      shift 2
      ;;
    --loop-id)
      LOOP_ID="$2"
      shift 2
      ;;
    --state-file)
      STATE_FILE="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 --iteration N --status STATUS --loop-id ID [--state-file FILE]"
      echo ""
      echo "Options:"
      echo "  --iteration   Current iteration number"
      echo "  --status      CI workflow status (success/failure/cancelled)"
      echo "  --loop-id     Unique loop identifier"
      echo "  --state-file  Path to state file (default: .github/state/loop-state.json)"
      echo "  --help        Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate required parameters
if [[ -z "$ITERATION" || -z "$STATUS" || -z "$LOOP_ID" ]]; then
  echo "❌ Error: Missing required parameters"
  echo "Use --help for usage information"
  exit 1
fi

# Create directories if they don't exist
mkdir -p "$(dirname "$STATE_FILE")"
mkdir -p "$REPORTS_DIR"

# Function to log with timestamp
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to update state file
update_state() {
  local current_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  
  # Read current state or create new one
  if [[ -f "$STATE_FILE" ]]; then
    local current_state=$(cat "$STATE_FILE")
  else
    local current_state='{}'
  fi
  
  # Update state with new information
  local updated_state=$(echo "$current_state" | jq \
    --arg iteration "$ITERATION" \
    --arg status "$STATUS" \
    --arg loop_id "$LOOP_ID" \
    --arg timestamp "$current_time" \
    '
    .loop_id = $loop_id |
    .current_iteration = ($iteration | tonumber) |
    .last_update = $timestamp |
    .iterations = (.iterations // []) |
    .iterations += [{
      "iteration": ($iteration | tonumber),
      "status": $status,
      "timestamp": $timestamp,
      "duration_seconds": 0
    }] |
    if $status == "success" then
      .status = "completed"
    else
      .status = "running" |
      .current_iteration = (.current_iteration + 1)
    end |
    .total_fixes_applied = (.total_fixes_applied // 0) + (if $status == "success" then 1 else 0 end)
    ')
  
  echo "$updated_state" > "$STATE_FILE"
  
  log "📝 State updated for iteration $ITERATION with status: $STATUS"
}

# Function to generate iteration report
generate_iteration_report() {
  local report_file="$REPORTS_DIR/iteration-$ITERATION-$(date +%Y%m%d_%H%M%S).md"
  
  cat > "$report_file" << EOF
# 🔄 Auto-Repair Loop - Iteration $ITERATION Report
# 自動修復ループ - 反復 $ITERATION レポート

## 📊 Basic Information / 基本情報

- **Iteration Number / 反復番号**: $ITERATION
- **Loop ID / ループID**: $LOOP_ID
- **Status / ステータス**: $STATUS
- **Timestamp / タイムスタンプ**: $(date '+%Y-%m-%d %H:%M:%S %Z')
- **Commit SHA**: ${GITHUB_SHA:-"N/A"}

## 📈 Results Summary / 結果サマリー

### Status Details / ステータス詳細

EOF

  case "$STATUS" in
    "success")
      cat >> "$report_file" << EOF
✅ **SUCCESS / 成功**

この反復では全てのテストが成功し、ビルドも完了しました。
All tests passed and build completed successfully in this iteration.

### Actions Taken / 実行されたアクション

- ✅ Linting and formatting checks passed / リンティング・フォーマットチェック成功
- ✅ Security scans completed without critical issues / セキュリティスキャン完了
- ✅ All unit tests passed / 全単体テスト成功
- ✅ Integration tests successful / 統合テスト成功
- ✅ Build and deployment completed / ビルド・デプロイ完了

### Next Steps / 次のステップ

システムが正常に動作しているため、ループを終了します。
System is functioning correctly, ending the loop.
EOF
      ;;
    "failure")
      cat >> "$report_file" << EOF
❌ **FAILURE / 失敗**

この反復では問題が検出されました。自動修復を試行します。
Issues were detected in this iteration. Auto-repair will be attempted.

### Detected Issues / 検出された問題

- 🔍 Test failures may indicate code issues / テスト失敗はコード問題を示す可能性
- 🏗️ Build failures may indicate dependency issues / ビルド失敗は依存関係問題を示す可能性
- 🔒 Security issues may require immediate attention / セキュリティ問題は即座の対応が必要

### Auto-Repair Actions / 自動修復アクション

次の反復で以下の修復を試行します:
The following repairs will be attempted in the next iteration:

1. 🔧 Code formatting and linting fixes / コード整形・リンティング修正
2. 📦 Dependency updates and conflict resolution / 依存関係更新・競合解決
3. 🧪 Test case fixes and improvements / テストケース修正・改善
4. 🔒 Security vulnerability patches / セキュリティ脆弱性パッチ

### Next Steps / 次のステップ

反復 $(($ITERATION + 1)) で自動修復を実行します。
Auto-repair will be executed in iteration $(($ITERATION + 1)).
EOF
      ;;
    "cancelled")
      cat >> "$report_file" << EOF
⏹️ **CANCELLED / キャンセル**

この反復はキャンセルされました。
This iteration was cancelled.

### Possible Reasons / 考えられる理由

- ⏰ Timeout due to long-running processes / 長時間実行によるタイムアウト
- 🚫 Manual cancellation / 手動キャンセル
- 🔧 System resource limitations / システムリソース制限

### Next Steps / 次のステップ

次の反復で再試行します。
Will retry in the next iteration.
EOF
      ;;
    *)
      cat >> "$report_file" << EOF
❓ **UNKNOWN STATUS / 不明なステータス**

予期しないステータスです: $STATUS
Unexpected status: $STATUS

### Next Steps / 次のステップ

ログを確認し、次の反復で再試行します。
Check logs and retry in the next iteration.
EOF
      ;;
  esac

  cat >> "$report_file" << EOF

## 📊 Loop Statistics / ループ統計

EOF

  if [[ -f "$STATE_FILE" ]]; then
    cat >> "$report_file" << EOF
\`\`\`json
$(cat "$STATE_FILE" | jq '.')
\`\`\`
EOF
  else
    cat >> "$report_file" << EOF
State file not found / ステートファイルが見つかりません
EOF
  fi

  cat >> "$report_file" << EOF

## 📂 Artifacts / 成果物

- **Report File / レポートファイル**: \`$report_file\`
- **State File / ステートファイル**: \`$STATE_FILE\`
- **Logs Directory / ログディレクトリ**: \`logs/\`

---

*Generated by Auto-Repair Loop System / 自動修復ループシステムにより生成*
*Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)*
EOF

  log "📋 Generated iteration report: $report_file"
}

# Function to check loop completion status
check_loop_completion() {
  if [[ ! -f "$STATE_FILE" ]]; then
    log "⚠️ State file not found, cannot determine completion status"
    return 1
  fi
  
  local max_iterations=$(jq -r '.max_iterations // 10' "$STATE_FILE")
  local current_iteration=$(jq -r '.current_iteration' "$STATE_FILE")
  local status=$(jq -r '.status' "$STATE_FILE")
  
  log "📊 Loop Status Check:"
  log "   Current Iteration: $current_iteration"
  log "   Max Iterations: $max_iterations"
  log "   Status: $status"
  
  if [[ "$status" == "success" || "$current_iteration" -gt "$max_iterations" ]]; then
    log "✅ Loop completion criteria met"
    return 0
  else
    log "🔄 Loop should continue"
    return 1
  fi
}

# Function to create summary report
create_summary_report() {
  local summary_file="$REPORTS_DIR/loop-summary-$LOOP_ID.md"
  
  if [[ ! -f "$STATE_FILE" ]]; then
    log "⚠️ Cannot create summary report: state file not found"
    return 1
  fi
  
  local total_iterations=$(jq -r '.current_iteration - 1' "$STATE_FILE")
  local total_fixes=$(jq -r '.total_fixes_applied // 0' "$STATE_FILE")
  local start_time=$(jq -r '.start_time' "$STATE_FILE")
  local final_status=$(jq -r '.status' "$STATE_FILE")
  
  cat > "$summary_file" << EOF
# 🎯 Auto-Repair Loop Summary Report
# 自動修復ループ サマリーレポート

## 📊 Overview / 概要

- **Loop ID / ループID**: $LOOP_ID
- **Total Iterations / 総反復数**: $total_iterations
- **Fixes Applied / 適用された修正**: $total_fixes
- **Final Status / 最終ステータス**: $final_status
- **Start Time / 開始時刻**: $start_time
- **End Time / 終了時刻**: $(date -u +%Y-%m-%dT%H:%M:%SZ)

## 📈 Iteration History / 反復履歴

EOF

  if jq -e '.iterations' "$STATE_FILE" > /dev/null 2>&1; then
    echo "| Iteration | Status | Timestamp |" >> "$summary_file"
    echo "|-----------|---------|-----------|" >> "$summary_file"
    
    jq -r '.iterations[] | "| \(.iteration) | \(.status) | \(.timestamp) |"' "$STATE_FILE" >> "$summary_file"
  else
    echo "No iteration history available / 反復履歴なし" >> "$summary_file"
  fi

  cat >> "$summary_file" << EOF

## 🏆 Results / 結果

EOF

  if [[ "$final_status" == "completed" ]]; then
    cat >> "$summary_file" << EOF
✅ **SUCCESS / 成功**

自動修復ループが正常に完了しました！
The auto-repair loop completed successfully!

### Achievements / 達成事項

- 🔧 システムの問題が自動的に修正されました
- ✅ 全てのテストが正常に通過しています
- 🚀 システムは正常に動作しています

EOF
  else
    cat >> "$summary_file" << EOF
⚠️ **PARTIAL SUCCESS / 部分的成功**

自動修復ループは最大反復数に達しました。
The auto-repair loop reached the maximum number of iterations.

### Status / ステータス

- 🔧 一部の問題が修正されました
- ⚠️ まだ解決されていない問題が残っている可能性があります
- 📋 手動での確認と修正が必要な場合があります

EOF
  fi

  cat >> "$summary_file" << EOF

## 📊 Detailed State / 詳細状態

\`\`\`json
$(cat "$STATE_FILE" | jq '.')
\`\`\`

---

*Generated by Auto-Repair Loop System / 自動修復ループシステムにより生成*
*Report ID: $LOOP_ID*
*Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ)*
EOF

  log "📋 Created summary report: $summary_file"
}

# Main execution
main() {
  log "🔄 Starting loop status update / ループ状態更新開始"
  log "📊 Parameters: Iteration=$ITERATION, Status=$STATUS, Loop_ID=$LOOP_ID"
  
  # Update state
  update_state
  
  # Generate iteration report
  generate_iteration_report
  
  # Check if loop should continue
  if check_loop_completion; then
    log "🎯 Loop completed, generating summary report"
    create_summary_report
  else
    log "🔄 Loop will continue to next iteration"
  fi
  
  log "✅ Loop status update completed / ループ状態更新完了"
}

# Execute main function
main "$@"