#!/bin/bash
# データ収集統合テストランナー

set -e

echo "========================================"
echo "データ収集機能 統合テスト実行"
echo "========================================"
echo ""

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# Python環境確認
if ! command -v python3 &> /dev/null; then
    echo "エラー: python3がインストールされていません"
    exit 1
fi

echo "Python環境: $(python3 --version)"
echo ""

# 依存パッケージチェック
echo "依存パッケージの確認中..."
python3 -c "import requests" 2>/dev/null || {
    echo "警告: requestsがインストールされていません"
    echo "インストール: pip3 install requests"
}

python3 -c "import feedparser" 2>/dev/null || {
    echo "警告: feedparserがインストールされていません"
    echo "インストール: pip3 install feedparser"
}

echo ""

# テスト実行
echo "テストを開始します..."
echo ""

chmod +x scripts/test_data_collection.py
python3 scripts/test_data_collection.py

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "========================================"
    echo "テスト完了: 成功"
    echo "========================================"
else
    echo "========================================"
    echo "テスト完了: 失敗 (終了コード: $exit_code)"
    echo "========================================"
fi

exit $exit_code
