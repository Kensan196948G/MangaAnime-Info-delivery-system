#!/bin/bash
###############################################################################
# スクリプト実行権限付与ヘルパー
#
# 全てのセキュリティツールスクリプトに実行権限を付与します
###############################################################################

echo "🔧 実行権限を付与中..."

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# Pythonスクリプト
chmod +x scripts/scan_sql_vulnerabilities.py
chmod +x scripts/analyze_database_secure.py

# Bashスクリプト
chmod +x scripts/setup_security_tools.sh
chmod +x scripts/make_executable.sh

echo "✅ 完了！"
echo ""
echo "実行可能なスクリプト:"
echo "  - scripts/scan_sql_vulnerabilities.py"
echo "  - scripts/analyze_database_secure.py"
echo "  - scripts/setup_security_tools.sh"
echo "  - scripts/make_executable.sh"
