#!/bin/bash
# Test Execution Script with Coverage
# ====================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Test Suite with Coverage Report${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Navigate to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Check pytest installation
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not installed${NC}"
    echo "Install with: pip install pytest pytest-cov"
    exit 1
fi

# Run tests with coverage
echo -e "${YELLOW}Running all tests with coverage...${NC}"
echo ""

pytest tests/ \
    --cov=app \
    --cov=modules \
    --cov-report=html:htmlcov \
    --cov-report=term-missing:skip-covered \
    --cov-report=json:coverage.json \
    --cov-fail-under=80 \
    -v \
    --tb=short

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  ✓ All Tests Passed${NC}"
    echo -e "${GREEN}  ✓ Coverage >= 80%${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${GREEN}Coverage Reports:${NC}"
    echo "  - HTML: htmlcov/index.html"
    echo "  - JSON: coverage.json"
    echo ""
    echo "Open HTML report: xdg-open htmlcov/index.html"
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  ✗ Tests Failed or Coverage < 80%${NC}"
    echo -e "${RED}========================================${NC}"
fi

exit $EXIT_CODE
