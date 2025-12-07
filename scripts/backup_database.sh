#!/bin/bash
# Database backup script for MangaAnime Info Delivery System
# Usage: ./backup_database.sh [backup_directory]

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATABASE_PATH="${PROJECT_ROOT}/db.sqlite3"
BACKUP_DIR="${1:-${PROJECT_ROOT}/backups}"
DATE_FORMAT=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILENAME="db_backup_${DATE_FORMAT}.sqlite3"
RETENTION_DAYS=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Database Backup Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if database exists
if [ ! -f "${DATABASE_PATH}" ]; then
    echo -e "${RED}Error: Database not found at ${DATABASE_PATH}${NC}"
    exit 1
fi

# Create backup directory if it doesn't exist
if [ ! -d "${BACKUP_DIR}" ]; then
    echo -e "${YELLOW}Creating backup directory: ${BACKUP_DIR}${NC}"
    mkdir -p "${BACKUP_DIR}"
fi

# Create backup
echo "Creating backup..."
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

# Use SQLite's backup command for consistency
sqlite3 "${DATABASE_PATH}" ".backup '${BACKUP_PATH}'"

if [ $? -eq 0 ]; then
    # Get file sizes for comparison
    ORIGINAL_SIZE=$(stat -c%s "${DATABASE_PATH}" 2>/dev/null || stat -f%z "${DATABASE_PATH}")
    BACKUP_SIZE=$(stat -c%s "${BACKUP_PATH}" 2>/dev/null || stat -f%z "${BACKUP_PATH}")

    echo -e "${GREEN}Backup created successfully!${NC}"
    echo "  Location: ${BACKUP_PATH}"
    echo "  Original size: $(numfmt --to=iec-i --suffix=B ${ORIGINAL_SIZE} 2>/dev/null || echo ${ORIGINAL_SIZE} bytes)"
    echo "  Backup size: $(numfmt --to=iec-i --suffix=B ${BACKUP_SIZE} 2>/dev/null || echo ${BACKUP_SIZE} bytes)"

    # Create compressed backup
    echo ""
    echo "Creating compressed backup..."
    gzip -c "${BACKUP_PATH}" > "${BACKUP_PATH}.gz"
    COMPRESSED_SIZE=$(stat -c%s "${BACKUP_PATH}.gz" 2>/dev/null || stat -f%z "${BACKUP_PATH}.gz")
    echo -e "${GREEN}Compressed backup created!${NC}"
    echo "  Location: ${BACKUP_PATH}.gz"
    echo "  Compressed size: $(numfmt --to=iec-i --suffix=B ${COMPRESSED_SIZE} 2>/dev/null || echo ${COMPRESSED_SIZE} bytes)"
else
    echo -e "${RED}Backup failed!${NC}"
    exit 1
fi

# Clean up old backups
echo ""
echo "Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
OLD_COUNT=$(find "${BACKUP_DIR}" -name "db_backup_*.sqlite3*" -mtime +${RETENTION_DAYS} 2>/dev/null | wc -l)

if [ ${OLD_COUNT} -gt 0 ]; then
    find "${BACKUP_DIR}" -name "db_backup_*.sqlite3*" -mtime +${RETENTION_DAYS} -delete
    echo -e "${YELLOW}Deleted ${OLD_COUNT} old backup(s)${NC}"
else
    echo "No old backups to delete"
fi

# Show current backup status
echo ""
echo -e "${GREEN}Current backups:${NC}"
ls -lh "${BACKUP_DIR}"/db_backup_*.sqlite3* 2>/dev/null | tail -5

TOTAL_BACKUPS=$(ls "${BACKUP_DIR}"/db_backup_*.sqlite3 2>/dev/null | wc -l)
echo ""
echo "Total backups: ${TOTAL_BACKUPS}"

echo ""
echo -e "${GREEN}Backup complete!${NC}"
echo "========================================"
