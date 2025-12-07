#!/bin/bash

# Google Calendar連携機能セットアップスクリプト

set -e

PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Google Calendar連携機能セットアップ"
echo "=========================================="

# 1. 状態確認
echo ""
echo "[1] 現在の状態を確認中..."
python3 check_calendar_status.py

# 2. config.jsonの calendar.enabled を true に設定
echo ""
echo "[2] config.json の calendar.enabled を true に設定中..."

if [ -f "config.json" ]; then
    # Pythonで安全にJSONを編集
    python3 - <<'EOF'
import json

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

if 'calendar' not in config:
    config['calendar'] = {}

config['calendar']['enabled'] = True
config['calendar']['calendar_id'] = config['calendar'].get('calendar_id', 'primary')
config['calendar']['event_color_anime'] = config['calendar'].get('event_color_anime', '9')
config['calendar']['event_color_manga'] = config['calendar'].get('event_color_manga', '10')

with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("✓ config.json を更新しました")
EOF
else
    echo "✗ config.json が見つかりません"
    exit 1
fi

# 3. 必要なPythonパッケージを確認
echo ""
echo "[3] 必要なパッケージを確認中..."

PACKAGES=(
    "google-auth"
    "google-auth-oauthlib"
    "google-auth-httplib2"
    "google-api-python-client"
)

for package in "${PACKAGES[@]}"; do
    if python3 -c "import ${package//-/_}" 2>/dev/null; then
        echo "  ✓ $package はインストール済み"
    else
        echo "  ✗ $package が見つかりません"
        echo "    インストールコマンド: pip3 install $package"
    fi
done

# 4. credentials.jsonの確認
echo ""
echo "[4] credentials.json の確認..."

if [ -f "credentials.json" ]; then
    echo "  ✓ credentials.json が存在します"
else
    echo "  ✗ credentials.json が見つかりません"
    echo ""
    echo "以下の手順で取得してください:"
    echo "1. Google Cloud Console にアクセス"
    echo "   https://console.cloud.google.com/apis/credentials"
    echo "2. 新しいプロジェクトを作成（または既存のプロジェクトを選択）"
    echo "3. 'OAuth 2.0 クライアント ID' を作成"
    echo "4. アプリケーションの種類: 'デスクトップアプリ'"
    echo "5. ダウンロードしたJSONファイルを credentials.json として保存"
    echo "6. このファイルをプロジェクトルートに配置"
fi

# 5. カレンダーモジュールの確認
echo ""
echo "[5] カレンダーモジュールの確認..."

if [ -f "modules/calendar_integration.py" ]; then
    echo "  ✓ modules/calendar_integration.py が存在します"

    # 簡易的な関数チェック
    if grep -q "def sync_releases_to_calendar" modules/calendar_integration.py; then
        echo "  ✓ sync_releases_to_calendar 関数あり"
    fi

    if grep -q "def create_calendar_event" modules/calendar_integration.py; then
        echo "  ✓ create_calendar_event 関数あり"
    fi

    if grep -q "def get_calendar_service" modules/calendar_integration.py; then
        echo "  ✓ get_calendar_service 関数あり"
    fi
else
    echo "  ✗ modules/calendar_integration.py が見つかりません"
    echo "  カレンダーモジュールを作成します..."

    # modulesディレクトリの作成
    mkdir -p modules

    # カレンダーモジュールの雛形を作成（別途詳細実装が必要）
    echo "  → modules/calendar_integration.py を作成してください"
fi

# 6. まとめ
echo ""
echo "=========================================="
echo "セットアップ完了"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "1. credentials.json をプロジェクトルートに配置（未配置の場合）"
echo "2. 必要なパッケージをインストール:"
echo "   pip3 install google-auth google-auth-oauthlib google-api-python-client"
echo "3. 初回認証の実行:"
echo "   python3 modules/calendar_integration.py"
echo "4. 動作確認:"
echo "   python3 -c 'from modules.calendar_integration import list_upcoming_events; list_upcoming_events()'"
echo ""
