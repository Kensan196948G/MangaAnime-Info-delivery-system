#!/bin/bash
# 分散通知cron設定スクリプト
# 1日3回（朝・昼・夜）自動送信でGmailレート制限を回避

PROJECT_DIR="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"

echo "============================================================"
echo "🚀 分散通知cron設定"
echo "============================================================"
echo ""
echo "以下のcron設定を追加します:"
echo ""
echo "# MangaAnime分散通知（Gmailレート制限対策）"
echo "0 8 * * * cd $PROJECT_DIR && /usr/bin/python3 scripts/distributed_notify.py --session morning >> logs/cron/notify_morning.log 2>&1"
echo "0 12 * * * cd $PROJECT_DIR && /usr/bin/python3 scripts/distributed_notify.py --session noon >> logs/cron/notify_noon.log 2>&1"
echo "0 20 * * * cd $PROJECT_DIR && /usr/bin/python3 scripts/distributed_notify.py --session evening >> logs/cron/notify_evening.log 2>&1"
echo ""
echo "============================================================"
echo ""

read -p "この設定をcrontabに追加しますか？ (y/N): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "❌ キャンセルしました"
    exit 0
fi

# 現在のcrontabをバックアップ
BACKUP_FILE="/tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || true
echo "📝 バックアップ作成: $BACKUP_FILE"

# 新しいcron設定を追加
(
    crontab -l 2>/dev/null || true
    echo ""
    echo "# ============================================================================"
    echo "# MangaAnime分散通知（Gmailレート制限対策）"
    echo "# 1日3回（朝8時、昼12時、夜20時）× 67通 = 201通/日"
    echo "# 5日間で865件完全送信"
    echo "# ============================================================================"
    echo ""
    echo "# 朝セッション（8:00）"
    echo "0 8 * * * cd $PROJECT_DIR && /usr/bin/python3 scripts/distributed_notify.py --session morning >> logs/cron/notify_morning.log 2>&1"
    echo ""
    echo "# 昼セッション（12:00）"
    echo "0 12 * * * cd $PROJECT_DIR && /usr/bin/python3 scripts/distributed_notify.py --session noon >> logs/cron/notify_noon.log 2>&1"
    echo ""
    echo "# 夜セッション（20:00）"
    echo "0 20 * * * cd $PROJECT_DIR && /usr/bin/python3 scripts/distributed_notify.py --session evening >> logs/cron/notify_evening.log 2>&1"
) | crontab -

echo ""
echo "✅ cron設定を追加しました"
echo ""
echo "確認コマンド:"
echo "  crontab -l | grep -A 2 'MangaAnime分散通知'"
echo ""
echo "ログ確認:"
echo "  tail -f logs/cron/notify_morning.log"
echo "  tail -f logs/cron/notify_noon.log"
echo "  tail -f logs/cron/notify_evening.log"
echo ""
echo "============================================================"
