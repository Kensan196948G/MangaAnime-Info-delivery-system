#!/bin/bash

# System health check script for 30-minute auto-repair system
# Validates configurations, checks dependencies, and verifies system readiness

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
STATE_FILE="$BASE_DIR/.repair_state.json"
LOG_DIR="$BASE_DIR/logs"
WORKFLOW_DIR="$BASE_DIR/.github/workflows"
HEALTH_LOG="$LOG_DIR/health_check_$(date +%Y%m%d_%H%M%S).log"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Health check results
HEALTH_SCORE=0
MAX_SCORE=0
ISSUES=()
WARNINGS=()
RECOMMENDATIONS=()

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    mkdir -p "$(dirname "$HEALTH_LOG")"
    echo "[$timestamp] [$level] $message" | tee -a "$HEALTH_LOG"
}

# Function to add points to health score
add_health_points() {
    local points="$1"
    local max_points="$2"
    HEALTH_SCORE=$((HEALTH_SCORE + points))
    MAX_SCORE=$((MAX_SCORE + max_points))
}

# Function to add issue
add_issue() {
    local message="$1"
    ISSUES+=("$message")
    log "ERROR" "$message"
}

# Function to add warning
add_warning() {
    local message="$1"
    WARNINGS+=("$message")
    log "WARNING" "$message"
}

# Function to add recommendation
add_recommendation() {
    local message="$1"
    RECOMMENDATIONS+=("$message")
    log "INFO" "Recommendation: $message"
}

# Function to display header
show_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                           SYSTEM HEALTH CHECK                               ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${CYAN}Auto-Repair System Health Validation${NC}"
    echo -e "${CYAN}Checking system configuration, dependencies, and readiness...${NC}"
    echo ""
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "System health check for the 30-minute auto-repair system"
    echo ""
    echo "Options:"
    echo "  --fix, -f            Attempt to fix detected issues automatically"
    echo "  --detailed, -d       Show detailed check results"
    echo "  --export, -e FILE    Export health report to file"
    echo "  --quiet, -q          Minimal output (exit codes only)"
    echo "  --config-only, -c    Check configuration files only"
    echo "  --deps-only          Check dependencies only"
    echo "  --github-only, -g    Check GitHub integration only"
    echo "  --help, -h           Show this help message"
    echo ""
    echo "Exit codes:"
    echo "  0 - All checks passed (healthy)"
    echo "  1 - Minor issues detected (warnings)"
    echo "  2 - Major issues detected (errors)"
    echo "  3 - Critical issues detected (system unusable)"
}

# Function to check system dependencies
check_dependencies() {
    echo -e "${YELLOW}🔧 CHECKING SYSTEM DEPENDENCIES${NC}"
    
    local dep_score=0
    local max_dep_score=50
    
    # Essential commands
    local essential_commands=("git" "jq" "curl" "python3" "pip3")
    local missing_essential=()
    
    for cmd in "${essential_commands[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            echo -e "${GREEN}   ✅ $cmd found${NC}"
            dep_score=$((dep_score + 5))
        else
            echo -e "${RED}   ❌ $cmd missing${NC}"
            missing_essential+=("$cmd")
        fi
    done
    
    if [[ ${#missing_essential[@]} -gt 0 ]]; then
        add_issue "Missing essential commands: ${missing_essential[*]}"
        add_recommendation "Install missing commands: sudo apt-get install ${missing_essential[*]}"
    fi
    
    # Optional but recommended commands
    local optional_commands=("gh" "bc" "sqlite3" "cron")
    for cmd in "${optional_commands[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            echo -e "${GREEN}   ✅ $cmd found (optional)${NC}"
            dep_score=$((dep_score + 2))
        else
            echo -e "${YELLOW}   ⚠️  $cmd missing (optional)${NC}"
            add_warning "$cmd not found - some features may be limited"
        fi
    done
    
    # Python packages
    echo "   Checking Python packages..."
    local python_packages=("requests" "PyYAML" "gitpython")
    for package in "${python_packages[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            echo -e "${GREEN}     ✅ Python $package available${NC}"
            dep_score=$((dep_score + 3))
        else
            echo -e "${YELLOW}     ⚠️  Python $package missing${NC}"
            add_warning "Python package $package not found"
            add_recommendation "Install with: pip3 install $package"
        fi
    done
    
    add_health_points "$dep_score" "$max_dep_score"
    echo -e "${CYAN}   Dependencies Score: $dep_score/$max_dep_score${NC}"
    echo ""
}

# Function to check GitHub integration
check_github_integration() {
    echo -e "${YELLOW}🐙 CHECKING GITHUB INTEGRATION${NC}"
    
    local github_score=0
    local max_github_score=30
    
    # Check if we're in a git repository
    if git rev-parse --git-dir &> /dev/null; then
        echo -e "${GREEN}   ✅ Git repository detected${NC}"
        github_score=$((github_score + 5))
        
        # Check remote origin
        if git remote get-url origin &> /dev/null; then
            local origin_url=$(git remote get-url origin)
            echo -e "${GREEN}   ✅ Git remote origin: $origin_url${NC}"
            github_score=$((github_score + 5))
            
            # Check if it's a GitHub repository
            if [[ "$origin_url" == *"github.com"* ]]; then
                echo -e "${GREEN}   ✅ GitHub repository confirmed${NC}"
                github_score=$((github_score + 5))
            else
                add_warning "Repository is not hosted on GitHub - some features may not work"
            fi
        else
            add_issue "No git remote origin configured"
        fi
    else
        add_issue "Not in a git repository"
    fi
    
    # Check GitHub CLI authentication
    if command -v gh &> /dev/null; then
        if gh auth status &> /dev/null; then
            echo -e "${GREEN}   ✅ GitHub CLI authenticated${NC}"
            github_score=$((github_score + 10))
            
            # Check GitHub API rate limit
            local rate_limit=$(gh api rate_limit --jq '.rate.remaining' 2>/dev/null || echo "unknown")
            if [[ "$rate_limit" != "unknown" ]]; then
                if [[ "$rate_limit" -gt 1000 ]]; then
                    echo -e "${GREEN}   ✅ GitHub API rate limit: $rate_limit remaining${NC}"
                    github_score=$((github_score + 5))
                elif [[ "$rate_limit" -gt 100 ]]; then
                    echo -e "${YELLOW}   ⚠️  GitHub API rate limit: $rate_limit remaining (low)${NC}"
                    add_warning "GitHub API rate limit is low"
                else
                    echo -e "${RED}   ❌ GitHub API rate limit: $rate_limit remaining (critical)${NC}"
                    add_issue "GitHub API rate limit critically low"
                fi
            fi
        else
            add_issue "GitHub CLI not authenticated"
            add_recommendation "Authenticate with: gh auth login"
        fi
    else
        add_warning "GitHub CLI not installed - workflow management limited"
        add_recommendation "Install GitHub CLI: https://cli.github.com/"
    fi
    
    add_health_points "$github_score" "$max_github_score"
    echo -e "${CYAN}   GitHub Integration Score: $github_score/$max_github_score${NC}"
    echo ""
}

# Function to check workflow configurations
check_workflow_configurations() {
    echo -e "${YELLOW}⚙️  CHECKING WORKFLOW CONFIGURATIONS${NC}"
    
    local workflow_score=0
    local max_workflow_score=40
    
    # Check if workflow directory exists
    if [[ -d "$WORKFLOW_DIR" ]]; then
        echo -e "${GREEN}   ✅ Workflow directory found${NC}"
        workflow_score=$((workflow_score + 5))
        
        # Find workflow files
        local workflow_files=()
        while IFS= read -r -d '' file; do
            workflow_files+=("$file")
        done < <(find "$WORKFLOW_DIR" -name "*.yml" -o -name "*.yaml" 2>/dev/null | head -20 | tr '\n' '\0')
        
        if [[ ${#workflow_files[@]} -gt 0 ]]; then
            echo -e "${GREEN}   ✅ Found ${#workflow_files[@]} workflow files${NC}"
            workflow_score=$((workflow_score + 5))
            
            # Validate each workflow file
            local valid_workflows=0
            for workflow_file in "${workflow_files[@]}"; do
                local workflow_name=$(basename "$workflow_file")
                
                # Basic YAML syntax check
                if python3 -c "import yaml; yaml.safe_load(open('$workflow_file'))" 2>/dev/null; then
                    echo -e "${GREEN}     ✅ $workflow_name (valid YAML)${NC}"
                    ((valid_workflows++))
                    
                    # Check for required fields
                    local has_name=$(grep -q "^name:" "$workflow_file" && echo "yes" || echo "no")
                    local has_on=$(grep -q "^on:" "$workflow_file" && echo "yes" || echo "no")
                    local has_jobs=$(grep -q "^jobs:" "$workflow_file" && echo "yes" || echo "no")
                    
                    if [[ "$has_name" == "yes" && "$has_on" == "yes" && "$has_jobs" == "yes" ]]; then
                        workflow_score=$((workflow_score + 2))
                    else
                        add_warning "$workflow_name missing required fields (name/on/jobs)"
                    fi
                    
                    # Check for auto-repair specific patterns
                    if grep -q "repair\|fix\|auto" "$workflow_file"; then
                        echo -e "${CYAN}       🔧 Auto-repair workflow detected${NC}"
                        workflow_score=$((workflow_score + 3))
                    fi
                else
                    echo -e "${RED}     ❌ $workflow_name (invalid YAML)${NC}"
                    add_issue "$workflow_name has invalid YAML syntax"
                fi
            done
            
            # Calculate workflow health percentage
            local workflow_health_pct=0
            if [[ ${#workflow_files[@]} -gt 0 ]]; then
                workflow_health_pct=$((valid_workflows * 100 / ${#workflow_files[@]}))
            fi
            
            if [[ $workflow_health_pct -eq 100 ]]; then
                echo -e "${GREEN}   ✅ All workflows valid (100%)${NC}"
                workflow_score=$((workflow_score + 10))
            elif [[ $workflow_health_pct -ge 80 ]]; then
                echo -e "${YELLOW}   ⚠️  Most workflows valid (${workflow_health_pct}%)${NC}"
                workflow_score=$((workflow_score + 5))
                add_warning "Some workflows have issues"
            else
                echo -e "${RED}   ❌ Many workflow issues (${workflow_health_pct}% valid)${NC}"
                add_issue "Multiple workflow configuration problems"
            fi
        else
            add_warning "No workflow files found"
            add_recommendation "Create workflow files in .github/workflows/"
        fi
    else
        add_issue "Workflow directory .github/workflows not found"
        add_recommendation "Create .github/workflows directory and add workflow files"
    fi
    
    add_health_points "$workflow_score" "$max_workflow_score"
    echo -e "${CYAN}   Workflow Configuration Score: $workflow_score/$max_workflow_score${NC}"
    echo ""
}

# Function to check system state and files
check_system_state() {
    echo -e "${YELLOW}📋 CHECKING SYSTEM STATE${NC}"
    
    local state_score=0
    local max_state_score=25
    
    # Check state file
    if [[ -f "$STATE_FILE" ]]; then
        echo -e "${GREEN}   ✅ State file found${NC}"
        state_score=$((state_score + 5))
        
        # Validate state file JSON
        if jq . "$STATE_FILE" &> /dev/null; then
            echo -e "${GREEN}   ✅ State file has valid JSON${NC}"
            state_score=$((state_score + 5))
            
            # Check state file content
            local current_iteration=$(jq -r '.current_iteration // 0' "$STATE_FILE" 2>/dev/null)
            local total_repairs=$(jq -r '.total_repairs // 0' "$STATE_FILE" 2>/dev/null)
            
            echo -e "${CYAN}     Current iteration: $current_iteration${NC}"
            echo -e "${CYAN}     Total repairs: $total_repairs${NC}"
            
            if [[ "$current_iteration" =~ ^[0-9]+$ ]] && [[ "$total_repairs" =~ ^[0-9]+$ ]]; then
                state_score=$((state_score + 5))
            else
                add_warning "State file contains invalid data"
            fi
        else
            add_issue "State file contains invalid JSON"
        fi
    else
        add_warning "State file not found - system may not have been initialized"
        add_recommendation "Initialize system by running the auto-repair script"
    fi
    
    # Check log directory
    if [[ -d "$LOG_DIR" ]]; then
        echo -e "${GREEN}   ✅ Log directory found${NC}"
        state_score=$((state_score + 3))
        
        # Check for recent log files
        local recent_logs=$(find "$LOG_DIR" -name "*.log" -type f -mtime -7 2>/dev/null | wc -l)
        if [[ $recent_logs -gt 0 ]]; then
            echo -e "${GREEN}   ✅ Recent log files found ($recent_logs)${NC}"
            state_score=$((state_score + 4))
        else
            add_warning "No recent log files found - system may be inactive"
        fi
    else
        add_warning "Log directory not found"
        add_recommendation "Create logs directory: mkdir -p $LOG_DIR"
    fi
    
    # Check for lock files
    if [[ -f "$BASE_DIR/.repair_lock" ]]; then
        local lock_age=$(( $(date +%s) - $(stat -c %Y "$BASE_DIR/.repair_lock" 2>/dev/null || echo "0") ))
        if [[ $lock_age -lt 3600 ]]; then # Less than 1 hour
            echo -e "${GREEN}   ✅ Active repair lock (${lock_age}s old)${NC}"
            state_score=$((state_score + 3))
        else
            echo -e "${YELLOW}   ⚠️  Stale repair lock (${lock_age}s old)${NC}"
            add_warning "Stale repair lock detected - may indicate stuck process"
            add_recommendation "Remove stale lock: rm -f $BASE_DIR/.repair_lock"
        fi
    else
        echo -e "${CYAN}   ℹ️  No active repair locks${NC}"
    fi
    
    add_health_points "$state_score" "$max_state_score"
    echo -e "${CYAN}   System State Score: $state_score/$max_state_score${NC}"
    echo ""
}

# Function to check system resources
check_system_resources() {
    echo -e "${YELLOW}💻 CHECKING SYSTEM RESOURCES${NC}"
    
    local resource_score=0
    local max_resource_score=20
    
    # Check disk space
    local disk_usage=$(df "$BASE_DIR" | tail -1 | awk '{print $5}' | sed 's/%//' 2>/dev/null || echo "100")
    if [[ $disk_usage -lt 80 ]]; then
        echo -e "${GREEN}   ✅ Disk usage: ${disk_usage}% (healthy)${NC}"
        resource_score=$((resource_score + 5))
    elif [[ $disk_usage -lt 95 ]]; then
        echo -e "${YELLOW}   ⚠️  Disk usage: ${disk_usage}% (warning)${NC}"
        add_warning "Disk space is getting low"
        resource_score=$((resource_score + 2))
    else
        echo -e "${RED}   ❌ Disk usage: ${disk_usage}% (critical)${NC}"
        add_issue "Disk space critically low"
    fi
    
    # Check memory usage
    local memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}' 2>/dev/null || echo "100")
    if [[ $memory_usage -lt 80 ]]; then
        echo -e "${GREEN}   ✅ Memory usage: ${memory_usage}% (healthy)${NC}"
        resource_score=$((resource_score + 5))
    elif [[ $memory_usage -lt 95 ]]; then
        echo -e "${YELLOW}   ⚠️  Memory usage: ${memory_usage}% (warning)${NC}"
        add_warning "Memory usage is high"
        resource_score=$((resource_score + 2))
    else
        echo -e "${RED}   ❌ Memory usage: ${memory_usage}% (critical)${NC}"
        add_issue "Memory usage critically high"
    fi
    
    # Check system load
    if command -v uptime &> /dev/null; then
        local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//' 2>/dev/null || echo "0.0")
        local load_int=$(echo "$load_avg" | cut -d'.' -f1)
        
        if [[ ${load_int:-0} -lt 2 ]]; then
            echo -e "${GREEN}   ✅ System load: $load_avg (healthy)${NC}"
            resource_score=$((resource_score + 5))
        elif [[ ${load_int:-0} -lt 5 ]]; then
            echo -e "${YELLOW}   ⚠️  System load: $load_avg (elevated)${NC}"
            add_warning "System load is elevated"
            resource_score=$((resource_score + 2))
        else
            echo -e "${RED}   ❌ System load: $load_avg (high)${NC}"
            add_issue "System load is very high"
        fi
    fi
    
    # Check available inodes
    local inode_usage=$(df -i "$BASE_DIR" | tail -1 | awk '{print $5}' | sed 's/%//' 2>/dev/null || echo "0")
    if [[ $inode_usage -lt 80 ]]; then
        echo -e "${GREEN}   ✅ Inode usage: ${inode_usage}% (healthy)${NC}"
        resource_score=$((resource_score + 5))
    elif [[ $inode_usage -lt 95 ]]; then
        echo -e "${YELLOW}   ⚠️  Inode usage: ${inode_usage}% (warning)${NC}"
        add_warning "Inode usage is high"
        resource_score=$((resource_score + 2))
    else
        echo -e "${RED}   ❌ Inode usage: ${inode_usage}% (critical)${NC}"
        add_issue "Inode usage critically high"
    fi
    
    add_health_points "$resource_score" "$max_resource_score"
    echo -e "${CYAN}   System Resources Score: $resource_score/$max_resource_score${NC}"
    echo ""
}

# Function to check permissions and access
check_permissions() {
    echo -e "${YELLOW}🔒 CHECKING PERMISSIONS AND ACCESS${NC}"
    
    local perm_score=0
    local max_perm_score=15
    
    # Check directory permissions
    if [[ -r "$BASE_DIR" && -w "$BASE_DIR" ]]; then
        echo -e "${GREEN}   ✅ Base directory readable and writable${NC}"
        perm_score=$((perm_score + 5))
    else
        add_issue "Base directory not accessible"
    fi
    
    # Check workflow directory permissions
    if [[ -d "$WORKFLOW_DIR" ]]; then
        if [[ -r "$WORKFLOW_DIR" ]]; then
            echo -e "${GREEN}   ✅ Workflow directory readable${NC}"
            perm_score=$((perm_score + 3))
        else
            add_issue "Workflow directory not readable"
        fi
    fi
    
    # Check log directory permissions
    if [[ -d "$LOG_DIR" ]] || mkdir -p "$LOG_DIR" 2>/dev/null; then
        if [[ -w "$LOG_DIR" ]]; then
            echo -e "${GREEN}   ✅ Log directory writable${NC}"
            perm_score=$((perm_score + 4))
        else
            add_issue "Log directory not writable"
        fi
    else
        add_issue "Cannot create log directory"
    fi
    
    # Check script execution permissions
    local script_files=("$SCRIPT_DIR"/*.sh)
    local executable_scripts=0
    for script in "${script_files[@]}"; do
        if [[ -f "$script" && -x "$script" ]]; then
            ((executable_scripts++))
        fi
    done
    
    if [[ $executable_scripts -gt 0 ]]; then
        echo -e "${GREEN}   ✅ $executable_scripts script(s) executable${NC}"
        perm_score=$((perm_score + 3))
    else
        add_warning "No executable scripts found"
        add_recommendation "Make scripts executable: chmod +x $SCRIPT_DIR/*.sh"
    fi
    
    add_health_points "$perm_score" "$max_perm_score"
    echo -e "${CYAN}   Permissions Score: $perm_score/$max_perm_score${NC}"
    echo ""
}

# Function to attempt automatic fixes
attempt_fixes() {
    echo -e "${YELLOW}🔧 ATTEMPTING AUTOMATIC FIXES${NC}"
    
    local fixes_applied=0
    
    # Fix script permissions
    if [[ -d "$SCRIPT_DIR" ]]; then
        echo "   Making scripts executable..."
        if chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null; then
            echo -e "${GREEN}   ✅ Fixed script permissions${NC}"
            ((fixes_applied++))
        fi
    fi
    
    # Create missing directories
    local missing_dirs=("$LOG_DIR")
    for dir in "${missing_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            echo "   Creating missing directory: $dir"
            if mkdir -p "$dir" 2>/dev/null; then
                echo -e "${GREEN}   ✅ Created directory: $dir${NC}"
                ((fixes_applied++))
            else
                echo -e "${RED}   ❌ Failed to create directory: $dir${NC}"
            fi
        fi
    done
    
    # Remove stale lock files
    if [[ -f "$BASE_DIR/.repair_lock" ]]; then
        local lock_age=$(( $(date +%s) - $(stat -c %Y "$BASE_DIR/.repair_lock" 2>/dev/null || echo "0") ))
        if [[ $lock_age -gt 3600 ]]; then # Older than 1 hour
            echo "   Removing stale lock file..."
            if rm -f "$BASE_DIR/.repair_lock" 2>/dev/null; then
                echo -e "${GREEN}   ✅ Removed stale lock file${NC}"
                ((fixes_applied++))
            fi
        fi
    fi
    
    # Initialize state file if missing
    if [[ ! -f "$STATE_FILE" ]]; then
        echo "   Creating initial state file..."
        if echo '{"current_iteration": 0, "total_repairs": 0, "initialized": true}' > "$STATE_FILE" 2>/dev/null; then
            echo -e "${GREEN}   ✅ Created initial state file${NC}"
            ((fixes_applied++))
        fi
    fi
    
    echo -e "${CYAN}   Applied $fixes_applied automatic fixes${NC}"
    
    if [[ $fixes_applied -gt 0 ]]; then
        add_recommendation "Re-run health check to verify fixes"
    fi
    
    echo ""
}

# Function to display final health summary
show_health_summary() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                              HEALTH SUMMARY                                  ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    
    # Calculate health percentage
    local health_percentage=0
    if [[ $MAX_SCORE -gt 0 ]]; then
        health_percentage=$((HEALTH_SCORE * 100 / MAX_SCORE))
    fi
    
    # Determine overall health status
    local health_status=""
    local health_color=""
    if [[ $health_percentage -ge 90 ]]; then
        health_status="EXCELLENT"
        health_color="${GREEN}"
    elif [[ $health_percentage -ge 80 ]]; then
        health_status="GOOD"
        health_color="${GREEN}"
    elif [[ $health_percentage -ge 70 ]]; then
        health_status="FAIR"
        health_color="${YELLOW}"
    elif [[ $health_percentage -ge 50 ]]; then
        health_status="POOR"
        health_color="${YELLOW}"
    else
        health_status="CRITICAL"
        health_color="${RED}"
    fi
    
    echo -e "${CYAN}Overall Health Score: ${health_color}${HEALTH_SCORE}/${MAX_SCORE} (${health_percentage}% - ${health_status})${NC}"
    echo ""
    
    # Show issues
    if [[ ${#ISSUES[@]} -gt 0 ]]; then
        echo -e "${RED}🚨 CRITICAL ISSUES (${#ISSUES[@]}):${NC}"
        for issue in "${ISSUES[@]}"; do
            echo -e "${RED}   ❌ $issue${NC}"
        done
        echo ""
    fi
    
    # Show warnings
    if [[ ${#WARNINGS[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  WARNINGS (${#WARNINGS[@]}):${NC}"
        for warning in "${WARNINGS[@]}"; do
            echo -e "${YELLOW}   ⚠️  $warning${NC}"
        done
        echo ""
    fi
    
    # Show recommendations
    if [[ ${#RECOMMENDATIONS[@]} -gt 0 ]]; then
        echo -e "${CYAN}💡 RECOMMENDATIONS (${#RECOMMENDATIONS[@]}):${NC}"
        for recommendation in "${RECOMMENDATIONS[@]}"; do
            echo -e "${CYAN}   💡 $recommendation${NC}"
        done
        echo ""
    fi
    
    # Health check log location
    echo -e "${CYAN}Health check log saved to: $(basename "$HEALTH_LOG")${NC}"
    echo ""
    
    log "INFO" "Health check completed - Score: $HEALTH_SCORE/$MAX_SCORE ($health_percentage%)"
}

# Function to export health report
export_health_report() {
    local output_file="$1"
    
    local health_percentage=0
    if [[ $MAX_SCORE -gt 0 ]]; then
        health_percentage=$((HEALTH_SCORE * 100 / MAX_SCORE))
    fi
    
    cat > "$output_file" << EOF
{
  "health_check": {
    "timestamp": "$(date -Iseconds)",
    "score": $HEALTH_SCORE,
    "max_score": $MAX_SCORE,
    "percentage": $health_percentage,
    "status": "$(if [[ $health_percentage -ge 80 ]]; then echo "healthy"; elif [[ $health_percentage -ge 50 ]]; then echo "warning"; else echo "critical"; fi)"
  },
  "issues": $(printf '%s\n' "${ISSUES[@]}" | jq -R . | jq -s .),
  "warnings": $(printf '%s\n' "${WARNINGS[@]}" | jq -R . | jq -s .),
  "recommendations": $(printf '%s\n' "${RECOMMENDATIONS[@]}" | jq -R . | jq -s .)
}
EOF
    
    echo -e "${GREEN}Health report exported to: $output_file${NC}"
}

# Main function
main() {
    local fix_issues=false
    local detailed_output=false
    local export_file=""
    local quiet_mode=false
    local config_only=false
    local deps_only=false
    local github_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --fix|-f)
                fix_issues=true
                shift
                ;;
            --detailed|-d)
                detailed_output=true
                shift
                ;;
            --export|-e)
                export_file="$2"
                shift 2
                ;;
            --quiet|-q)
                quiet_mode=true
                shift
                ;;
            --config-only|-c)
                config_only=true
                shift
                ;;
            --deps-only)
                deps_only=true
                shift
                ;;
            --github-only|-g)
                github_only=true
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
    
    # Initialize logging
    mkdir -p "$(dirname "$HEALTH_LOG")"
    log "INFO" "Starting system health check"
    
    if [[ "$quiet_mode" == "false" ]]; then
        show_header
    fi
    
    # Run health checks based on options
    if [[ "$deps_only" == "true" ]]; then
        check_dependencies
    elif [[ "$github_only" == "true" ]]; then
        check_github_integration
    elif [[ "$config_only" == "true" ]]; then
        check_workflow_configurations
    else
        # Run all checks
        check_dependencies
        check_github_integration
        check_workflow_configurations
        check_system_state
        check_system_resources
        check_permissions
    fi
    
    # Attempt fixes if requested
    if [[ "$fix_issues" == "true" ]]; then
        attempt_fixes
    fi
    
    # Show summary unless in quiet mode
    if [[ "$quiet_mode" == "false" ]]; then
        show_health_summary
    fi
    
    # Export report if requested
    if [[ -n "$export_file" ]]; then
        export_health_report "$export_file"
    fi
    
    # Determine exit code
    local exit_code=0
    if [[ ${#ISSUES[@]} -gt 5 ]]; then
        exit_code=3  # Critical
    elif [[ ${#ISSUES[@]} -gt 0 ]]; then
        exit_code=2  # Major issues
    elif [[ ${#WARNINGS[@]} -gt 0 ]]; then
        exit_code=1  # Minor issues
    fi
    
    log "INFO" "Health check completed with exit code $exit_code"
    exit $exit_code
}

# Check for required dependencies
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required but not installed${NC}"
    echo -e "${YELLOW}Install with: sudo apt-get install jq${NC}"
    exit 3
fi

# Run the health check
main "$@"