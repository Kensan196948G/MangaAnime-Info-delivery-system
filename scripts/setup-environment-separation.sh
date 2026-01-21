#!/bin/bash

##############################################################################
# MangaAnime情報配信システム - 環境分離セットアップスクリプト
##############################################################################
#
# 用途: 開発環境と本番環境を完全に分離し、Git Worktreeベースの並列開発環境を構築
#
# 実行方法:
#   sudo bash scripts/setup-environment-separation.sh
#
# 前提条件:
#   - sudo権限（NOPASSWD設定推奨）
#   - Git インストール済み
#   - Python 3.8+ インストール済み
#   - Node.js インストール済み（オプション）
#
##############################################################################

set -e  # エラーで即座に終了
set -u  # 未定義変数使用時にエラー

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

log_section() {
    echo -e "\n${CYAN}===================================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}===================================================${NC}\n"
}

# プロジェクトルート取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"

log_info "プロジェクトルート: $PROJECT_ROOT"
log_info "プロジェクト名: $PROJECT_NAME"

# 設定
PROD_DIR="$PROJECT_ROOT"
DEV_DIR="${PROJECT_ROOT}-dev"
IP_ADDRESS="192.168.0.187"
DEV_HTTP_PORT="5000"
DEV_HTTPS_PORT="8444"
PROD_HTTP_PORT="3030"
PROD_HTTPS_PORT="8446"

##############################################################################
# Phase 1: 前提条件チェック
##############################################################################

log_section "Phase 1: 前提条件チェック"

# Gitリポジトリ確認
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    log_error "Gitリポジトリが見つかりません: $PROJECT_ROOT/.git"
    exit 1
fi
log_success "Gitリポジトリ確認完了"

# Python確認
if ! command -v python3 &> /dev/null; then
    log_error "Python3がインストールされていません"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
log_success "Python3 確認完了: $PYTHON_VERSION"

# sudo権限確認
if [ "$EUID" -ne 0 ]; then
    log_error "このスクリプトはsudo権限で実行する必要があります"
    log_info "実行方法: sudo bash $0"
    exit 1
fi
log_success "sudo権限確認完了"

# 実行ユーザー取得（sudoで実行されている場合、元のユーザーを取得）
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(eval echo ~$REAL_USER)
log_info "実行ユーザー: $REAL_USER"

##############################################################################
# Phase 2: Git Worktree構成
##############################################################################

log_section "Phase 2: Git Worktree構成"

cd "$PROJECT_ROOT"

# developブランチ作成（存在しない場合）
if ! git show-ref --verify --quiet refs/heads/develop; then
    log_info "developブランチを作成します..."
    sudo -u "$REAL_USER" git branch develop
    log_success "developブランチ作成完了"
else
    log_warning "developブランチは既に存在します"
fi

# 開発環境Worktree作成
if [ -d "$DEV_DIR" ]; then
    log_warning "開発環境ディレクトリが既に存在します: $DEV_DIR"
    log_info "既存の開発環境は削除せず保持します"
fi

if [ ! -d "$DEV_DIR" ]; then
    log_info "開発環境Worktreeを作成します..."
    cd "$PROJECT_ROOT"
    sudo -u "$REAL_USER" git worktree add "$DEV_DIR" develop
    log_success "開発環境Worktree作成完了: $DEV_DIR"
fi

# Worktree一覧表示
log_info "Worktree一覧:"
sudo -u "$REAL_USER" git worktree list

##############################################################################
# Phase 3: ディレクトリ構造整備
##############################################################################

log_section "Phase 3: ディレクトリ構造整備"

# 本番環境ディレクトリ
log_info "本番環境ディレクトリを整備します..."
mkdir -p "$PROD_DIR"/{data,logs/prod,backups/prod,config}
chown -R "$REAL_USER:$REAL_USER" "$PROD_DIR"/{data,logs,backups,config}

# 開発環境ディレクトリ
log_info "開発環境ディレクトリを整備します..."
mkdir -p "$DEV_DIR"/{data,logs/dev,backups/dev,config,sample_data}
chown -R "$REAL_USER:$REAL_USER" "$DEV_DIR"/{data,logs,backups,config,sample_data}

log_success "ディレクトリ構造整備完了"

##############################################################################
# Phase 4: Python仮想環境構築
##############################################################################

log_section "Phase 4: Python仮想環境構築"

# 本番環境Python仮想環境
if [ ! -d "$PROD_DIR/venv_prod" ]; then
    log_info "本番環境Python仮想環境を作成します..."
    cd "$PROD_DIR"
    sudo -u "$REAL_USER" python3 -m venv venv_prod
    sudo -u "$REAL_USER" "$PROD_DIR/venv_prod/bin/pip" install --upgrade pip setuptools wheel
    if [ -f "$PROD_DIR/requirements.txt" ]; then
        sudo -u "$REAL_USER" "$PROD_DIR/venv_prod/bin/pip" install -r requirements.txt
    fi
    # Gunicornインストール（本番環境用）
    sudo -u "$REAL_USER" "$PROD_DIR/venv_prod/bin/pip" install gunicorn
    log_success "本番環境Python仮想環境作成完了"
else
    log_warning "本番環境Python仮想環境は既に存在します"
fi

# 開発環境Python仮想環境
if [ ! -d "$DEV_DIR/venv_dev" ]; then
    log_info "開発環境Python仮想環境を作成します..."
    cd "$DEV_DIR"
    sudo -u "$REAL_USER" python3 -m venv venv_dev
    sudo -u "$REAL_USER" "$DEV_DIR/venv_dev/bin/pip" install --upgrade pip setuptools wheel
    if [ -f "$DEV_DIR/requirements.txt" ]; then
        sudo -u "$REAL_USER" "$DEV_DIR/venv_dev/bin/pip" install -r requirements.txt
    fi
    # 開発用パッケージインストール
    sudo -u "$REAL_USER" "$DEV_DIR/venv_dev/bin/pip" install pytest pytest-cov black flake8 mypy ipython
    log_success "開発環境Python仮想環境作成完了"
else
    log_warning "開発環境Python仮想環境は既に存在します"
fi

##############################################################################
# Phase 5: 設定ファイル作成
##############################################################################

log_section "Phase 5: 設定ファイル作成"

# 本番環境設定ファイル
if [ -f "$PROD_DIR/config/config.json" ] && [ ! -f "$PROD_DIR/config/config.prod.json" ]; then
    log_info "本番環境設定ファイルを作成します..."
    sudo -u "$REAL_USER" cp "$PROD_DIR/config/config.json" "$PROD_DIR/config/config.prod.json"

    # 本番環境設定を更新
    sudo -u "$REAL_USER" python3 << EOF
import json
with open('$PROD_DIR/config/config.prod.json', 'r') as f:
    config = json.load(f)

config['system']['environment'] = 'production'
config['server']['port'] = $PROD_HTTP_PORT
config['database']['path'] = 'data/prod_db.sqlite3'
config['logging']['file_path'] = './logs/prod/app.log'

with open('$PROD_DIR/config/config.prod.json', 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
EOF
    log_success "本番環境設定ファイル作成完了"
fi

# 開発環境設定ファイル
if [ -f "$DEV_DIR/config/config.json" ] && [ ! -f "$DEV_DIR/config/config.dev.json" ]; then
    log_info "開発環境設定ファイルを作成します..."
    sudo -u "$REAL_USER" cp "$DEV_DIR/config/config.json" "$DEV_DIR/config/config.dev.json"

    # 開発環境設定を更新
    sudo -u "$REAL_USER" python3 << EOF
import json
with open('$DEV_DIR/config/config.dev.json', 'r') as f:
    config = json.load(f)

config['system']['environment'] = 'development'
config['system']['log_level'] = 'DEBUG'
config['server']['port'] = $DEV_HTTP_PORT
config['database']['path'] = 'data/dev_db.sqlite3'
config['logging']['file_path'] = './logs/dev/app.log'

with open('$DEV_DIR/config/config.dev.json', 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
EOF
    log_success "開発環境設定ファイル作成完了"
fi

##############################################################################
# Phase 6: SSL証明書生成
##############################################################################

log_section "Phase 6: SSL証明書生成"

SSL_BASE_DIR="/etc/ssl/mangaanime"

# SSL証明書ディレクトリ作成
mkdir -p "$SSL_BASE_DIR"/{dev,prod}

# 開発環境用SSL証明書
if [ ! -f "$SSL_BASE_DIR/dev/server.crt" ]; then
    log_info "開発環境用SSL証明書を生成します..."
    openssl req -x509 -nodes -days 3650 \
        -newkey rsa:2048 \
        -keyout "$SSL_BASE_DIR/dev/server.key" \
        -out "$SSL_BASE_DIR/dev/server.crt" \
        -subj "/C=JP/ST=Tokyo/L=Tokyo/O=MangaAnime Dev/CN=$IP_ADDRESS" \
        -addext "subjectAltName=IP:$IP_ADDRESS,DNS:localhost" \
        2>/dev/null

    chmod 600 "$SSL_BASE_DIR/dev/server.key"
    chmod 644 "$SSL_BASE_DIR/dev/server.crt"
    log_success "開発環境用SSL証明書生成完了"
else
    log_warning "開発環境用SSL証明書は既に存在します"
fi

# 本番環境用SSL証明書
if [ ! -f "$SSL_BASE_DIR/prod/server.crt" ]; then
    log_info "本番環境用SSL証明書を生成します..."
    openssl req -x509 -nodes -days 3650 \
        -newkey rsa:2048 \
        -keyout "$SSL_BASE_DIR/prod/server.key" \
        -out "$SSL_BASE_DIR/prod/server.crt" \
        -subj "/C=JP/ST=Tokyo/L=Tokyo/O=MangaAnime Prod/CN=$IP_ADDRESS" \
        -addext "subjectAltName=IP:$IP_ADDRESS,DNS:localhost" \
        2>/dev/null

    chmod 600 "$SSL_BASE_DIR/prod/server.key"
    chmod 644 "$SSL_BASE_DIR/prod/server.crt"
    log_success "本番環境用SSL証明書生成完了"
else
    log_warning "本番環境用SSL証明書は既に存在します"
fi

##############################################################################
# Phase 7: systemdサービスファイル作成
##############################################################################

log_section "Phase 7: systemdサービスファイル作成"

# 開発環境サービスファイル
DEV_SERVICE_FILE="/etc/systemd/system/mangaanime-web-dev.service"
if [ ! -f "$DEV_SERVICE_FILE" ]; then
    log_info "開発環境systemdサービスファイルを作成します..."
    cat > "$DEV_SERVICE_FILE" << EOF
[Unit]
Description=MangaAnime Information Delivery System - Development Environment
After=network.target
Wants=network.target

[Service]
Type=simple
User=$REAL_USER
Group=$REAL_USER
WorkingDirectory=$DEV_DIR

Environment="FLASK_ENV=development"
Environment="FLASK_DEBUG=1"
Environment="CONFIG_FILE=config/config.dev.json"
Environment="DATABASE_PATH=data/dev_db.sqlite3"
Environment="LOG_PATH=logs/dev/app.log"
Environment="PORT=$DEV_HTTP_PORT"
Environment="PATH=$DEV_DIR/venv_dev/bin:/usr/local/bin:/usr/bin:/bin"

ExecStart=$DEV_DIR/venv_dev/bin/python $DEV_DIR/app/web_app.py

Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

StandardOutput=append:$DEV_DIR/logs/dev/systemd.log
StandardError=append:$DEV_DIR/logs/dev/systemd_error.log

NoNewPrivileges=true
PrivateTmp=true

LimitNOFILE=65536
MemoryLimit=2G
CPUQuota=100%

[Install]
WantedBy=multi-user.target
EOF
    log_success "開発環境systemdサービスファイル作成完了"
else
    log_warning "開発環境systemdサービスファイルは既に存在します"
fi

# 本番環境サービスファイル
PROD_SERVICE_FILE="/etc/systemd/system/mangaanime-web-prod.service"
if [ ! -f "$PROD_SERVICE_FILE" ]; then
    log_info "本番環境systemdサービスファイルを作成します..."
    cat > "$PROD_SERVICE_FILE" << EOF
[Unit]
Description=MangaAnime Information Delivery System - Production Environment
After=network.target
Wants=network.target

[Service]
Type=simple
User=$REAL_USER
Group=$REAL_USER
WorkingDirectory=$PROD_DIR

Environment="FLASK_ENV=production"
Environment="FLASK_DEBUG=0"
Environment="CONFIG_FILE=config/config.prod.json"
Environment="DATABASE_PATH=data/prod_db.sqlite3"
Environment="LOG_PATH=logs/prod/app.log"
Environment="PORT=$PROD_HTTP_PORT"
Environment="PATH=$PROD_DIR/venv_prod/bin:/usr/local/bin:/usr/bin:/bin"

ExecStart=$PROD_DIR/venv_prod/bin/gunicorn \
    --bind 0.0.0.0:$PROD_HTTP_PORT \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile $PROD_DIR/logs/prod/gunicorn_access.log \
    --error-logfile $PROD_DIR/logs/prod/gunicorn_error.log \
    --log-level info \
    app.web_app:app

Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

StandardOutput=append:$PROD_DIR/logs/prod/systemd.log
StandardError=append:$PROD_DIR/logs/prod/systemd_error.log

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROD_DIR/data $PROD_DIR/logs

LimitNOFILE=65536
MemoryLimit=4G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
EOF
    log_success "本番環境systemdサービスファイル作成完了"
else
    log_warning "本番環境systemdサービスファイルは既に存在します"
fi

# systemd設定再読み込み
systemctl daemon-reload
log_success "systemd設定再読み込み完了"

##############################################################################
# Phase 8: サービス有効化・起動
##############################################################################

log_section "Phase 8: サービス有効化・起動"

# 既存サービス停止（存在する場合）
if systemctl is-active --quiet mangaanime-web.service; then
    log_info "既存のmangaanime-web.serviceを停止します..."
    systemctl stop mangaanime-web.service
    log_success "既存サービス停止完了"
fi

# 開発環境サービス有効化
systemctl enable mangaanime-web-dev.service
log_success "開発環境サービス有効化完了"

# 本番環境サービス有効化
systemctl enable mangaanime-web-prod.service
log_success "本番環境サービス有効化完了"

# サービス起動確認
read -p "サービスを今すぐ起動しますか？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "開発環境サービスを起動します..."
    systemctl start mangaanime-web-dev.service
    sleep 3
    if systemctl is-active --quiet mangaanime-web-dev.service; then
        log_success "開発環境サービス起動成功"
    else
        log_error "開発環境サービス起動失敗"
        systemctl status mangaanime-web-dev.service
    fi

    log_info "本番環境サービスを起動します..."
    systemctl start mangaanime-web-prod.service
    sleep 3
    if systemctl is-active --quiet mangaanime-web-prod.service; then
        log_success "本番環境サービス起動成功"
    else
        log_error "本番環境サービス起動失敗"
        systemctl status mangaanime-web-prod.service
    fi
fi

##############################################################################
# Phase 9: 完了レポート
##############################################################################

log_section "セットアップ完了"

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  MangaAnime情報配信システム - 環境分離セットアップ完了${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${CYAN}📁 ディレクトリ構成:${NC}"
echo -e "  本番環境: $PROD_DIR"
echo -e "  開発環境: $DEV_DIR\n"

echo -e "${CYAN}🌐 アクセスURL:${NC}"
echo -e "  ${YELLOW}【開発環境】${NC}"
echo -e "    HTTP  : http://$IP_ADDRESS:$DEV_HTTP_PORT"
echo -e "    HTTPS : https://$IP_ADDRESS:$DEV_HTTPS_PORT (要Nginx設定)"
echo -e "  ${GREEN}【本番環境】${NC}"
echo -e "    HTTP  : http://$IP_ADDRESS:$PROD_HTTP_PORT"
echo -e "    HTTPS : https://$IP_ADDRESS:$PROD_HTTPS_PORT (要Nginx設定)\n"

echo -e "${CYAN}⚙️  systemdサービス:${NC}"
echo -e "  開発環境: mangaanime-web-dev.service"
echo -e "  本番環境: mangaanime-web-prod.service\n"

echo -e "${CYAN}🔧 管理コマンド:${NC}"
echo -e "  # サービス状態確認"
echo -e "  sudo systemctl status mangaanime-web-dev.service"
echo -e "  sudo systemctl status mangaanime-web-prod.service\n"
echo -e "  # サービス起動"
echo -e "  sudo systemctl start mangaanime-web-dev.service"
echo -e "  sudo systemctl start mangaanime-web-prod.service\n"
echo -e "  # サービス停止"
echo -e "  sudo systemctl stop mangaanime-web-dev.service"
echo -e "  sudo systemctl stop mangaanime-web-prod.service\n"
echo -e "  # サービス再起動"
echo -e "  sudo systemctl restart mangaanime-web-dev.service"
echo -e "  sudo systemctl restart mangaanime-web-prod.service\n"
echo -e "  # ログ確認"
echo -e "  sudo journalctl -u mangaanime-web-dev.service -f"
echo -e "  sudo journalctl -u mangaanime-web-prod.service -f\n"

echo -e "${CYAN}🌳 Git Worktree管理:${NC}"
echo -e "  # Worktree一覧表示"
echo -e "  cd $PROD_DIR && git worktree list\n"
echo -e "  # 機能開発用Worktree作成"
echo -e "  cd $PROD_DIR && git worktree add ../MangaAnime-Info-delivery-system-feature-XXX feature/XXX\n"
echo -e "  # Worktree削除"
echo -e "  cd $PROD_DIR && git worktree remove ../MangaAnime-Info-delivery-system-feature-XXX\n"

echo -e "${CYAN}📚 次のステップ:${NC}"
echo -e "  1. Nginx設定（HTTPS対応）"
echo -e "  2. ファイアウォール設定（ポート開放）"
echo -e "  3. サンプルデータ投入（開発環境）"
echo -e "  4. 本番データ移行・クリーニング"
echo -e "  5. ブックマーク作成\n"

echo -e "${CYAN}📖 詳細ドキュメント:${NC}"
echo -e "  $PROD_DIR/docs/ENVIRONMENT_SEPARATION_DESIGN.md\n"

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
log_success "環境分離セットアップが正常に完了しました!"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
