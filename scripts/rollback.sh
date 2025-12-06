#!/bin/bash

#######################################
# Rollback Script
# MangaAnime Info Delivery System
#######################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
PROJECT_DIR="/opt/mangaanime-system"
BACKUP_DIR="/opt/mangaanime-backups"
LOG_FILE="/var/log/mangaanime/rollback.log"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# List available backups
list_backups() {
    log "Available backups:"
    ls -lt "$BACKUP_DIR" | grep "^d" | awk '{print NR". "$9" ("$6" "$7" "$8")"}'
}

# Restore from backup
restore_backup() {
    local backup_name=$1

    if [ -z "$backup_name" ]; then
        error "Backup name is required"
        exit 1
    fi

    if [ ! -d "$BACKUP_DIR/$backup_name" ]; then
        error "Backup not found: $backup_name"
        exit 1
    fi

    log "Restoring from backup: $backup_name"

    # Stop services
    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.prod.yml down

    # Restore database
    if [ -f "$BACKUP_DIR/$backup_name/production.db" ]; then
        cp "$BACKUP_DIR/$backup_name/production.db" "$PROJECT_DIR/data/"
        log "Database restored"
    fi

    # Restore config
    if [ -d "$BACKUP_DIR/$backup_name/config" ]; then
        cp -r "$BACKUP_DIR/$backup_name/config/"* "$PROJECT_DIR/config/"
        log "Configuration restored"
    fi

    # Restart services
    docker-compose -f docker-compose.prod.yml up -d

    log "Rollback completed successfully"
}

# Main
main() {
    if [ -z "$1" ]; then
        list_backups
        echo ""
        read -p "Enter backup name to restore (or 'q' to quit): " backup_name

        if [ "$backup_name" = "q" ]; then
            exit 0
        fi
    else
        backup_name=$1
    fi

    restore_backup "$backup_name"
}

main "$@"
