#!/bin/bash
# File migration script for MangaAnime-Info-delivery-system restructuring
# Author: System Architecture Designer
# Date: 2025-11-14
#
# Usage: bash scripts/migrate_files.sh --phase <phase_number> [--dry-run]

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DRY_RUN=false
PHASE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --phase)
            PHASE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 --phase <phase_number> [--dry-run]"
            exit 1
            ;;
    esac
done

# Validate phase
if [ -z "$PHASE" ]; then
    echo "Error: --phase is required"
    echo "Usage: $0 --phase <phase_number> [--dry-run]"
    echo ""
    echo "Available phases:"
    echo "  1 - Main applications"
    echo "  2 - Authentication"
    echo "  3 - Tests"
    echo "  4 - Tools"
    echo "  5 - Scripts"
    echo "  6 - Data and config"
    echo "  all - Run all phases"
    exit 1
fi

# Function to move file with backup
move_file() {
    local src="$1"
    local dst="$2"

    if [ ! -f "$src" ]; then
        echo -e "${YELLOW}[SKIP]${NC} $src (not found)"
        return
    fi

    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY-RUN]${NC} Would move: $src -> $dst"
        return
    fi

    # Create destination directory if it doesn't exist
    mkdir -p "$(dirname "$dst")"

    # Move file
    mv "$src" "$dst"
    echo -e "${GREEN}[MOVED]${NC} $src -> $dst"
}

# Function to create symlink for backward compatibility
create_symlink() {
    local target="$1"
    local link_name="$2"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY-RUN]${NC} Would create symlink: $link_name -> $target"
        return
    fi

    ln -sf "$target" "$link_name"
    echo -e "${GREEN}[SYMLINK]${NC} $link_name -> $target"
}

# Phase 1: Main applications
phase_1() {
    echo -e "${YELLOW}=== Phase 1: Main Applications ===${NC}"

    move_file "web_app.py" "app/web_app.py"
    move_file "release_notifier.py" "app/release_notifier.py"
    move_file "dashboard_main.py" "app/dashboard_main.py"

    # Create backward compatibility symlinks
    if [ "$DRY_RUN" = false ]; then
        create_symlink "app/web_app.py" "web_app.py"
        create_symlink "app/release_notifier.py" "release_notifier.py"
        create_symlink "app/dashboard_main.py" "dashboard_main.py"
    fi
}

# Phase 2: Authentication
phase_2() {
    echo -e "${YELLOW}=== Phase 2: Authentication ===${NC}"

    move_file "auth_config.py" "auth/auth_config.py"
    move_file "oauth_setup_helper.py" "auth/oauth_setup_helper.py"
    move_file "create_token.py" "auth/token_generators/create_token.py"
    move_file "create_token_simple.py" "auth/token_generators/create_token_simple.py"
    move_file "generate_token.py" "auth/token_generators/generate_token.py"

    # Archive deprecated
    move_file "create_token_improved.py" "archive/deprecated/create_token_improved.py"
    move_file "create_token_manual.py" "archive/deprecated/create_token_manual.py"
}

# Phase 3: Tests
phase_3() {
    echo -e "${YELLOW}=== Phase 3: Tests ===${NC}"

    # Test runners
    move_file "test_runner.py" "tests/runners/test_runner.py"
    move_file "simple_test_runner.py" "tests/runners/simple_test_runner.py"
    move_file "run_check.py" "tests/runners/run_check.py"
    move_file "run_failing_tests.py" "tests/runners/run_failing_tests.py"
    move_file "simple_test_check.py" "tests/runners/simple_test_check.py"

    # Test utilities
    move_file "analyze_tests.py" "tests/utilities/analyze_tests.py"
    move_file "examine_test_content.py" "tests/utilities/examine_test_content.py"
    move_file "get_test_info.py" "tests/utilities/get_test_info.py"
    move_file "list_tests.py" "tests/utilities/list_tests.py"
    move_file "verify_tests.py" "tests/utilities/verify_tests.py"
    move_file "fix_all_tests.py" "tests/utilities/fix_all_tests.py"
    move_file "fix_tests_final.py" "tests/utilities/fix_tests_final.py"
    move_file "run_fixed_tests.py" "tests/utilities/run_fixed_tests.py"
    move_file "simple_phase2_test.py" "tests/utilities/simple_phase2_test.py"
    move_file "test_discovery.py" "tests/utilities/test_discovery.py"

    # E2E tests
    move_file "test_backend_api.py" "tests/e2e/test_backend_api.py"
    move_file "test_enhanced_backend.py" "tests/e2e/test_enhanced_backend.py"
    move_file "test_phase2_implementation.py" "tests/e2e/test_phase2_implementation.py"

    # Integration tests
    move_file "test_email_delivery.py" "tests/integration/test_email_delivery.py"
    move_file "test_gmail_auth.py" "tests/integration/test_gmail_auth.py"
    move_file "test_smtp_email.py" "tests/integration/test_smtp_email.py"
    move_file "test_mailer_improvements.py" "tests/integration/test_mailer_improvements.py"
    move_file "test_notification.py" "tests/integration/test_notification.py"
    move_file "test_secret_key.py" "tests/integration/test_secret_key.py"
}

# Phase 4: Tools
phase_4() {
    echo -e "${YELLOW}=== Phase 4: Tools ===${NC}"

    # Monitoring
    move_file "continuous_monitor.py" "tools/monitoring/continuous_monitor.py"
    move_file "performance_benchmark.py" "tools/monitoring/performance_benchmark.py"
    move_file "check_structure.py" "tools/monitoring/check_structure.py"
    move_file "check_doc_references.py" "tools/monitoring/check_doc_references.py"

    # Repair
    move_file "auto_repair_loop.py" "tools/repair/auto_repair_loop.py"
    move_file "fix_config_errors.py" "tools/repair/fix_config_errors.py"
    move_file "fix_database_integrity.py" "tools/repair/fix_database_integrity.py"

    # Validation
    move_file "validate_system.py" "tools/validation/validate_system.py"

    # Linting
    move_file "auto_fix_lint.py" "tools/linting/auto_fix_lint.py"
    move_file "fix_f821_imports.py" "tools/linting/fix_f821_imports.py"

    # Setup
    move_file "setup.py" "tools/setup/setup.py"
    move_file "setup_system.py" "tools/setup/setup_system.py"
    move_file "init_demo_db.py" "tools/setup/init_demo_db.py"
    move_file "security_qa_cli.py" "tools/setup/security_qa_cli.py"
    move_file "example_usage.py" "tools/setup/example_usage.py"
    move_file "direct_file_check.py" "tools/setup/direct_file_check.py"
}

# Phase 5: Scripts
phase_5() {
    echo -e "${YELLOW}=== Phase 5: Scripts ===${NC}"

    # Startup scripts (already in scripts/, need to organize into subdirs)
    # Note: This might need manual review as scripts/ already has content
    echo "Note: Shell scripts reorganization may require manual review"

    # Move startup scripts if they exist in root
    move_file "start_mangaanime_web.sh" "scripts/startup/start_web.sh"
    move_file "start_webui_manual.sh" "scripts/startup/start_webui.sh"
    move_file "start-automation.sh" "scripts/startup/start_automation.sh"
    move_file "start-local-repair.sh" "scripts/startup/start_repair.sh"
    move_file "start-repair-background.sh" "scripts/startup/start_repair_bg.sh"
    move_file "start_integrated_ai_development.sh" "scripts/startup/start_ai_dev.sh"
    move_file "quick_start.sh" "scripts/startup/quick_start.sh"
    move_file "run_now.sh" "scripts/startup/run_now.sh"
    move_file "run_claude_autoloop.sh" "scripts/startup/run_claude.sh"

    # Setup scripts
    move_file "setup_cron.sh" "scripts/setup/setup_cron.sh"
    move_file "setup_email.sh" "scripts/setup/setup_email.sh"
    move_file "setup_env.sh" "scripts/setup/setup_env.sh"
    move_file "install_auto_startup.sh" "scripts/setup/install_autostart.sh"
    move_file "install_webui_autostart.sh" "scripts/setup/install_webui_autostart.sh"

    # Maintenance scripts
    move_file "backup_full.sh" "scripts/maintenance/backup_full.sh"
    move_file "run_validation.sh" "scripts/maintenance/validate.sh"
    move_file "check_tests.sh" "scripts/maintenance/check_tests.sh"
    move_file "test-repair-demo.sh" "scripts/maintenance/test_repair.sh"
    move_file "local-repair-system.sh" "scripts/maintenance/repair_system.sh"
    move_file "show_webui_access.sh" "scripts/maintenance/show_access.sh"

    # Archive deprecated Python startup
    move_file "start_web_ui.py" "archive/deprecated/start_web_ui.py"
}

# Phase 6: Data and config
phase_6() {
    echo -e "${YELLOW}=== Phase 6: Data and Config ===${NC}"

    # Reports
    move_file "CRITICAL_FIXES_REPORT.json" "reports/critical_fixes.json"
    move_file "performance-regression-report.json" "reports/performance_regression.json"
    move_file "phase2_test_results.json" "reports/phase2_test_results.json"
    move_file "qa_audit_report.json" "reports/qa_audit.json"
    move_file "security_audit_report.json" "reports/security_audit.json"
    move_file "repair_summary.json" "reports/repair_summary.json"
    move_file "DOC_REFERENCE_REPORT.json" "reports/doc_references.json"

    # Output files
    move_file "coverage_output.txt" "output/coverage.txt"
    move_file "test_results.txt" "output/test_results.txt"
    move_file "test_summary.txt" "output/test_summary.txt"
    move_file "init_output.txt" "output/init_output.txt"
    move_file "temp_file_check.txt" "output/temp_file_check.txt"

    # Database
    if [ "$DRY_RUN" = false ]; then
        if [ -f "db.sqlite3" ]; then
            echo -e "${YELLOW}[WARNING]${NC} Database file will be moved. Creating backup first..."
            cp "db.sqlite3" "db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)"
        fi
    fi
    move_file "db.sqlite3" "data/db.sqlite3"

    # Systemd services
    move_file "local-automation.service" "systemd/local-automation.service"
    move_file "mangaanime-web.service" "systemd/mangaanime-web.service"

    # Database migrations
    move_file "optimize_database.sql" "database/migrations/optimize_database.sql"

    # Archive old versions
    move_file "web_ui.py" "archive/old_versions/web_ui_old.py"
    move_file "Makefile.new" "archive/old_versions/Makefile.new"
}

# Main execution
main() {
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}MangaAnime File Migration Script${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}Running in DRY-RUN mode (no actual changes)${NC}"
        echo ""
    fi

    case $PHASE in
        1)
            phase_1
            ;;
        2)
            phase_2
            ;;
        3)
            phase_3
            ;;
        4)
            phase_4
            ;;
        5)
            phase_5
            ;;
        6)
            phase_6
            ;;
        all)
            phase_1
            echo ""
            phase_2
            echo ""
            phase_3
            echo ""
            phase_4
            echo ""
            phase_5
            echo ""
            phase_6
            ;;
        *)
            echo -e "${RED}Error: Invalid phase: $PHASE${NC}"
            exit 1
            ;;
    esac

    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}Phase $PHASE completed!${NC}"
    echo -e "${GREEN}=========================================${NC}"

    if [ "$DRY_RUN" = false ]; then
        echo ""
        echo -e "${YELLOW}Next steps:${NC}"
        echo "  1. Run: python3 tools/setup/fix_import_paths.py"
        echo "  2. Run: pytest tests/ -v"
        echo "  3. Run: python3 tools/validation/validate_system.py"
    fi
}

main
