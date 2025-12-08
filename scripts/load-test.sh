#!/bin/bash
# Load Test Script for Monitoring System
# 監視システムの動作確認用負荷テストスクリプト

set -e

APP_URL="http://localhost:5000"
DURATION=${1:-60}  # デフォルト60秒
CONCURRENCY=${2:-10}  # デフォルト10並列

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================"
echo -e "${BLUE}MangaAnime Monitoring Load Test${NC}"
echo "================================================"
echo ""
echo "Configuration:"
echo "  App URL:      $APP_URL"
echo "  Duration:     ${DURATION}s"
echo "  Concurrency:  $CONCURRENCY"
echo ""

# 1. アプリケーション起動確認
echo -e "${YELLOW}[1/5] Checking application...${NC}"
if curl -s "$APP_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Application is running${NC}"
else
    echo -e "${RED}✗ Application is not running${NC}"
    echo "Please start the application first:"
    echo "  python examples/monitoring_integration.py"
    exit 1
fi
echo ""

# 2. 監視スタック確認
echo -e "${YELLOW}[2/5] Checking monitoring stack...${NC}"

if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Prometheus is running${NC}"
else
    echo -e "${RED}✗ Prometheus is not running${NC}"
fi

if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Grafana is running${NC}"
else
    echo -e "${RED}✗ Grafana is not running${NC}"
fi

if curl -s http://localhost:16686 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Jaeger is running${NC}"
else
    echo -e "${RED}✗ Jaeger is not running${NC}"
fi
echo ""

# 3. 負荷テスト関数
run_requests() {
    local endpoint=$1
    local requests=$2
    local name=$3

    echo -e "${YELLOW}Running $name test...${NC}"

    for i in $(seq 1 $requests); do
        curl -s "$APP_URL$endpoint" > /dev/null &
    done

    wait
    echo -e "${GREEN}✓ Completed $requests requests to $endpoint${NC}"
}

# 4. 負荷テスト実行
echo -e "${YELLOW}[3/5] Running load tests...${NC}"
echo ""

# 基本的なリクエスト
run_requests "/" 100 "Index"
sleep 1

# API Works取得
run_requests "/api/works" 100 "Works"
sleep 1

# Pending Releases取得
run_requests "/api/releases/pending" 100 "Pending Releases"
sleep 1

# API Fetch シミュレーション
run_requests "/api/fetch/simulate?source=anilist" 50 "API Fetch"
sleep 1

# 通知シミュレーション
run_requests "/api/notify/simulate?type=email" 50 "Notification"
sleep 1

# カレンダー同期シミュレーション
run_requests "/api/calendar/simulate" 30 "Calendar Sync"
sleep 1

# 様々なレイテンシでの負荷
echo -e "${YELLOW}Testing with various latencies...${NC}"
for duration in 0.1 0.5 1.0 2.0; do
    run_requests "/api/load/simulate?duration=$duration" 20 "Load ($duration s)"
    sleep 1
done

# エラーを含む負荷
echo -e "${YELLOW}Testing with errors...${NC}"
for error_rate in 0.1 0.3 0.5; do
    run_requests "/api/load/simulate?duration=0.5&error_rate=$error_rate" 20 "Load (error rate: $error_rate)"
    sleep 1
done

echo ""
echo -e "${GREEN}✓ Load tests completed${NC}"
echo ""

# 5. メトリクス確認
echo -e "${YELLOW}[4/5] Checking metrics...${NC}"
sleep 5  # メトリクス集約を待つ

METRICS=$(curl -s "$APP_URL/metrics")

# 基本メトリクス確認
if echo "$METRICS" | grep -q "http_requests_total"; then
    echo -e "${GREEN}✓ http_requests_total metric found${NC}"
    REQUEST_COUNT=$(echo "$METRICS" | grep "http_requests_total" | head -1)
    echo "  $REQUEST_COUNT"
else
    echo -e "${RED}✗ http_requests_total metric not found${NC}"
fi

if echo "$METRICS" | grep -q "http_request_duration_seconds"; then
    echo -e "${GREEN}✓ http_request_duration_seconds metric found${NC}"
else
    echo -e "${RED}✗ http_request_duration_seconds metric not found${NC}"
fi

if echo "$METRICS" | grep -q "system_cpu_usage_percent"; then
    echo -e "${GREEN}✓ system_cpu_usage_percent metric found${NC}"
    CPU_USAGE=$(echo "$METRICS" | grep "system_cpu_usage_percent" | head -1)
    echo "  $CPU_USAGE"
else
    echo -e "${RED}✗ system_cpu_usage_percent metric not found${NC}"
fi

echo ""

# 6. サマリー表示
echo -e "${YELLOW}[5/5] Summary${NC}"
echo ""
echo "Load test completed successfully!"
echo ""
echo "Next steps:"
echo ""
echo "1. Check Grafana Dashboard:"
echo "   http://localhost:3000/d/mangaanime-main"
echo ""
echo "2. Check Prometheus Metrics:"
echo "   http://localhost:9090/graph"
echo "   Example queries:"
echo "     - rate(http_requests_total[5m])"
echo "     - histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
echo ""
echo "3. Check Jaeger Traces:"
echo "   http://localhost:16686"
echo "   Service: mangaanime-info-delivery"
echo ""
echo "4. Check Alertmanager:"
echo "   http://localhost:9093"
echo ""
echo "================================================"
echo ""
