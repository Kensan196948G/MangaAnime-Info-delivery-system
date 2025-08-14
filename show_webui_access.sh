#!/bin/bash

# WebUIアクセス情報表示スクリプト

# 色設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# IPアドレス取得
IP_ADDRESS=$(hostname -I | awk '{print $1}')

echo -e "${BLUE}🌐 MangaAnime WebUI アクセス情報${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}📍 ローカルアクセス:${NC}"
echo "   http://localhost:3030"
echo ""
echo -e "${GREEN}🌍 ネットワークアクセス (推奨):${NC}"
echo "   http://${IP_ADDRESS}:3030"
echo ""
echo -e "${GREEN}📱 主要ページ:${NC}"
echo "   📊 ダッシュボード: http://${IP_ADDRESS}:3030/dashboard"
echo "   📋 リリース一覧: http://${IP_ADDRESS}:3030/releases"
echo "   📅 カレンダー: http://${IP_ADDRESS}:3030/calendar"
echo "   ⚙️  設定: http://${IP_ADDRESS}:3030/config"
echo "   📝 ログ: http://${IP_ADDRESS}:3030/logs"
echo ""
echo -e "${YELLOW}💡 コマンド:${NC}"
echo "   WebUI起動: ./start_webui_manual.sh"
echo "   接続テスト: curl -I http://${IP_ADDRESS}:3030"
echo ""

# WebUIが起動しているかチェック
if curl -s -I http://localhost:3030 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ WebUIは現在起動中です${NC}"
else
    echo -e "${YELLOW}⚠️  WebUIは起動していません${NC}"
    echo "   起動方法: ./start_webui_manual.sh"
fi
echo ""