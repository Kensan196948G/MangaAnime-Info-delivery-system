#!/bin/bash
# アニメ・マンガ情報配信システム - 日次配信設定スクリプト
#
# 日本時間での配信スケジュール設定:
# - 朝8時: メイン配信時刻
# - 昼12時: 大量通知時の追加配信
# - 夜20時: 大量通知時の追加配信
#
# Usage:
#    ./scripts/setup_daily_delivery.sh [install|remove|status|test]

set -euo pipefail

# 設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_PATH="$(which python3)"
NOTIFIER_SCRIPT="$PROJECT_ROOT/release_notifier.py"
LOG_DIR="$PROJECT_ROOT/logs"
CRON_COMMENT="# MangaAnime Notification System"

# ログディレクトリの作成
mkdir -p "$LOG_DIR"

# 色付きメッセージ
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# crontab エントリの定義
get_cron_entries() {
    cat << EOF
$CRON_COMMENT - Daily Delivery
# 朝8時（JST）- メインの配信時刻
0 8 * * * cd "$PROJECT_ROOT" && "$PYTHON_PATH" "$NOTIFIER_SCRIPT" >> "$LOG_DIR/daily_delivery.log" 2>&1

# 昼12時（JST）- 大量通知時の追加配信
0 12 * * * cd "$PROJECT_ROOT" && "$PYTHON_PATH" "$NOTIFIER_SCRIPT" >> "$LOG_DIR/daily_delivery.log" 2>&1

# 夜20時（JST）- 大量通知時の追加配信
0 20 * * * cd "$PROJECT_ROOT" && "$PYTHON_PATH" "$NOTIFIER_SCRIPT" >> "$LOG_DIR/daily_delivery.log" 2>&1

# 毎日午前2時にログローテーション
0 2 * * * find "$LOG_DIR" -name "*.log" -type f -mtime +7 -delete

EOF
}

# 現在のタイムゾーン確認
check_timezone() {
    local current_tz
    current_tz=$(timedatectl show --property=Timezone --value 2>/dev/null || echo "Unknown")
    
    log_info "現在のタイムゾーン: $current_tz"
    
    if [[ "$current_tz" != "Asia/Tokyo" ]]; then
        log_warning "タイムゾーンが日本時間に設定されていません"
        log_info "日本時間に設定するには:"
        log_info "  sudo timedatectl set-timezone Asia/Tokyo"
        echo
    fi
}

# 前提条件チェック
check_prerequisites() {
    log_info "前提条件をチェックしています..."
    
    # Python 3の確認
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3が見つかりません"
        exit 1
    fi
    
    # notifier スクリプトの確認
    if [[ ! -f "$NOTIFIER_SCRIPT" ]]; then
        log_error "release_notifier.py が見つかりません: $NOTIFIER_SCRIPT"
        exit 1
    fi
    
    # 設定ファイルの確認
    if [[ ! -f "$PROJECT_ROOT/config.json" ]]; then
        log_warning "config.json が見つかりません"
        log_info "設定ファイルを作成してください"
    fi
    
    # crontab の確認
    if ! command -v crontab &> /dev/null; then
        log_error "crontab コマンドが見つかりません"
        exit 1
    fi
    
    check_timezone
    log_success "前提条件チェック完了"
}

# crontab インストール
install_cron() {
    log_info "配信スケジュールをインストールしています..."
    
    check_prerequisites
    
    # 既存エントリの削除（重複防止）
    remove_cron_silent
    
    # 現在のcrontabを取得
    local current_cron
    current_cron=$(crontab -l 2>/dev/null || echo "")
    
    # 新しいエントリを追加
    {
        echo "$current_cron"
        echo ""
        get_cron_entries
    } | crontab -
    
    log_success "配信スケジュールをインストールしました"
    log_info "配信時刻:"
    log_info "  ・朝8時   - メイン配信"
    log_info "  ・昼12時  - 大量通知時の追加配信"
    log_info "  ・夜20時  - 大量通知時の追加配信"
    echo
    
    # 設定確認
    show_status
}

# crontab 削除（メッセージ出力あり）
remove_cron() {
    log_info "配信スケジュールを削除しています..."
    
    if remove_cron_silent; then
        log_success "配信スケジュールを削除しました"
    else
        log_warning "削除するエントリが見つかりませんでした"
    fi
}

# crontab 削除（メッセージ出力なし）
remove_cron_silent() {
    local current_cron
    current_cron=$(crontab -l 2>/dev/null || echo "")
    
    if [[ -z "$current_cron" ]]; then
        return 1
    fi
    
    # MangaAnime Notification System のエントリを削除
    local new_cron
    new_cron=$(echo "$current_cron" | grep -v "$CRON_COMMENT" | grep -v "$NOTIFIER_SCRIPT" || true)
    
    # 空行を削除
    new_cron=$(echo "$new_cron" | sed '/^$/d')
    
    # crontab を更新
    if [[ -n "$new_cron" ]]; then
        echo "$new_cron" | crontab -
    else
        crontab -r 2>/dev/null || true
    fi
    
    return 0
}

# 状態表示
show_status() {
    log_info "現在の配信スケジュール状況:"
    echo
    
    local current_cron
    current_cron=$(crontab -l 2>/dev/null || echo "")
    
    if echo "$current_cron" | grep -q "$CRON_COMMENT"; then
        log_success "配信スケジュールが設定されています"
        echo
        echo "設定されたスケジュール:"
        echo "$current_cron" | grep -A 10 "$CRON_COMMENT"
    else
        log_warning "配信スケジュールが設定されていません"
        log_info "インストールするには: $0 install"
    fi
    
    echo
    check_timezone
    
    # 次回実行時刻の表示
    if command -v systemctl &> /dev/null && systemctl is-active --quiet cron; then
        log_success "cron サービスが実行中です"
    elif command -v service &> /dev/null && service cron status &> /dev/null; then
        log_success "cron サービスが実行中です"
    else
        log_warning "cron サービスの状態を確認できません"
    fi
    
    # ログファイルの状態
    if [[ -f "$LOG_DIR/daily_delivery.log" ]]; then
        local log_size
        log_size=$(du -h "$LOG_DIR/daily_delivery.log" | cut -f1)
        log_info "配信ログファイル: $LOG_DIR/daily_delivery.log ($log_size)"
        
        # 最新のログエントリを表示
        log_info "最新の配信ログ（最後の5行）:"
        tail -n 5 "$LOG_DIR/daily_delivery.log" 2>/dev/null || log_warning "ログが空です"
    else
        log_info "配信ログファイル: まだ作成されていません"
    fi
}

# テスト実行
test_delivery() {
    log_info "配信システムのテスト実行を開始..."
    
    check_prerequisites
    
    log_info "ドライランモードでテスト実行中..."
    
    if cd "$PROJECT_ROOT" && "$PYTHON_PATH" "$NOTIFIER_SCRIPT" --dry-run --verbose; then
        log_success "テスト実行が完了しました"
        log_info "実際の配信を行う準備ができています"
    else
        log_error "テスト実行が失敗しました"
        log_info "設定ファイルやAPI認証情報を確認してください"
        exit 1
    fi
}

# ヘルプ表示
show_help() {
    cat << EOF
アニメ・マンガ情報配信システム - 日次配信設定スクリプト

Usage: $0 [COMMAND]

Commands:
    install    配信スケジュールをcrontabにインストール
    remove     配信スケジュールをcrontabから削除
    status     現在の配信スケジュール状況を表示
    test       配信システムのテスト実行（ドライラン）
    help       このヘルプを表示

配信スケジュール:
    朝8時   - メイン配信時刻
    昼12時  - 大量通知時の追加配信
    夜20時  - 大量通知時の追加配信

注意事項:
    ・システムのタイムゾーンが Asia/Tokyo に設定されていることを確認してください
    ・config.json とAPI認証情報が正しく設定されていることを確認してください
    ・ログは $LOG_DIR/daily_delivery.log に出力されます

EOF
}

# メイン処理
main() {
    local command="${1:-help}"
    
    case "$command" in
        "install")
            install_cron
            ;;
        "remove")
            remove_cron
            ;;
        "status")
            show_status
            ;;
        "test")
            test_delivery
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "不明なコマンド: $command"
            echo
            show_help
            exit 1
            ;;
    esac
}

# スクリプト実行
main "$@"