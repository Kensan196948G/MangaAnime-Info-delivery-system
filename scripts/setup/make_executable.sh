#!/bin/bash
# 実行権限付与スクリプト

cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

echo "実行権限を付与しています..."

chmod +x setup_google_calendar.sh
chmod +x test_calendar_dry_run.py
chmod +x modules/calendar_template.py

echo "完了！"
echo ""
echo "以下のファイルに実行権限を付与しました:"
echo "  - setup_google_calendar.sh"
echo "  - test_calendar_dry_run.py"
echo "  - modules/calendar_template.py"
