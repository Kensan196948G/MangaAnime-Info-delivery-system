#!/bin/bash
# Fix permissions for monitoring scripts

PROJECT_ROOT="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"

echo "Fixing permissions for monitoring scripts..."

chmod +x "$PROJECT_ROOT/scripts/setup-monitoring.sh"
chmod +x "$PROJECT_ROOT/scripts/load-test.sh"
chmod +x "$PROJECT_ROOT/examples/monitoring_integration.py"

echo "Done!"
