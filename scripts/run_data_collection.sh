#!/bin/bash
# データ収集実行スクリプト
# 作成日: 2025-12-06

PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
cd "$PROJECT_ROOT"

echo "========================================="
echo "データ収集タスク実行開始"
echo "========================================="
echo ""

# 1. 現状確認
echo "[1/5] 現状確認中..."
echo "--- DBファイル確認 ---"
if [ -f "db.sqlite3" ]; then
    echo "✓ db.sqlite3 存在確認"
    sqlite3 db.sqlite3 "SELECT COUNT(*) as work_count FROM works;" 2>/dev/null && \
    sqlite3 db.sqlite3 "SELECT COUNT(*) as release_count FROM releases;" 2>/dev/null
else
    echo "✗ db.sqlite3 が見つかりません"
fi
echo ""

# 2. Pythonスクリプト存在確認
echo "[2/5] データ収集スクリプト確認中..."
echo "--- Pythonスクリプトリスト ---"
find . -name "*.py" -path "*/modules/*" -o -name "release_notifier.py" | grep -E "(release_notifier|anime_|manga_)" | sort
echo ""

# 3. config.json確認
echo "[3/5] 設定ファイル確認中..."
if [ -f "config.json" ]; then
    echo "✓ config.json 存在確認"
    echo "--- API設定状況 ---"
    grep -E "(anilist|rss|api)" config.json | head -10
else
    echo "✗ config.json が見つかりません"
fi
echo ""

# 4. データ収集実行
echo "[4/5] データ収集実行..."
if [ -f "app/release_notifier.py" ]; then
    echo "実行: python3 app/release_notifier.py --dry-run"
    python3 app/release_notifier.py --dry-run 2>&1 | tee /tmp/data_collection_log.txt

    if [ $? -ne 0 ]; then
        echo "⚠ dry-runオプションが無効な可能性があります。通常実行を試みます..."
        python3 app/release_notifier.py 2>&1 | tee /tmp/data_collection_log.txt
    fi
else
    echo "✗ app/release_notifier.py が見つかりません"
fi
echo ""

# 5. 収集後データ確認
echo "[5/5] 収集後データ確認..."
if [ -f "db.sqlite3" ]; then
    echo "--- 収集後データ件数 ---"
    sqlite3 db.sqlite3 "SELECT COUNT(*) as work_count FROM works;"
    sqlite3 db.sqlite3 "SELECT COUNT(*) as release_count FROM releases;"
    echo ""
    echo "--- 最新5件の作品 ---"
    sqlite3 db.sqlite3 "SELECT id, title, type FROM works ORDER BY created_at DESC LIMIT 5;"
    echo ""
    echo "--- 最新5件のリリース ---"
    sqlite3 db.sqlite3 "SELECT id, work_id, release_type, platform, release_date FROM releases ORDER BY created_at DESC LIMIT 5;"
fi
echo ""

echo "========================================="
echo "データ収集タスク完了"
echo "========================================="
echo "詳細ログ: /tmp/data_collection_log.txt"
