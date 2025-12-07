#!/bin/bash

# Google Calendar連携機能の最終セットアップスクリプト

set -e

PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Google Calendar連携 - 最終セットアップ"
echo "=========================================="

# 実行権限を付与
echo ""
echo "[1] スクリプトに実行権限を付与..."

chmod +x check_calendar_status.py 2>/dev/null || true
chmod +x enable_calendar.py 2>/dev/null || true
chmod +x test_calendar_dryrun.py 2>/dev/null || true
chmod +x run_calendar_integration_test.sh 2>/dev/null || true
chmod +x setup_calendar.sh 2>/dev/null || true
chmod +x finalize_calendar_setup.sh 2>/dev/null || true

if [ -f "modules/calendar_integration.py" ]; then
    chmod +x modules/calendar_integration.py 2>/dev/null || true
fi

echo "  ✓ 実行権限を付与しました"

# modulesディレクトリの確認
echo ""
echo "[2] modulesディレクトリの確認..."

if [ ! -d "modules" ]; then
    echo "  → modulesディレクトリを作成します"
    mkdir -p modules
    touch modules/__init__.py
fi

echo "  ✓ modulesディレクトリ: OK"

# docsディレクトリの確認
echo ""
echo "[3] docsディレクトリの確認..."

if [ ! -d "docs" ]; then
    echo "  → docsディレクトリを作成します"
    mkdir -p docs
fi

echo "  ✓ docsディレクトリ: OK"

# .gitignoreの更新
echo ""
echo "[4] .gitignoreの更新..."

if [ -f ".gitignore" ]; then
    if ! grep -q "credentials.json" .gitignore; then
        echo "" >> .gitignore
        echo "# Google Calendar認証情報" >> .gitignore
        echo "credentials.json" >> .gitignore
        echo "token.json" >> .gitignore
        echo "  ✓ .gitignoreに認証情報を追加しました"
    else
        echo "  ✓ .gitignoreは既に設定済みです"
    fi
else
    # .gitignoreが存在しない場合は作成
    cat > .gitignore <<'EOF'
# Google Calendar認証情報
credentials.json
token.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# ログ
*.log
logs/

# データベース
*.db
*.sqlite
*.sqlite3

# 環境
.env
.venv
env/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
EOF
    echo "  ✓ .gitignoreを作成しました"
fi

# 統合テストの実行
echo ""
echo "[5] 統合テストを実行..."
echo ""

bash run_calendar_integration_test.sh

# 最終メッセージ
echo ""
echo "=========================================="
echo "セットアップ完了"
echo "=========================================="
echo ""
echo "作成されたファイル:"
echo "  - modules/calendar_integration.py (カレンダー統合モジュール)"
echo "  - enable_calendar.py (設定有効化)"
echo "  - check_calendar_status.py (状態確認)"
echo "  - test_calendar_dryrun.py (Dry-runテスト)"
echo "  - docs/CALENDAR_SETUP_GUIDE.md (詳細ガイド)"
echo "  - CALENDAR_INTEGRATION_REPORT.md (実装レポート)"
echo "  - QUICKSTART_CALENDAR.md (クイックスタート)"
echo ""
echo "次のステップ:"
echo "  1. QUICKSTART_CALENDAR.md を参照"
echo "  2. credentials.json を取得・配置"
echo "  3. 初回認証を実行"
echo ""
echo "詳細情報:"
echo "  - クイックスタート: cat QUICKSTART_CALENDAR.md"
echo "  - 詳細ガイド: cat docs/CALENDAR_SETUP_GUIDE.md"
echo "  - 実装レポート: cat CALENDAR_INTEGRATION_REPORT.md"
echo ""
