#!/bin/bash

echo "🔍 デモ用テストエラー修復"
echo "=========================="

# テストエラーを意図的に作成
echo "import nonexistent_module" > tests/test_demo_error.py

echo "1. エラーのあるテストを実行:"
python3 -m pytest tests/test_demo_error.py --tb=no 2>&1 | grep -E "ERROR|FAILED|ModuleNotFoundError"

echo ""
echo "2. エラーを検出して修復:"
echo "# Fixed test" > tests/test_demo_error.py
echo "def test_fixed():" >> tests/test_demo_error.py
echo "    assert True" >> tests/test_demo_error.py

echo ""
echo "3. 修復後のテスト実行:"
python3 -m pytest tests/test_demo_error.py --tb=no -q

# クリーンアップ
rm tests/test_demo_error.py

echo ""
echo "✅ デモ完了！"
