#!/bin/bash
# ファイル読み取り用スクリプト
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

echo "=== app/web_app.py ==="
head -100 app/web_app.py

echo -e "\n=== app/routes/auth.py ==="
cat app/routes/auth.py

echo -e "\n=== app/routes/__init__.py ==="
cat app/routes/__init__.py

echo -e "\n=== templates/base.html (header部分) ==="
head -80 templates/base.html

echo -e "\n=== ログイン必須候補のルート検索 ==="
grep -n "def.*settings\|def.*delete\|def.*update\|def.*config" app/web_app.py | head -20
