#!/bin/bash
# ユーザーテーブルマイグレーション実行スクリプト
# 使用方法: bash scripts/run_migration.sh [migrate|verify|rollback]

set -e  # エラー時に停止

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  ユーザーDBマイグレーションスクリプト${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Python仮想環境の確認
if [ -d "venv" ]; then
    echo -e "${GREEN}仮想環境を有効化中...${NC}"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo -e "${GREEN}仮想環境を有効化中...${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}警告: 仮想環境が見つかりません${NC}"
fi

# 必要なパッケージのチェック
echo -e "${BLUE}依存関係をチェック中...${NC}"
python3 -c "import flask, werkzeug" 2>/dev/null || {
    echo -e "${RED}エラー: 必要なパッケージがインストールされていません${NC}"
    echo -e "${YELLOW}以下のコマンドでインストールしてください:${NC}"
    echo "pip install -r requirements.txt"
    exit 1
}

# マイグレーションファイルの存在確認
if [ ! -f "migrations/007_users_table.sql" ]; then
    echo -e "${RED}エラー: マイグレーションファイルが見つかりません${NC}"
    echo "migrations/007_users_table.sql"
    exit 1
fi

echo -e "${GREEN}マイグレーションファイル確認: OK${NC}"
echo ""

# コマンド引数の処理
COMMAND=${1:-migrate}

case $COMMAND in
    migrate)
        echo -e "${YELLOW}マイグレーションを開始します...${NC}"
        echo -e "${YELLOW}この操作はデータベースを変更します。${NC}"
        echo -e "${YELLOW}バックアップが自動作成されます。${NC}"
        echo ""
        read -p "続行しますか? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}マイグレーションがキャンセルされました${NC}"
            exit 1
        fi

        echo ""
        echo -e "${GREEN}マイグレーション実行中...${NC}"
        python3 scripts/migrate_users_to_db.py migrate

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}============================================${NC}"
            echo -e "${GREEN}  マイグレーション完了!${NC}"
            echo -e "${GREEN}============================================${NC}"
            echo ""
            echo -e "${BLUE}次のステップ:${NC}"
            echo "1. 環境変数を設定: export USE_DB_STORE=true"
            echo "2. アプリケーションを再起動"
            echo "3. デフォルト管理者でログイン (admin / changeme123)"
            echo "4. パスワードを変更"
            echo ""
        else
            echo -e "${RED}マイグレーションに失敗しました${NC}"
            exit 1
        fi
        ;;

    verify)
        echo -e "${BLUE}マイグレーション結果を検証中...${NC}"
        python3 scripts/migrate_users_to_db.py verify
        ;;

    rollback)
        echo -e "${YELLOW}ロールバックを開始します...${NC}"
        echo -e "${RED}警告: 最新のバックアップに戻します${NC}"
        echo ""
        read -p "本当に実行しますか? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}ロールバックがキャンセルされました${NC}"
            exit 1
        fi

        python3 scripts/migrate_users_to_db.py rollback
        ;;

    *)
        echo -e "${RED}エラー: 不明なコマンド '$COMMAND'${NC}"
        echo ""
        echo "使用方法:"
        echo "  bash scripts/run_migration.sh migrate   - マイグレーション実行"
        echo "  bash scripts/run_migration.sh verify    - 検証のみ"
        echo "  bash scripts/run_migration.sh rollback  - ロールバック"
        exit 1
        ;;
esac

exit 0
