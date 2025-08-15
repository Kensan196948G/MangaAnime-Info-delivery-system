#!/bin/bash
# MangaAnime配信システム crontab設定スクリプト

echo "⏰ MangaAnime メール配信スケジュール設定"
echo "=========================================="
echo ""
echo "配信時間を選択してください："
echo "1) 毎日朝8時に配信"
echo "2) 毎日朝8時と夜20時の2回配信" 
echo "3) 朝7時、昼12時、夜18時の3回配信"
echo "4) 毎時間配信（テスト用）"
echo "5) カスタム設定"
echo ""
read -p "選択 (1-5): " choice

PROJECT_DIR="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
PYTHON_PATH="${PROJECT_DIR}/venv/bin/python"
SCRIPT_PATH="${PROJECT_DIR}/release_notifier.py"
LOG_DIR="${PROJECT_DIR}/logs"

# ログディレクトリ作成
mkdir -p ${LOG_DIR}

# 既存のMangaAnime関連のcron設定を削除
crontab -l 2>/dev/null | grep -v "MangaAnime" > /tmp/crontab_temp || true

# 選択に応じてcron設定を追加
case $choice in
    1)
        echo "# MangaAnime 毎日朝8時配信" >> /tmp/crontab_temp
        echo "0 8 * * * cd ${PROJECT_DIR} && ${PYTHON_PATH} ${SCRIPT_PATH} >> ${LOG_DIR}/mangaanime_\$(date +\%Y\%m\%d).log 2>&1" >> /tmp/crontab_temp
        echo "✅ 毎日朝8時に配信するよう設定しました"
        ;;
    2)
        echo "# MangaAnime 朝8時と夜20時の2回配信" >> /tmp/crontab_temp
        echo "0 8 * * * cd ${PROJECT_DIR} && ${PYTHON_PATH} ${SCRIPT_PATH} >> ${LOG_DIR}/mangaanime_morning_\$(date +\%Y\%m\%d).log 2>&1" >> /tmp/crontab_temp
        echo "0 20 * * * cd ${PROJECT_DIR} && ${PYTHON_PATH} ${SCRIPT_PATH} >> ${LOG_DIR}/mangaanime_evening_\$(date +\%Y\%m\%d).log 2>&1" >> /tmp/crontab_temp
        echo "✅ 毎日朝8時と夜20時に配信するよう設定しました"
        ;;
    3)
        echo "# MangaAnime 1日3回配信（7時、12時、18時）" >> /tmp/crontab_temp
        echo "0 7 * * * cd ${PROJECT_DIR} && ${PYTHON_PATH} ${SCRIPT_PATH} >> ${LOG_DIR}/mangaanime_morning_\$(date +\%Y\%m\%d).log 2>&1" >> /tmp/crontab_temp
        echo "0 12 * * * cd ${PROJECT_DIR} && ${PYTHON_PATH} ${SCRIPT_PATH} >> ${LOG_DIR}/mangaanime_noon_\$(date +\%Y\%m\%d).log 2>&1" >> /tmp/crontab_temp
        echo "0 18 * * * cd ${PROJECT_DIR} && ${PYTHON_PATH} ${SCRIPT_PATH} >> ${LOG_DIR}/mangaanime_evening_\$(date +\%Y\%m\%d).log 2>&1" >> /tmp/crontab_temp
        echo "✅ 朝7時、昼12時、夜18時に配信するよう設定しました"
        ;;
    4)
        echo "# MangaAnime 毎時間配信（テスト用）" >> /tmp/crontab_temp
        echo "0 * * * * cd ${PROJECT_DIR} && ${PYTHON_PATH} ${SCRIPT_PATH} >> ${LOG_DIR}/mangaanime_hourly_\$(date +\%Y\%m\%d_\%H).log 2>&1" >> /tmp/crontab_temp
        echo "✅ 毎時間配信するよう設定しました（テスト用）"
        ;;
    5)
        echo "カスタム設定を入力してください"
        echo "例: 毎日朝9時30分の場合 → 30 9 * * *"
        read -p "cron形式: " custom_cron
        echo "# MangaAnime カスタム配信" >> /tmp/crontab_temp
        echo "${custom_cron} cd ${PROJECT_DIR} && ${PYTHON_PATH} ${SCRIPT_PATH} >> ${LOG_DIR}/mangaanime_custom_\$(date +\%Y\%m\%d).log 2>&1" >> /tmp/crontab_temp
        echo "✅ カスタム設定を適用しました: ${custom_cron}"
        ;;
    *)
        echo "❌ 無効な選択です"
        exit 1
        ;;
esac

# ログクリーンアップ設定を追加（30日以上前のログを削除）
echo "# MangaAnime ログクリーンアップ（日曜深夜2時）" >> /tmp/crontab_temp
echo "0 2 * * 0 find ${LOG_DIR} -name 'mangaanime_*.log' -mtime +30 -delete" >> /tmp/crontab_temp

# crontabを更新
crontab /tmp/crontab_temp
rm /tmp/crontab_temp

echo ""
echo "📋 現在のcrontab設定:"
echo "------------------------"
crontab -l | grep MangaAnime
echo "------------------------"
echo ""
echo "✅ 設定完了！"
echo ""
echo "💡 ヒント:"
echo "  - 設定を確認: crontab -l"
echo "  - 設定を編集: crontab -e"
echo "  - ログ確認: tail -f ${LOG_DIR}/mangaanime_*.log"
echo "  - 手動実行: python ${SCRIPT_PATH}"