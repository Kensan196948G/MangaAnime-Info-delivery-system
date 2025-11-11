#!/bin/bash
set -e

# Test execution script for Manga/Anime Information Delivery System
# This script provides comprehensive test execution with various options

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
COVERAGE_THRESHOLD=80
VERBOSE=false
PARALLEL=false
FAIL_FAST=false
OUTPUT_FORMAT="term"
REPORTS_DIR="test-reports"
MARKERS=""
TIMEOUT=300

# Function to display help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Test execution script for Manga/Anime notification system"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE         Test type: unit, integration, e2e, performance, all (default: all)"
    echo "  -c, --coverage NUM      Coverage threshold percentage (default: 80)"
    echo "  -v, --verbose           Verbose output"
    echo "  -p, --parallel          Run tests in parallel"
    echo "  -f, --fail-fast         Stop on first failure"
    echo "  -o, --output FORMAT     Output format: term, html, xml, json (default: term)"
    echo "  -r, --reports-dir DIR   Reports directory (default: test-reports)"
    echo "  -m, --markers MARKERS   Pytest markers to run (e.g., 'not slow')"
    echo "  -T, --timeout SECONDS   Test timeout in seconds (default: 300)"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --type unit --verbose"
    echo "  $0 --type performance --parallel --output html"
    echo "  $0 --markers 'not slow and not api' --fail-fast"
    echo ""
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                TEST_TYPE="$2"
                shift 2
                ;;
            -c|--coverage)
                COVERAGE_THRESHOLD="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -p|--parallel)
                PARALLEL=true
                shift
                ;;
            -f|--fail-fast)
                FAIL_FAST=true
                shift
                ;;
            -o|--output)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            -r|--reports-dir)
                REPORTS_DIR="$2"
                shift 2
                ;;
            -m|--markers)
                MARKERS="$2"
                shift 2
                ;;
            -T|--timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
}

# Function to log with timestamp and color
log() {
    local level=$1
    local message=$2
    local color=$3
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if [[ -n $color ]]; then
        echo -e "${color}[$timestamp] [$level] $message${NC}"
    else
        echo "[$timestamp] [$level] $message"
    fi
}

# Function to check prerequisites
check_prerequisites() {
    log "INFO" "Checking prerequisites..." "$BLUE"
    
    # Check if pytest is installed
    if ! command -v pytest &> /dev/null; then
        log "ERROR" "pytest is not installed. Please install with: pip install pytest" "$RED"
        exit 1
    fi
    
    # Check if coverage is installed
    if ! command -v pytest-cov &> /dev/null && ! python -c "import pytest_cov" &> /dev/null; then
        log "WARNING" "pytest-cov is not installed. Coverage reporting will be disabled." "$YELLOW"
    fi
    
    # Check if pytest-xdist is installed for parallel execution
    if $PARALLEL && ! python -c "import xdist" &> /dev/null; then
        log "WARNING" "pytest-xdist is not installed. Parallel execution will be disabled." "$YELLOW"
        PARALLEL=false
    fi
    
    # Check if pytest-html is installed for HTML reports
    if [[ $OUTPUT_FORMAT == "html" ]] && ! python -c "import pytest_html" &> /dev/null; then
        log "WARNING" "pytest-html is not installed. HTML reports will be disabled." "$YELLOW"
        OUTPUT_FORMAT="term"
    fi
    
    log "INFO" "Prerequisites check completed." "$GREEN"
}

# Function to setup environment
setup_environment() {
    log "INFO" "Setting up test environment..." "$BLUE"
    
    # Create reports directory
    mkdir -p "$REPORTS_DIR"
    
    # Set environment variables for testing
    export TEST_MODE=true
    export LOG_LEVEL=DEBUG
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    # Clean up any previous test artifacts
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
    
    log "INFO" "Test environment setup completed." "$GREEN"
}

# Function to build pytest command
build_pytest_command() {
    local cmd="pytest"
    
    # Add test paths based on test type
    case $TEST_TYPE in
        unit)
            cmd="$cmd tests/test_database.py tests/test_config.py tests/test_filtering.py"
            ;;
        integration)
            cmd="$cmd tests/test_anilist_api.py tests/test_rss_processing.py tests/test_google_apis.py tests/test_mailer_integration.py tests/test_calendar_integration.py"
            ;;
        e2e)
            cmd="$cmd tests/test_e2e_workflow.py"
            ;;
        performance)
            cmd="$cmd tests/test_performance.py"
            ;;
        all)
            cmd="$cmd tests/"
            ;;
        *)
            log "ERROR" "Invalid test type: $TEST_TYPE" "$RED"
            exit 1
            ;;
    esac
    
    # Add verbose output
    if $VERBOSE; then
        cmd="$cmd -v"
    fi
    
    # Add parallel execution
    if $PARALLEL; then
        local num_workers=$(nproc 2>/dev/null || echo 4)
        cmd="$cmd -n $num_workers"
    fi
    
    # Add fail-fast option
    if $FAIL_FAST; then
        cmd="$cmd -x"
    fi
    
    # Add markers
    if [[ -n $MARKERS ]]; then
        cmd="$cmd -m '$MARKERS'"
    fi
    
    # Add timeout
    cmd="$cmd --timeout=$TIMEOUT"
    
    # Add coverage reporting
    if command -v pytest-cov &> /dev/null || python -c "import pytest_cov" &> /dev/null 2>&1; then
        cmd="$cmd --cov=modules --cov-report=term-missing --cov-report=html:$REPORTS_DIR/coverage-html --cov-fail-under=$COVERAGE_THRESHOLD"
    fi
    
    # Add output format specific options
    case $OUTPUT_FORMAT in
        html)
            cmd="$cmd --html=$REPORTS_DIR/report.html --self-contained-html"
            ;;
        xml)
            cmd="$cmd --junitxml=$REPORTS_DIR/report.xml"
            ;;
        json)
            cmd="$cmd --json-report --json-report-file=$REPORTS_DIR/report.json"
            ;;
    esac
    
    # Add common options
    cmd="$cmd --tb=short --strict-markers --strict-config"
    
    echo "$cmd"
}

# Function to run tests
run_tests() {
    log "INFO" "Starting test execution..." "$BLUE"
    
    local pytest_cmd=$(build_pytest_command)
    log "INFO" "Executing: $pytest_cmd" "$BLUE"
    
    local start_time=$(date +%s)
    local exit_code=0
    
    # Run the tests
    if $VERBOSE; then
        eval "$pytest_cmd"
        exit_code=$?
    else
        eval "$pytest_cmd" 2>&1 | tee "$REPORTS_DIR/test_output.log"
        exit_code=${PIPESTATUS[0]}
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [[ $exit_code -eq 0 ]]; then
        log "INFO" "All tests passed successfully in ${duration}s!" "$GREEN"
    else
        log "ERROR" "Tests failed with exit code $exit_code after ${duration}s" "$RED"
    fi
    
    return $exit_code
}

# Function to generate summary report
generate_summary() {
    log "INFO" "Generating test summary..." "$BLUE"
    
    local summary_file="$REPORTS_DIR/summary.txt"
    
    cat > "$summary_file" << EOF
Manga/Anime Notification System Test Summary
==========================================

Execution Details:
- Test Type: $TEST_TYPE
- Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
- Coverage Threshold: ${COVERAGE_THRESHOLD}%
- Parallel Execution: $PARALLEL
- Fail Fast: $FAIL_FAST
- Output Format: $OUTPUT_FORMAT

Test Files Executed:
EOF
    
    # List test files that were run
    case $TEST_TYPE in
        unit)
            echo "- Unit Tests: database, config, filtering" >> "$summary_file"
            ;;
        integration)
            echo "- Integration Tests: AniList API, RSS processing, Gmail, Calendar" >> "$summary_file"
            ;;
        e2e)
            echo "- End-to-End Tests: complete workflow testing" >> "$summary_file"
            ;;
        performance)
            echo "- Performance Tests: load testing, resource usage" >> "$summary_file"
            ;;
        all)
            echo "- All Test Suites: comprehensive testing" >> "$summary_file"
            ;;
    esac
    
    echo "" >> "$summary_file"
    
    # Add coverage information if available
    if [[ -f "$REPORTS_DIR/coverage-html/index.html" ]]; then
        echo "Coverage Reports Generated:" >> "$summary_file"
        echo "- HTML Report: $REPORTS_DIR/coverage-html/index.html" >> "$summary_file"
    fi
    
    # Add output reports
    case $OUTPUT_FORMAT in
        html)
            echo "- HTML Test Report: $REPORTS_DIR/report.html" >> "$summary_file"
            ;;
        xml)
            echo "- JUnit XML Report: $REPORTS_DIR/report.xml" >> "$summary_file"
            ;;
        json)
            echo "- JSON Report: $REPORTS_DIR/report.json" >> "$summary_file"
            ;;
    esac
    
    log "INFO" "Summary report generated: $summary_file" "$GREEN"
}

# Function to run linting and code quality checks
run_quality_checks() {
    log "INFO" "Running code quality checks..." "$BLUE"
    
    # Check if flake8 is available
    if command -v flake8 &> /dev/null; then
        log "INFO" "Running flake8 linting..." "$BLUE"
        flake8 modules/ tests/ --output-file="$REPORTS_DIR/flake8_report.txt" --format=text || {
            log "WARNING" "Flake8 found issues. Check $REPORTS_DIR/flake8_report.txt" "$YELLOW"
        }
    fi
    
    # Check if black is available
    if command -v black &> /dev/null; then
        log "INFO" "Checking code formatting with black..." "$BLUE"
        black --check --diff modules/ tests/ > "$REPORTS_DIR/black_report.txt" 2>&1 || {
            log "WARNING" "Black formatting issues found. Check $REPORTS_DIR/black_report.txt" "$YELLOW"
        }
    fi
    
    # Check if mypy is available
    if command -v mypy &> /dev/null; then
        log "INFO" "Running type checking with mypy..." "$BLUE"
        mypy modules/ --ignore-missing-imports --output "$REPORTS_DIR/mypy_report.txt" || {
            log "WARNING" "MyPy type checking issues found. Check $REPORTS_DIR/mypy_report.txt" "$YELLOW"
        }
    fi
    
    log "INFO" "Code quality checks completed." "$GREEN"
}

# Function to check for security vulnerabilities
run_security_checks() {
    log "INFO" "Running security checks..." "$BLUE"
    
    # Check if safety is available
    if command -v safety &> /dev/null; then
        log "INFO" "Checking dependencies with safety..." "$BLUE"
        safety check --json --output "$REPORTS_DIR/safety_report.json" || {
            log "WARNING" "Security vulnerabilities found. Check $REPORTS_DIR/safety_report.json" "$YELLOW"
        }
    fi
    
    # Check if bandit is available
    if command -v bandit &> /dev/null; then
        log "INFO" "Running bandit security analysis..." "$BLUE"
        bandit -r modules/ -f json -o "$REPORTS_DIR/bandit_report.json" || {
            log "WARNING" "Security issues found. Check $REPORTS_DIR/bandit_report.json" "$YELLOW"
        }
    fi
    
    log "INFO" "Security checks completed." "$GREEN"
}

# Function to cleanup after tests
cleanup() {
    log "INFO" "Cleaning up test environment..." "$BLUE"
    
    # Remove temporary test files
    find . -name "test_*.db" -delete 2>/dev/null || true
    find . -name "*.tmp" -delete 2>/dev/null || true
    
    # Preserve important artifacts
    if [[ -d "$REPORTS_DIR" ]]; then
        log "INFO" "Test reports preserved in: $REPORTS_DIR" "$GREEN"
    fi
    
    log "INFO" "Cleanup completed." "$GREEN"
}

# Main execution function
main() {
    local start_time=$(date +%s)
    local overall_exit_code=0
    
    # Parse arguments
    parse_args "$@"
    
    # Display banner
    echo -e "${BLUE}"
    echo "=============================================="
    echo " Manga/Anime Notification System Test Runner"
    echo "=============================================="
    echo -e "${NC}"
    
    # Setup
    check_prerequisites
    setup_environment
    
    # Run main tests
    if ! run_tests; then
        overall_exit_code=1
    fi
    
    # Run additional checks if requested
    if [[ $TEST_TYPE == "all" ]] || [[ $TEST_TYPE == "quality" ]]; then
        run_quality_checks
        run_security_checks
    fi
    
    # Generate reports
    generate_summary
    
    # Display final results
    local end_time=$(date +%s)
    local total_duration=$((end_time - start_time))
    
    echo -e "${BLUE}"
    echo "=============================================="
    if [[ $overall_exit_code -eq 0 ]]; then
        echo -e "${GREEN} ✅ ALL TESTS COMPLETED SUCCESSFULLY!"
        echo -e "${GREEN} Total execution time: ${total_duration}s"
        echo -e "${GREEN} Reports available in: $REPORTS_DIR"
    else
        echo -e "${RED} ❌ TESTS FAILED!"
        echo -e "${RED} Total execution time: ${total_duration}s"
        echo -e "${RED} Check reports in: $REPORTS_DIR for details"
    fi
    echo "=============================================="
    echo -e "${NC}"
    
    # Cleanup
    cleanup
    
    exit $overall_exit_code
}

# Trap to ensure cleanup on script interruption
trap 'log "INFO" "Script interrupted. Cleaning up..." "$YELLOW"; cleanup; exit 130' INT TERM

# Run main function with all arguments
main "$@"