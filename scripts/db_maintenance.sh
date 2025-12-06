#!/bin/bash
# データベースメンテナンススクリプト
# 定期実行推奨: crontab設定例
#   週次VACUUM: 0 3 * * 0 /path/to/db_maintenance.sh --vacuum
#   日次ANALYZE: 0 4 * * * /path/to/db_maintenance.sh --analyze
#   月次バックアップ: 0 2 1 * * /path/to/db_maintenance.sh --backup

set -e

# プロジェクトルートディレクトリ
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DB_PATH="$PROJECT_ROOT/db.sqlite3"
BACKUP_DIR="$PROJECT_ROOT/backups"
LOG_DIR="$PROJECT_ROOT/logs"

# ログファイル
LOG_FILE="$LOG_DIR/db_maintenance.log"

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# エラーハンドリング
error() {
    log "ERROR: $1"
    exit 1
}

# ディレクトリ作成
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

# データベースファイルチェック
if [ ! -f "$DB_PATH" ]; then
    error "データベースファイルが見つかりません: $DB_PATH"
fi

# 使用方法
usage() {
    cat << EOF
使用方法: $0 [OPTIONS]

OPTIONS:
    --vacuum        VACUUM（データベース最適化）を実行
    --analyze       ANALYZE（統計情報更新）を実行
    --backup        バックアップを作成
    --check         整合性チェックを実行
    --all           全メンテナンスを実行（推奨）
    --help, -h      このヘルプを表示

例:
    $0 --vacuum
    $0 --backup
    $0 --all

EOF
    exit 0
}

# VACUUM実行
run_vacuum() {
    log "VACUUM開始..."

    # データベースサイズ（VACUUM前）
    SIZE_BEFORE=$(du -h "$DB_PATH" | cut -f1)
    log "  VACUUM前のサイズ: $SIZE_BEFORE"

    # VACUUM実行
    sqlite3 "$DB_PATH" "VACUUM;" || error "VACUUM実行に失敗しました"

    # データベースサイズ（VACUUM後）
    SIZE_AFTER=$(du -h "$DB_PATH" | cut -f1)
    log "  VACUUM後のサイズ: $SIZE_AFTER"

    log "VACUUM完了"
}

# ANALYZE実行
run_analyze() {
    log "ANALYZE開始..."
    sqlite3 "$DB_PATH" "ANALYZE;" || error "ANALYZE実行に失敗しました"
    log "ANALYZE完了"
}

# バックアップ作成
run_backup() {
    log "バックアップ開始..."

    # タイムスタンプ付きバックアップファイル名
    TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3"
    DUMP_FILE="$BACKUP_DIR/db_dump_$TIMESTAMP.sql"

    # SQLite形式でバックアップ
    log "  ファイルコピー: $BACKUP_FILE"
    cp "$DB_PATH" "$BACKUP_FILE" || error "バックアップコピーに失敗しました"

    # SQLダンプ形式でもバックアップ
    log "  SQLダンプ: $DUMP_FILE"
    sqlite3 "$DB_PATH" .dump > "$DUMP_FILE" || error "SQLダンプに失敗しました"

    # ダンプを圧縮
    gzip "$DUMP_FILE"
    log "  圧縮完了: $DUMP_FILE.gz"

    # 古いバックアップを削除（30日以上前）
    log "  古いバックアップを削除中..."
    find "$BACKUP_DIR" -name "db_backup_*.sqlite3" -mtime +30 -delete
    find "$BACKUP_DIR" -name "db_dump_*.sql.gz" -mtime +30 -delete

    # バックアップファイル数を表示
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "db_backup_*.sqlite3" | wc -l)
    DUMP_COUNT=$(find "$BACKUP_DIR" -name "db_dump_*.sql.gz" | wc -l)
    log "  現在のバックアップ: SQLite形式 ${BACKUP_COUNT}件, ダンプ形式 ${DUMP_COUNT}件"

    log "バックアップ完了"
}

# 整合性チェック
run_check() {
    log "整合性チェック開始..."

    # 基本的な整合性チェック
    log "  PRAGMA integrity_check..."
    INTEGRITY=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;")
    if [ "$INTEGRITY" != "ok" ]; then
        error "整合性チェックに失敗しました: $INTEGRITY"
    fi
    log "    ✓ OK"

    # 外部キーチェック
    log "  PRAGMA foreign_key_check..."
    FK_CHECK=$(sqlite3 "$DB_PATH" "PRAGMA foreign_key_check;")
    if [ -n "$FK_CHECK" ]; then
        log "    ⚠ 外部キー制約違反が検出されました:"
        echo "$FK_CHECK" | tee -a "$LOG_FILE"
    else
        log "    ✓ OK"
    fi

    # クイックチェック
    log "  PRAGMA quick_check..."
    QUICK_CHECK=$(sqlite3 "$DB_PATH" "PRAGMA quick_check;")
    if [ "$QUICK_CHECK" != "ok" ]; then
        error "クイックチェックに失敗しました: $QUICK_CHECK"
    fi
    log "    ✓ OK"

    log "整合性チェック完了"
}

# 統計情報表示
show_stats() {
    log "データベース統計情報:"

    # ファイルサイズ
    SIZE=$(du -h "$DB_PATH" | cut -f1)
    log "  データベースサイズ: $SIZE"

    # テーブル別レコード数
    log "  テーブル別レコード数:"
    sqlite3 "$DB_PATH" "
        SELECT 'works' as table_name, COUNT(*) as count FROM works
        UNION ALL
        SELECT 'releases', COUNT(*) FROM releases;
    " | while read line; do
        log "    $line"
    done

    # インデックス数
    INDEX_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
    log "  インデックス数: $INDEX_COUNT"

    # WALモードチェック
    JOURNAL_MODE=$(sqlite3 "$DB_PATH" "PRAGMA journal_mode;")
    log "  ジャーナルモード: $JOURNAL_MODE"

    # 外部キー制約チェック
    FK_ENABLED=$(sqlite3 "$DB_PATH" "PRAGMA foreign_keys;")
    log "  外部キー制約: $([ "$FK_ENABLED" = "1" ] && echo "有効" || echo "無効")"
}

# 全メンテナンス実行
run_all() {
    log "========================================="
    log "全メンテナンス開始"
    log "========================================="

    run_backup
    echo ""
    run_check
    echo ""
    run_analyze
    echo ""
    run_vacuum
    echo ""
    show_stats

    log "========================================="
    log "全メンテナンス完了"
    log "========================================="
}

# メイン処理
main() {
    if [ $# -eq 0 ]; then
        usage
    fi

    case "$1" in
        --vacuum)
            run_vacuum
            ;;
        --analyze)
            run_analyze
            ;;
        --backup)
            run_backup
            ;;
        --check)
            run_check
            ;;
        --stats)
            show_stats
            ;;
        --all)
            run_all
            ;;
        --help|-h)
            usage
            ;;
        *)
            echo "エラー: 不明なオプション: $1"
            echo ""
            usage
            ;;
    esac
}

main "$@"
