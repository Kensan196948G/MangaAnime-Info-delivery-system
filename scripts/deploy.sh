#!/bin/bash

#######################################
# Production Deployment Script
# MangaAnime Info Delivery System
#######################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/mangaanime-system"
BACKUP_DIR="/opt/mangaanime-backups"
LOG_FILE="/var/log/mangaanime/deploy.log"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root or with sudo
check_permissions() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Backup current deployment
backup_current() {
    log "Creating backup of current deployment..."

    BACKUP_NAME="backup-$(date +'%Y%m%d-%H%M%S')"
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

    # Backup database
    if [ -f "$PROJECT_DIR/data/production.db" ]; then
        cp "$PROJECT_DIR/data/production.db" "$BACKUP_DIR/$BACKUP_NAME/"
        log "Database backed up"
    fi

    # Backup config
    if [ -d "$PROJECT_DIR/config" ]; then
        cp -r "$PROJECT_DIR/config" "$BACKUP_DIR/$BACKUP_NAME/"
        log "Configuration backed up"
    fi

    # Keep only last 10 backups
    cd "$BACKUP_DIR"
    ls -t | tail -n +11 | xargs -r rm -rf

    log "Backup completed: $BACKUP_NAME"
}

# Pull latest code
pull_latest() {
    log "Pulling latest Docker images..."

    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.prod.yml pull

    log "Images pulled successfully"
}

# Stop services
stop_services() {
    log "Stopping services..."

    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.prod.yml down

    log "Services stopped"
}

# Start services
start_services() {
    log "Starting services..."

    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.prod.yml up -d

    log "Services started"
}

# Health check
health_check() {
    log "Running health check..."

    sleep 10

    # Check if containers are running
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log "Containers are running"
    else
        error "Containers are not running!"
        return 1
    fi

    # Check application health endpoint
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log "Application health check passed"
    else
        warning "Application health check failed (endpoint may not be implemented)"
    fi

    return 0
}

# Rollback
rollback() {
    error "Deployment failed! Rolling back..."

    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml up -d --force-recreate

    error "Rollback completed"
    exit 1
}

# Cleanup
cleanup() {
    log "Cleaning up old Docker resources..."

    docker image prune -f
    docker volume prune -f

    log "Cleanup completed"
}

# Main deployment flow
main() {
    log "========================================="
    log "Starting production deployment"
    log "========================================="

    check_permissions
    backup_current
    stop_services
    pull_latest
    start_services

    if health_check; then
        cleanup
        log "========================================="
        log "Deployment completed successfully!"
        log "========================================="
    else
        rollback
    fi
}

# Run main function
main "$@"
