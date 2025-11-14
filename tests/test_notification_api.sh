#!/bin/bash

################################################################################
# テスト通知API 包括的テストスクリプト
#
# 使用方法:
#   bash tests/test_notification_api.sh [API_URL]
#
# 引数:
#   API_URL: APIのベースURL (デフォルト: http://localhost:5000)
#
# 例:
#   bash tests/test_notification_api.sh
#   bash tests/test_notification_api.sh http://localhost:8080
################################################################################

set -e

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# APIベースURL
API_URL="${1:-http://localhost:5000}"
ENDPOINT="${API_URL}/api/test-notification"

# テスト結果カウンター
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# テストレポートファイル
REPORT_FILE="test-reports/notification_api_test_$(date +%Y%m%d_%H%M%S).txt"
mkdir -p test-reports

# ヘッダー出力
echo "======================================================================"
echo "テスト通知API 包括的テスト"
echo "======================================================================"
echo "API URL: ${API_URL}"
echo "テスト開始時刻: $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================================"
echo "" | tee "${REPORT_FILE}"

# テスト関数
run_test() {
    local test_name="$1"
    local expected_status="$2"
    local json_data="$3"
    local description="$4"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "${BLUE}[Test ${TOTAL_TESTS}]${NC} ${test_name}" | tee -a "${REPORT_FILE}"
    echo "  説明: ${description}" | tee -a "${REPORT_FILE}"
    echo "  期待HTTPステータス: ${expected_status}" | tee -a "${REPORT_FILE}"

    # curlでリクエスト実行
    if [ -n "${json_data}" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "${json_data}" \
            "${ENDPOINT}" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            "${ENDPOINT}" 2>&1)
    fi

    # レスポンスコードを取得
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)

    echo "  実際のHTTPステータス: ${http_code}" | tee -a "${REPORT_FILE}"
    echo "  レスポンス: ${response_body}" | tee -a "${REPORT_FILE}"

    # ステータスコード検証
    if [ "${http_code}" = "${expected_status}" ]; then
        echo -e "  ${GREEN}✅ PASSED${NC}" | tee -a "${REPORT_FILE}"
        PASSED_TESTS=$((PASSED_TESTS + 1))

        # JSONレスポンスの検証（jqが利用可能な場合）
        if command -v jq &> /dev/null; then
            if echo "${response_body}" | jq . &> /dev/null; then
                echo "  JSON形式: ✅ 有効" | tee -a "${REPORT_FILE}"
            else
                echo "  JSON形式: ⚠️ 無効" | tee -a "${REPORT_FILE}"
            fi
        fi
    else
        echo -e "  ${RED}❌ FAILED${NC}" | tee -a "${REPORT_FILE}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    echo "" | tee -a "${REPORT_FILE}"
    sleep 1
}

# サーバー稼働確認
echo -e "${YELLOW}[準備]${NC} サーバー稼働確認..." | tee -a "${REPORT_FILE}"
if curl -s --head "${API_URL}" > /dev/null; then
    echo -e "${GREEN}✅ サーバー稼働中${NC}" | tee -a "${REPORT_FILE}"
else
    echo -e "${RED}❌ サーバーに接続できません${NC}" | tee -a "${REPORT_FILE}"
    echo "API URL: ${API_URL}" | tee -a "${REPORT_FILE}"
    echo "サーバーが起動していることを確認してください。" | tee -a "${REPORT_FILE}"
    exit 1
fi
echo "" | tee -a "${REPORT_FILE}"

################################################################################
# テストケース1: 正常系 - 基本的なテスト通知
################################################################################
run_test \
    "正常系: 基本的なテスト通知" \
    "200" \
    '{"message": "テスト通知です"}' \
    "正しいパラメータでテスト通知を送信"

################################################################################
# テストケース2: 正常系 - カスタムメッセージ
################################################################################
run_test \
    "正常系: カスタムメッセージ" \
    "200" \
    '{"message": "システム動作確認: 2024年11月14日"}' \
    "カスタムメッセージでテスト通知を送信"

################################################################################
# テストケース3: 正常系 - 日本語メッセージ
################################################################################
run_test \
    "正常系: 日本語メッセージ" \
    "200" \
    '{"message": "テスト通知：システムが正常に動作しています 🎬"}' \
    "日本語と絵文字を含むメッセージ"

################################################################################
# テストケース4: 正常系 - 空のメッセージ（デフォルト使用）
################################################################################
run_test \
    "正常系: 空のメッセージ" \
    "200" \
    '{}' \
    "メッセージ未指定でデフォルトメッセージを使用"

################################################################################
# テストケース5: 正常系 - 長いメッセージ
################################################################################
long_message=$(printf '%.0s長' {1..100})
run_test \
    "正常系: 長いメッセージ" \
    "200" \
    "{\"message\": \"${long_message}\"}" \
    "100文字の長いメッセージ"

################################################################################
# テストケース6: 異常系 - 不正なJSON
################################################################################
echo -e "${BLUE}[Test $((TOTAL_TESTS + 1))]${NC} 異常系: 不正なJSON" | tee -a "${REPORT_FILE}"
echo "  説明: 不正なJSON形式のリクエスト" | tee -a "${REPORT_FILE}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d '{invalid json}' \
    "${ENDPOINT}" 2>&1)

http_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | head -n -1)

echo "  HTTPステータス: ${http_code}" | tee -a "${REPORT_FILE}"
echo "  レスポンス: ${response_body}" | tee -a "${REPORT_FILE}"

if [ "${http_code}" = "400" ] || [ "${http_code}" = "500" ]; then
    echo -e "  ${GREEN}✅ PASSED${NC} (エラーが適切に処理された)" | tee -a "${REPORT_FILE}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "  ${RED}❌ FAILED${NC}" | tee -a "${REPORT_FILE}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo "" | tee -a "${REPORT_FILE}"

################################################################################
# テストケース7: 異常系 - Content-Typeなし
################################################################################
echo -e "${BLUE}[Test $((TOTAL_TESTS + 1))]${NC} 異常系: Content-Typeなし" | tee -a "${REPORT_FILE}"
echo "  説明: Content-Typeヘッダーなしのリクエスト" | tee -a "${REPORT_FILE}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

response=$(curl -s -w "\n%{http_code}" -X POST \
    -d '{"message": "テスト"}' \
    "${ENDPOINT}" 2>&1)

http_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | head -n -1)

echo "  HTTPステータス: ${http_code}" | tee -a "${REPORT_FILE}"
echo "  レスポンス: ${response_body}" | tee -a "${REPORT_FILE}"

# Content-Typeなしでも処理されるか、適切にエラーになるかを確認
if [ "${http_code}" = "200" ] || [ "${http_code}" = "400" ] || [ "${http_code}" = "415" ]; then
    echo -e "  ${GREEN}✅ PASSED${NC} (適切に処理された)" | tee -a "${REPORT_FILE}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "  ${RED}❌ FAILED${NC}" | tee -a "${REPORT_FILE}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo "" | tee -a "${REPORT_FILE}"

################################################################################
# テストケース8: 異常系 - GETメソッド
################################################################################
echo -e "${BLUE}[Test $((TOTAL_TESTS + 1))]${NC} 異常系: GETメソッド" | tee -a "${REPORT_FILE}"
echo "  説明: 許可されていないGETメソッドでのリクエスト" | tee -a "${REPORT_FILE}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

response=$(curl -s -w "\n%{http_code}" -X GET \
    "${ENDPOINT}" 2>&1)

http_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | head -n -1)

echo "  HTTPステータス: ${http_code}" | tee -a "${REPORT_FILE}"
echo "  レスポンス: ${response_body}" | tee -a "${REPORT_FILE}"

if [ "${http_code}" = "405" ]; then
    echo -e "  ${GREEN}✅ PASSED${NC} (405 Method Not Allowed)" | tee -a "${REPORT_FILE}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "  ${RED}❌ FAILED${NC}" | tee -a "${REPORT_FILE}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo "" | tee -a "${REPORT_FILE}"

################################################################################
# テストケース9: パフォーマンステスト - 連続リクエスト
################################################################################
echo -e "${BLUE}[Test $((TOTAL_TESTS + 1))]${NC} パフォーマンステスト: 連続リクエスト" | tee -a "${REPORT_FILE}"
echo "  説明: 5回の連続リクエストでレスポンスタイムを測定" | tee -a "${REPORT_FILE}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

total_time=0
success_count=0

for i in {1..5}; do
    start_time=$(date +%s%N)
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d '{"message": "パフォーマンステスト"}' \
        "${ENDPOINT}" 2>&1)
    end_time=$(date +%s%N)

    http_code=$(echo "$response" | tail -n1)
    elapsed=$((($end_time - $start_time) / 1000000)) # ミリ秒に変換
    total_time=$((total_time + elapsed))

    if [ "${http_code}" = "200" ]; then
        success_count=$((success_count + 1))
    fi

    echo "  リクエスト${i}: ${elapsed}ms (HTTP ${http_code})" | tee -a "${REPORT_FILE}"
    sleep 1
done

average_time=$((total_time / 5))
echo "  平均レスポンスタイム: ${average_time}ms" | tee -a "${REPORT_FILE}"
echo "  成功率: ${success_count}/5" | tee -a "${REPORT_FILE}"

if [ ${success_count} -ge 3 ]; then
    echo -e "  ${GREEN}✅ PASSED${NC} (5回中${success_count}回成功)" | tee -a "${REPORT_FILE}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "  ${RED}❌ FAILED${NC}" | tee -a "${REPORT_FILE}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo "" | tee -a "${REPORT_FILE}"

################################################################################
# テスト結果サマリー
################################################################################
echo "======================================================================"
echo "テスト結果サマリー"
echo "======================================================================"
echo "総テスト数: ${TOTAL_TESTS}" | tee -a "${REPORT_FILE}"
echo -e "${GREEN}成功: ${PASSED_TESTS}${NC}" | tee -a "${REPORT_FILE}"
echo -e "${RED}失敗: ${FAILED_TESTS}${NC}" | tee -a "${REPORT_FILE}"

success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo "成功率: ${success_rate}%" | tee -a "${REPORT_FILE}"

echo "テスト終了時刻: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "${REPORT_FILE}"
echo "レポートファイル: ${REPORT_FILE}" | tee -a "${REPORT_FILE}"
echo "======================================================================" | tee -a "${REPORT_FILE}"

if [ ${FAILED_TESTS} -eq 0 ]; then
    echo -e "${GREEN}✅ 全てのテストが成功しました！${NC}"
    exit 0
else
    echo -e "${RED}❌ ${FAILED_TESTS}個のテストが失敗しました${NC}"
    exit 1
fi
