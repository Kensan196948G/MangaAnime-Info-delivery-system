#!/bin/bash

echo "🚀 自動修復システムをバックグラウンドで起動します"
echo "================================================"

# ログファイル名（タイムスタンプ付き）
LOG_FILE="repair-$(date +%Y%m%d-%H%M%S).log"

# バックグラウンド実行
nohup ./local-repair-system.sh > "$LOG_FILE" 2>&1 &
PID=$!

echo "✅ 起動完了"
echo "  プロセスID: $PID"
echo "  ログファイル: $LOG_FILE"
echo ""
echo "📋 便利なコマンド:"
echo "  ログ監視: tail -f $LOG_FILE"
echo "  プロセス確認: ps -p $PID"
echo "  停止: kill $PID"
echo ""
echo "🔍 現在の状態:"
ps -p $PID -o pid,cmd,stat,etime
