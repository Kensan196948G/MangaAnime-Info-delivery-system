#!/bin/bash

# Auto-Repair System Management Script
# Usage: ./manage-repair-system.sh [command] [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_DIR="$PROJECT_ROOT/.github/repair-state"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if jq is available
check_dependencies() {
    if ! command -v jq &> /dev/null; then
        print_error "jq is required but not installed. Please install jq first."
        exit 1
    fi
    
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is required but not installed. Please install gh first."
        exit 1
    fi
}

# Function to show current system status
show_status() {
    print_status "Auto-Repair System Status"
    echo "=========================="
    
    if [[ -f "$STATE_DIR/loop-state.json" ]]; then
        local iteration=$(jq -r '.iteration // 0' "$STATE_DIR/loop-state.json")
        local last_run=$(jq -r '.last_run // "never"' "$STATE_DIR/loop-state.json")
        local total_repairs=$(jq -r '.total_repairs // 0' "$STATE_DIR/loop-state.json")
        
        echo "Current Iteration: $iteration/10"
        echo "Last Run: $last_run"
        echo "Total Repairs: $total_repairs"
    else
        print_warning "Loop state file not found"
    fi
    
    if [[ -f "$STATE_DIR/repair-history.json" ]]; then
        local success_rate=$(jq -r '.success_rate // 0' "$STATE_DIR/repair-history.json")
        local total_attempts=$(jq -r '.total_repairs // 0' "$STATE_DIR/repair-history.json")
        
        echo "Success Rate: $success_rate%"
        echo "Total Attempts: $total_attempts"
    fi
    
    echo ""
    print_status "Recent Failed Workflows:"
    gh run list --status failure --limit 5 --json workflowName,createdAt,conclusion | \
        jq -r '.[] | "- \(.workflowName) (\(.conclusion), \(.createdAt))"' || \
        print_warning "Could not fetch workflow status"
}

# Function to reset the loop system
reset_loop() {
    print_status "Resetting auto-repair loop system..."
    
    # Reset loop state
    if [[ -f "$STATE_DIR/loop-state.json" ]]; then
        jq '.iteration = 0 | .start_time = "" | .last_run = ""' "$STATE_DIR/loop-state.json" > "$STATE_DIR/loop-state.json.tmp"
        mv "$STATE_DIR/loop-state.json.tmp" "$STATE_DIR/loop-state.json"
        print_success "Loop state reset"
    fi
    
    # Optionally reset history (with confirmation)
    if [[ "$1" == "--clear-history" ]]; then
        read -p "Are you sure you want to clear repair history? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo '{"repairs": [], "total_repairs": 0, "success_rate": 0, "statistics": {"by_error_type": {}, "by_strategy": {}, "by_month": {}}}' > "$STATE_DIR/repair-history.json"
            print_success "Repair history cleared"
        fi
    fi
}

# Function to trigger workflows
trigger_workflow() {
    local workflow_name="$1"
    local args="${@:2}"
    
    print_status "Triggering workflow: $workflow_name"
    
    case "$workflow_name" in
        "loop"|"auto-repair")
            gh workflow run auto-repair-loop.yml $args
            ;;
        "verify")
            gh workflow run verify-repair.yml $args
            ;;
        "repair")
            if [[ -z "$2" ]]; then
                print_error "Run ID required for repair workflow"
                exit 1
            fi
            gh workflow run parallel-repair.yml --field run_id="$2" --field iteration="1"
            ;;
        *)
            print_error "Unknown workflow: $workflow_name"
            print_status "Available workflows: loop, verify, repair"
            exit 1
            ;;
    esac
    
    print_success "Workflow triggered successfully"
}

# Function to show repair history
show_history() {
    local limit="${1:-10}"
    
    print_status "Recent Repair History (last $limit entries):"
    echo "=============================================="
    
    if [[ -f "$STATE_DIR/repair-history.json" ]]; then
        jq -r --arg limit "$limit" '
            .repairs[-($limit | tonumber):] | 
            .[] | 
            "\(.timestamp) | \(.error_type) | \(if .success then "✅ SUCCESS" else "❌ FAILED" end) | Run #\(.run_id)"
        ' "$STATE_DIR/repair-history.json" | column -t -s '|'
    else
        print_warning "No repair history found"
    fi
}

# Function to show error patterns
show_patterns() {
    print_status "Error Pattern Analysis:"
    echo "======================="
    
    if [[ -f "$STATE_DIR/error-patterns.json" ]]; then
        jq -r '
            .patterns | 
            to_entries | 
            map("\(.key): \(.value.count) occurrences") | 
            .[]
        ' "$STATE_DIR/error-patterns.json"
    else
        print_warning "No error patterns found"
    fi
}

# Function to check system health
health_check() {
    print_status "Performing system health check..."
    echo "================================"
    
    local issues=0
    
    # Check if state files exist
    for file in "loop-state.json" "repair-history.json" "error-patterns.json"; do
        if [[ ! -f "$STATE_DIR/$file" ]]; then
            print_error "Missing state file: $file"
            issues=$((issues + 1))
        else
            # Validate JSON
            if ! jq empty "$STATE_DIR/$file" 2>/dev/null; then
                print_error "Invalid JSON in: $file"
                issues=$((issues + 1))
            else
                print_success "State file OK: $file"
            fi
        fi
    done
    
    # Check GitHub CLI auth
    if gh auth status &>/dev/null; then
        print_success "GitHub CLI authenticated"
    else
        print_error "GitHub CLI not authenticated"
        issues=$((issues + 1))
    fi
    
    # Check for workflow files
    for workflow in "auto-repair-loop.yml" "parallel-repair.yml" "verify-repair.yml"; do
        if [[ -f "$PROJECT_ROOT/.github/workflows/$workflow" ]]; then
            print_success "Workflow file OK: $workflow"
        else
            print_error "Missing workflow file: $workflow"
            issues=$((issues + 1))
        fi
    done
    
    echo ""
    if [[ $issues -eq 0 ]]; then
        print_success "System health check passed!"
    else
        print_error "System health check failed with $issues issues"
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "Auto-Repair System Management Script"
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  status                    Show current system status"
    echo "  reset [--clear-history]   Reset loop iteration (optionally clear history)"
    echo "  trigger <workflow> [args] Trigger a specific workflow"
    echo "  history [limit]           Show repair history (default: 10 entries)"
    echo "  patterns                  Show error pattern analysis"
    echo "  health                    Perform system health check"
    echo "  help                      Show this help message"
    echo ""
    echo "Workflow options for 'trigger':"
    echo "  loop                      Trigger auto-repair loop"
    echo "  verify                    Trigger verification workflow"
    echo "  repair <run_id>           Trigger repair for specific run ID"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 reset"
    echo "  $0 trigger loop --field force_reset=true"
    echo "  $0 history 20"
    echo "  $0 health"
}

# Main script logic
main() {
    check_dependencies
    
    case "${1:-help}" in
        "status")
            show_status
            ;;
        "reset")
            reset_loop "$2"
            ;;
        "trigger")
            trigger_workflow "${@:2}"
            ;;
        "history")
            show_history "$2"
            ;;
        "patterns")
            show_patterns
            ;;
        "health")
            health_check
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"