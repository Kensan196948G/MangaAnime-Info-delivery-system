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

# 現在のIPアドレス取得
IP_ADDRESS=$(hostname -I | awk '{print $1}')

# WebUI起動
echo "🌐 WebUI起動中..."
echo "   📍 ローカルアクセス: http://localhost:3030"
echo "   🌍 ネットワークアクセス: http://${IP_ADDRESS}:3030"
echo "   📱 管理ダッシュボード: http://${IP_ADDRESS}:3030/dashboard"
echo ""
python web_app.py
