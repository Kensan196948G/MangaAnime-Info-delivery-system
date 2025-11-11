#!/bin/bash
# ローカル専用修復システム（GitHub Actions無効時用）

set -euo pipefail

# 設定
REPO="Kensan196948G/MangaAnime-Info-delivery-system"
WORK_DIR="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
LOG_DIR="$WORK_DIR/logs/local-repair"
STATE_FILE="$WORK_DIR/.github/repair-state/local-state.json"

# カラーコード
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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
        *)       echo "[$timestamp] $message" ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_DIR/local-$(date +%Y%m%d).log"
}

# ローカルファイルチェック
check_local_files() {
    log "INFO" "ローカルファイルの整合性をチェック中..."
    
    local issues=0
    
    # package.jsonチェック
    if [[ -f "$WORK_DIR/package.json" ]]; then
        if ! python3 -c "import json; json.load(open('$WORK_DIR/package.json'))" 2>/dev/null; then
            log "ERROR" "package.jsonに構文エラーがあります"
            ((issues++))
        fi
    fi
    
    # YAMLファイルチェック
    find "$WORK_DIR/.github/workflows" -name "*.yml" -o -name "*.yaml" 2>/dev/null | while read -r yaml_file; do
        if ! python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
            log "ERROR" "YAML構文エラー: $(basename $yaml_file)"
            ((issues++))
        else
            log "SUCCESS" "YAML検証OK: $(basename $yaml_file)"
        fi
    done
    
    # 権限チェック
    if [[ ! -w "$WORK_DIR/.github" ]]; then
        log "ERROR" ".githubディレクトリへの書き込み権限がありません"
        ((issues++))
    fi
    
    return $issues
}

# 依存関係の修復
fix_dependencies() {
    log "INFO" "依存関係をチェック・修復中..."
    
    cd "$WORK_DIR"
    
    # Node.js依存関係
    if [[ -f "package.json" ]]; then
        log "INFO" "Node.js依存関係を更新中..."
        
        # package-lock.jsonを削除して再生成
        rm -f package-lock.json
        npm install --legacy-peer-deps 2>&1 | tail -20
        
        # 脆弱性修正
        npm audit fix --force 2>&1 | tail -10 || true
        
        log "SUCCESS" "Node.js依存関係を更新しました"
    fi
    
    # Python依存関係
    if [[ -f "requirements.txt" ]]; then
        log "INFO" "Python依存関係を更新中..."
        
        if [[ -d ".venv" ]]; then
            source .venv/bin/activate
        fi
        
        pip install -r requirements.txt --upgrade 2>&1 | tail -10
        
        log "SUCCESS" "Python依存関係を更新しました"
    fi
}

# Gitリポジトリの状態確認
check_git_status() {
    log "INFO" "Gitリポジトリの状態を確認中..."
    
    cd "$WORK_DIR"
    
    # 未コミットの変更確認
    if ! git diff --quiet; then
        log "WARNING" "未コミットの変更があります"
        
        echo -e "${YELLOW}変更されたファイル:${NC}"
        git diff --name-only
        
        read -p "変更をコミットしますか？ (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add -A
            git commit -m "🔧 ローカル自動修復による変更

- 依存関係の更新
- 構成ファイルの修正

[Local Repair System]"
            git push
            log "SUCCESS" "変更をコミット・プッシュしました"
        fi
    else
        log "SUCCESS" "リポジトリはクリーンな状態です"
    fi
}

# メインループ
main() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     ローカル専用修復システム（GitHub Actions無効時用）    ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
    echo
    
    while true; do
        log "INFO" "=== 修復サイクル開始 ==="
        
        # 1. ローカルファイルチェック
        if check_local_files; then
            log "SUCCESS" "ローカルファイルは正常です"
        else
            log "WARNING" "ローカルファイルに問題があります"
        fi
        
        # 2. 依存関係の修復
        fix_dependencies
        
        # 3. Git状態確認
        check_git_status
        
        # 4. GitHub Actions状態確認（情報のみ）
        log "INFO" "GitHub Actions実行状況:"
        gh run list --repo "$REPO" --limit 5 | head -10
        
        log "INFO" "=== 修復サイクル完了 ==="
        
        # 次のサイクルまで待機
        echo -e "${CYAN}次の修復サイクルまで30分待機します...${NC}"
        echo "停止するには Ctrl+C を押してください"
        
        # 30分待機（デバッグ時は短縮可能）
        sleep 1800
    done
}

# 実行
case "${1:-}" in
    start)
        main
        ;;
    once)
        log "INFO" "単発実行モード"
        check_local_files
        fix_dependencies
        check_git_status
        ;;
    *)
        echo "使用方法: $0 {start|once}"
        echo ""
        echo "  start - 30分サイクルで継続実行"
        echo "  once  - 1回だけ実行"
        exit 1
        ;;
esac