#!/bin/bash

# =============================================================================
# Auto-Repair System Monitor
# Real-time monitoring of workflow status and repair statistics
# =============================================================================

set -euo pipefail

# Color definitions for output
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
readonly METRICS_FILE="$LOG_DIR/repair_metrics.json"
readonly STATUS_FILE="$LOG_DIR/system_status.json"

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

# Function to print section headers
print_header() {
    local title="$1"
    echo
    print_colored "$CYAN" "╔══════════════════════════════════════════════════════════════════════════════╗"
    printf "${CYAN}║${NC} %-76s ${CYAN}║${NC}\n" "$title"
    print_colored "$CYAN" "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo
}

# Function to check GitHub API rate limit
check_rate_limit() {
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        local rate_limit
        rate_limit=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
            "$GITHUB_API/rate_limit" | jq -r '.rate.remaining // 0')
        
        if [[ "$rate_limit" -lt 10 ]]; then
            print_colored "$YELLOW" "⚠️  GitHub API rate limit low: $rate_limit requests remaining"
        else
            print_colored "$GREEN" "✅ GitHub API rate limit: $rate_limit requests remaining"
        fi
    else
        print_colored "$YELLOW" "⚠️  GITHUB_TOKEN not set - using unauthenticated requests"
    fi
}

# Function to get workflow status
get_workflow_status() {
    local workflow_runs
    local status_counts
    
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        workflow_runs=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
            "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/actions/runs?per_page=20" \
            | jq -r '.workflow_runs[]' 2>/dev/null || echo "[]")
    else
        workflow_runs=$(curl -s \
            "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/actions/runs?per_page=20" \
            | jq -r '.workflow_runs[]' 2>/dev/null || echo "[]")
    fi
    
    if [[ "$workflow_runs" == "[]" ]]; then
        print_colored "$YELLOW" "📊 No recent workflow runs found"
        return
    fi
    
    # Count statuses
    local success_count failed_count in_progress_count
    success_count=$(echo "$workflow_runs" | jq -s '[.[] | select(.conclusion == "success")] | length' 2>/dev/null || echo "0")
    failed_count=$(echo "$workflow_runs" | jq -s '[.[] | select(.conclusion == "failure")] | length' 2>/dev/null || echo "0")
    in_progress_count=$(echo "$workflow_runs" | jq -s '[.[] | select(.status == "in_progress")] | length' 2>/dev/null || echo "0")
    
    print_colored "$GREEN" "✅ Successful runs: $success_count"
    print_colored "$RED" "❌ Failed runs: $failed_count"
    print_colored "$YELLOW" "🔄 In progress: $in_progress_count"
    
    # Show recent runs
    echo
    print_colored "$WHITE" "Recent Workflow Runs:"
    echo "$workflow_runs" | jq -s '.[:5]' | jq -r '.[] | 
        "\(.created_at) | \(.name) | \(.conclusion // .status) | \(.html_url)"' 2>/dev/null | \
    while IFS='|' read -r date name status url; do
        case "$status" in
            *success*) color="$GREEN" ;;
            *failure*) color="$RED" ;;
            *in_progress*) color="$YELLOW" ;;
            *) color="$WHITE" ;;
        esac
        printf "${color}%-20s %-30s %-15s${NC}\n" "$date" "$name" "$status"
    done || print_colored "$YELLOW" "Unable to parse workflow data"
}

# Function to display repair statistics
show_repair_stats() {
    if [[ -f "$METRICS_FILE" ]]; then
        local total_attempts successful_repairs success_rate
        total_attempts=$(jq -r '.total_repair_attempts // 0' "$METRICS_FILE")
        successful_repairs=$(jq -r '.successful_repairs // 0' "$METRICS_FILE")
        
        if [[ "$total_attempts" -gt 0 ]]; then
            success_rate=$(echo "scale=2; $successful_repairs * 100 / $total_attempts" | bc)
        else
            success_rate="0.00"
        fi
        
        print_colored "$WHITE" "📈 Repair Statistics:"
        print_colored "$BLUE" "   Total repair attempts: $total_attempts"
        print_colored "$GREEN" "   Successful repairs: $successful_repairs"
        print_colored "$PURPLE" "   Success rate: ${success_rate}%"
        
        # Show error pattern effectiveness
        local patterns
        patterns=$(jq -r '.pattern_effectiveness // {}' "$METRICS_FILE")
        if [[ "$patterns" != "{}" ]]; then
            echo
            print_colored "$WHITE" "🎯 Most Effective Patterns:"
            echo "$patterns" | jq -r 'to_entries | sort_by(.value.success_rate) | reverse | .[:3][] | 
                "   \(.key): \(.value.success_rate * 100 | floor)% success rate (\(.value.uses) uses)"'
        fi
    else
        print_colored "$YELLOW" "📊 No repair statistics available yet"
    fi
}

# Function to check system health
check_system_health() {
    local health_score=100
    local issues=()
    
    # Check disk space
    local disk_usage
    disk_usage=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ "$disk_usage" -gt 90 ]]; then
        health_score=$((health_score - 20))
        issues+=("High disk usage: ${disk_usage}%")
    fi
    
    # Check log file sizes
    if [[ -d "$LOG_DIR" ]]; then
        local log_size
        log_size=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1 || echo "0K")
        if [[ "${log_size%M}" -gt 100 ]] 2>/dev/null; then
            health_score=$((health_score - 10))
            issues+=("Large log directory: $log_size")
        fi
    fi
    
    # Check for stuck processes
    local repair_processes
    repair_processes=$(pgrep -f "auto-repair" | wc -l)
    if [[ "$repair_processes" -gt 3 ]]; then
        health_score=$((health_score - 15))
        issues+=("Multiple repair processes running: $repair_processes")
    fi
    
    # Display health status
    if [[ "$health_score" -gt 80 ]]; then
        print_colored "$GREEN" "💚 System Health: Excellent ($health_score/100)"
    elif [[ "$health_score" -gt 60 ]]; then
        print_colored "$YELLOW" "💛 System Health: Good ($health_score/100)"
    elif [[ "$health_score" -gt 40 ]]; then
        print_colored "$YELLOW" "🧡 System Health: Fair ($health_score/100)"
    else
        print_colored "$RED" "❤️  System Health: Poor ($health_score/100)"
    fi
    
    if [[ "${#issues[@]}" -gt 0 ]]; then
        echo
        print_colored "$WHITE" "⚠️  Issues detected:"
        for issue in "${issues[@]}"; do
            print_colored "$YELLOW" "   • $issue"
        done
    fi
}

# Function to display recent logs
show_recent_logs() {
    local log_file="$LOG_DIR/auto_repair.log"
    
    if [[ -f "$log_file" ]]; then
        print_colored "$WHITE" "📝 Recent Log Entries (last 10):"
        echo
        tail -n 10 "$log_file" | while IFS= read -r line; do
            case "$line" in
                *ERROR*) print_colored "$RED" "$line" ;;
                *SUCCESS*) print_colored "$GREEN" "$line" ;;
                *WARNING*) print_colored "$YELLOW" "$line" ;;
                *INFO*) print_colored "$BLUE" "$line" ;;
                *) echo "$line" ;;
            esac
        done
    else
        print_colored "$YELLOW" "📝 No log file found at $log_file"
    fi
}

# Function to display real-time monitoring
real_time_monitor() {
    print_header "🔄 Real-time Auto-Repair System Monitor"
    
    while true; do
        clear
        print_header "🔄 Auto-Repair System Monitor - $(date '+%Y-%m-%d %H:%M:%S')"
        
        check_rate_limit
        echo
        
        print_colored "$WHITE" "📊 Workflow Status:"
        get_workflow_status
        echo
        
        show_repair_stats
        echo
        
        check_system_health
        echo
        
        show_recent_logs
        
        print_colored "$CYAN" "\n🔄 Refreshing in 30 seconds... (Press Ctrl+C to exit)"
        sleep 30
    done
}

# Function to display help
show_help() {
    cat << EOF
Auto-Repair System Monitor

Usage: $0 [OPTIONS]

OPTIONS:
    -r, --realtime     Start real-time monitoring (default)
    -s, --status       Show current status only
    -h, --health       Check system health only
    -l, --logs         Show recent logs only
    --help             Show this help message

EXAMPLES:
    $0                 # Start real-time monitoring
    $0 --status        # Show current status
    $0 --health        # Check system health
    $0 --logs          # Show recent logs

EOF
}

# Main execution
main() {
    # Create log directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    case "${1:-}" in
        -r|--realtime|"")
            real_time_monitor
            ;;
        -s|--status)
            print_header "📊 Current System Status"
            check_rate_limit
            get_workflow_status
            show_repair_stats
            ;;
        -h|--health)
            print_header "💚 System Health Check"
            check_system_health
            ;;
        -l|--logs)
            print_header "📝 Recent Logs"
            show_recent_logs
            ;;
        --help)
            show_help
            ;;
        *)
            print_colored "$RED" "❌ Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Trap Ctrl+C for clean exit
trap 'print_colored "$YELLOW" "\n👋 Monitoring stopped."; exit 0' INT

# Check dependencies
if ! command -v jq &> /dev/null; then
    print_colored "$RED" "❌ jq is required but not installed. Please install it first."
    exit 1
fi

if ! command -v bc &> /dev/null; then
    print_colored "$RED" "❌ bc is required but not installed. Please install it first."
    exit 1
fi

# Run main function with all arguments
main "$@"