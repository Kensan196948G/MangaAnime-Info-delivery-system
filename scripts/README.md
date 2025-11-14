# Auto-Repair System Monitoring & Operations Scripts

This directory contains comprehensive monitoring and operation scripts for the 30-minute cycle auto-repair system.

## Scripts Overview

### 📊 monitor-30min-loop.sh
**Real-time monitoring script with auto-refresh capabilities**

```bash
# Basic monitoring (refreshes every 10 seconds)
./monitor-30min-loop.sh

# Custom refresh interval
./monitor-30min-loop.sh --refresh-interval 5

# Show help
./monitor-30min-loop.sh --help
```

**Features:**
- Live system status with color-coded output
- Current loop iteration and cycle status
- GitHub Actions workflow monitoring
- Active repair process detection
- Recent activity logs
- System resource usage
- Workflow health indicators
- Next action predictions
- Interactive keyboard shortcuts (q=quit, r=refresh, h=help)

### 🐍 repair-dashboard.py
**Comprehensive Python dashboard with analytics and export capabilities**

```bash
# Interactive dashboard
./repair-dashboard.py --interactive

# Single view dashboard
./repair-dashboard.py --dashboard

# Watch mode (auto-refresh every 30 seconds)
./repair-dashboard.py --watch 30

# Export data
./repair-dashboard.py --export json --output repair_data.json
./repair-dashboard.py --export csv --output repair_data.csv

# Generate trend graphs
./repair-dashboard.py --graph --output trends.png
```

**Features:**
- Comprehensive system overview with statistics
- Historical trend analysis and visualization
- Performance metrics calculation
- SQLite database for analytics storage
- Export capabilities (JSON/CSV)
- Graphical trend generation (requires matplotlib)
- Interactive mode with real-time updates
- Repair statistics and success rates

**Dependencies:**
```bash
# Required
pip3 install sqlite3

# Optional (for advanced features)
pip3 install matplotlib pandas numpy seaborn scikit-learn
```

### 🚨 emergency-stop.sh
**Emergency stop script with state preservation**

```bash
# Interactive emergency stop
./emergency-stop.sh

# Force stop without confirmation
./emergency-stop.sh --force

# Check system status only
./emergency-stop.sh --status

# Resume from saved state
./emergency-stop.sh --resume

# Force kill all processes
./emergency-stop.sh --kill-all

# Preserve state files for debugging
./emergency-stop.sh --preserve-state
```

**Features:**
- Immediate termination of all repair operations
- GitHub workflow cancellation
- State preservation for recovery
- Graceful shutdown with fallback to force termination
- Emergency state backup and restore
- Lock file management
- Process cleanup and validation
- Detailed logging of emergency actions

### 📈 repair-analytics.py
**Advanced analytics with ML-powered insights**

```bash
# Show analytics dashboard
./repair-analytics.py --dashboard

# Analyze failure patterns
./repair-analytics.py --patterns

# Generate optimization recommendations
./repair-analytics.py --recommendations

# Trend analysis (last 30 days)
./repair-analytics.py --trends 30

# Detect anomalies using ML
./repair-analytics.py --anomalies

# Create visualizations
./repair-analytics.py --visualize --output-dir analytics_output

# Export comprehensive report
./repair-analytics.py --export analysis_report.json
```

**Features:**
- Advanced failure pattern analysis
- Machine learning anomaly detection
- Performance metrics calculation
- Optimization recommendations generation
- Trend analysis and predictions
- Comprehensive visualization creation
- Statistical analysis and reporting
- Success rate tracking and improvement suggestions

**ML Dependencies:**
```bash
pip3 install pandas numpy matplotlib seaborn scikit-learn
```

### ⚕️ system-health.sh
**Comprehensive system health validation**

```bash
# Full health check
./system-health.sh

# Check with automatic fixes
./system-health.sh --fix

# Detailed output
./system-health.sh --detailed

# Export health report
./system-health.sh --export health_report.json

# Check specific components
./system-health.sh --deps-only      # Dependencies only
./system-health.sh --github-only    # GitHub integration only
./system-health.sh --config-only    # Configuration files only

# Quiet mode (exit codes only)
./system-health.sh --quiet
```

**Features:**
- Comprehensive dependency validation
- GitHub integration verification
- Workflow configuration validation
- System resource monitoring
- Permission and access checks
- Automatic issue resolution
- Health scoring system
- Detailed reporting and recommendations

**Health Score Categories:**
- **90-100%**: Excellent (All systems optimal)
- **80-89%**: Good (Minor optimizations available)
- **70-79%**: Fair (Some issues need attention)
- **50-69%**: Poor (Multiple issues detected)
- **0-49%**: Critical (System needs immediate attention)

## Quick Start

1. **Make scripts executable:**
```bash
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

2. **Install dependencies:**
```bash
# Essential dependencies
sudo apt-get install jq bc sqlite3 curl git python3 python3-pip

# Python packages
pip3 install requests PyYAML gitpython

# Optional ML/visualization packages
pip3 install matplotlib pandas numpy seaborn scikit-learn
```

3. **Run system health check:**
```bash
./scripts/system-health.sh --fix
```

4. **Start monitoring:**
```bash
# Terminal 1: Real-time monitor
./scripts/monitor-30min-loop.sh

# Terminal 2: Analytics dashboard
./scripts/repair-dashboard.py --interactive
```

## Integration with Auto-Repair System

These scripts integrate seamlessly with the main auto-repair system:

- **State File**: All scripts read from `.repair_state.json` for current system status
- **Log Directory**: Centralized logging in `logs/` directory
- **Database**: Shared analytics database at `repair_analytics.db`
- **Workflow Integration**: Direct GitHub Actions integration via GitHub CLI

## Monitoring Workflow

1. **Continuous Monitoring**: Use `monitor-30min-loop.sh` for real-time status
2. **Daily Analytics**: Run `repair-analytics.py --dashboard` for insights
3. **Weekly Health Checks**: Execute `system-health.sh --detailed --export`
4. **Emergency Response**: Use `emergency-stop.sh` when immediate intervention needed

## Exit Codes

All scripts follow consistent exit code conventions:

- **0**: Success/Healthy
- **1**: Warnings/Minor issues
- **2**: Errors/Major issues  
- **3**: Critical/System unusable

## File Structure

```
scripts/
├── monitor-30min-loop.sh     # Real-time monitoring
├── repair-dashboard.py       # Comprehensive dashboard
├── emergency-stop.sh         # Emergency stop system
├── repair-analytics.py       # Advanced analytics
├── system-health.sh          # Health validation
└── README.md                 # This documentation

Related files:
├── .repair_state.json        # Current system state
├── repair_analytics.db       # Analytics database
├── logs/                     # System logs
└── .github/workflows/        # GitHub Actions workflows
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
```bash
chmod +x scripts/*.sh scripts/*.py
```

2. **Missing Dependencies**
```bash
./scripts/system-health.sh --deps-only
```

3. **GitHub CLI Not Authenticated**
```bash
gh auth login
```

4. **Database Issues**
```bash
rm repair_analytics.db  # Will be recreated automatically
```

### Log Locations

- **Health Checks**: `logs/health_check_YYYYMMDD_HHMMSS.log`
- **Emergency Stops**: `logs/emergency_stop_YYYYMMDD_HHMMSS.log`
- **Analytics**: Stored in SQLite database `repair_analytics.db`
- **Monitoring**: Real-time display only (use `--export` for persistence)

## Support

For issues or questions:
1. Run `./scripts/system-health.sh --detailed` for diagnostics
2. Check `logs/` directory for error details
3. Use `./scripts/emergency-stop.sh --status` to verify system state
4. Generate analytics report with `./scripts/repair-analytics.py --export`