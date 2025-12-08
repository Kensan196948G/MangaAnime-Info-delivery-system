#!/bin/bash

# 型チェックスクリプト

set -e

echo "======================================"
echo "Python型チェック開始"
echo "======================================"

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# 型ヒント付きモジュールのリスト
TYPED_MODULES=(
    "modules/types_helper.py"
    "modules/config_typed.py"
    "modules/mailer_typed.py"
    "modules/calendar_typed.py"
    "modules/anime_anilist_typed.py"
    "modules/manga_rss_typed.py"
    "modules/filter_logic_typed.py"
)

echo ""
echo "対象ファイル:"
for module in "${TYPED_MODULES[@]}"; do
    echo "  - $module"
done

echo ""
echo "======================================"
echo "mypy実行中..."
echo "======================================"

# mypyがインストールされているか確認
if ! command -v mypy &> /dev/null; then
    echo "エラー: mypyがインストールされていません"
    echo "インストール: pip install mypy"
    exit 1
fi

# 各モジュールに対してmypyを実行
total_errors=0
for module in "${TYPED_MODULES[@]}"; do
    if [ -f "$module" ]; then
        echo ""
        echo "チェック: $module"
        echo "--------------------------------------"

        # mypyを実行してエラー数をカウント
        if mypy "$module" 2>&1 | tee /tmp/mypy_output.txt; then
            echo "✓ エラーなし"
        else
            error_count=$(grep -c "error:" /tmp/mypy_output.txt || echo "0")
            total_errors=$((total_errors + error_count))
            echo "✗ エラー: $error_count件"
        fi
    else
        echo "警告: $module が見つかりません"
    fi
done

echo ""
echo "======================================"
echo "型チェック完了"
echo "======================================"
echo "総エラー数: $total_errors"

if [ $total_errors -eq 0 ]; then
    echo "✓ すべてのモジュールが型チェックに合格しました！"
    exit 0
else
    echo "✗ 型エラーが見つかりました"
    exit 1
fi
