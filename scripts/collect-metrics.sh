#!/bin/bash

# =============================================================================
# Auto-Repair System Metrics Collection
# Gathers performance data and generates comprehensive reports
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
readonly METRICS_DIR="$LOG_DIR/metrics"
readonly REPORTS_DIR="$LOG_DIR/reports"
readonly ML_MODELS_DIR="$PROJECT_ROOT/.github/ml-models"

# File paths
readonly METRICS_FILE="$METRICS_DIR/repair_metrics.json"
readonly PATTERNS_FILE="$ML_MODELS_DIR/error-patterns.json"
readonly AUTO_REPAIR_LOG="$LOG_DIR/auto_repair.log"
readonly GITHUB_LOG="$LOG_DIR/github_actions.log"

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

# Function to create directory structure
setup_directories() {
    mkdir -p "$LOG_DIR" "$METRICS_DIR" "$REPORTS_DIR"
    print_colored "$GREEN" "✅ Created directory structure"
}

# Function to initialize metrics file
initialize_metrics() {
    if [[ ! -f "$METRICS_FILE" ]]; then
        cat > "$METRICS_FILE" << EOF
{
  "collection_started": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "total_repair_attempts": 0,
  "successful_repairs": 0,
  "failed_repairs": 0,
  "average_repair_time": 0,
  "pattern_effectiveness": {},
  "error_categories": {
    "dependency": {"count": 0, "success_rate": 0},
    "test": {"count": 0, "success_rate": 0},
    "build": {"count": 0, "success_rate": 0},
    "type": {"count": 0, "success_rate": 0},
    "network": {"count": 0, "success_rate": 0}
  },
  "daily_metrics": {},
  "workflow_performance": {
    "total_runs": 0,
    "successful_runs": 0,
    "failed_runs": 0,
    "average_duration": 0,
    "fastest_run": null,
    "slowest_run": null
  },
  "ml_model_accuracy": {
    "pattern_matches": 0,
    "correct_predictions": 0,
    "false_positives": 0,
    "false_negatives": 0,
    "confidence_scores": []
  }
}
EOF
        print_colored "$GREEN" "✅ Initialized metrics file"
    fi
}

# Function to collect GitHub workflow metrics
collect_workflow_metrics() {
    print_colored "$BLUE" "📊 Collecting GitHub workflow metrics..."
    
    local workflow_data
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        workflow_data=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
            "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/actions/runs?per_page=100" \
            2>/dev/null || echo '{"workflow_runs": []}')
    else
        workflow_data=$(curl -s \
            "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/actions/runs?per_page=100" \
            2>/dev/null || echo '{"workflow_runs": []}')
    fi
    
    if [[ "$(echo "$workflow_data" | jq -r '.workflow_runs // [] | length')" -eq 0 ]]; then
        print_colored "$YELLOW" "⚠️  No workflow data available"
        return
    fi
    
    # Calculate workflow metrics
    local total_runs successful_runs failed_runs avg_duration
    total_runs=$(echo "$workflow_data" | jq '.workflow_runs | length')
    successful_runs=$(echo "$workflow_data" | jq '[.workflow_runs[] | select(.conclusion == "success")] | length')
    failed_runs=$(echo "$workflow_data" | jq '[.workflow_runs[] | select(.conclusion == "failure")] | length')
    
    # Calculate average duration (in seconds)
    avg_duration=$(echo "$workflow_data" | jq -r '
        [.workflow_runs[] | select(.conclusion != null) | 
         ((.updated_at | fromdateiso8601) - (.created_at | fromdateiso8601))] | 
        if length > 0 then (add / length) else 0 end')
    
    # Update metrics file
    local updated_metrics
    updated_metrics=$(jq --argjson total "$total_runs" \
                         --argjson successful "$successful_runs" \
                         --argjson failed "$failed_runs" \
                         --argjson duration "$avg_duration" \
                         '.workflow_performance.total_runs = $total |
                          .workflow_performance.successful_runs = $successful |
                          .workflow_performance.failed_runs = $failed |
                          .workflow_performance.average_duration = $duration |
                          .last_updated = now | strftime("%Y-%m-%dT%H:%M:%SZ")' \
                         "$METRICS_FILE")
    
    echo "$updated_metrics" > "$METRICS_FILE"
    print_colored "$GREEN" "✅ Updated workflow metrics: $total_runs total, $successful_runs successful"
}

# Function to analyze error patterns from logs
analyze_error_patterns() {
    print_colored "$BLUE" "🔍 Analyzing error patterns from logs..."
    
    if [[ ! -f "$AUTO_REPAIR_LOG" ]]; then
        print_colored "$YELLOW" "⚠️  Auto repair log not found"
        return
    fi
    
    # Extract error information from logs
    local error_patterns=()
    local repair_attempts=0
    local successful_repairs=0
    
    # Parse log entries
    while IFS= read -r line; do
        if [[ "$line" =~ REPAIR_ATTEMPT ]]; then
            ((repair_attempts++))
        elif [[ "$line" =~ REPAIR_SUCCESS ]]; then
            ((successful_repairs++))
        fi
    done < "$AUTO_REPAIR_LOG"
    
    # Update pattern effectiveness
    if [[ -f "$PATTERNS_FILE" ]]; then
        local patterns_data
        patterns_data=$(jq --argjson attempts "$repair_attempts" \
                          --argjson successful "$successful_repairs" \
                          '.repair_history.pattern_matches.total_attempts = $attempts |
                           .repair_history.pattern_matches.successful_repairs = $successful |
                           .repair_history.success_metrics.total_attempts = $attempts |
                           .repair_history.success_metrics.successful_repairs = $successful |
                           .last_updated = now | strftime("%Y-%m-%dT%H:%M:%SZ")' \
                          "$PATTERNS_FILE")
        
        echo "$patterns_data" > "$PATTERNS_FILE"
    fi
    
    # Update main metrics
    local updated_metrics
    updated_metrics=$(jq --argjson attempts "$repair_attempts" \
                         --argjson successful "$successful_repairs" \
                         --argjson failed $((repair_attempts - successful_repairs)) \
                         '.total_repair_attempts = $attempts |
                          .successful_repairs = $successful |
                          .failed_repairs = $failed |
                          .last_updated = now | strftime("%Y-%m-%dT%H:%M:%SZ")' \
                         "$METRICS_FILE")
    
    echo "$updated_metrics" > "$METRICS_FILE"
    print_colored "$GREEN" "✅ Analyzed $repair_attempts repair attempts, $successful_repairs successful"
}

# Function to calculate ML model accuracy
calculate_ml_accuracy() {
    print_colored "$BLUE" "🤖 Calculating ML model accuracy..."
    
    if [[ ! -f "$PATTERNS_FILE" ]]; then
        print_colored "$YELLOW" "⚠️  ML patterns file not found"
        return
    fi
    
    # Extract accuracy metrics from patterns file
    local pattern_matches correct_predictions
    pattern_matches=$(jq -r '.repair_history.success_metrics.total_attempts // 0' "$PATTERNS_FILE")
    correct_predictions=$(jq -r '.repair_history.success_metrics.successful_repairs // 0' "$PATTERNS_FILE")
    
    local accuracy=0
    if [[ "$pattern_matches" -gt 0 ]]; then
        accuracy=$(echo "scale=4; $correct_predictions / $pattern_matches" | bc)
    fi
    
    # Update ML accuracy metrics
    local updated_metrics
    updated_metrics=$(jq --argjson matches "$pattern_matches" \
                         --argjson correct "$correct_predictions" \
                         --argjson acc "$accuracy" \
                         '.ml_model_accuracy.pattern_matches = $matches |
                          .ml_model_accuracy.correct_predictions = $correct |
                          .ml_model_accuracy.accuracy = $acc |
                          .last_updated = now | strftime("%Y-%m-%dT%H:%M:%SZ")' \
                         "$METRICS_FILE")
    
    echo "$updated_metrics" > "$METRICS_FILE"
    print_colored "$GREEN" "✅ ML accuracy: $(echo "$accuracy * 100" | bc | cut -d. -f1)%"
}

# Function to collect daily metrics
collect_daily_metrics() {
    local today
    today=$(date +"%Y-%m-%d")
    
    print_colored "$BLUE" "📅 Collecting daily metrics for $today..."
    
    # Count today's activities from logs
    local daily_repairs=0
    local daily_successes=0
    
    if [[ -f "$AUTO_REPAIR_LOG" ]]; then
        daily_repairs=$(grep "$today" "$AUTO_REPAIR_LOG" | grep -c "REPAIR_ATTEMPT" || true)
        daily_successes=$(grep "$today" "$AUTO_REPAIR_LOG" | grep -c "REPAIR_SUCCESS" || true)
    fi
    
    # Update daily metrics
    local updated_metrics
    updated_metrics=$(jq --arg date "$today" \
                         --argjson repairs "$daily_repairs" \
                         --argjson successes "$daily_successes" \
                         '.daily_metrics[$date] = {
                            "repair_attempts": $repairs,
                            "successful_repairs": $successes,
                            "success_rate": (if $repairs > 0 then ($successes / $repairs) else 0 end)
                          } |
                          .last_updated = now | strftime("%Y-%m-%dT%H:%M:%SZ")' \
                         "$METRICS_FILE")
    
    echo "$updated_metrics" > "$METRICS_FILE"
    print_colored "$GREEN" "✅ Daily metrics: $daily_repairs attempts, $daily_successes successful"
}

# Function to generate comprehensive report
generate_report() {
    local report_type="${1:-full}"
    local report_file="$REPORTS_DIR/repair_report_$(date +%Y%m%d_%H%M%S).json"
    
    print_colored "$BLUE" "📝 Generating $report_type report..."
    
    if [[ ! -f "$METRICS_FILE" ]]; then
        print_colored "$RED" "❌ Metrics file not found. Run collection first."
        return 1
    fi
    
    # Create comprehensive report
    local report_data
    report_data=$(jq --arg type "$report_type" \
                     --arg generated "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
                     '{
                       report_type: $type,
                       generated_at: $generated,
                       summary: {
                         total_repair_attempts: .total_repair_attempts,
                         successful_repairs: .successful_repairs,
                         overall_success_rate: (if .total_repair_attempts > 0 then (.successful_repairs / .total_repair_attempts) else 0 end),
                         ml_model_accuracy: .ml_model_accuracy.accuracy,
                         workflow_success_rate: (if .workflow_performance.total_runs > 0 then (.workflow_performance.successful_runs / .workflow_performance.total_runs) else 0 end)
                       },
                       detailed_metrics: .,
                       recommendations: []
                     }' "$METRICS_FILE")
    
    # Add recommendations based on metrics
    local success_rate
    success_rate=$(echo "$report_data" | jq -r '.summary.overall_success_rate')
    
    if (( $(echo "$success_rate < 0.8" | bc -l) )); then
        report_data=$(echo "$report_data" | jq '.recommendations += ["Consider updating error patterns for better accuracy"]')
    fi
    
    if (( $(echo "$success_rate < 0.5" | bc -l) )); then
        report_data=$(echo "$report_data" | jq '.recommendations += ["Review and expand ML training data"]')
    fi
    
    # Save report
    echo "$report_data" > "$report_file"
    
    # Generate human-readable summary
    local summary_file="$REPORTS_DIR/summary_$(date +%Y%m%d_%H%M%S).txt"
    cat > "$summary_file" << EOF
Auto-Repair System Report
Generated: $(date)
========================

SUMMARY:
- Total repair attempts: $(echo "$report_data" | jq -r '.summary.total_repair_attempts')
- Successful repairs: $(echo "$report_data" | jq -r '.summary.successful_repairs')
- Overall success rate: $(echo "$report_data" | jq -r '(.summary.overall_success_rate * 100 | floor)')%
- ML model accuracy: $(echo "$report_data" | jq -r '(.summary.ml_model_accuracy * 100 | floor)')%
- Workflow success rate: $(echo "$report_data" | jq -r '(.summary.workflow_success_rate * 100 | floor)')%

RECOMMENDATIONS:
EOF
    
    echo "$report_data" | jq -r '.recommendations[]' | sed 's/^/- /' >> "$summary_file"
    
    print_colored "$GREEN" "✅ Report generated:"
    print_colored "$WHITE" "   JSON: $report_file"
    print_colored "$WHITE" "   Summary: $summary_file"
}

# Function to export metrics for external analysis
export_metrics() {
    local format="${1:-json}"
    local export_file="$REPORTS_DIR/metrics_export_$(date +%Y%m%d_%H%M%S).$format"
    
    print_colored "$BLUE" "📤 Exporting metrics in $format format..."
    
    case "$format" in
        json)
            cp "$METRICS_FILE" "$export_file"
            ;;
        csv)
            # Convert daily metrics to CSV
            echo "Date,Repair Attempts,Successful Repairs,Success Rate" > "$export_file"
            jq -r '.daily_metrics | to_entries[] | 
                   "\(.key),\(.value.repair_attempts),\(.value.successful_repairs),\(.value.success_rate)"' \
                   "$METRICS_FILE" >> "$export_file"
            ;;
        *)
            print_colored "$RED" "❌ Unsupported format: $format"
            return 1
            ;;
    esac
    
    print_colored "$GREEN" "✅ Metrics exported to: $export_file"
}

# Function to clean old reports
clean_old_reports() {
    local days="${1:-7}"
    
    print_colored "$BLUE" "🧹 Cleaning reports older than $days days..."
    
    if [[ -d "$REPORTS_DIR" ]]; then
        find "$REPORTS_DIR" -name "*.json" -mtime +$days -delete
        find "$REPORTS_DIR" -name "*.txt" -mtime +$days -delete
        find "$REPORTS_DIR" -name "*.csv" -mtime +$days -delete
        print_colored "$GREEN" "✅ Cleaned old reports"
    fi
}

# Function to show help
show_help() {
    cat << EOF
Auto-Repair System Metrics Collection

Usage: $0 [COMMAND] [OPTIONS]

COMMANDS:
    collect        Collect all metrics (default)
    report         Generate comprehensive report
    export         Export metrics for analysis
    clean          Clean old reports
    
OPTIONS:
    --format FORMAT    Export format (json, csv) [default: json]
    --type TYPE        Report type (full, summary) [default: full]
    --days DAYS        Days to keep reports [default: 7]
    --help             Show this help message

EXAMPLES:
    $0                 # Collect all metrics
    $0 report          # Generate full report
    $0 export --format csv
    $0 clean --days 14

EOF
}

# Main execution function
main() {
    setup_directories
    initialize_metrics
    
    local command="${1:-collect}"
    
    case "$command" in
        collect)
            collect_workflow_metrics
            analyze_error_patterns
            calculate_ml_accuracy
            collect_daily_metrics
            print_colored "$GREEN" "✅ All metrics collected successfully"
            ;;
        report)
            local report_type="${2:-full}"
            generate_report "$report_type"
            ;;
        export)
            local format="json"
            if [[ "${2:-}" == "--format" ]] && [[ -n "${3:-}" ]]; then
                format="$3"
            fi
            export_metrics "$format"
            ;;
        clean)
            local days="7"
            if [[ "${2:-}" == "--days" ]] && [[ -n "${3:-}" ]]; then
                days="$3"
            fi
            clean_old_reports "$days"
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
    
    if ! command -v bc &> /dev/null; then
        missing_deps+=("bc")
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

# Run dependency check and main function
check_dependencies
main "$@"