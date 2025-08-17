#!/bin/bash

# =============================================================================
# Auto-Repair System Setup Script
# Initializes the complete auto-repair system infrastructure
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
readonly SCRIPTS_DIR="$PROJECT_ROOT/scripts"

# System requirements
readonly REQUIRED_PACKAGES=("jq" "curl" "bc" "git" "python3" "pip3")
readonly REQUIRED_PYTHON_PACKAGES=("requests" "pyyaml" "gitpython")

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

# Function to log setup steps
log_setup() {
    local message="$1"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [SETUP] $message" >> "$LOG_DIR/setup.log"
    print_colored "$BLUE" "🔧 $message"
}

# Function to check system requirements
check_system_requirements() {
    print_header "System Requirements Check"
    
    local missing_packages=()
    local all_good=true
    
    # Check OS
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_colored "$YELLOW" "⚠️  Warning: This script is optimized for Linux. Some features may not work properly."
    fi
    
    # Check required system packages
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if command -v "$package" &> /dev/null; then
            print_colored "$GREEN" "✅ $package is installed"
        else
            missing_packages+=("$package")
            all_good=false
        fi
    done
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        local python_version
        python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        if [[ "$(echo "$python_version" | cut -d. -f1)" -ge 3 ]] && [[ "$(echo "$python_version" | cut -d. -f2)" -ge 7 ]]; then
            print_colored "$GREEN" "✅ Python $python_version is compatible"
        else
            print_colored "$RED" "❌ Python 3.7+ required, found $python_version"
            all_good=false
        fi
    fi
    
    # Check Git repository
    if [[ -d "$PROJECT_ROOT/.git" ]]; then
        print_colored "$GREEN" "✅ Git repository detected"
    else
        print_colored "$YELLOW" "⚠️  Not a Git repository. Some features may be limited."
    fi
    
    # Check GitHub CLI (optional)
    if command -v gh &> /dev/null; then
        print_colored "$GREEN" "✅ GitHub CLI available"
    else
        print_colored "$YELLOW" "⚠️  GitHub CLI not installed (optional)"
    fi
    
    if [[ "${#missing_packages[@]}" -gt 0 ]]; then
        print_colored "$RED" "❌ Missing required packages: ${missing_packages[*]}"
        print_colored "$WHITE" "Install them with:"
        print_colored "$WHITE" "   sudo apt-get update && sudo apt-get install ${missing_packages[*]}"
        
        if [[ "${1:-}" != "--force" ]]; then
            print_colored "$RED" "Aborting setup. Use --force to continue anyway."
            exit 1
        fi
    fi
    
    log_setup "System requirements check completed"
}

# Function to create directory structure
create_directories() {
    print_header "Creating Directory Structure"
    
    local directories=(
        "$LOG_DIR"
        "$BACKUP_DIR"
        "$ML_MODELS_DIR"
        "$WORKFLOWS_DIR"
        "$SCRIPTS_DIR"
        "$LOG_DIR/metrics"
        "$LOG_DIR/reports"
        "$BACKUP_DIR/daily"
        "$BACKUP_DIR/manual"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            print_colored "$GREEN" "✅ Created: $dir"
        else
            print_colored "$BLUE" "📁 Already exists: $dir"
        fi
    done
    
    log_setup "Directory structure created"
}

# Function to set up file permissions
setup_permissions() {
    print_header "Setting Up File Permissions"
    
    # Make scripts executable
    local script_files=(
        "$SCRIPTS_DIR/monitor-repair.sh"
        "$SCRIPTS_DIR/collect-metrics.sh"
        "$SCRIPTS_DIR/manual-repair.sh"
        "$SCRIPTS_DIR/setup-repair-system.sh"
    )
    
    for script in "${script_files[@]}"; do
        if [[ -f "$script" ]]; then
            chmod +x "$script"
            print_colored "$GREEN" "✅ Made executable: $(basename "$script")"
        else
            print_colored "$YELLOW" "⚠️  Script not found: $(basename "$script")"
        fi
    done
    
    # Set appropriate permissions for directories
    chmod 755 "$LOG_DIR" "$BACKUP_DIR" "$SCRIPTS_DIR" 2>/dev/null || true
    chmod 644 "$ML_MODELS_DIR"/*.json 2>/dev/null || true
    
    log_setup "File permissions configured"
}

# Function to install Python dependencies
install_python_dependencies() {
    print_header "Installing Python Dependencies"
    
    if ! command -v pip3 &> /dev/null; then
        print_colored "$RED" "❌ pip3 not found. Please install Python pip first."
        return 1
    fi
    
    # Check and install required Python packages
    for package in "${REQUIRED_PYTHON_PACKAGES[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            print_colored "$GREEN" "✅ Python package '$package' is installed"
        else
            print_colored "$YELLOW" "📦 Installing Python package: $package"
            pip3 install "$package" --user || {
                print_colored "$RED" "❌ Failed to install $package"
                return 1
            }
            print_colored "$GREEN" "✅ Installed: $package"
        fi
    done
    
    # Install additional useful packages
    local optional_packages=("github3.py" "click" "rich")
    for package in "${optional_packages[@]}"; do
        if ! python3 -c "import ${package%.*}" 2>/dev/null; then
            print_colored "$BLUE" "📦 Installing optional package: $package"
            pip3 install "$package" --user 2>/dev/null || \
                print_colored "$YELLOW" "⚠️  Failed to install optional package: $package"
        fi
    done
    
    log_setup "Python dependencies installed"
}

# Function to configure GitHub integration
configure_github() {
    print_header "Configuring GitHub Integration"
    
    # Check for GitHub token
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        print_colored "$GREEN" "✅ GITHUB_TOKEN is set"
        
        # Test token validity
        if curl -s -H "Authorization: token $GITHUB_TOKEN" \
           "https://api.github.com/rate_limit" | jq -e '.rate' >/dev/null 2>&1; then
            print_colored "$GREEN" "✅ GitHub token is valid"
        else
            print_colored "$RED" "❌ GitHub token appears to be invalid"
        fi
    else
        print_colored "$YELLOW" "⚠️  GITHUB_TOKEN not set"
        print_colored "$WHITE" "To enable GitHub API features:"
        print_colored "$WHITE" "1. Create a personal access token at: https://github.com/settings/tokens"
        print_colored "$WHITE" "2. Set the token: export GITHUB_TOKEN='your_token_here'"
        print_colored "$WHITE" "3. Add to your shell profile for persistence"
    fi
    
    # Check repository configuration
    if [[ -d "$PROJECT_ROOT/.git" ]]; then
        local repo_url
        repo_url=$(git -C "$PROJECT_ROOT" remote get-url origin 2>/dev/null || echo "")
        
        if [[ "$repo_url" =~ github\.com ]]; then
            local repo_name
            repo_name=$(echo "$repo_url" | sed 's/.*github\.com[:/]\([^.]*\)\.git/\1/')
            export GITHUB_REPOSITORY="$repo_name"
            print_colored "$GREEN" "✅ GitHub repository: $repo_name"
        else
            print_colored "$YELLOW" "⚠️  Repository is not hosted on GitHub"
        fi
    fi
    
    log_setup "GitHub integration configured"
}

# Function to initialize ML models
initialize_ml_models() {
    print_header "Initializing ML Models"
    
    local patterns_file="$ML_MODELS_DIR/error-patterns.json"
    
    if [[ ! -f "$patterns_file" ]]; then
        print_colored "$YELLOW" "⚠️  ML patterns file not found. Creating basic version..."
        
        # Create a minimal patterns file if it doesn't exist
        cat > "$patterns_file" << 'EOF'
{
  "version": "1.0.0",
  "last_updated": "2025-08-17T00:00:00Z",
  "error_categories": {
    "dependency": {
      "weight": 0.9,
      "patterns": []
    },
    "test": {
      "weight": 0.8,
      "patterns": []
    },
    "build": {
      "weight": 0.85,
      "patterns": []
    }
  },
  "repair_history": {
    "successful_repairs": [],
    "failed_repairs": []
  }
}
EOF
        print_colored "$GREEN" "✅ Created basic ML patterns file"
    else
        print_colored "$GREEN" "✅ ML patterns file exists"
        
        # Validate JSON structure
        if jq empty "$patterns_file" 2>/dev/null; then
            print_colored "$GREEN" "✅ ML patterns file is valid JSON"
        else
            print_colored "$RED" "❌ ML patterns file contains invalid JSON"
            return 1
        fi
    fi
    
    log_setup "ML models initialized"
}

# Function to create system configuration
create_system_config() {
    print_header "Creating System Configuration"
    
    local config_file="$PROJECT_ROOT/repair_system.conf"
    
    cat > "$config_file" << EOF
# Auto-Repair System Configuration
# Generated on $(date)

# System paths
PROJECT_ROOT="$PROJECT_ROOT"
LOG_DIR="$LOG_DIR"
BACKUP_DIR="$BACKUP_DIR"
ML_MODELS_DIR="$ML_MODELS_DIR"

# GitHub configuration
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# Repair system settings
MAX_REPAIR_ATTEMPTS=3
REPAIR_COOLDOWN=300
AUTO_BACKUP=true
NOTIFICATION_LEVEL="INFO"

# Monitoring settings
MONITOR_INTERVAL=30
LOG_RETENTION_DAYS=30
METRICS_RETENTION_DAYS=90

# ML model settings
CONFIDENCE_THRESHOLD=0.75
LEARNING_RATE=0.1
PATTERN_MATCHING_THRESHOLD=0.6

EOF
    
    print_colored "$GREEN" "✅ Created system configuration: $config_file"
    log_setup "System configuration created"
}

# Function to set up cron jobs
setup_cron_jobs() {
    print_header "Setting Up Cron Jobs"
    
    # Check if user wants to set up cron jobs
    read -p "Do you want to set up automated cron jobs? (y/N): " setup_cron
    
    if [[ "$setup_cron" =~ ^[Yy]$ ]]; then
        local cron_entries=(
            "0 */6 * * * $SCRIPTS_DIR/collect-metrics.sh collect >/dev/null 2>&1"
            "0 2 * * * $SCRIPTS_DIR/collect-metrics.sh clean --days 7 >/dev/null 2>&1"
            "*/30 * * * * $SCRIPTS_DIR/monitor-repair.sh --status >/dev/null 2>&1"
        )
        
        print_colored "$BLUE" "📅 Suggested cron jobs:"
        for entry in "${cron_entries[@]}"; do
            print_colored "$WHITE" "   $entry"
        done
        
        echo
        read -p "Add these cron jobs? (y/N): " add_cron
        
        if [[ "$add_cron" =~ ^[Yy]$ ]]; then
            for entry in "${cron_entries[@]}"; do
                (crontab -l 2>/dev/null || true; echo "$entry") | crontab -
            done
            print_colored "$GREEN" "✅ Cron jobs added"
        else
            print_colored "$BLUE" "ℹ️  You can add these manually later with 'crontab -e'"
        fi
    else
        print_colored "$BLUE" "ℹ️  Skipping cron job setup"
    fi
    
    log_setup "Cron job setup completed"
}

# Function to create example workflows
create_example_workflows() {
    print_header "Creating Example Workflows"
    
    local workflow_file="$WORKFLOWS_DIR/auto-repair-example.yml"
    
    if [[ ! -f "$workflow_file" ]]; then
        cat > "$workflow_file" << 'EOF'
name: Auto-Repair Example

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  auto-repair:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt || true
    
    - name: Run auto-repair system
      run: |
        chmod +x scripts/*.sh
        ./scripts/collect-metrics.sh collect
    
    - name: Monitor system health
      run: |
        ./scripts/monitor-repair.sh --health
EOF
        
        print_colored "$GREEN" "✅ Created example workflow: $workflow_file"
    else
        print_colored "$BLUE" "📁 Example workflow already exists"
    fi
    
    log_setup "Example workflows created"
}

# Function to run system validation
validate_system() {
    print_header "Validating System Setup"
    
    local validation_errors=0
    
    # Check critical files
    local critical_files=(
        "$ML_MODELS_DIR/error-patterns.json"
        "$SCRIPTS_DIR/monitor-repair.sh"
        "$SCRIPTS_DIR/collect-metrics.sh"
        "$SCRIPTS_DIR/manual-repair.sh"
    )
    
    for file in "${critical_files[@]}"; do
        if [[ -f "$file" ]] && [[ -r "$file" ]]; then
            print_colored "$GREEN" "✅ $(basename "$file") - OK"
        else
            print_colored "$RED" "❌ $(basename "$file") - Missing or not readable"
            ((validation_errors++))
        fi
    done
    
    # Test script executability
    for script in "$SCRIPTS_DIR"/*.sh; do
        if [[ -x "$script" ]]; then
            print_colored "$GREEN" "✅ $(basename "$script") - Executable"
        else
            print_colored "$RED" "❌ $(basename "$script") - Not executable"
            ((validation_errors++))
        fi
    done
    
    # Test JSON validity
    if jq empty "$ML_MODELS_DIR/error-patterns.json" 2>/dev/null; then
        print_colored "$GREEN" "✅ ML patterns JSON - Valid"
    else
        print_colored "$RED" "❌ ML patterns JSON - Invalid"
        ((validation_errors++))
    fi
    
    # Test basic functionality
    if "$SCRIPTS_DIR/monitor-repair.sh" --help >/dev/null 2>&1; then
        print_colored "$GREEN" "✅ Monitor script - Functional"
    else
        print_colored "$RED" "❌ Monitor script - Not functional"
        ((validation_errors++))
    fi
    
    echo
    if [[ "$validation_errors" -eq 0 ]]; then
        print_colored "$GREEN" "🎉 System validation passed! All components are working correctly."
    else
        print_colored "$RED" "❌ System validation failed with $validation_errors errors."
        return 1
    fi
    
    log_setup "System validation completed with $validation_errors errors"
}

# Function to show next steps
show_next_steps() {
    print_header "Next Steps"
    
    print_colored "$WHITE" "Your auto-repair system is now set up! Here's what you can do next:"
    echo
    
    print_colored "$GREEN" "🔧 Basic Operations:"
    print_colored "$WHITE" "   • Monitor system: $SCRIPTS_DIR/monitor-repair.sh"
    print_colored "$WHITE" "   • Collect metrics: $SCRIPTS_DIR/collect-metrics.sh"
    print_colored "$WHITE" "   • Manual repairs: $SCRIPTS_DIR/manual-repair.sh"
    echo
    
    print_colored "$GREEN" "📊 Configuration:"
    print_colored "$WHITE" "   • Configuration file: $PROJECT_ROOT/repair_system.conf"
    print_colored "$WHITE" "   • ML patterns: $ML_MODELS_DIR/error-patterns.json"
    print_colored "$WHITE" "   • Logs directory: $LOG_DIR"
    echo
    
    print_colored "$GREEN" "🚀 Getting Started:"
    print_colored "$WHITE" "   1. Set GITHUB_TOKEN environment variable"
    print_colored "$WHITE" "   2. Run: $SCRIPTS_DIR/monitor-repair.sh"
    print_colored "$WHITE" "   3. Test manual repair: $SCRIPTS_DIR/manual-repair.sh"
    print_colored "$WHITE" "   4. Review logs in: $LOG_DIR"
    echo
    
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
        print_colored "$YELLOW" "⚠️  Remember to set up your GitHub token for full functionality!"
    fi
}

# Function to show help
show_help() {
    cat << EOF
Auto-Repair System Setup Script

Usage: $0 [OPTIONS]

OPTIONS:
    --force            Continue setup even if requirements are missing
    --skip-cron        Skip cron job setup
    --skip-validation  Skip system validation
    --help             Show this help message

FEATURES:
    • System requirements check
    • Directory structure creation
    • File permissions setup
    • Python dependencies installation
    • GitHub integration configuration
    • ML models initialization
    • Cron jobs setup (optional)
    • System validation

EXAMPLES:
    $0                 # Full setup with prompts
    $0 --force         # Force setup even with missing requirements
    $0 --skip-cron     # Setup without cron jobs

EOF
}

# Main execution function
main() {
    local force_setup=false
    local skip_cron=false
    local skip_validation=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                force_setup=true
                shift
                ;;
            --skip-cron)
                skip_cron=true
                shift
                ;;
            --skip-validation)
                skip_validation=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_colored "$RED" "❌ Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    print_header "🚀 Auto-Repair System Setup"
    print_colored "$WHITE" "Setting up the automatic error repair system..."
    echo
    
    # Create initial log directory
    mkdir -p "$LOG_DIR"
    
    # Run setup steps
    if [[ "$force_setup" == true ]]; then
        check_system_requirements --force
    else
        check_system_requirements
    fi
    
    create_directories
    setup_permissions
    install_python_dependencies
    configure_github
    initialize_ml_models
    create_system_config
    create_example_workflows
    
    if [[ "$skip_cron" != true ]]; then
        setup_cron_jobs
    fi
    
    if [[ "$skip_validation" != true ]]; then
        validate_system
    fi
    
    show_next_steps
    
    print_colored "$GREEN" "✅ Auto-repair system setup completed successfully!"
}

# Trap errors
trap 'print_colored "$RED" "❌ Setup failed at line $LINENO. Check the logs for details."; exit 1' ERR

# Run main function with all arguments
main "$@"