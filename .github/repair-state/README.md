# Auto-Repair Loop System State

This directory contains the state management files for the automated GitHub Actions repair system.

## File Descriptions

### `loop-state.json`
Tracks the current iteration and status of the auto-repair loop.
- `iteration`: Current loop iteration (0-10)
- `start_time`: When the current loop cycle started
- `last_run`: Last execution timestamp
- `total_repairs`: Total number of repairs attempted

### `repair-history.json`
Historical log of all repair attempts with outcomes.
- `repairs[]`: Array of repair records with success/failure status
- `total_repairs`: Total count of repair attempts
- `success_rate`: Overall success percentage
- `statistics`: Breakdown by error type, strategy, and time period

### `error-patterns.json`
Machine learning database for error pattern recognition.
- `patterns{}`: Error type frequencies and success rates
- `learning_data`: Successful/failed patterns for ML improvement
- `common_fixes`: Most effective repair strategies per error type

## System Operation

The auto-repair system operates in three main workflows:

1. **auto-repair-loop.yml** (every 30 minutes)
   - Detects failed workflows
   - Triggers parallel repairs
   - Manages loop iteration state

2. **parallel-repair.yml** (on-demand)
   - Analyzes specific failure patterns
   - Executes targeted repair strategies
   - Commits and pushes fixes

3. **verify-repair.yml** (every 40 minutes)
   - Validates repair effectiveness
   - Determines if loop should continue
   - Creates issues for manual intervention

## Manual Management

To manually reset the system:
```bash
# Reset loop iteration
gh workflow run auto-repair-loop.yml --field force_reset=true

# Trigger immediate verification
gh workflow run verify-repair.yml

# View current state
cat .github/repair-state/loop-state.json | jq .
```

## Monitoring

Check system health:
```bash
# View recent repairs
cat .github/repair-state/repair-history.json | jq '.repairs[-10:]'

# Check success rate
cat .github/repair-state/repair-history.json | jq '.success_rate'

# View error patterns
cat .github/repair-state/error-patterns.json | jq '.patterns'
```