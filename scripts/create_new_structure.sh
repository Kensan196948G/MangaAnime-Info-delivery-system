#!/bin/bash
# Create new directory structure for MangaAnime-Info-delivery-system
# Author: System Architecture Designer
# Date: 2025-11-14

set -e

echo "========================================="
echo "Creating new directory structure..."
echo "========================================="

# Function to create directory with message
create_dir() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo "[CREATED] $1"
    else
        echo "[EXISTS]  $1"
    fi
}

# Main application
create_dir "app"

# Authentication
create_dir "auth/token_generators"

# Scripts organization
create_dir "scripts/startup"
create_dir "scripts/setup"
create_dir "scripts/maintenance"

# Tools organization
create_dir "tools/monitoring"
create_dir "tools/repair"
create_dir "tools/validation"
create_dir "tools/linting"
create_dir "tools/setup"

# Tests organization
create_dir "tests/unit"
create_dir "tests/integration"
create_dir "tests/e2e"
create_dir "tests/security"
create_dir "tests/runners"
create_dir "tests/utilities"
create_dir "tests/fixtures"

# Binary/executable scripts
create_dir "bin"

# Data files
create_dir "data/backups"

# Reports
create_dir "reports"

# Temporary output
create_dir "output"

# Systemd service definitions
create_dir "systemd"

# Database migrations
create_dir "database/migrations"

# Archive
create_dir "archive/old_versions"
create_dir "archive/deprecated"

echo ""
echo "========================================="
echo "Directory structure created successfully!"
echo "========================================="
echo ""
echo "Summary:"
echo "  - Main app:        app/"
echo "  - Auth:            auth/"
echo "  - Scripts:         scripts/{startup,setup,maintenance}/"
echo "  - Tools:           tools/{monitoring,repair,validation,linting,setup}/"
echo "  - Tests:           tests/{unit,integration,e2e,security,runners,utilities,fixtures}/"
echo "  - Binaries:        bin/"
echo "  - Data:            data/"
echo "  - Reports:         reports/"
echo "  - Output:          output/"
echo "  - Systemd:         systemd/"
echo "  - Database:        database/"
echo "  - Archive:         archive/"
echo ""
