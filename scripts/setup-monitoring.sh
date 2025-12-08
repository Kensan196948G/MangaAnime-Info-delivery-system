#!/bin/bash
# Monitoring Stack Setup Script

set -e

PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
cd "$PROJECT_ROOT"

echo "================================================"
echo "MangaAnime Monitoring Stack Setup"
echo "================================================"
echo ""

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 依存関係チェック
echo -e "${YELLOW}[1/7] Checking dependencies...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
echo ""

# 2. Python依存パッケージインストール
echo -e "${YELLOW}[2/7] Installing Python monitoring packages...${NC}"
pip install prometheus-client psutil opentelemetry-api opentelemetry-sdk \
    opentelemetry-exporter-jaeger opentelemetry-instrumentation-flask \
    opentelemetry-instrumentation-requests opentelemetry-instrumentation-sqlite3 \
    --quiet

echo -e "${GREEN}✓ Python packages installed${NC}"
echo ""

# 3. ディレクトリ構造作成
echo -e "${YELLOW}[3/7] Creating directory structure...${NC}"
mkdir -p config/prometheus
mkdir -p config/grafana/dashboards
mkdir -p config/grafana/datasources
mkdir -p config/alertmanager
mkdir -p docs/monitoring
mkdir -p logs/monitoring

echo -e "${GREEN}✓ Directory structure created${NC}"
echo ""

# 4. 環境変数設定確認
echo -e "${YELLOW}[4/7] Checking environment variables...${NC}"

if [ -z "$SLACK_WEBHOOK_URL" ]; then
    echo -e "${YELLOW}Warning: SLACK_WEBHOOK_URL not set${NC}"
    echo "Please set it with: export SLACK_WEBHOOK_URL='your-webhook-url'"
else
    echo -e "${GREEN}✓ SLACK_WEBHOOK_URL is set${NC}"
    # Alertmanager設定更新
    sed -i "s|YOUR_SLACK_WEBHOOK_URL|$SLACK_WEBHOOK_URL|g" config/alertmanager/config.yml
fi

if [ -z "$DISCORD_WEBHOOK_URL" ]; then
    echo -e "${YELLOW}Warning: DISCORD_WEBHOOK_URL not set${NC}"
    echo "Please set it with: export DISCORD_WEBHOOK_URL='your-webhook-url'"
else
    echo -e "${GREEN}✓ DISCORD_WEBHOOK_URL is set${NC}"
    # Alertmanager設定更新
    sed -i "s|YOUR_DISCORD_WEBHOOK_URL|$DISCORD_WEBHOOK_URL|g" config/alertmanager/config.yml
fi

echo ""

# 5. Docker Composeファイル検証
echo -e "${YELLOW}[5/7] Validating Docker Compose configuration...${NC}"
if docker-compose -f docker-compose-monitoring.yml config > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker Compose configuration is valid${NC}"
else
    echo -e "${RED}Error: Docker Compose configuration is invalid${NC}"
    exit 1
fi

echo ""

# 6. 監視スタック起動
echo -e "${YELLOW}[6/7] Starting monitoring stack...${NC}"
docker-compose -f docker-compose-monitoring.yml up -d

echo -e "${GREEN}✓ Monitoring stack started${NC}"
echo ""

# 7. ヘルスチェック
echo -e "${YELLOW}[7/7] Performing health checks...${NC}"
sleep 10

# Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Prometheus is healthy (http://localhost:9090)${NC}"
else
    echo -e "${RED}✗ Prometheus is not healthy${NC}"
fi

# Grafana
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Grafana is healthy (http://localhost:3000)${NC}"
else
    echo -e "${RED}✗ Grafana is not healthy${NC}"
fi

# Alertmanager
if curl -s http://localhost:9093/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Alertmanager is healthy (http://localhost:9093)${NC}"
else
    echo -e "${RED}✗ Alertmanager is not healthy${NC}"
fi

# Jaeger
if curl -s http://localhost:16686 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Jaeger is healthy (http://localhost:16686)${NC}"
else
    echo -e "${RED}✗ Jaeger is not healthy${NC}"
fi

echo ""
echo "================================================"
echo -e "${GREEN}Monitoring Stack Setup Complete!${NC}"
echo "================================================"
echo ""
echo "Access URLs:"
echo "  - Prometheus:    http://localhost:9090"
echo "  - Grafana:       http://localhost:3000 (admin/admin123)"
echo "  - Alertmanager:  http://localhost:9093"
echo "  - Jaeger UI:     http://localhost:16686"
echo "  - Node Exporter: http://localhost:9100/metrics"
echo "  - cAdvisor:      http://localhost:8080"
echo ""
echo "Next steps:"
echo "  1. Configure Slack/Discord webhooks in config/alertmanager/config.yml"
echo "  2. Add metrics endpoint to your Flask app with init_metrics(app)"
echo "  3. Enable tracing with init_tracing() in your application"
echo "  4. Check Grafana dashboard at http://localhost:3000"
echo ""
echo "For more information, see docs/monitoring/README.md"
echo ""
