#!/bin/bash
# Google API認証の初期セットアップスクリプト

set -e  # エラーが発生したら終了

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# プロジェクトルートの検出
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Google API 認証セットアップスクリプト${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "プロジェクトルート: $PROJECT_ROOT"
echo ""

# Step 1: credentials.json の確認
echo -e "${YELLOW}[Step 1/5]${NC} credentials.json の確認"
if [ -f "$PROJECT_ROOT/credentials.json" ]; then
    echo -e "${GREEN}✅ credentials.json が見つかりました${NC}"
else
    echo -e "${RED}❌ credentials.json が見つかりません${NC}"
    echo ""
    echo "以下の手順で取得してください:"
    echo "1. https://console.cloud.google.com/ にアクセス"
    echo "2. プロジェクトを作成"
    echo "3. Google Calendar API と Gmail API を有効化"
    echo "4. OAuth 2.0 クライアントID（デスクトップアプリ）を作成"
    echo "5. credentials.json をダウンロード"
    echo ""
    echo "詳細手順: $PROJECT_ROOT/docs/GOOGLE_API_SETUP.md"
    echo ""

    # サンプルファイルの確認
    if [ -f "$PROJECT_ROOT/credentials.json.sample" ]; then
        echo -e "${BLUE}参考: credentials.json.sample が利用可能です${NC}"
        echo "cp credentials.json.sample credentials.json"
        echo "（編集してあなたのクライアントIDとシークレットを入力してください）"
    fi

    exit 1
fi

# Step 2: Python環境の確認
echo ""
echo -e "${YELLOW}[Step 2/5]${NC} Python環境の確認"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python3が見つかりました: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python3が見つかりません${NC}"
    echo "Python 3.8以上をインストールしてください"
    exit 1
fi

# Step 3: 必要なパッケージのインストール
echo ""
echo -e "${YELLOW}[Step 3/5]${NC} 必要なパッケージのインストール"

REQUIRED_PACKAGES=(
    "google-auth>=2.23.0"
    "google-auth-oauthlib>=1.1.0"
    "google-auth-httplib2>=0.1.1"
    "google-api-python-client>=2.100.0"
)

echo "以下のパッケージをインストールします:"
for package in "${REQUIRED_PACKAGES[@]}"; do
    echo "  - $package"
done

read -p "インストールを続行しますか? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install --upgrade "${REQUIRED_PACKAGES[@]}"
    echo -e "${GREEN}✅ パッケージのインストール完了${NC}"
else
    echo -e "${YELLOW}⚠️  パッケージのインストールをスキップしました${NC}"
    echo "手動でインストールする場合:"
    echo "  pip install -r requirements.txt"
fi

# Step 4: .gitignoreの確認
echo ""
echo -e "${YELLOW}[Step 4/5]${NC} .gitignore の確認"

GITIGNORE_PATH="$PROJECT_ROOT/.gitignore"
REQUIRED_ENTRIES=(
    "credentials.json"
    "token.json"
    "token.pickle"
)

if [ -f "$GITIGNORE_PATH" ]; then
    MISSING_ENTRIES=()
    for entry in "${REQUIRED_ENTRIES[@]}"; do
        if ! grep -q "^$entry$" "$GITIGNORE_PATH"; then
            MISSING_ENTRIES+=("$entry")
        fi
    done

    if [ ${#MISSING_ENTRIES[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ .gitignore に必要なエントリがすべて含まれています${NC}"
    else
        echo -e "${YELLOW}⚠️  .gitignore に以下のエントリが不足しています:${NC}"
        for entry in "${MISSING_ENTRIES[@]}"; do
            echo "  - $entry"
        done
        echo ""
        read -p ".gitignore に追加しますか? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "" >> "$GITIGNORE_PATH"
            echo "# Google API認証情報（追加: $(date +%Y-%m-%d)）" >> "$GITIGNORE_PATH"
            for entry in "${MISSING_ENTRIES[@]}"; do
                echo "$entry" >> "$GITIGNORE_PATH"
            done
            echo -e "${GREEN}✅ .gitignore を更新しました${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  .gitignore が見つかりません（作成を推奨）${NC}"
fi

# Step 5: 初回認証テスト
echo ""
echo -e "${YELLOW}[Step 5/5]${NC} 初回認証テスト"
echo ""
echo "これから認証テストを実行します。"
echo "ブラウザが開いてGoogle認証画面が表示されます。"
echo ""
read -p "認証テストを実行しますか? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$PROJECT_ROOT"

    # テストスクリプトの存在確認
    if [ -f "$PROJECT_ROOT/scripts/test_google_apis.py" ]; then
        echo ""
        echo -e "${BLUE}認証テストを開始します...${NC}"
        echo ""

        if python3 "$PROJECT_ROOT/scripts/test_google_apis.py"; then
            echo ""
            echo -e "${GREEN}🎉 認証テスト成功！${NC}"
            echo -e "${GREEN}セットアップが完了しました${NC}"
        else
            echo ""
            echo -e "${RED}❌ 認証テストに失敗しました${NC}"
            echo "詳細は上記のエラーメッセージを確認してください"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️  テストスクリプトが見つかりません${NC}"
        echo "手動で認証を実行してください:"
        echo "  python3 modules/auth_helper.py"
    fi
else
    echo -e "${YELLOW}⚠️  認証テストをスキップしました${NC}"
    echo ""
    echo "後で手動で実行する場合:"
    echo "  cd $PROJECT_ROOT"
    echo "  python3 scripts/test_google_apis.py"
fi

# 完了メッセージ
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}セットアップスクリプト完了${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "次のステップ:"
echo "1. システムの動作確認"
echo "   python3 scripts/test_google_apis.py"
echo ""
echo "2. ドキュメントの確認"
echo "   - 完全ガイド: docs/GOOGLE_API_SETUP.md"
echo "   - チェックリスト: docs/CREDENTIALS_SETUP_CHECKLIST.md"
echo ""
echo "3. システムの実行"
echo "   python3 release_notifier.py"
echo ""
