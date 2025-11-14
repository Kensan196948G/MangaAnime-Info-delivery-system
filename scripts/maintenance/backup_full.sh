#!/bin/bash

# MangaAnime情報配信システム フルバックアップスクリプト
# 30分おき自動実行用

# 設定
SOURCE_DIR="/media/kensan/LinuxHDD/MangaAnime-Info-delivery-system"
BACKUP_BASE_DIR="/media/kensan/LinuxHDD/MangaAnime-Info-delivery-system-BackUp"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
BACKUP_DIR="${BACKUP_BASE_DIR}/MangaAnime-Info-delivery-system-${TIMESTAMP}"
LOG_FILE="${SOURCE_DIR}/logs/backup.log"

# ログ出力関数
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# バックアップ開始
log_message "🔄 フルバックアップ開始: $BACKUP_DIR"

# バックアップディレクトリ作成
if ! mkdir -p "$BACKUP_DIR"; then
    log_message "❌ バックアップディレクトリ作成失敗: $BACKUP_DIR"
    exit 1
fi

# プロジェクト全体をバックアップ（.git と venv を除外）
log_message "📁 プロジェクトファイルのコピー開始"
if rsync -av --exclude='.git' --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' --exclude='logs/backup.log' "$SOURCE_DIR/" "$BACKUP_DIR/"; then
    log_message "✅ プロジェクトファイルのコピー完了"
else
    log_message "❌ プロジェクトファイルのコピー失敗"
    exit 1
fi

# バックアップサイズ計算
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log_message "📊 バックアップサイズ: $BACKUP_SIZE"

# 古いバックアップの削除（7日以上前のものを削除）
log_message "🗑️ 古いバックアップの削除開始（7日以上前）"
find "$BACKUP_BASE_DIR" -name "MangaAnime-Info-delivery-system-*" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null
DELETED_COUNT=$(find "$BACKUP_BASE_DIR" -name "MangaAnime-Info-delivery-system-*" -type d -mtime +7 2>/dev/null | wc -l)
log_message "🗑️ 削除した古いバックアップ: ${DELETED_COUNT}個"

# バックアップ一覧確認
TOTAL_BACKUPS=$(find "$BACKUP_BASE_DIR" -name "MangaAnime-Info-delivery-system-*" -type d | wc -l)
BACKUP_BASE_SIZE=$(du -sh "$BACKUP_BASE_DIR" | cut -f1)

log_message "📋 バックアップ統計:"
log_message "   - 今回作成: $BACKUP_DIR"
log_message "   - バックアップ総数: ${TOTAL_BACKUPS}個"
log_message "   - バックアップ領域使用量: $BACKUP_BASE_SIZE"

log_message "✅ フルバックアップ完了"

# バックアップの整合性チェック
if [ -f "$BACKUP_DIR/db.sqlite3" ] && [ -f "$BACKUP_DIR/config.json" ]; then
    log_message "✅ 重要ファイルの存在確認OK"
else
    log_message "⚠️ 重要ファイルの存在確認NG - バックアップを確認してください"
fi

exit 0