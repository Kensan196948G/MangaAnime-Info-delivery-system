#!/bin/bash

# =============================================================================
# MangaAnime エラー監視・通知スクリプト
# 配信エラーやシステムエラーを監視してメール通知を送信
# =============================================================================

set -e

# 色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# プロジェクトディレクトリ
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
LOG_DIR="$PROJECT_DIR/logs"
PYTHON_ENV="$PROJECT_DIR/venv/bin/python"
ERROR_NOTIFIER="$PROJECT_DIR/modules/error_notifier.py"

# ログファイル
APP_LOG="$LOG_DIR/app.log"
SYSTEM_LOG="$LOG_DIR/system.log"
BACKUP_LOG="$LOG_DIR/backup.log"
CRON_LOG="$LOG_DIR/cron_$(date +%Y%m).log"
ERROR_MONITOR_LOG="$LOG_DIR/error_monitor.log"

# 関数定義
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$ERROR_MONITOR_LOG"
}

send_error_notification() {
    local error_type="$1"
    local error_message="$2"
    local error_details="$3"
    local log_file="$4"
    
    cd "$PROJECT_DIR"
    
    if [ -f "$PYTHON_ENV" ] && [ -f "$ERROR_NOTIFIER" ]; then
        if "$PYTHON_ENV" "$ERROR_NOTIFIER" "$error_type" "$error_message" "$error_details" "$log_file" 2>/dev/null; then
            log_message "✅ エラー通知送信成功: $error_type"
            return 0
        else
            log_message "❌ エラー通知送信失敗: $error_type"
            return 1
        fi
    else
        log_message "❌ エラー通知システムが利用できません"
        return 1
    fi
}

check_log_errors() {
    local log_file="$1"
    local check_name="$2"
    local time_minutes="${3:-60}"  # デフォルト60分
    
    if [ ! -f "$log_file" ]; then
        return 0
    fi
    
    # 指定時間内のエラーをチェック
    local since_time=$(date -d "$time_minutes minutes ago" '+%Y-%m-%d %H:%M:%S')
    local error_count=$(grep -E "(ERROR|CRITICAL|FATAL)" "$log_file" 2>/dev/null | \
                       awk -v since="$since_time" '$0 >= since' | wc -l)
    
    if [ "$error_count" -gt 0 ]; then
        local recent_errors=$(grep -E "(ERROR|CRITICAL|FATAL)" "$log_file" 2>/dev/null | \
                             awk -v since="$since_time" '$0 >= since' | tail -5)
        
        send_error_notification \
            "$check_name エラー検出" \
            "過去${time_minutes}分間に${error_count}件のエラーが検出されました" \
            "$recent_errors" \
            "$log_file"
        
        return 1
    fi
    
    return 0
}

check_cron_failures() {
    local time_minutes="${1:-30}"
    
    # Cron実行失敗をチェック
    local failed_crons=$(grep -E "(失敗|failed|error)" "$CRON_LOG" 2>/dev/null | \
                         grep "$(date -d "$time_minutes minutes ago" '+%Y-%m-%d')" | \
                         wc -l)
    
    if [ "$failed_crons" -gt 0 ]; then
        local failure_details=$(grep -E "(失敗|failed|error)" "$CRON_LOG" 2>/dev/null | \
                               grep "$(date -d "$time_minutes minutes ago" '+%Y-%m-%d')" | \
                               tail -3)
        
        send_error_notification \
            "Cron実行エラー" \
            "過去${time_minutes}分間にCron実行で${failed_crons}件の失敗が発生しました" \
            "$failure_details" \
            "$CRON_LOG"
        
        return 1
    fi
    
    return 0
}

check_backup_failures() {
    local time_minutes="${1:-60}"
    
    if [ ! -f "$BACKUP_LOG" ]; then
        return 0
    fi
    
    # バックアップ失敗をチェック
    local backup_errors=$(grep -E "(失敗|❌|ERROR)" "$BACKUP_LOG" 2>/dev/null | \
                         grep "$(date -d "$time_minutes minutes ago" '+%Y-%m-%d')" | \
                         wc -l)
    
    if [ "$backup_errors" -gt 0 ]; then
        local error_details=$(grep -E "(失敗|❌|ERROR)" "$BACKUP_LOG" 2>/dev/null | \
                             grep "$(date -d "$time_minutes minutes ago" '+%Y-%m-%d')" | \
                             tail -3)
        
        send_error_notification \
            "バックアップエラー" \
            "過去${time_minutes}分間にバックアップで${backup_errors}件のエラーが発生しました" \
            "$error_details" \
            "$BACKUP_LOG"
        
        return 1
    fi
    
    return 0
}

check_disk_space() {
    local threshold="${1:-90}"  # デフォルト90%
    
    local disk_usage=$(df "$PROJECT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$disk_usage" -gt "$threshold" ]; then
        local disk_info=$(df -h "$PROJECT_DIR")
        
        send_error_notification \
            "ディスク容量警告" \
            "ディスク使用率が${disk_usage}%に達しました（閾値: ${threshold}%）" \
            "$disk_info" \
            ""
        
        return 1
    fi
    
    return 0
}

check_process_health() {
    # WebUI プロセスチェック
    if ! pgrep -f "web_app.py" >/dev/null 2>&1; then
        send_error_notification \
            "WebUI プロセス停止" \
            "MangaAnime WebUIプロセスが停止しています" \
            "プロセス: web_app.py が見つかりません" \
            "$APP_LOG"
        
        return 1
    fi
    
    return 0
}

# メイン処理
main() {
    local check_type="${1:-all}"
    local error_count=0
    
    log_message "🔍 エラー監視開始 (チェック種別: $check_type)"
    
    # ログディレクトリ作成
    mkdir -p "$LOG_DIR"
    
    case "$check_type" in
        "logs")
            log_message "📋 ログエラーチェック"
            check_log_errors "$APP_LOG" "アプリケーションログ" 60 || ((error_count++))
            check_log_errors "$SYSTEM_LOG" "システムログ" 60 || ((error_count++))
            ;;
            
        "cron")
            log_message "⏰ Cronエラーチェック"
            check_cron_failures 30 || ((error_count++))
            ;;
            
        "backup")
            log_message "💾 バックアップエラーチェック"
            check_backup_failures 60 || ((error_count++))
            ;;
            
        "system")
            log_message "🖥️ システムヘルスチェック"
            check_disk_space 90 || ((error_count++))
            check_process_health || ((error_count++))
            ;;
            
        "test")
            log_message "🧪 テスト通知送信"
            send_error_notification \
                "テスト通知" \
                "エラー監視システムのテストです" \
                "システムは正常に動作しています" \
                ""
            ;;
            
        "all"|*)
            log_message "🔍 全体エラーチェック"
            check_log_errors "$APP_LOG" "アプリケーションログ" 30 || ((error_count++))
            check_cron_failures 15 || ((error_count++))
            check_backup_failures 30 || ((error_count++))
            check_disk_space 85 || ((error_count++))
            check_process_health || ((error_count++))
            ;;
    esac
    
    if [ "$error_count" -eq 0 ]; then
        log_message "✅ エラー監視完了 - 問題なし"
    else
        log_message "⚠️ エラー監視完了 - ${error_count}件の問題を検出"
    fi
    
    exit $error_count
}

# 使用方法表示
show_usage() {
    echo "使用方法: $0 [check_type]"
    echo ""
    echo "check_type:"
    echo "  all     - 全項目チェック (デフォルト)"
    echo "  logs    - ログファイルエラーチェック"
    echo "  cron    - Cron実行エラーチェック"
    echo "  backup  - バックアップエラーチェック"
    echo "  system  - システムヘルスチェック"
    echo "  test    - テスト通知送信"
    echo ""
    echo "例:"
    echo "  $0 all      # 全体チェック"
    echo "  $0 logs     # ログのみチェック"
    echo "  $0 test     # テスト通知"
}

# 引数チェック
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    show_usage
    exit 0
fi

# メイン実行
main "$@"