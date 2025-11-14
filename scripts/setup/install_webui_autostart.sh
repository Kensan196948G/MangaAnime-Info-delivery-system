#!/bin/bash

# =============================================================================
# MangaAnime WebUI 自動起動設定スクリプト
# =============================================================================

set -e

echo "🚀 MangaAnime WebUI 自動起動設定を開始します..."

# 色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
SERVICE_NAME="mangaanime-web"
SERVICE_FILE="$PROJECT_DIR/mangaanime-web.service"

# 前提条件チェック
echo -e "${BLUE}📋 前提条件チェック...${NC}"

if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}❌ サービスファイルが見つかりません: $SERVICE_FILE${NC}"
    exit 1
fi

if [ ! -f "$PROJECT_DIR/web_app.py" ]; then
    echo -e "${RED}❌ web_app.py が見つかりません${NC}"
    exit 1
fi

if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "${YELLOW}⚠️  Python仮想環境が見つかりません。作成しますか？ (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${BLUE}🐍 Python仮想環境を作成中...${NC}"
        cd "$PROJECT_DIR"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        echo -e "${GREEN}✅ Python仮想環境作成完了${NC}"
    else
        echo -e "${RED}❌ Python仮想環境が必要です${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ 前提条件チェック完了${NC}"
echo ""

# systemdサービス設定
echo -e "${BLUE}⚙️  systemdサービス設定中...${NC}"

echo "以下のコマンドを手動で実行してください（sudo権限が必要）:"
echo ""
echo -e "${YELLOW}# サービスファイルをコピー${NC}"
echo "sudo cp $SERVICE_FILE /etc/systemd/system/"
echo ""
echo -e "${YELLOW}# systemdリロード${NC}"
echo "sudo systemctl daemon-reload"
echo ""
echo -e "${YELLOW}# サービス有効化${NC}"
echo "sudo systemctl enable $SERVICE_NAME"
echo ""
echo -e "${YELLOW}# サービス開始${NC}"
echo "sudo systemctl start $SERVICE_NAME"
echo ""
echo -e "${YELLOW}# サービス状態確認${NC}"
echo "sudo systemctl status $SERVICE_NAME"
echo ""

# 自動実行用のワンライナーコマンドも提供
echo -e "${BLUE}📝 ワンライナーコマンド（コピー&ペースト用）:${NC}"
echo ""
echo -e "${GREEN}sudo cp $SERVICE_FILE /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable $SERVICE_NAME && sudo systemctl start $SERVICE_NAME && sudo systemctl status $SERVICE_NAME${NC}"
echo ""

# 検証用のコマンド
echo -e "${BLUE}🔍 設定後の確認コマンド:${NC}"
echo ""
echo "# サービス状態確認"
echo "systemctl is-enabled $SERVICE_NAME"
echo "systemctl is-active $SERVICE_NAME"
echo ""
echo "# ログ確認"
echo "journalctl -u $SERVICE_NAME -f"
echo ""
echo "# WebUI動作確認"
IP_ADDRESS=$(hostname -I | awk '{print $1}')
echo "curl -I http://localhost:3030"
echo "curl -I http://${IP_ADDRESS}:3030"
echo ""

# 起動スクリプトの作成
echo -e "${BLUE}📝 手動起動スクリプトも作成します...${NC}"

cat > "$PROJECT_DIR/start_webui_manual.sh" << 'EOF'
#!/bin/bash

# Manual WebUI startup script
cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"

echo "🚀 MangaAnime WebUI を手動起動します..."

# 仮想環境のアクティベート
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Python仮想環境をアクティベート"
else
    echo "❌ Python仮想環境が見つかりません"
    exit 1
fi

# WebUI起動
echo "🌐 WebUI起動中... (http://localhost:5000)"
python web_app.py
EOF

chmod +x "$PROJECT_DIR/start_webui_manual.sh"

echo -e "${GREEN}✅ 手動起動スクリプト作成完了: start_webui_manual.sh${NC}"
echo ""

echo -e "${GREEN}🎉 WebUI自動起動設定準備完了！${NC}"
echo ""
echo -e "${YELLOW}💡 次のステップ:${NC}"
echo "1. 上記のワンライナーコマンドを実行してsystemdサービスを設定"
echo "2. 再起動後にWebUIが自動で起動することを確認"
echo "3. 手動起動が必要な場合は ./start_webui_manual.sh を実行"
echo ""