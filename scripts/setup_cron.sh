#!/bin/bash
# cronスケジューラー設定スクリプト

echo "=== cron スケジューラー設定 ==="
echo ""

PROJECT_DIR="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
PYTHON_PATH="/usr/bin/python3"
LOG_DIR="$PROJECT_DIR/logs"

# ログディレクトリ作成
mkdir -p "$LOG_DIR"

# crontab エントリ
CRON_ENTRY="0 8 * * * cd $PROJECT_DIR && $PYTHON_PATH app/release_notifier.py >> $LOG_DIR/cron.log 2>&1"

echo "設定するcronエントリ:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$CRON_ENTRY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "実行タイミング: 毎朝8時"
echo "ログ出力先: $LOG_DIR/cron.log"
echo ""

# 既存のcrontab確認
echo "現在のcrontab:"
crontab -l 2>/dev/null || echo "  (設定なし)"
echo ""

# 確認
read -p "この設定を追加しますか？ (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # crontabに追加
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✅ cron設定完了"
    echo ""
    echo "確認:"
    crontab -l | grep "release_notifier"
else
    echo "キャンセルしました"
    echo ""
    echo "手動で設定する場合:"
    echo "  crontab -e"
    echo "  上記のエントリを追加"
fi
