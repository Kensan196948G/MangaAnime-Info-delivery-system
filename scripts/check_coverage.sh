#!/bin/bash
# テストカバレッジ確認スクリプト

cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo "=========================================="
echo "テストカバレッジ確認"
echo "=========================================="
echo "プロジェクトパス: $PROJECT_ROOT"
echo ""

# pytest-covがインストールされているか確認
if ! python3 -m pip list | grep -q pytest-cov; then
    echo "pytest-covをインストール中..."
    python3 -m pip install pytest-cov
fi

# テストカバレッジを実行
echo "テストカバレッジを実行中..."
python3 -m pytest tests/ \
    --cov=app \
    --cov=modules \
    --cov-report=term-missing \
    --cov-report=html:coverage_html \
    --cov-report=json:coverage.json \
    -v

echo ""
echo "=========================================="
echo "カバレッジレポートが生成されました:"
echo "- HTML: coverage_html/index.html"
echo "- JSON: coverage.json"
echo "=========================================="
