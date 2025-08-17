#!/bin/bash

# Real-time monitoring script for 30-minute auto-repair loop
# Usage: ./monitor-30min-loop.sh [--refresh-interval SECONDS]

set -euo pipefail

# Default configuration
REFRESH_INTERVAL=10
STATE_FILE="$(dirname "$0")/../.github/repair-state/loop-state.json"
LOG_DIR="$(dirname "$0")/../.github/logs"
WORKFLOW_DIR="$(dirname "$0")/../.github/workflows"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --refresh-interval)
            REFRESH_INTERVAL="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--refresh-interval SECONDS]"
            echo "Monitor the 30-minute auto-repair loop in real-time"
            echo ""
            echo "Options:"
            echo "  --refresh-interval SECONDS  Set refresh interval (default: 10)"
            echo "  -h, --help                  Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to display header
show_header() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                     30-Minute Auto-Repair Loop Monitor                      ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${CYAN}Last updated: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""
}

# Function to get current loop status
get_loop_status() {
    if [[ -f "$STATE_FILE" ]]; then
        local state=$(cat "$STATE_FILE" 2>/dev/null || echo '{}')
        local current_iteration=$(echo "$state" | jq -r '.current_iteration // 0' 2>/dev/null || echo "0")
        local start_time=$(echo "$state" | jq -r '.start_time // "unknown"' 2>/dev/null || echo "unknown")
        local last_repair=$(echo "$state" | jq -r '.last_repair_time // "never"' 2>/dev/null || echo "never")
        local total_repairs=$(echo "$state" | jq -r '.total_repairs // 0' 2>/dev/null || echo "0")
        local successful_repairs=$(echo "$state" | jq -r '.successful_repairs // 0' 2>/dev/null || echo "0")
        local failed_repairs=$(echo "$state" | jq -r '.failed_repairs // 0' 2>/dev/null || echo "0")
        
        echo -e "${YELLOW}📊 LOOP STATUS${NC}"
        echo -e "   Current Iteration: ${GREEN}$current_iteration${NC}/210 (30 min × 7 cycles)"
        echo -e "   Loop Start Time:   ${CYAN}$start_time${NC}"
        echo -e "   Last Repair:       ${CYAN}$last_repair${NC}"
        echo -e "   Total Repairs:     ${BLUE}$total_repairs${NC}"
        echo -e "   Successful:        ${GREEN}$successful_repairs${NC}"
        echo -e "   Failed:            ${RED}$failed_repairs${NC}"
        
        if [[ "$total_repairs" -gt 0 ]]; then
            local success_rate=$(echo "scale=1; $successful_repairs * 100 / $total_repairs" | bc 2>/dev/null || echo "0")
            echo -e "   Success Rate:      ${GREEN}${success_rate}%${NC}"
        fi
    else
        echo -e "${RED}❌ No state file found - Loop may not be running${NC}"
    fi
    echo ""
}

# Function to check GitHub Actions status
check_github_actions() {
    echo -e "${YELLOW}🔄 GITHUB ACTIONS STATUS${NC}"
    
    # Check if GitHub CLI is available
    if ! command -v gh &> /dev/null; then
        echo -e "   ${RED}GitHub CLI not installed - Cannot check workflow status${NC}"
        echo ""
        return
    fi
    
    # Get recent workflow runs
    local workflow_runs=$(gh run list --limit 5 --json status,conclusion,workflowName,createdAt 2>/dev/null || echo "[]")
    
    if [[ "$workflow_runs" == "[]" ]]; then
        echo -e "   ${YELLOW}No recent workflow runs found${NC}"
    else
        echo "$workflow_runs" | jq -r '.[] | "   \(.workflowName): \(.status) (\(.conclusion // "running")) - \(.createdAt)"' | while read line; do
            if [[ "$line" == *"success"* ]]; then
                echo -e "   ${GREEN}✅ $line${NC}"
            elif [[ "$line" == *"failure"* ]]; then
                echo -e "   ${RED}❌ $line${NC}"
            elif [[ "$line" == *"running"* ]]; then
                echo -e "   ${BLUE}🔄 $line${NC}"
            else
                echo -e "   ${YELLOW}⏳ $line${NC}"
            fi
        done
    fi
    echo ""
}

# Function to check active repairs
check_active_repairs() {
    echo -e "${YELLOW}🔧 ACTIVE REPAIRS${NC}"
    
    local active_count=0
    
    # Check for running workflow processes
    local gh_processes=$(pgrep -f "gh.*workflow.*run" 2>/dev/null || true)
    if [[ -n "$gh_processes" ]]; then
        echo -e "   ${BLUE}🔄 GitHub workflow execution detected${NC}"
        active_count=$((active_count + 1))
    fi
    
    # Check for repair lock files
    if [[ -f "../.repair_lock" ]]; then
        local lock_time=$(stat -c %Y "../.repair_lock" 2>/dev/null || echo "0")
        local current_time=$(date +%s)
        local lock_age=$((current_time - lock_time))
        
        if [[ $lock_age -lt 1800 ]]; then # 30 minutes
            echo -e "   ${YELLOW}🔒 Repair lock active (${lock_age}s ago)${NC}"
            active_count=$((active_count + 1))
        else
            echo -e "   ${RED}⚠️  Stale repair lock detected (${lock_age}s old)${NC}"
        fi
    fi
    
    if [[ $active_count -eq 0 ]]; then
        echo -e "   ${GREEN}✅ No active repairs${NC}"
    fi
    echo ""
}

# Function to show recent logs
show_recent_logs() {
    echo -e "${YELLOW}📋 RECENT ACTIVITY${NC}"
    
    if [[ -d "$LOG_DIR" ]]; then
        local latest_log=$(find "$LOG_DIR" -name "*.log" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2- || echo "")
        
        if [[ -n "$latest_log" ]]; then
            echo -e "   Latest log: ${CYAN}$(basename "$latest_log")${NC}"
            echo "   Last 5 entries:"
            tail -5 "$latest_log" 2>/dev/null | sed 's/^/     /' || echo "     No log entries found"
        else
            echo -e "   ${YELLOW}No log files found${NC}"
        fi
    else
        echo -e "   ${YELLOW}Log directory not found${NC}"
    fi
    echo ""
}

# Function to show system resources
show_system_resources() {
    echo -e "${YELLOW}💻 SYSTEM RESOURCES${NC}"
    
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//' || echo "unknown")
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}' || echo "unknown")
    local disk_usage=$(df . | tail -1 | awk '{print $5}' | sed 's/%//' || echo "unknown")
    
    echo -e "   CPU Usage:    ${GREEN}${cpu_usage}%${NC}"
    echo -e "   Memory Usage: ${GREEN}${memory_usage}%${NC}"
    echo -e "   Disk Usage:   ${GREEN}${disk_usage}%${NC}"
    echo ""
}

# Function to show workflow health
show_workflow_health() {
    echo -e "${YELLOW}⚕️  WORKFLOW HEALTH${NC}"
    
    local workflow_count=0
    local healthy_count=0
    
    if [[ -d "$WORKFLOW_DIR" ]]; then
        for workflow in "$WORKFLOW_DIR"/*.yml "$WORKFLOW_DIR"/*.yaml; do
            if [[ -f "$workflow" ]]; then
                workflow_count=$((workflow_count + 1))
                local workflow_name=$(basename "$workflow")
                
                # Basic syntax check
                if python3 -c "import yaml; yaml.safe_load(open('$workflow'))" 2>/dev/null; then
                    echo -e "   ${GREEN}✅ $workflow_name${NC}"
                    healthy_count=$((healthy_count + 1))
                else
                    echo -e "   ${RED}❌ $workflow_name (syntax error)${NC}"
                fi
            fi
        done
    fi
    
    if [[ $workflow_count -eq 0 ]]; then
        echo -e "   ${YELLOW}No workflows found${NC}"
    else
        echo -e "   Health: ${healthy_count}/${workflow_count} workflows OK"
    fi
    echo ""
}

# Function to show next action prediction
show_next_action() {
    echo -e "${YELLOW}🔮 NEXT ACTION PREDICTION${NC}"
    
    if [[ -f "$STATE_FILE" ]]; then
        local state=$(cat "$STATE_FILE" 2>/dev/null || echo '{}')
        local last_check=$(echo "$state" | jq -r '.last_check_time // "unknown"' 2>/dev/null || echo "unknown")
        
        if [[ "$last_check" != "unknown" ]]; then
            local last_check_timestamp=$(date -d "$last_check" +%s 2>/dev/null || echo "0")
            local current_timestamp=$(date +%s)
            local time_since_check=$((current_timestamp - last_check_timestamp))
            local time_until_next=$((1800 - time_since_check)) # 30 minutes = 1800 seconds
            
            if [[ $time_until_next -gt 0 ]]; then
                local minutes=$((time_until_next / 60))
                local seconds=$((time_until_next % 60))
                echo -e "   Next check in: ${CYAN}${minutes}m ${seconds}s${NC}"
            else
                echo -e "   ${GREEN}Check overdue - should run soon${NC}"
            fi
        else
            echo -e "   ${YELLOW}Unknown - no previous check recorded${NC}"
        fi
    else
        echo -e "   ${YELLOW}Unknown - no state file${NC}"
    fi
    echo ""
}

# Function to show help
show_help() {
    echo -e "${CYAN}KEYBOARD SHORTCUTS:${NC}"
    echo "   q, Q, Ctrl+C - Quit monitor"
    echo "   r, R         - Force refresh"
    echo "   h, ?         - Show this help"
    echo ""
    echo -e "${CYAN}AUTO-REFRESH: Every ${REFRESH_INTERVAL} seconds${NC}"
    echo -e "${CYAN}Press any key to refresh immediately...${NC}"
}

# Main monitoring loop
main() {
    # Set up signal handlers
    trap 'echo -e "\n${YELLOW}Monitor stopped${NC}"; exit 0' INT TERM
    
    echo -e "${GREEN}Starting 30-minute loop monitor...${NC}"
    echo -e "${CYAN}Refresh interval: ${REFRESH_INTERVAL} seconds${NC}"
    echo -e "${CYAN}Press 'q' to quit, 'h' for help${NC}"
    sleep 2
    
    while true; do
        show_header
        get_loop_status
        check_github_actions
        check_active_repairs
        show_recent_logs
        show_system_resources
        show_workflow_health
        show_next_action
        show_help
        
        # Wait for refresh interval or user input
        if read -t "$REFRESH_INTERVAL" -n 1 key 2>/dev/null; then
            case "$key" in
                q|Q)
                    echo -e "\n${YELLOW}Monitor stopped by user${NC}"
                    exit 0
                    ;;
                r|R)
                    continue
                    ;;
                h|\?)
                    echo -e "\n${BLUE}Monitor will refresh automatically every ${REFRESH_INTERVAL} seconds${NC}"
                    echo -e "${BLUE}Press Enter to continue...${NC}"
                    read
                    ;;
            esac
        fi
    done
}

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    if ! command -v jq &> /dev/null; then
        missing_deps+=("jq")
    fi
    
    if ! command -v bc &> /dev/null; then
        missing_deps+=("bc")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        echo -e "${RED}Missing dependencies: ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}Install with: sudo apt-get install ${missing_deps[*]}${NC}"
        exit 1
    fi
}

# Run the monitor
check_dependencies
main