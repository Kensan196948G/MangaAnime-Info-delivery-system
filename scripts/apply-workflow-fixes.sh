#!/bin/bash

###############################################################################
# GitHub Actions ワークフロー修正適用スクリプト
#
# 説明: 修正されたワークフローファイルを適用します
# 作成日: 2025-11-15
# バージョン: 1.0.0
###############################################################################

set -euo pipefail

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# プロジェクトルートディレクトリ
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKFLOW_DIR="$PROJECT_ROOT/.github/workflows"
BACKUP_DIR="$WORKFLOW_DIR/backup"

# ログ関数
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

# ヘッダー表示
print_header() {
    echo "================================================================================"
    echo "  GitHub Actions ワークフロー修正適用スクリプト"
    echo "================================================================================"
    echo ""
}

# バックアップディレクトリ作成
create_backup_dir() {
    log_info "バックアップディレクトリを作成中..."

    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        log_success "バックアップディレクトリを作成しました: $BACKUP_DIR"
    else
        log_info "バックアップディレクトリは既に存在します"
    fi
}

# 既存ファイルのバックアップ
backup_existing_files() {
    log_info "既存ファイルをバックアップ中..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local files_backed_up=0

    if [ -f "$WORKFLOW_DIR/auto-error-detection-repair.yml" ]; then
        cp "$WORKFLOW_DIR/auto-error-detection-repair.yml" \
           "$BACKUP_DIR/auto-error-detection-repair.yml.$timestamp"
        log_success "バックアップ: auto-error-detection-repair.yml → auto-error-detection-repair.yml.$timestamp"
        ((files_backed_up++))
    fi

    if [ -f "$WORKFLOW_DIR/auto-error-detection-repair-v2.yml" ]; then
        cp "$WORKFLOW_DIR/auto-error-detection-repair-v2.yml" \
           "$BACKUP_DIR/auto-error-detection-repair-v2.yml.$timestamp"
        log_success "バックアップ: auto-error-detection-repair-v2.yml → auto-error-detection-repair-v2.yml.$timestamp"
        ((files_backed_up++))
    fi

    if [ $files_backed_up -eq 0 ]; then
        log_warning "バックアップするファイルが見つかりませんでした"
    else
        log_success "合計 $files_backed_up ファイルをバックアップしました"
    fi
}

# 修正版ファイルの適用
apply_fixed_files() {
    log_info "修正版ファイルを適用中..."

    local files_applied=0

    if [ -f "$WORKFLOW_DIR/auto-error-detection-repair-fixed.yml" ]; then
        mv "$WORKFLOW_DIR/auto-error-detection-repair-fixed.yml" \
           "$WORKFLOW_DIR/auto-error-detection-repair.yml"
        log_success "適用: auto-error-detection-repair-fixed.yml → auto-error-detection-repair.yml"
        ((files_applied++))
    else
        log_error "修正版ファイルが見つかりません: auto-error-detection-repair-fixed.yml"
    fi

    if [ -f "$WORKFLOW_DIR/auto-error-detection-repair-v2-fixed.yml" ]; then
        mv "$WORKFLOW_DIR/auto-error-detection-repair-v2-fixed.yml" \
           "$WORKFLOW_DIR/auto-error-detection-repair-v2.yml"
        log_success "適用: auto-error-detection-repair-v2-fixed.yml → auto-error-detection-repair-v2.yml"
        ((files_applied++))
    else
        log_error "修正版ファイルが見つかりません: auto-error-detection-repair-v2-fixed.yml"
    fi

    if [ $files_applied -eq 0 ]; then
        log_error "適用するファイルが見つかりませんでした"
        return 1
    else
        log_success "合計 $files_applied ファイルを適用しました"
    fi
}

# 検証（actionlint）
validate_workflows() {
    log_info "ワークフローファイルを検証中..."

    local validation_failed=0

    # actionlintがインストールされているか確認
    if ! command -v actionlint &> /dev/null; then
        log_warning "actionlintがインストールされていません。検証をスキップします"
        return 0
    fi

    if [ -f "$WORKFLOW_DIR/auto-error-detection-repair.yml" ]; then
        if actionlint "$WORKFLOW_DIR/auto-error-detection-repair.yml"; then
            log_success "検証成功: auto-error-detection-repair.yml"
        else
            log_error "検証失敗: auto-error-detection-repair.yml"
            ((validation_failed++))
        fi
    fi

    if [ -f "$WORKFLOW_DIR/auto-error-detection-repair-v2.yml" ]; then
        if actionlint "$WORKFLOW_DIR/auto-error-detection-repair-v2.yml"; then
            log_success "検証成功: auto-error-detection-repair-v2.yml"
        else
            log_error "検証失敗: auto-error-detection-repair-v2.yml"
            ((validation_failed++))
        fi
    fi

    if [ $validation_failed -gt 0 ]; then
        log_error "検証に失敗したファイルが $validation_failed 個あります"
        return 1
    fi

    log_success "すべてのワークフローファイルの検証に成功しました"
}

# バックアップからの復元
restore_from_backup() {
    log_info "バックアップから復元中..."

    local latest_backup=$(ls -t "$BACKUP_DIR"/*.yml.* 2>/dev/null | head -1)

    if [ -z "$latest_backup" ]; then
        log_error "復元するバックアップが見つかりません"
        return 1
    fi

    local timestamp=$(echo "$latest_backup" | sed 's/.*\.\([0-9_]*\)$/\1/')

    if [ -f "$BACKUP_DIR/auto-error-detection-repair.yml.$timestamp" ]; then
        cp "$BACKUP_DIR/auto-error-detection-repair.yml.$timestamp" \
           "$WORKFLOW_DIR/auto-error-detection-repair.yml"
        log_success "復元: auto-error-detection-repair.yml"
    fi

    if [ -f "$BACKUP_DIR/auto-error-detection-repair-v2.yml.$timestamp" ]; then
        cp "$BACKUP_DIR/auto-error-detection-repair-v2.yml.$timestamp" \
           "$WORKFLOW_DIR/auto-error-detection-repair-v2.yml"
        log_success "復元: auto-error-detection-repair-v2.yml"
    fi

    log_success "バックアップからの復元が完了しました"
}

# サマリー表示
print_summary() {
    echo ""
    echo "================================================================================"
    echo "  適用サマリー"
    echo "================================================================================"
    echo ""
    echo "✅ バックアップ: $BACKUP_DIR"
    echo "✅ 適用済みファイル:"
    echo "   - auto-error-detection-repair.yml"
    echo "   - auto-error-detection-repair-v2.yml"
    echo ""
    echo "📝 次のステップ:"
    echo "   1. git status でファイルの変更を確認"
    echo "   2. git add .github/workflows/"
    echo "   3. git commit -m \"fix: GitHub Actions ワークフローの修正を適用\""
    echo "   4. git push"
    echo "   5. GitHub Actionsページでワークフローの実行を確認"
    echo ""
    echo "📚 ドキュメント:"
    echo "   - 検証レポート: docs/workflow-validation-report.md"
    echo "   - 修正内容詳細: docs/workflow-fixes-changelog.md"
    echo ""
    echo "================================================================================"
}

# メイン処理
main() {
    print_header

    # ディレクトリの存在確認
    if [ ! -d "$WORKFLOW_DIR" ]; then
        log_error "ワークフローディレクトリが見つかりません: $WORKFLOW_DIR"
        exit 1
    fi

    # 確認プロンプト
    echo "この操作により、以下のファイルが置き換えられます:"
    echo "  - auto-error-detection-repair.yml"
    echo "  - auto-error-detection-repair-v2.yml"
    echo ""
    echo "既存のファイルは $BACKUP_DIR にバックアップされます。"
    echo ""
    read -p "続行しますか? (y/N): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "操作をキャンセルしました"
        exit 0
    fi

    # 処理実行
    create_backup_dir
    backup_existing_files

    if apply_fixed_files; then
        if validate_workflows; then
            print_summary
            log_success "修正の適用が完了しました"
            exit 0
        else
            log_error "検証に失敗しました。バックアップから復元します..."
            restore_from_backup
            exit 1
        fi
    else
        log_error "修正ファイルの適用に失敗しました"
        exit 1
    fi
}

# エラーハンドリング
trap 'log_error "エラーが発生しました。処理を中断します"; exit 1' ERR

# スクリプト実行
main "$@"
