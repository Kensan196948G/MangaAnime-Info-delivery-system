#!/bin/bash

# スキーマ分析スクリプト
DB_PATH="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/data/db.sqlite3"

echo "===== SQLiteスキーマ分析 ====="
echo

echo "1. calendar_events テーブルのスキーマ:"
sqlite3 "$DB_PATH" ".schema calendar_events"
echo

echo "2. releases テーブルのスキーマ:"
sqlite3 "$DB_PATH" ".schema releases"
echo

echo "3. calendar_events テーブルの既存データサンプル:"
sqlite3 "$DB_PATH" "SELECT COUNT(*) as total_records FROM calendar_events LIMIT 5;" 2>/dev/null || echo "テーブルが存在しない可能性があります"
echo

echo "4. releases テーブルの既存データサンプル:"
sqlite3 "$DB_PATH" "SELECT COUNT(*) as total_records FROM releases;" 2>/dev/null || echo "テーブルが存在しない可能性があります"
echo

echo "5. 全テーブルの一覧:"
sqlite3 "$DB_PATH" ".tables"
echo

echo "6. 全スキーマ定義:"
sqlite3 "$DB_PATH" ".schema"
