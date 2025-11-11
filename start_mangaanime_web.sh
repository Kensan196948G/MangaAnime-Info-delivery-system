#!/bin/bash

# MangaAnime Web UI 起動スクリプト
# このスクリプトは systemd から呼び出されます

cd /media/kensan/LinuxHDD/MangaAnime-Info-delivery-system

# 仮想環境の有効化
source venv/bin/activate

# ログディレクトリの作成
mkdir -p logs

# Flask アプリケーションの起動
echo "$(date): Starting MangaAnime Web UI..." >> logs/startup.log
python web_app.py >> logs/webapp.log 2>&1