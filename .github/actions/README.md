# SubAgent Parallel Repair System - Custom Actions

This directory contains custom GitHub Actions designed for the SubAgent parallel repair system, optimized for 30-minute cycle operations with 25-minute timeout enforcement.

## 🛠️ Actions Overview

### 1. parallel-error-analyzer/
**Parallel Error Analysis Action**

Analyzes multiple workflow errors simultaneously using matrix strategy with concurrent pattern matching.

**Key Features:**
- Supports up to 5 concurrent error analyses
- Advanced pattern matching with confidence scoring
- Returns detailed repair strategies for each error
- Configurable analysis timeout (default: 5 minutes)

**Usage:**
```yaml
- name: Analyze Errors in Parallel
  uses: ./.github/actions/parallel-error-analyzer
  with:
    error-logs: ${{ toJson(steps.collect-errors.outputs.error-logs) }}
    max-concurrent: '5'
    analysis-timeout: '300'
    pattern-db-path: '.github/repair-patterns.json'
```

### 2. subagent-repair-executor/
**SubAgent Repair Executor**

Executes repairs in parallel threads with comprehensive progress tracking and 25-minute timeout enforcement.

**Key Features:**
- Parallel repair execution (up to 5 threads)
- 25-minute timeout enforcement
- Dry-run mode for testing
- Real-time progress reporting
- Automatic rollback on critical failures

**Usage:**
```yaml
- name: Execute Repairs in Parallel
  uses: ./.github/actions/subagent-repair-executor
  with:
    repair-strategies: ${{ steps.analyze-errors.outputs.repair-strategies }}
    max-parallel: '5'
    execution-timeout: '25'
    dry-run: 'false'
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### 3. repair-state-manager/
**State Management Action**

Manages repair state, loop iteration tracking, and pattern learning with persistent JSON storage.

**Key Features:**
- Loop iteration tracking (7 cycles × 30 iterations)
- Repair history management
- Pattern learning and accuracy tracking
- Statistical analysis and recommendations
- State persistence across workflow runs

**Usage:**
```yaml
- name: Update Repair State
  uses: ./.github/actions/repair-state-manager
  with:
    operation: 'update'
    iteration-number: ${{ github.run_number }}
    repair-results: ${{ steps.execute-repairs.outputs.execution-results }}
    state-file-path: '.github/repair-state.json'
```

### 4. repair-validator/
**Repair Validation Action**

Validates repair effectiveness and determines loop continuation with comprehensive testing.

**Key Features:**
- Multi-level validation (quick/thorough/comprehensive)
- Effectiveness scoring (0-100)
- Side-effects detection
- System integrity verification
- Loop continuation logic

**Usage:**
```yaml
- name: Validate Repair Effectiveness
  uses: ./.github/actions/repair-validator
  with:
    repair-results: ${{ steps.execute-repairs.outputs.execution-results }}
    previous-errors: ${{ steps.collect-errors.outputs.error-logs }}
    validation-mode: 'thorough'
    success-threshold: '0.7'
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

## 🔄 Integration with Main Workflow

These actions are designed to work together in a cohesive repair pipeline:

```yaml
name: SubAgent Parallel Repair System

on:
  workflow_dispatch:
  schedule:
    - cron: '*/30 * * * *'  # Every 30 minutes

jobs:
  parallel-repair:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
      
    - name: Load State
      uses: ./.github/actions/repair-state-manager
      with:
        operation: 'load'
        
    - name: Collect Errors
      id: collect-errors
      run: |
        # Error collection logic
        
    - name: Analyze Errors
      id: analyze-errors
      uses: ./.github/actions/parallel-error-analyzer
      with:
        error-logs: ${{ steps.collect-errors.outputs.error-logs }}
        max-concurrent: '5'
        
    - name: Execute Repairs
      id: execute-repairs
      uses: ./.github/actions/subagent-repair-executor
      with:
        repair-strategies: ${{ steps.analyze-errors.outputs.repair-strategies }}
        execution-timeout: '25'
        github-token: ${{ secrets.GITHUB_TOKEN }}
        
    - name: Validate Repairs
      id: validate-repairs
      uses: ./.github/actions/repair-validator
      with:
        repair-results: ${{ steps.execute-repairs.outputs.execution-results }}
        previous-errors: ${{ steps.collect-errors.outputs.error-logs }}
        github-token: ${{ secrets.GITHUB_TOKEN }}
        
    - name: Update State
      uses: ./.github/actions/repair-state-manager
      with:
        operation: 'update'
        iteration-number: ${{ github.run_number }}
        repair-results: ${{ steps.execute-repairs.outputs.execution-results }}
        
    - name: Determine Next Action
      run: |
        if [[ "${{ steps.validate-repairs.outputs.continue-loop }}" == "true" ]]; then
          echo "🔄 Scheduling next repair cycle"
        else
          echo "✅ Repair cycle complete"
        fi
```

## 📊 Performance Characteristics

### Timing Constraints
- **Total cycle time:** 30 minutes
- **Repair execution timeout:** 25 minutes
- **Analysis timeout:** 5 minutes per error
- **Validation timeout:** 2 minutes per repair

### Concurrency Limits
- **Error analysis:** Up to 5 concurrent analyses
- **Repair execution:** Up to 5 parallel threads
- **Memory usage:** Optimized for GitHub Actions runners
- **API rate limits:** Respects GitHub API constraints

### State Management
- **Persistence:** JSON files in `.github/` directory
- **History retention:** Last 100 repair cycles
- **Pattern learning:** Continuous accuracy improvement
- **Statistics tracking:** Success rates, timing, effectiveness

## 🔧 Configuration

### Required Secrets
- `GITHUB_TOKEN`: Standard GitHub token with appropriate permissions

### Optional Configuration Files
- `.github/repair-patterns.json`: Custom error patterns
- `.github/repair-state.json`: Persistent state (auto-created)
- `.github/repair-config.json`: System configuration

### Environment Variables
- `DEBUG_MODE`: Enable verbose logging (default: false)
- `MAX_ITERATIONS`: Override default iteration limit
- `TIMEOUT_BUFFER`: Additional timeout buffer in seconds

## 🚀 Deployment

1. Ensure all actions are in place in `.github/actions/`
2. Install dependencies for each action:
   ```bash
   cd .github/actions/parallel-error-analyzer && npm install
   cd ../subagent-repair-executor && npm install
   cd ../repair-state-manager && npm install
   cd ../repair-validator && npm install
   ```
3. Configure your main workflow to use these actions
4. Test with dry-run mode first
5. Monitor execution through GitHub Actions logs

## 📈 Monitoring and Metrics

Each action provides detailed metrics and logging:

- **Performance metrics:** Execution times, success rates
- **Error analysis:** Pattern matching accuracy, repair effectiveness
- **System health:** Resource usage, timeout occurrences
- **Learning progress:** Pattern accuracy improvements over time

For detailed monitoring, check the outputs of each action and the persistent state files.