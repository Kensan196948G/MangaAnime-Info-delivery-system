#!/bin/bash
# MangaAnime Info Delivery System - Cron Setup Script

echo "================================================"
echo "MangaAnime Info Delivery System - Cron Setup"
echo "================================================"

# プロジェクトディレクトリの取得
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$(which python3)"

# cronジョブ設定
CRON_SCHEDULE="0 8 * * *"  # 毎朝8:00
CRON_COMMAND="${PYTHON_PATH} ${PROJECT_DIR}/release_notifier.py --config ${PROJECT_DIR}/config.json"

echo "Project Directory: ${PROJECT_DIR}"
echo "Python Path: ${PYTHON_PATH}"
echo "Schedule: ${CRON_SCHEDULE} (Daily at 08:00)"
echo ""

# 既存のcronジョブをチェック
echo "Checking existing cron jobs..."
EXISTING_JOB=$(crontab -l 2>/dev/null | grep "release_notifier.py")

if [ ! -z "$EXISTING_JOB" ]; then
    echo "⚠️  Warning: Existing cron job found:"
    echo "   $EXISTING_JOB"
    echo ""
    read -p "Do you want to replace it? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
    
    # 既存のジョブを削除
    (crontab -l 2>/dev/null | grep -v "release_notifier.py") | crontab -
fi

# 新しいcronジョブを追加
echo "Adding new cron job..."
(crontab -l 2>/dev/null; echo "${CRON_SCHEDULE} ${CRON_COMMAND} >> ${PROJECT_DIR}/logs/cron.log 2>&1") | crontab -

# 確認
echo ""
echo "✅ Cron job added successfully!"
echo ""
echo "Current crontab:"
echo "----------------"
crontab -l | grep "release_notifier.py"
echo ""

# ログディレクトリの作成
mkdir -p "${PROJECT_DIR}/logs"
touch "${PROJECT_DIR}/logs/cron.log"

echo "📝 Log file: ${PROJECT_DIR}/logs/cron.log"
echo ""
echo "================================================"
echo "Setup complete!"
echo ""
echo "The system will run automatically every day at 08:00."
echo "To run manually: python3 release_notifier.py"
echo "To check logs: tail -f logs/cron.log"
echo "================================================"