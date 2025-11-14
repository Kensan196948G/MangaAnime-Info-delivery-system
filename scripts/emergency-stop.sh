#!/bin/bash

# Emergency stop script for 30-minute auto-repair system
# Immediately stops all repair workflows and saves state for recovery

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
STATE_FILE="$BASE_DIR/.repair_state.json"
EMERGENCY_STATE_FILE="$BASE_DIR/.emergency_state_$(date +%Y%m%d_%H%M%S).json"
LOCK_FILE="$BASE_DIR/.repair_lock"
LOG_FILE="$BASE_DIR/logs/emergency_stop_$(date +%Y%m%d_%H%M%S).log"
PID_FILE="$BASE_DIR/.repair_processes.pid"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Function to display header
show_header() {
    echo -e "${RED}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                           EMERGENCY STOP SYSTEM                             ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${YELLOW}WARNING: This will immediately stop all auto-repair operations!${NC}"
    echo ""
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Emergency stop script for the 30-minute auto-repair system"
    echo ""
    echo "Options:"
    echo "  --force, -f          Force stop without confirmation"
    echo "  --resume, -r         Resume from saved emergency state"
    echo "  --status, -s         Show current system status"
    echo "  --kill-all, -k       Kill all related processes forcefully"
    echo "  --preserve-state     Don't clear state files (for debugging)"
    echo "  --help, -h           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                   Interactive emergency stop"
    echo "  $0 --force           Force stop without confirmation"
    echo "  $0 --resume          Resume from last emergency stop"
    echo "  $0 --status          Check system status"
}

# Function to check current system status
check_system_status() {
    echo -e "${CYAN}🔍 CHECKING SYSTEM STATUS${NC}"
    
    local active_processes=0
    local github_workflows=0
    local repair_locks=0
    
    # Check for running repair processes
    if pgrep -f "repair" > /dev/null 2>&1; then
        active_processes=$(pgrep -f "repair" | wc -l)
        echo -e "${YELLOW}   Active repair processes: $active_processes${NC}"
    else
        echo -e "${GREEN}   No active repair processes found${NC}"
    fi
    
    # Check for GitHub workflow runs
    if command -v gh &> /dev/null; then
        local running_workflows=$(gh run list --status in_progress --json status 2>/dev/null | jq '. | length' 2>/dev/null || echo "0")
        github_workflows=$running_workflows
        if [[ $github_workflows -gt 0 ]]; then
            echo -e "${YELLOW}   Running GitHub workflows: $github_workflows${NC}"
        else
            echo -e "${GREEN}   No running GitHub workflows${NC}"
        fi
    else
        echo -e "${YELLOW}   GitHub CLI not available - cannot check workflows${NC}"
    fi
    
    # Check for lock files
    if [[ -f "$LOCK_FILE" ]]; then
        local lock_age=$(( $(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo "0") ))
        echo -e "${YELLOW}   Repair lock file exists (${lock_age}s old)${NC}"
        repair_locks=1
    else
        echo -e "${GREEN}   No repair lock files found${NC}"
    fi
    
    # Check state file
    if [[ -f "$STATE_FILE" ]]; then
        local state_content=$(cat "$STATE_FILE" 2>/dev/null || echo "{}")
        local current_iteration=$(echo "$state_content" | jq -r '.current_iteration // 0' 2>/dev/null || echo "0")
        echo -e "${CYAN}   Current loop iteration: $current_iteration${NC}"
    else
        echo -e "${YELLOW}   No state file found${NC}"
    fi
    
    echo ""
    
    # Return status code
    if [[ $active_processes -gt 0 || $github_workflows -gt 0 || $repair_locks -gt 0 ]]; then
        return 1  # System is active
    else
        return 0  # System is idle
    fi
}

# Function to save current state for recovery
save_emergency_state() {
    echo -e "${BLUE}💾 SAVING EMERGENCY STATE${NC}"
    
    local emergency_state="{\"timestamp\": \"$(date -Iseconds)\"}"
    
    # Save current state file if it exists
    if [[ -f "$STATE_FILE" ]]; then
        local current_state=$(cat "$STATE_FILE" 2>/dev/null || echo "{}")
        emergency_state=$(echo "$emergency_state" | jq --argjson state "$current_state" '. + {saved_state: $state}')
        echo -e "${GREEN}   Saved current repair state${NC}"
    fi
    
    # Save running processes
    local processes=()
    while IFS= read -r line; do
        processes+=("$line")
    done < <(ps aux | grep -E "(repair|github)" | grep -v grep | awk '{print $2, $11}' || true)
    
    if [[ ${#processes[@]} -gt 0 ]]; then
        local processes_json=$(printf '%s\n' "${processes[@]}" | jq -R . | jq -s .)
        emergency_state=$(echo "$emergency_state" | jq --argjson procs "$processes_json" '. + {running_processes: $procs}')
        echo -e "${GREEN}   Saved ${#processes[@]} running processes${NC}"
    fi
    
    # Save GitHub workflow status
    if command -v gh &> /dev/null; then
        local workflows=$(gh run list --status in_progress --json id,workflowName,status,conclusion 2>/dev/null || echo "[]")
        emergency_state=$(echo "$emergency_state" | jq --argjson workflows "$workflows" '. + {github_workflows: $workflows}')
        echo -e "${GREEN}   Saved GitHub workflow status${NC}"
    fi
    
    # Write emergency state
    echo "$emergency_state" | jq . > "$EMERGENCY_STATE_FILE"
    echo -e "${CYAN}   Emergency state saved to: $(basename "$EMERGENCY_STATE_FILE")${NC}"
    
    log "INFO" "Emergency state saved to $EMERGENCY_STATE_FILE"
}

# Function to stop all repair processes
stop_repair_processes() {
    echo -e "${RED}🛑 STOPPING REPAIR PROCESSES${NC}"
    
    local stopped_count=0
    
    # Stop repair-related processes
    while IFS= read -r pid; do
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}   Stopping process $pid${NC}"
            if kill -TERM "$pid" 2>/dev/null; then
                ((stopped_count++))
                log "INFO" "Stopped repair process $pid"
            else
                echo -e "${RED}   Failed to stop process $pid${NC}"
                log "WARNING" "Failed to stop repair process $pid"
            fi
        fi
    done < <(pgrep -f "repair" 2>/dev/null || true)
    
    # Wait for graceful shutdown
    if [[ $stopped_count -gt 0 ]]; then
        echo -e "${BLUE}   Waiting for graceful shutdown...${NC}"
        sleep 5
    fi
    
    # Force kill if needed
    local remaining_processes=$(pgrep -f "repair" 2>/dev/null || true)
    if [[ -n "$remaining_processes" ]]; then
        echo -e "${RED}   Force killing remaining processes...${NC}"
        while IFS= read -r pid; do
            if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid" 2>/dev/null || true
                log "WARNING" "Force killed repair process $pid"
            fi
        done < <(echo "$remaining_processes")
    fi
    
    echo -e "${GREEN}   Stopped $stopped_count repair processes${NC}"
}

# Function to cancel GitHub workflows
cancel_github_workflows() {
    echo -e "${RED}🚫 CANCELLING GITHUB WORKFLOWS${NC}"
    
    if ! command -v gh &> /dev/null; then
        echo -e "${YELLOW}   GitHub CLI not available - cannot cancel workflows${NC}"
        return
    fi
    
    local cancelled_count=0
    
    # Get running workflows
    local workflow_ids=$(gh run list --status in_progress --json id --jq '.[].id' 2>/dev/null || true)
    
    if [[ -z "$workflow_ids" ]]; then
        echo -e "${GREEN}   No running workflows to cancel${NC}"
        return
    fi
    
    while IFS= read -r workflow_id; do
        if [[ -n "$workflow_id" ]]; then
            echo -e "${YELLOW}   Cancelling workflow $workflow_id${NC}"
            if gh run cancel "$workflow_id" 2>/dev/null; then
                ((cancelled_count++))
                log "INFO" "Cancelled GitHub workflow $workflow_id"
            else
                echo -e "${RED}   Failed to cancel workflow $workflow_id${NC}"
                log "WARNING" "Failed to cancel GitHub workflow $workflow_id"
            fi
        fi
    done < <(echo "$workflow_ids")
    
    echo -e "${GREEN}   Cancelled $cancelled_count workflows${NC}"
}

# Function to clear system state
clear_system_state() {
    echo -e "${RED}🧹 CLEARING SYSTEM STATE${NC}"
    
    local preserve_state="${1:-false}"
    
    if [[ "$preserve_state" == "false" ]]; then
        # Remove lock files
        if [[ -f "$LOCK_FILE" ]]; then
            rm -f "$LOCK_FILE"
            echo -e "${GREEN}   Removed repair lock file${NC}"
            log "INFO" "Removed repair lock file"
        fi
        
        # Clear PID file
        if [[ -f "$PID_FILE" ]]; then
            rm -f "$PID_FILE"
            echo -e "${GREEN}   Removed PID file${NC}"
            log "INFO" "Removed PID file"
        fi
        
        # Reset state file
        if [[ -f "$STATE_FILE" ]]; then
            echo '{"emergency_stop": true, "timestamp": "'$(date -Iseconds)'"}' > "$STATE_FILE"
            echo -e "${GREEN}   Reset state file${NC}"
            log "INFO" "Reset state file to emergency stop state"
        fi
    else
        echo -e "${YELLOW}   Preserving state files for debugging${NC}"
        log "INFO" "Preserved state files as requested"
    fi
    
    # Clear any pending operations
    local temp_files=$(find "$BASE_DIR" -name "*.tmp" -o -name "*.lock" -o -name "*.pending" 2>/dev/null || true)
    if [[ -n "$temp_files" ]]; then
        echo "$temp_files" | xargs rm -f 2>/dev/null || true
        echo -e "${GREEN}   Cleaned up temporary files${NC}"
    fi
}

# Function to resume from emergency state
resume_from_emergency_state() {
    echo -e "${BLUE}🔄 RESUMING FROM EMERGENCY STATE${NC}"
    
    # Find latest emergency state file
    local latest_emergency_state=$(find "$BASE_DIR" -name ".emergency_state_*.json" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2- || echo "")
    
    if [[ -z "$latest_emergency_state" || ! -f "$latest_emergency_state" ]]; then
        echo -e "${RED}   No emergency state file found${NC}"
        log "ERROR" "No emergency state file found for resume"
        return 1
    fi
    
    echo -e "${CYAN}   Found emergency state: $(basename "$latest_emergency_state")${NC}"
    
    # Load emergency state
    local emergency_state=$(cat "$latest_emergency_state" 2>/dev/null || echo "{}")
    local saved_state=$(echo "$emergency_state" | jq -r '.saved_state // "{}"' 2>/dev/null || echo "{}")
    
    if [[ "$saved_state" != "{}" ]]; then
        # Restore previous state
        echo "$saved_state" > "$STATE_FILE"
        echo -e "${GREEN}   Restored previous repair state${NC}"
        log "INFO" "Restored repair state from emergency backup"
        
        # Show what was restored
        local current_iteration=$(echo "$saved_state" | jq -r '.current_iteration // 0' 2>/dev/null || echo "0")
        local total_repairs=$(echo "$saved_state" | jq -r '.total_repairs // 0' 2>/dev/null || echo "0")
        
        echo -e "${CYAN}   Restored iteration: $current_iteration${NC}"
        echo -e "${CYAN}   Total repairs: $total_repairs${NC}"
    else
        echo -e "${YELLOW}   No saved state to restore${NC}"
    fi
    
    # Remove emergency state file
    rm -f "$latest_emergency_state"
    echo -e "${GREEN}   Cleaned up emergency state file${NC}"
    
    echo -e "${GREEN}✅ Resume complete - you can now restart the repair system${NC}"
}

# Function to perform emergency stop
emergency_stop() {
    local force_stop="${1:-false}"
    local preserve_state="${2:-false}"
    
    show_header
    
    if [[ "$force_stop" == "false" ]]; then
        # Check current status first
        if check_system_status; then
            echo -e "${GREEN}✅ System appears to be idle - no emergency stop needed${NC}"
            read -p "Continue with emergency stop anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}Emergency stop cancelled${NC}"
                exit 0
            fi
        fi
        
        echo -e "${RED}⚠️  This will immediately stop all auto-repair operations!${NC}"
        echo -e "${YELLOW}The following actions will be performed:${NC}"
        echo "   • Stop all repair processes"
        echo "   • Cancel running GitHub workflows"
        echo "   • Clear system locks and temporary files"
        echo "   • Save current state for recovery"
        echo ""
        read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
        echo
        
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Emergency stop cancelled${NC}"
            exit 0
        fi
    fi
    
    echo -e "${RED}🚨 INITIATING EMERGENCY STOP${NC}"
    log "WARNING" "Emergency stop initiated by user"
    
    # Save current state before stopping
    save_emergency_state
    
    # Stop all processes
    stop_repair_processes
    
    # Cancel GitHub workflows
    cancel_github_workflows
    
    # Clear system state
    clear_system_state "$preserve_state"
    
    echo ""
    echo -e "${GREEN}✅ EMERGENCY STOP COMPLETE${NC}"
    echo -e "${CYAN}Emergency state saved to: $(basename "$EMERGENCY_STATE_FILE")${NC}"
    echo -e "${CYAN}Log file: $(basename "$LOG_FILE")${NC}"
    echo ""
    echo -e "${YELLOW}To resume the system:${NC}"
    echo "   $0 --resume"
    echo ""
    
    log "INFO" "Emergency stop completed successfully"
}

# Main function
main() {
    local force_stop=false
    local preserve_state=false
    local resume_mode=false
    local status_only=false
    local kill_all=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force|-f)
                force_stop=true
                shift
                ;;
            --preserve-state)
                preserve_state=true
                shift
                ;;
            --resume|-r)
                resume_mode=true
                shift
                ;;
            --status|-s)
                status_only=true
                shift
                ;;
            --kill-all|-k)
                kill_all=true
                force_stop=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Create logs directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Handle different modes
    if [[ "$status_only" == "true" ]]; then
        show_header
        if check_system_status; then
            echo -e "${GREEN}✅ System is idle${NC}"
            exit 0
        else
            echo -e "${YELLOW}⚠️  System has active operations${NC}"
            exit 1
        fi
    elif [[ "$resume_mode" == "true" ]]; then
        show_header
        resume_from_emergency_state
    elif [[ "$kill_all" == "true" ]]; then
        echo -e "${RED}🔥 FORCE KILLING ALL PROCESSES${NC}"
        log "WARNING" "Force kill all processes initiated"
        
        # Kill all related processes
        pkill -f "repair" 2>/dev/null || true
        pkill -f "github" 2>/dev/null || true
        pkill -f "gh.*run" 2>/dev/null || true
        
        # Clear all state
        clear_system_state false
        
        echo -e "${GREEN}✅ All processes terminated${NC}"
        log "INFO" "Force kill completed"
    else
        emergency_stop "$force_stop" "$preserve_state"
    fi
}

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    if ! command -v jq &> /dev/null; then
        missing_deps+=("jq")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        echo -e "${RED}Missing dependencies: ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}Install with: sudo apt-get install ${missing_deps[*]}${NC}"
        exit 1
    fi
}

# Signal handlers
trap 'echo -e "\n${YELLOW}Emergency stop script interrupted${NC}"; exit 130' INT TERM

# Run the script
check_dependencies
main "$@"