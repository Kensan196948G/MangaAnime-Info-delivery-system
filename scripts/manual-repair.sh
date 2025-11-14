#!/bin/bash

# =============================================================================
# Manual Auto-Repair System Trigger
# Allows manual workflow execution and repair operations
# =============================================================================

set -euo pipefail

# Color definitions
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly LOG_DIR="$PROJECT_ROOT/logs"
readonly BACKUP_DIR="$PROJECT_ROOT/backups"
readonly ML_MODELS_DIR="$PROJECT_ROOT/.github/ml-models"
readonly WORKFLOWS_DIR="$PROJECT_ROOT/.github/workflows"

# File paths
readonly REPAIR_LOG="$LOG_DIR/manual_repair.log"
readonly PATTERNS_FILE="$ML_MODELS_DIR/error-patterns.json"
readonly REPAIR_HISTORY="$LOG_DIR/repair_history.json"

# GitHub API configuration
readonly GITHUB_API="https://api.github.com"
readonly REPO_OWNER="${GITHUB_REPOSITORY%/*}"
readonly REPO_NAME="${GITHUB_REPOSITORY#*/}"

# Function to print colored output
print_colored() {
    local color="$1"
    local message="$2"
    echo -e "${color}${message}${NC}"
}

# Function to log messages
log_message() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$REPAIR_LOG"
    
    case "$level" in
        ERROR) print_colored "$RED" "❌ $message" ;;
        SUCCESS) print_colored "$GREEN" "✅ $message" ;;
        WARNING) print_colored "$YELLOW" "⚠️  $message" ;;
        INFO) print_colored "$BLUE" "ℹ️  $message" ;;
        *) echo "$message" ;;
    esac
}

# Function to create backup before repair
create_backup() {
    local backup_name="manual_repair_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Backup critical files
    if [[ -f "$PATTERNS_FILE" ]]; then
        cp "$PATTERNS_FILE" "$backup_path/"
    fi
    
    # Backup workflow files
    if [[ -d "$WORKFLOWS_DIR" ]]; then
        cp -r "$WORKFLOWS_DIR" "$backup_path/"
    fi
    
    # Backup main Python files
    find "$PROJECT_ROOT" -name "*.py" -maxdepth 2 -exec cp {} "$backup_path/" \; 2>/dev/null || true
    
    log_message "INFO" "Backup created at: $backup_path"
    echo "$backup_path"
}

# Function to show available workflows
show_workflows() {
    print_colored "$CYAN" "📋 Available GitHub Workflows:"
    echo
    
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        local workflows
        workflows=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
            "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/actions/workflows" \
            2>/dev/null || echo '{"workflows": []}')
    else
        local workflows
        workflows=$(curl -s \
            "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/actions/workflows" \
            2>/dev/null || echo '{"workflows": []}')
    fi
    
    if [[ "$(echo "$workflows" | jq -r '.workflows // [] | length')" -eq 0 ]]; then
        print_colored "$YELLOW" "⚠️  No workflows found or API unavailable"
        return
    fi
    
    echo "$workflows" | jq -r '.workflows[] | "\(.id) | \(.name) | \(.state)"' | \
    while IFS='|' read -r id name state; do
        case "$state" in
            *active*) color="$GREEN" ;;
            *disabled*) color="$RED" ;;
            *) color="$WHITE" ;;
        esac
        printf "${color}%-10s %-40s %s${NC}\n" "$id" "$name" "$state"
    done
}

# Function to trigger workflow
trigger_workflow() {
    local workflow_id="$1"
    local ref="${2:-main}"
    
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
        log_message "ERROR" "GITHUB_TOKEN not set. Cannot trigger workflows."
        return 1
    fi
    
    log_message "INFO" "Triggering workflow $workflow_id on ref $ref"
    
    local response
    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/actions/workflows/$workflow_id/dispatches" \
        -d "{\"ref\":\"$ref\"}" 2>/dev/null)
    
    local http_code="${response: -3}"
    
    if [[ "$http_code" == "204" ]]; then
        log_message "SUCCESS" "Workflow triggered successfully"
        return 0
    else
        log_message "ERROR" "Failed to trigger workflow. HTTP code: $http_code"
        return 1
    fi
}

# Function to show workflow runs
show_workflow_runs() {
    local limit="${1:-10}"
    
    print_colored "$CYAN" "📊 Recent Workflow Runs (last $limit):"
    echo
    
    local runs
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        runs=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
            "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/actions/runs?per_page=$limit" \
            2>/dev/null || echo '{"workflow_runs": []}')
    else
        runs=$(curl -s \
            "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/actions/runs?per_page=$limit" \
            2>/dev/null || echo '{"workflow_runs": []}')
    fi
    
    if [[ "$(echo "$runs" | jq -r '.workflow_runs // [] | length')" -eq 0 ]]; then
        print_colored "$YELLOW" "⚠️  No workflow runs found"
        return
    fi
    
    printf "%-20s %-30s %-15s %-10s\n" "DATE" "WORKFLOW" "STATUS" "DURATION"
    echo "--------------------------------------------------------------------------------"
    
    echo "$runs" | jq -r '.workflow_runs[] | 
        "\(.created_at) | \(.name) | \(.conclusion // .status) | \(.run_number)"' | \
    while IFS='|' read -r date name status run_num; do
        case "$status" in
            *success*) color="$GREEN" ;;
            *failure*) color="$RED" ;;
            *in_progress*) color="$YELLOW" ;;
            *cancelled*) color="$PURPLE" ;;
            *) color="$WHITE" ;;
        esac
        printf "${color}%-20s %-30s %-15s %-10s${NC}\n" \
            "$(echo "$date" | cut -d'T' -f1)" \
            "$(echo "$name" | cut -c1-28)" \
            "$status" \
            "$run_num"
    done
}

# Function to analyze recent failures
analyze_failures() {
    print_colored "$CYAN" "🔍 Analyzing Recent Failures:"
    echo
    
    local runs
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        runs=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
            "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/actions/runs?status=failure&per_page=20" \
            2>/dev/null || echo '{"workflow_runs": []}')
    else
        runs=$(curl -s \
            "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/actions/runs?status=failure&per_page=20" \
            2>/dev/null || echo '{"workflow_runs": []}')
    fi
    
    local failure_count
    failure_count=$(echo "$runs" | jq -r '.workflow_runs // [] | length')
    
    if [[ "$failure_count" -eq 0 ]]; then
        print_colored "$GREEN" "✅ No recent failures found!"
        return
    fi
    
    print_colored "$RED" "Found $failure_count recent failures:"
    
    # Analyze common failure patterns
    local patterns=()
    echo "$runs" | jq -r '.workflow_runs[].name' | sort | uniq -c | sort -nr | head -5 | \
    while read -r count workflow; do
        print_colored "$YELLOW" "  • $workflow: $count failures"
    done
    
    # Show most recent failure details
    local latest_failure
    latest_failure=$(echo "$runs" | jq -r '.workflow_runs[0]')
    
    if [[ "$latest_failure" != "null" ]]; then
        echo
        print_colored "$WHITE" "Most Recent Failure:"
        echo "$latest_failure" | jq -r '"  Workflow: \(.name)
  Date: \(.created_at)
  URL: \(.html_url)"'
    fi
}

# Function to apply error pattern repair
apply_pattern_repair() {
    local pattern_id="$1"
    local target_file="${2:-}"
    
    if [[ ! -f "$PATTERNS_FILE" ]]; then
        log_message "ERROR" "Error patterns file not found"
        return 1
    fi
    
    # Get pattern details
    local pattern_data
    pattern_data=$(jq -r --arg id "$pattern_id" '
        .error_categories[] | .patterns[] | select(.id == $id)' "$PATTERNS_FILE" 2>/dev/null)
    
    if [[ -z "$pattern_data" || "$pattern_data" == "null" ]]; then
        log_message "ERROR" "Pattern ID $pattern_id not found"
        return 1
    fi
    
    local pattern_name
    pattern_name=$(echo "$pattern_data" | jq -r '.name')
    
    log_message "INFO" "Applying repair pattern: $pattern_name"
    
    # Get repair strategies
    local strategies
    strategies=$(echo "$pattern_data" | jq -r '.repair_strategies[]')
    
    echo "$strategies" | jq -r '. | "\(.priority) | \(.action) | \(.command)"' | \
    sort -n | while IFS='|' read -r priority action command; do
        log_message "INFO" "Executing repair action: $action"
        
        # Replace placeholders in command
        local final_command="$command"
        if [[ -n "$target_file" ]]; then
            final_command="${final_command//\{file\}/$target_file}"
        fi
        
        # Execute command with safety checks
        if [[ "$action" == "fix_permissions" ]]; then
            if [[ -f "$target_file" ]]; then
                chmod +x "$target_file"
                log_message "SUCCESS" "Fixed permissions for $target_file"
            fi
        elif [[ "$action" == "install_package" ]]; then
            # Extract package name from command
            local package_name
            package_name=$(echo "$final_command" | grep -o 'pip install [^[:space:]]*' | cut -d' ' -f3)
            if [[ -n "$package_name" ]]; then
                pip install "$package_name"
                log_message "SUCCESS" "Installed package: $package_name"
            fi
        else
            # Generic command execution with timeout
            timeout 300 bash -c "$final_command" 2>&1 | head -20 || \
                log_message "WARNING" "Command execution failed or timed out"
        fi
    done
    
    # Update pattern usage statistics
    local updated_patterns
    updated_patterns=$(jq --arg id "$pattern_id" '
        (.error_categories[] | .patterns[] | select(.id == $id) | .uses) += 1 |
        .last_updated = now | strftime("%Y-%m-%dT%H:%M:%SZ")' "$PATTERNS_FILE")
    
    echo "$updated_patterns" > "$PATTERNS_FILE"
    log_message "SUCCESS" "Pattern repair completed for: $pattern_name"
}

# Function to show available patterns
show_patterns() {
    if [[ ! -f "$PATTERNS_FILE" ]]; then
        print_colored "$RED" "❌ Error patterns file not found"
        return 1
    fi
    
    print_colored "$CYAN" "🎯 Available Error Patterns:"
    echo
    
    printf "%-10s %-20s %-30s %-10s\n" "ID" "CATEGORY" "NAME" "SUCCESS%"
    echo "--------------------------------------------------------------------------------"
    
    jq -r '.error_categories | to_entries[] | 
           .key as $category | 
           .value.patterns[] | 
           "\(.id) | \($category) | \(.name) | \(.success_rate * 100 | floor)"' \
           "$PATTERNS_FILE" | \
    while IFS='|' read -r id category name success; do
        if [[ "$success" -gt 80 ]]; then
            color="$GREEN"
        elif [[ "$success" -gt 60 ]]; then
            color="$YELLOW"
        else
            color="$RED"
        fi
        printf "${color}%-10s %-20s %-30s %-10s${NC}\n" "$id" "$category" "$name" "$success%"
    done
}

# Function to rollback recent changes
rollback_changes() {
    local backup_dir="$1"
    
    if [[ ! -d "$backup_dir" ]]; then
        log_message "ERROR" "Backup directory not found: $backup_dir"
        return 1
    fi
    
    log_message "INFO" "Rolling back changes from backup: $backup_dir"
    
    # Restore pattern file
    if [[ -f "$backup_dir/error-patterns.json" ]]; then
        cp "$backup_dir/error-patterns.json" "$PATTERNS_FILE"
        log_message "SUCCESS" "Restored error patterns file"
    fi
    
    # Restore workflow files
    if [[ -d "$backup_dir/workflows" ]]; then
        rm -rf "$WORKFLOWS_DIR"
        cp -r "$backup_dir/workflows" "$WORKFLOWS_DIR"
        log_message "SUCCESS" "Restored workflow files"
    fi
    
    log_message "SUCCESS" "Rollback completed"
}

# Function to show repair history
show_repair_history() {
    local limit="${1:-10}"
    
    print_colored "$CYAN" "📜 Repair History (last $limit entries):"
    echo
    
    if [[ ! -f "$REPAIR_LOG" ]]; then
        print_colored "$YELLOW" "⚠️  No repair history found"
        return
    fi
    
    tail -n "$limit" "$REPAIR_LOG" | while IFS= read -r line; do
        case "$line" in
            *ERROR*) print_colored "$RED" "$line" ;;
            *SUCCESS*) print_colored "$GREEN" "$line" ;;
            *WARNING*) print_colored "$YELLOW" "$line" ;;
            *INFO*) print_colored "$BLUE" "$line" ;;
            *) echo "$line" ;;
        esac
    done
}

# Function to show interactive menu
show_menu() {
    clear
    print_colored "$CYAN" "╔══════════════════════════════════════════════════════════════════════════════╗"
    print_colored "$CYAN" "║                          Manual Repair System                               ║"
    print_colored "$CYAN" "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo
    print_colored "$WHITE" "Available Actions:"
    print_colored "$GREEN" "1. Show Workflows"
    print_colored "$GREEN" "2. Trigger Workflow"
    print_colored "$GREEN" "3. Show Workflow Runs"
    print_colored "$GREEN" "4. Analyze Failures"
    print_colored "$GREEN" "5. Show Error Patterns"
    print_colored "$GREEN" "6. Apply Pattern Repair"
    print_colored "$GREEN" "7. Show Repair History"
    print_colored "$GREEN" "8. Create Backup"
    print_colored "$GREEN" "9. Rollback Changes"
    print_colored "$RED" "0. Exit"
    echo
}

# Function to run interactive mode
interactive_mode() {
    while true; do
        show_menu
        read -p "Select an option (0-9): " choice
        echo
        
        case "$choice" in
            1)
                show_workflows
                read -p "Press Enter to continue..."
                ;;
            2)
                show_workflows
                echo
                read -p "Enter workflow ID to trigger: " workflow_id
                if [[ -n "$workflow_id" ]]; then
                    trigger_workflow "$workflow_id"
                fi
                read -p "Press Enter to continue..."
                ;;
            3)
                read -p "Number of runs to show (default 10): " limit
                show_workflow_runs "${limit:-10}"
                read -p "Press Enter to continue..."
                ;;
            4)
                analyze_failures
                read -p "Press Enter to continue..."
                ;;
            5)
                show_patterns
                read -p "Press Enter to continue..."
                ;;
            6)
                show_patterns
                echo
                read -p "Enter pattern ID to apply: " pattern_id
                read -p "Enter target file (optional): " target_file
                if [[ -n "$pattern_id" ]]; then
                    apply_pattern_repair "$pattern_id" "$target_file"
                fi
                read -p "Press Enter to continue..."
                ;;
            7)
                read -p "Number of entries to show (default 10): " limit
                show_repair_history "${limit:-10}"
                read -p "Press Enter to continue..."
                ;;
            8)
                backup_path=$(create_backup)
                print_colored "$GREEN" "✅ Backup created: $backup_path"
                read -p "Press Enter to continue..."
                ;;
            9)
                read -p "Enter backup directory path: " backup_dir
                if [[ -n "$backup_dir" ]]; then
                    rollback_changes "$backup_dir"
                fi
                read -p "Press Enter to continue..."
                ;;
            0)
                print_colored "$GREEN" "👋 Goodbye!"
                break
                ;;
            *)
                print_colored "$RED" "❌ Invalid option. Please try again."
                sleep 2
                ;;
        esac
    done
}

# Function to show help
show_help() {
    cat << EOF
Manual Auto-Repair System

Usage: $0 [COMMAND] [OPTIONS]

COMMANDS:
    interactive         Start interactive mode (default)
    workflows           Show available workflows
    trigger ID [REF]    Trigger workflow by ID
    runs [LIMIT]        Show recent workflow runs
    failures            Analyze recent failures
    patterns            Show available error patterns
    apply ID [FILE]     Apply error pattern repair
    history [LIMIT]     Show repair history
    backup              Create backup
    rollback DIR        Rollback from backup directory

OPTIONS:
    --help              Show this help message

EXAMPLES:
    $0                  # Start interactive mode
    $0 workflows        # Show workflows
    $0 trigger 12345    # Trigger workflow ID 12345
    $0 apply dep_001 file.py  # Apply dependency pattern to file.py

ENVIRONMENT:
    GITHUB_TOKEN        Required for triggering workflows
    GITHUB_REPOSITORY   Repository in format owner/repo

EOF
}

# Main execution function
main() {
    # Create necessary directories
    mkdir -p "$LOG_DIR" "$BACKUP_DIR"
    
    # Initialize log file
    if [[ ! -f "$REPAIR_LOG" ]]; then
        touch "$REPAIR_LOG"
    fi
    
    local command="${1:-interactive}"
    
    case "$command" in
        interactive|"")
            interactive_mode
            ;;
        workflows)
            show_workflows
            ;;
        trigger)
            if [[ -z "${2:-}" ]]; then
                log_message "ERROR" "Workflow ID required"
                exit 1
            fi
            trigger_workflow "$2" "${3:-main}"
            ;;
        runs)
            show_workflow_runs "${2:-10}"
            ;;
        failures)
            analyze_failures
            ;;
        patterns)
            show_patterns
            ;;
        apply)
            if [[ -z "${2:-}" ]]; then
                log_message "ERROR" "Pattern ID required"
                exit 1
            fi
            apply_pattern_repair "$2" "${3:-}"
            ;;
        history)
            show_repair_history "${2:-10}"
            ;;
        backup)
            create_backup
            ;;
        rollback)
            if [[ -z "${2:-}" ]]; then
                log_message "ERROR" "Backup directory required"
                exit 1
            fi
            rollback_changes "$2"
            ;;
        --help)
            show_help
            ;;
        *)
            print_colored "$RED" "❌ Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    if ! command -v jq &> /dev/null; then
        missing_deps+=("jq")
    fi
    
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    if [[ "${#missing_deps[@]}" -gt 0 ]]; then
        print_colored "$RED" "❌ Missing dependencies: ${missing_deps[*]}"
        print_colored "$YELLOW" "Please install them first:"
        print_colored "$WHITE" "   sudo apt-get install ${missing_deps[*]}"
        exit 1
    fi
}

# Set up GitHub repository info if not set
if [[ -z "${GITHUB_REPOSITORY:-}" ]]; then
    if [[ -d "$PROJECT_ROOT/.git" ]]; then
        GITHUB_REPOSITORY=$(git -C "$PROJECT_ROOT" remote get-url origin 2>/dev/null | \
                           sed 's/.*github\.com[:/]\([^.]*\)\.git/\1/' || echo "")
        export GITHUB_REPOSITORY
    fi
fi

# Run dependency check and main function
check_dependencies
main "$@"