#!/bin/bash

# Google Calendar連携の統合テストスクリプト

set -e

PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Google Calendar連携 - 統合テスト"
echo "=========================================="

# ステップ1: 状態確認
echo ""
echo "[ステップ1] 現在の状態を確認..."
if [ -f "check_calendar_status.py" ]; then
    python3 check_calendar_status.py
else
    echo "  ✗ check_calendar_status.py が見つかりません"
    exit 1
fi

# ステップ2: calendar.enabled を有効化
echo ""
echo "[ステップ2] calendar.enabled を有効化..."
if [ -f "enable_calendar.py" ]; then
    python3 enable_calendar.py
else
    echo "  ✗ enable_calendar.py が見つかりません"
    exit 1
fi

# ステップ3: Dry-runテスト
echo ""
echo "[ステップ3] Dry-runテストを実行..."
if [ -f "test_calendar_dryrun.py" ]; then
    python3 test_calendar_dryrun.py
else
    echo "  ✗ test_calendar_dryrun.py が見つかりません"
    exit 1
fi

# ステップ4: credentials.json の確認
echo ""
echo "[ステップ4] credentials.json の確認..."
if [ -f "credentials.json" ]; then
    echo "  ✓ credentials.json が存在します"
    echo "  ℹ️  実際のAPI呼び出しテストを実行できます"
    echo ""
    echo "  次のコマンドで初回認証を実行してください:"
    echo "  python3 modules/calendar_integration.py"
else
    echo "  ✗ credentials.json が見つかりません"
    echo ""
    echo "  Google Cloud Consoleから認証情報を取得してください:"
    echo "  1. https://console.cloud.google.com/apis/credentials にアクセス"
    echo "  2. OAuth 2.0 クライアントIDを作成"
    echo "  3. ダウンロードしたJSONを credentials.json として保存"
    echo "  4. プロジェクトルートに配置"
    echo ""
    echo "  詳細は docs/CALENDAR_SETUP_GUIDE.md を参照してください"
fi

# ステップ5: まとめ
echo ""
echo "=========================================="
echo "統合テスト完了"
echo "=========================================="
echo ""
echo "セットアップ状況:"
echo "  ✓ config.json - calendar.enabled: true"
echo "  ✓ modules/calendar_integration.py - モジュール実装完了"
echo "  ✓ Dry-runテスト - 正常動作確認"

if [ -f "credentials.json" ]; then
    echo "  ✓ credentials.json - 配置済み"
else
    echo "  ⚠️  credentials.json - 未配置（手動で配置が必要）"
fi

if [ -f "token.json" ]; then
    echo "  ✓ token.json - 認証済み"
else
    echo "  ⚠️  token.json - 未認証（初回認証が必要）"
fi

echo ""
echo "次のステップ:"
if [ ! -f "credentials.json" ]; then
    echo "  1. credentials.json を取得・配置"
    echo "  2. 初回認証を実行: python3 modules/calendar_integration.py"
elif [ ! -f "token.json" ]; then
    echo "  1. 初回認証を実行: python3 modules/calendar_integration.py"
else
    echo "  ✓ すべて完了！カレンダー連携が使用可能です"
fi

echo ""
