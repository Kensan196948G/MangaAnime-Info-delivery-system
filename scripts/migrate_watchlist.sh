#!/bin/bash
# ウォッチリスト機能マイグレーション実行スクリプト
# 作成日: 2025-12-07

set -e

echo "=========================================="
echo "ウォッチリスト機能マイグレーション"
echo "=========================================="
echo ""

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# データベースファイル確認
DB_FILE="db.sqlite3"

if [ ! -f "$DB_FILE" ]; then
    echo "エラー: データベースファイル ($DB_FILE) が見つかりません"
    exit 1
fi

echo "データベース: $DB_FILE"
echo ""

# バックアップ作成
BACKUP_FILE="${DB_FILE}.backup_$(date +%Y%m%d_%H%M%S)"
echo "バックアップ作成中: $BACKUP_FILE"
cp "$DB_FILE" "$BACKUP_FILE"
echo "✓ バックアップ完了"
echo ""

# マイグレーション実行
MIGRATION_FILE="migrations/008_watchlist.sql"

if [ ! -f "$MIGRATION_FILE" ]; then
    echo "エラー: マイグレーションファイル ($MIGRATION_FILE) が見つかりません"
    exit 1
fi

echo "マイグレーション実行中: $MIGRATION_FILE"
sqlite3 "$DB_FILE" < "$MIGRATION_FILE"
echo "✓ マイグレーション完了"
echo ""

# テーブル確認
echo "作成されたテーブル・ビューを確認中..."
sqlite3 "$DB_FILE" "SELECT name, type FROM sqlite_master WHERE name LIKE '%watchlist%' ORDER BY type, name;"
echo ""

# インデックス確認
echo "作成されたインデックスを確認中..."
sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%watchlist%';"
echo ""

# トリガー確認
echo "作成されたトリガーを確認中..."
sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE '%watchlist%';"
echo ""

echo "=========================================="
echo "マイグレーション完了"
echo "=========================================="
echo ""
echo "バックアップファイル: $BACKUP_FILE"
echo ""
echo "次のステップ:"
echo "1. アプリケーションサーバーを再起動してください"
echo "2. ウォッチリスト機能をテストしてください"
echo "   - /watchlist にアクセス"
echo "   - 作品をウォッチリストに追加"
echo "   - 通知設定を変更"
echo ""
