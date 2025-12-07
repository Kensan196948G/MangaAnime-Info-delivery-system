#!/bin/bash
################################################################################
# Google Calendar連携 セットアップスクリプト
#
# このスクリプトは、Googleカレンダー連携機能のセットアップを支援します。
################################################################################

set -e  # エラー時に停止

PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
cd "$PROJECT_ROOT"

echo "================================================================================"
echo "  Google Calendar連携 セットアップ"
echo "================================================================================"

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ステップ1: 環境確認
echo -e "\n${BLUE}[ステップ1] 環境確認${NC}"
echo "--------------------------------------------------------------------------------"

# Pythonバージョン確認
echo -n "Pythonバージョン: "
python3 --version

# 必要なパッケージ確認
echo -e "\n必要なPythonパッケージ確認:"

PACKAGES=(
    "google-auth"
    "google-auth-oauthlib"
    "google-auth-httplib2"
    "google-api-python-client"
)

MISSING_PACKAGES=()

for package in "${PACKAGES[@]}"; do
    if python3 -c "import ${package//-/_}" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $package"
    else
        echo -e "  ${RED}✗${NC} $package (未インストール)"
        MISSING_PACKAGES+=("$package")
    fi
done

# パッケージインストール
if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo -e "\n${YELLOW}必要なパッケージをインストールします...${NC}"
    pip3 install "${MISSING_PACKAGES[@]}"
    echo -e "${GREEN}✓ インストール完了${NC}"
else
    echo -e "\n${GREEN}✓ 全ての必要パッケージがインストール済みです${NC}"
fi

# ステップ2: 認証ファイル確認
echo -e "\n${BLUE}[ステップ2] 認証ファイル確認${NC}"
echo "--------------------------------------------------------------------------------"

if [ -f "credentials.json" ]; then
    echo -e "${GREEN}✓ credentials.json が見つかりました${NC}"
else
    echo -e "${RED}✗ credentials.json が見つかりません${NC}"
    echo ""
    echo "Google Cloud Consoleから credentials.json を取得してください:"
    echo "  1. https://console.cloud.google.com/ にアクセス"
    echo "  2. プロジェクトを作成または選択"
    echo "  3. 'APIとサービス' → 'ライブラリ' → 'Google Calendar API' を有効化"
    echo "  4. 'APIとサービス' → '認証情報' → 'OAuth 2.0 クライアントID' を作成"
    echo "  5. アプリケーションの種類: 'デスクトップアプリ'"
    echo "  6. credentials.json をダウンロード"
    echo "  7. ダウンロードしたファイルを $PROJECT_ROOT/ に配置"
    echo ""
    read -p "credentials.json を配置しましたか? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}セットアップを中断します${NC}"
        exit 1
    fi

    if [ ! -f "credentials.json" ]; then
        echo -e "${RED}✗ credentials.json が見つかりません。配置後に再実行してください。${NC}"
        exit 1
    fi
fi

# パーミッション設定
echo -e "\ncredentials.json のパーミッションを設定..."
chmod 600 credentials.json
echo -e "${GREEN}✓ パーミッション設定完了 (600)${NC}"

if [ -f "token.json" ]; then
    echo -e "${GREEN}✓ token.json が見つかりました（既に認証済み）${NC}"
else
    echo -e "${YELLOW}! token.json が見つかりません（初回認証が必要）${NC}"
fi

# ステップ3: config.json確認
echo -e "\n${BLUE}[ステップ3] config.json 確認${NC}"
echo "--------------------------------------------------------------------------------"

if [ -f "config.json" ]; then
    echo -e "${GREEN}✓ config.json が見つかりました${NC}"

    # Google Calendar設定確認
    if grep -q '"calendar"' config.json; then
        echo -e "${GREEN}✓ Google Calendar設定が存在します${NC}"
    else
        echo -e "${YELLOW}! Google Calendar設定が見つかりません${NC}"
        echo "config.jsonに以下の設定を追加することを推奨します:"
        echo ""
        cat <<'EOF'
{
  "google": {
    "calendar": {
      "enabled": true,
      "calendar_id": "primary",
      "timezone": "Asia/Tokyo",
      "event_duration_minutes": 30,
      "reminder_minutes": [1440, 60],
      "colors": {
        "anime": "9",
        "manga": "10"
      }
    }
  }
}
EOF
        echo ""
    fi
else
    echo -e "${YELLOW}! config.json が見つかりません${NC}"
    echo "デフォルト設定で動作します"
fi

# ステップ4: modules/calendar.py確認
echo -e "\n${BLUE}[ステップ4] カレンダーモジュール確認${NC}"
echo "--------------------------------------------------------------------------------"

if [ -d "modules" ]; then
    if [ -f "modules/calendar.py" ]; then
        echo -e "${GREEN}✓ modules/calendar.py が見つかりました${NC}"
    else
        echo -e "${YELLOW}! modules/calendar.py が見つかりません${NC}"

        if [ -f "modules/calendar_template.py" ]; then
            echo -e "${BLUE}calendar_template.py をコピーしますか?${NC}"
            read -p "コピーする (y/N): " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                cp modules/calendar_template.py modules/calendar.py
                echo -e "${GREEN}✓ modules/calendar.py を作成しました${NC}"
            fi
        fi
    fi
else
    echo -e "${RED}✗ modules/ ディレクトリが見つかりません${NC}"
fi

# ステップ5: 認証テスト
echo -e "\n${BLUE}[ステップ5] 認証テスト実行${NC}"
echo "--------------------------------------------------------------------------------"

if [ -f "modules/calendar.py" ]; then
    echo "認証テストを実行しますか?"
    echo "（初回の場合、ブラウザが開いてGoogleアカウントでのログインが求められます）"
    read -p "実行する (y/N): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "\n${YELLOW}認証テスト実行中...${NC}\n"
        python3 modules/calendar.py --authenticate

        if [ -f "token.json" ]; then
            echo -e "\n${GREEN}✓ 認証成功！token.json が生成されました${NC}"
            chmod 600 token.json
        else
            echo -e "\n${RED}✗ 認証に失敗しました${NC}"
        fi
    fi
else
    echo -e "${YELLOW}modules/calendar.py が存在しないため、認証テストをスキップします${NC}"
fi

# セットアップ完了
echo ""
echo "================================================================================"
echo -e "${GREEN}  セットアップ完了${NC}"
echo "================================================================================"

echo -e "\n次のステップ:"
echo "  1. Dry-runテストを実行:"
echo "     python3 test_calendar_dry_run.py"
echo ""
echo "  2. テストイベントを作成:"
echo "     python3 modules/calendar.py --create-test-event"
echo ""
echo "  3. 調査レポートを確認:"
echo "     cat CALENDAR_INVESTIGATION_REPORT.md"
echo ""

# 状態サマリー
echo "現在の状態:"
[ -f "credentials.json" ] && echo -e "  ${GREEN}✓${NC} credentials.json" || echo -e "  ${RED}✗${NC} credentials.json"
[ -f "token.json" ] && echo -e "  ${GREEN}✓${NC} token.json" || echo -e "  ${YELLOW}!${NC} token.json (要認証)"
[ -f "config.json" ] && echo -e "  ${GREEN}✓${NC} config.json" || echo -e "  ${YELLOW}!${NC} config.json"
[ -f "modules/calendar.py" ] && echo -e "  ${GREEN}✓${NC} modules/calendar.py" || echo -e "  ${RED}✗${NC} modules/calendar.py"

echo ""
echo "================================================================================"
