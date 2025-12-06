#!/bin/bash
# プロジェクト構造確認

cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

echo "=== ルートディレクトリ ==="
ls -la

echo -e "\n=== README確認 ==="
if [ -f "README.md" ]; then
    head -50 README.md
fi

echo -e "\n=== modules/ディレクトリ ==="
if [ -d "modules" ]; then
    ls -la modules/
fi

echo -e "\n=== backend/ディレクトリ ==="
if [ -d "backend" ]; then
    ls -la backend/
fi

echo -e "\n=== app/ディレクトリ ==="
if [ -d "app" ]; then
    ls -la app/
fi

echo -e "\n=== config.json存在確認 ==="
if [ -f "config.json" ]; then
    echo "config.json exists"
    # Google Calendar関連の設定を抽出
    grep -A 10 "calendar" config.json 2>/dev/null || echo "calendar設定なし"
fi

echo -e "\n=== credentials/token確認 ==="
find . -maxdepth 3 -name "credentials.json" -o -name "token.json" 2>/dev/null

echo -e "\n=== Pythonスクリプト確認 ==="
find . -maxdepth 2 -name "*.py" -type f 2>/dev/null

echo -e "\n=== Google Calendar APIインポート確認 ==="
grep -r "google.*calendar\|googleapiclient" --include="*.py" modules/ backend/ app/ 2>/dev/null | head -20
