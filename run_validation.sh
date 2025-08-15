#!/bin/bash
# アニメ・マンガ情報配信システム - 最終検証実行スクリプト
# Final Validation Execution Script

set -e  # エラー時に停止

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# プロジェクトルート設定
PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
cd "$PROJECT_ROOT"

# ロゴ表示
echo -e "${CYAN}"
echo "========================================================================="
echo "🎯 アニメ・マンガ情報配信システム - 最終検証スイート"
echo "   Final System Validation Suite"
echo "========================================================================="
echo -e "${NC}"

# 使用方法表示
show_usage() {
    echo -e "${WHITE}使用方法:${NC}"
    echo "  $0 [オプション]"
    echo ""
    echo -e "${WHITE}オプション:${NC}"
    echo "  -h, --help           このヘルプを表示"
    echo "  -q, --quick          高速チェックのみ実行"
    echo "  -p, --performance    パフォーマンステストのみ実行"
    echo "  -i, --integration    統合テストのみ実行"
    echo "  -m, --monitoring     ヘルスチェックのみ実行"
    echo "  -f, --full           完全検証実行（デフォルト）"
    echo "  -s, --setup          初期セットアップのみ実行"
    echo "  -c, --clean          クリーンアップのみ実行"
    echo "  --debug              デバッグモードで実行"
    echo ""
    echo -e "${WHITE}例:${NC}"
    echo "  $0 --quick                # 高速チェック"
    echo "  $0 --performance          # パフォーマンステスト"
    echo "  $0 --full                 # 完全検証"
    echo ""
}

# ログ関数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_section() {
    echo ""
    echo -e "${PURPLE}🔹 $1${NC}"
    echo "----------------------------------------"
}

# 前提条件チェック
check_prerequisites() {
    log_section "前提条件チェック"
    
    # Python確認
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python: $PYTHON_VERSION"
    else
        log_error "Python3がインストールされていません"
        exit 1
    fi
    
    # pip確認
    if command -v pip3 &> /dev/null; then
        log_success "pip3: 利用可能"
    else
        log_error "pip3がインストールされていません"
        exit 1
    fi
    
    # インターネット接続確認
    if ping -c 1 google.com &> /dev/null; then
        log_success "インターネット接続: OK"
    else
        log_warning "インターネット接続に問題があります"
    fi
    
    # ディスク容量確認
    AVAILABLE_SPACE=$(df "$PROJECT_ROOT" | tail -1 | awk '{print $4}')
    if [ "$AVAILABLE_SPACE" -gt 1000000 ]; then  # 1GB以上
        log_success "ディスク容量: 十分"
    else
        log_warning "ディスク容量が不足している可能性があります"
    fi
}

# セットアップ実行
setup_system() {
    log_section "システムセットアップ"
    
    # ディレクトリ作成
    mkdir -p logs config templates static
    log_success "ディレクトリ構造作成完了"
    
    # 依存関係インストール
    if [ -f "requirements.txt" ]; then
        log_info "依存関係をインストール中..."
        pip3 install -r requirements.txt --quiet --user || {
            log_error "依存関係のインストールに失敗しました"
            exit 1
        }
        log_success "依存関係インストール完了"
    else
        log_warning "requirements.txtが見つかりません"
    fi
    
    # スクリプト権限設定
    chmod +x scripts/*.py 2>/dev/null || true
    chmod +x scripts/*.sh 2>/dev/null || true
    log_success "実行権限設定完了"
}

# 高速チェック
quick_check() {
    log_section "高速システムチェック"
    
    # Python環境
    echo -n "🐍 Python環境: "
    python3 -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
    
    # SQLite
    echo -n "🗃️  SQLite: "
    python3 -c "import sqlite3; print(f'バージョン {sqlite3.sqlite_version}')"
    
    # 主要パッケージ
    echo -n "📦 パッケージ: "
    if python3 -c "import requests, aiohttp, flask" &>/dev/null; then
        echo "主要パッケージOK"
    else
        echo "パッケージに問題があります"
    fi
    
    # ファイル確認
    echo -n "📊 データベース: "
    [ -f "db.sqlite3" ] && echo "存在" || echo "未作成"
    
    echo -n "⚙️  設定ファイル: "
    [ -f "config/config.json" ] && echo "存在" || echo "未作成"
    
    log_success "高速チェック完了"
}

# パフォーマンステスト実行
run_performance_test() {
    log_section "パフォーマンステスト実行"
    
    if [ -f "scripts/performance_validation.py" ]; then
        log_info "パフォーマンス検証を実行中..."
        python3 scripts/performance_validation.py || {
            log_error "パフォーマンステストに失敗しました"
            return 1
        }
        log_success "パフォーマンステスト完了"
    else
        log_error "パフォーマンステストスクリプトが見つかりません"
        return 1
    fi
}

# 統合テスト実行
run_integration_test() {
    log_section "統合テスト実行"
    
    if [ -f "scripts/integration_test.py" ]; then
        log_info "統合テストを実行中..."
        python3 scripts/integration_test.py || {
            log_error "統合テストに失敗しました"
            return 1
        }
        log_success "統合テスト完了"
    else
        log_error "統合テストスクリプトが見つかりません"
        return 1
    fi
}

# 監視テスト実行
run_monitoring_test() {
    log_section "システム監視テスト実行"
    
    if [ -f "scripts/operational_monitoring.py" ]; then
        log_info "システムヘルスチェックを実行中..."
        python3 scripts/operational_monitoring.py || {
            log_error "ヘルスチェックに失敗しました"
            return 1
        }
        log_success "ヘルスチェック完了"
    else
        log_error "監視スクリプトが見つかりません"
        return 1
    fi
}

# 完全検証実行
run_full_validation() {
    log_section "完全システム検証実行"
    
    if [ -f "scripts/final_validation.py" ]; then
        log_info "最終システム検証を実行中（数分かかる場合があります）..."
        python3 scripts/final_validation.py || {
            log_error "最終検証に失敗しました"
            return 1
        }
        log_success "最終検証完了"
    else
        log_error "最終検証スクリプトが見つかりません"
        return 1
    fi
}

# クリーンアップ
cleanup() {
    log_section "システムクリーンアップ"
    
    # 一時ファイル削除
    rm -f test_db.sqlite3
    rm -f logs/monitoring.pid
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    log_success "クリーンアップ完了"
}

# 結果表示
show_results() {
    log_section "検証結果"
    
    # 結果ファイル確認
    if [ -f "FINAL_VALIDATION_REPORT.txt" ]; then
        log_success "詳細レポートが生成されました: FINAL_VALIDATION_REPORT.txt"
        echo ""
        # レポートのサマリー部分を表示
        head -n 20 "FINAL_VALIDATION_REPORT.txt"
        echo ""
        echo "詳細は以下のファイルを確認してください:"
        echo "  📄 FINAL_VALIDATION_REPORT.txt (人間可読版)"
        echo "  📄 FINAL_VALIDATION_REPORT.json (詳細データ)"
    fi
    
    # ログファイル確認
    if [ -d "logs" ] && [ "$(ls -A logs/)" ]; then
        echo ""
        log_info "ログファイルが以下に保存されました:"
        ls -la logs/*.log 2>/dev/null | while read line; do
            echo "    $line"
        done
    fi
}

# デバッグ情報表示
show_debug_info() {
    log_section "デバッグ情報"
    
    echo "1. システム情報:"
    echo "   OS: $(uname -s) $(uname -r)"
    echo "   アーキテクチャ: $(uname -m)"
    echo "   CPU: $(nproc) コア"
    echo "   メモリ: $(free -h | grep '^Mem:' | awk '{print $2}') 総容量"
    echo ""
    
    echo "2. Python環境:"
    python3 -c "
import sys
print(f'   Python: {sys.version}')
print(f'   実行可能ファイル: {sys.executable}')
print(f'   パス: {sys.path[:3]}...')
"
    echo ""
    
    echo "3. プロジェクト構成:"
    find . -maxdepth 2 -name "*.py" | head -10 | while read file; do
        echo "   $file"
    done
    echo ""
    
    echo "4. 権限情報:"
    ls -la . | head -5
}

# メイン処理
main() {
    local mode="full"
    local debug_mode=false
    
    # 引数解析
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -q|--quick)
                mode="quick"
                shift
                ;;
            -p|--performance)
                mode="performance"
                shift
                ;;
            -i|--integration)
                mode="integration"
                shift
                ;;
            -m|--monitoring)
                mode="monitoring"
                shift
                ;;
            -f|--full)
                mode="full"
                shift
                ;;
            -s|--setup)
                mode="setup"
                shift
                ;;
            -c|--clean)
                mode="clean"
                shift
                ;;
            --debug)
                debug_mode=true
                shift
                ;;
            *)
                log_error "未知のオプション: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # デバッグモード
    if [ "$debug_mode" = true ]; then
        show_debug_info
    fi
    
    # 実行開始時刻記録
    START_TIME=$(date +%s)
    
    # 前提条件チェック（クリーンアップ以外）
    if [ "$mode" != "clean" ]; then
        check_prerequisites
    fi
    
    # モード別実行
    case $mode in
        quick)
            quick_check
            ;;
        performance)
            setup_system
            run_performance_test || exit 1
            ;;
        integration)
            setup_system
            run_integration_test || exit 1
            ;;
        monitoring)
            setup_system
            run_monitoring_test || exit 1
            ;;
        setup)
            setup_system
            ;;
        clean)
            cleanup
            ;;
        full)
            setup_system
            run_full_validation || exit 1
            show_results
            ;;
        *)
            log_error "未知のモード: $mode"
            exit 1
            ;;
    esac
    
    # 実行時間計算
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo ""
    log_success "検証完了 (実行時間: ${DURATION}秒)"
    
    if [ "$mode" = "full" ]; then
        echo ""
        echo -e "${WHITE}🎉 システム検証が完了しました！${NC}"
        echo "結果を確認して、本番運用の準備を行ってください。"
    fi
}

# エラーハンドリング
trap 'log_error "スクリプト実行中にエラーが発生しました"; exit 1' ERR

# メイン関数実行
main "$@"