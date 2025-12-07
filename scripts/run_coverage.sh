#!/bin/bash

# テストカバレッジ実行スクリプト
# MangaAnime-Info-delivery-system プロジェクトの包括的テストとカバレッジレポート生成

echo "========================================="
echo "  テストカバレッジ測定開始"
echo "========================================="

# プロジェクトルートに移動
cd "$(dirname "$0")"

# 環境変数設定
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export USE_DB_AUDIT_LOG=false  # テスト時はメモリ版を使用

echo ""
echo "1. 新規追加テストの実行..."
echo "========================================="

# 個別テスト実行（新規作成分）
echo ""
echo "[1/5] ユーザーデータベーステスト"
python3 -m pytest tests/test_user_db.py -v --tb=short 2>&1 | head -100

echo ""
echo "[2/5] ブルートフォース対策テスト"
python3 -m pytest tests/test_brute_force.py -v --tb=short 2>&1 | head -100

echo ""
echo "[3/5] 監査ログデータベーステスト"
python3 -m pytest tests/test_audit_log_comprehensive.py -v --tb=short 2>&1 | head -100

echo ""
echo "[4/5] APIキー管理テスト"
python3 -m pytest tests/test_api_key_comprehensive.py -v --tb=short 2>&1 | head -100

echo ""
echo "[5/5] 認証統合テスト"
python3 -m pytest tests/test_auth_integration_comprehensive.py -v --tb=short 2>&1 | head -100

echo ""
echo "========================================="
echo "2. 既存テストの実行..."
echo "========================================="

# 既存のテスト（一部）
python3 -m pytest tests/test_api_key_auth.py -v --tb=short 2>&1 | head -50
python3 -m pytest tests/test_session_security.py -v --tb=short 2>&1 | head -50
python3 -m pytest tests/test_rate_limiter.py -v --tb=short 2>&1 | head -50

echo ""
echo "========================================="
echo "3. カバレッジレポート生成..."
echo "========================================="

# カバレッジレポート生成
python3 -m pytest tests/ \
    --cov=app/models \
    --cov=app/routes \
    --cov=app/utils \
    --cov=modules/brute_force_protection \
    --cov=modules/audit_log_db \
    --cov-report=html:htmlcov \
    --cov-report=term \
    --cov-report=json:coverage.json \
    -v \
    2>&1 | tee coverage_output.txt

echo ""
echo "========================================="
echo "4. カバレッジサマリー"
echo "========================================="

# カバレッジ結果の抽出
if [ -f coverage_output.txt ]; then
    echo ""
    grep -A 20 "TOTAL" coverage_output.txt || echo "カバレッジサマリーの抽出に失敗"
fi

echo ""
echo "========================================="
echo "5. レポート出力先"
echo "========================================="
echo "HTML レポート: htmlcov/index.html"
echo "JSON レポート: coverage.json"
echo "テキスト出力: coverage_output.txt"

echo ""
echo "========================================="
echo "  完了"
echo "========================================="
