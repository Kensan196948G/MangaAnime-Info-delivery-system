#!/usr/bin/env node
/**
 * Performance Report Generator for Auto-Repair Loop System
 * アニメ・マンガ情報配信システム - パフォーマンスレポート生成器
 */

const fs = require('fs');
const path = require('path');

// Default configuration
const config = {
  iteration: 1,
  loopId: 'unknown',
  ciStatus: 'unknown',
  runId: 'unknown',
  outputDir: 'reports',
  stateFile: '.github/state/loop-state.json'
};

// Parse command line arguments
function parseArgs() {
  const args = process.argv.slice(2);
  
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i];
    const value = args[i + 1];
    
    switch (key) {
      case '--iteration':
        config.iteration = parseInt(value) || 1;
        break;
      case '--loop-id':
        config.loopId = value || 'unknown';
        break;
      case '--ci-status':
        config.ciStatus = value || 'unknown';
        break;
      case '--run-id':
        config.runId = value || 'unknown';
        break;
      case '--output-dir':
        config.outputDir = value || 'reports';
        break;
      case '--state-file':
        config.stateFile = value || '.github/state/loop-state.json';
        break;
      case '--help':
        console.log(`
Usage: node performance-report.js [options]

Options:
  --iteration N        Current iteration number
  --loop-id ID         Unique loop identifier
  --ci-status STATUS   CI workflow status (success/failure/cancelled)
  --run-id ID          GitHub Actions run ID
  --output-dir DIR     Output directory for reports (default: reports)
  --state-file FILE    Path to state file (default: .github/state/loop-state.json)
  --help               Show this help message
        `);
        process.exit(0);
      default:
        console.error(`Unknown option: ${key}`);
        process.exit(1);
    }
  }
}

// Utility functions
function log(message) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${message}`);
}

function ensureDirectory(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
    log(`📁 Created directory: ${dir}`);
  }
}

function loadState() {
  try {
    if (fs.existsSync(config.stateFile)) {
      const data = fs.readFileSync(config.stateFile, 'utf8');
      return JSON.parse(data);
    }
  } catch (error) {
    log(`⚠️ Error loading state file: ${error.message}`);
  }
  return {};
}

function saveState(state) {
  try {
    ensureDirectory(path.dirname(config.stateFile));
    fs.writeFileSync(config.stateFile, JSON.stringify(state, null, 2));
    log(`💾 State saved to: ${config.stateFile}`);
  } catch (error) {
    log(`❌ Error saving state: ${error.message}`);
  }
}

// Performance metrics calculation
function calculateMetrics(state) {
  const startTime = state.start_time ? new Date(state.start_time) : new Date();
  const currentTime = new Date();
  const totalDuration = Math.floor((currentTime - startTime) / 1000); // seconds
  
  const iterations = state.iterations || [];
  const successCount = iterations.filter(i => i.status === 'success').length;
  const failureCount = iterations.filter(i => i.status === 'failure').length;
  const totalIterations = iterations.length;
  
  const successRate = totalIterations > 0 ? (successCount / totalIterations * 100).toFixed(1) : 0;
  const averageIterationTime = totalIterations > 0 ? Math.floor(totalDuration / totalIterations) : 0;
  
  return {
    totalDuration,
    totalIterations,
    successCount,
    failureCount,
    successRate,
    averageIterationTime,
    currentIteration: config.iteration,
    currentStatus: config.ciStatus
  };
}

// Generate performance charts (ASCII art)
function generatePerformanceChart(iterations) {
  if (!iterations || iterations.length === 0) {
    return 'No iteration data available / 反復データなし';
  }
  
  const maxIterations = Math.min(iterations.length, 20); // Show last 20 iterations
  const recentIterations = iterations.slice(-maxIterations);
  
  let chart = '\n```\nIteration Performance Chart / 反復パフォーマンスチャート\n\n';
  chart += 'Iteration |  Status  | Result\n';
  chart += '----------|----------|--------\n';
  
  recentIterations.forEach((iteration, index) => {
    const iterNum = String(iteration.iteration || index + 1).padStart(9, ' ');
    const status = iteration.status.padEnd(8, ' ');
    const symbol = iteration.status === 'success' ? '✅' : 
                   iteration.status === 'failure' ? '❌' : '⚠️';
    
    chart += `${iterNum} | ${status} | ${symbol}\n`;
  });
  
  chart += '\n```\n';
  return chart;
}

// Generate trend analysis
function generateTrendAnalysis(iterations) {
  if (!iterations || iterations.length < 3) {
    return {
      trend: 'insufficient_data',
      description: 'データ不足により傾向分析不可 / Insufficient data for trend analysis',
      recommendation: '更なるデータ収集が必要 / More data collection needed'
    };
  }
  
  const recent = iterations.slice(-5); // Last 5 iterations
  const successCount = recent.filter(i => i.status === 'success').length;
  const failureCount = recent.filter(i => i.status === 'failure').length;
  
  if (successCount >= 3) {
    return {
      trend: 'improving',
      description: '改善傾向 - 成功率が向上しています / Improving trend - success rate is increasing',
      recommendation: '現在の修復戦略を継続 / Continue current repair strategy'
    };
  } else if (failureCount >= 4) {
    return {
      trend: 'degrading',
      description: '悪化傾向 - 失敗が続いています / Degrading trend - failures are persisting',
      recommendation: '修復戦略の見直しが必要 / Repair strategy review needed'
    };
  } else {
    return {
      trend: 'stable',
      description: '安定状態 - 成功と失敗が混在 / Stable state - mixed success and failures',
      recommendation: '継続的な監視が必要 / Continuous monitoring required'
    };
  }
}

// Generate detailed performance report
function generateDetailedReport(state, metrics) {
  const timestamp = new Date().toISOString();
  const trendAnalysis = generateTrendAnalysis(state.iterations);
  const performanceChart = generatePerformanceChart(state.iterations);
  
  return `# 📊 Performance Report - Iteration ${config.iteration}
# パフォーマンスレポート - 反復 ${config.iteration}

## 📈 Executive Summary / エグゼクティブサマリー

- **Loop ID / ループID**: ${config.loopId}
- **Current Iteration / 現在の反復**: ${metrics.currentIteration}
- **Current Status / 現在のステータス**: ${metrics.currentStatus}
- **Total Runtime / 総実行時間**: ${Math.floor(metrics.totalDuration / 3600)}h ${Math.floor((metrics.totalDuration % 3600) / 60)}m ${metrics.totalDuration % 60}s
- **Success Rate / 成功率**: ${metrics.successRate}%
- **GitHub Actions Run ID**: ${config.runId}

## 🎯 Key Performance Indicators / 主要パフォーマンス指標

### Overall Metrics / 全体メトリクス

| Metric / メトリクス | Value / 値 | Description / 説明 |
|---------------------|------------|-------------------|
| Total Iterations / 総反復数 | ${metrics.totalIterations} | 実行された総反復数 |
| Successful Iterations / 成功反復数 | ${metrics.successCount} | 成功した反復の数 |
| Failed Iterations / 失敗反復数 | ${metrics.failureCount} | 失敗した反復の数 |
| Success Rate / 成功率 | ${metrics.successRate}% | 全反復における成功の割合 |
| Average Iteration Time / 平均反復時間 | ${metrics.averageIterationTime}s | 1反復あたりの平均実行時間 |

### Current Iteration Details / 現在の反復詳細

- **Iteration Number / 反復番号**: ${config.iteration}
- **Status / ステータス**: ${config.ciStatus}
- **Timestamp / タイムスタンプ**: ${timestamp}
- **Loop Progress / ループ進捗**: ${config.iteration}/${state.max_iterations || 10}

## 📊 Performance Visualization / パフォーマンス可視化

${performanceChart}

## 📈 Trend Analysis / 傾向分析

### Current Trend / 現在の傾向
**${trendAnalysis.trend.toUpperCase()}**

${trendAnalysis.description}

### Recommendation / 推奨事項
${trendAnalysis.recommendation}

## 🔍 Detailed Analysis / 詳細分析

### System Health / システム健全性

`;

  // Add system health indicators
  const healthIndicators = [];
  
  if (metrics.successRate >= 80) {
    healthIndicators.push('🟢 **Excellent**: Success rate above 80% / 成功率80%以上');
  } else if (metrics.successRate >= 60) {
    healthIndicators.push('🟡 **Good**: Success rate 60-80% / 成功率60-80%');
  } else if (metrics.successRate >= 40) {
    healthIndicators.push('🟠 **Fair**: Success rate 40-60% / 成功率40-60%');
  } else {
    healthIndicators.push('🔴 **Poor**: Success rate below 40% / 成功率40%未満');
  }
  
  if (metrics.totalIterations <= 3) {
    healthIndicators.push('🔵 **Early Stage**: Still gathering data / データ収集段階');
  } else if (metrics.totalIterations >= 8) {
    healthIndicators.push('🟣 **Mature**: Sufficient data for analysis / 分析に十分なデータ');
  }
  
  return `${healthIndicators.join('\n')}\n\n### Performance Trends / パフォーマンス傾向

${trendAnalysis.trend === 'improving' ? '📈' : trendAnalysis.trend === 'degrading' ? '📉' : '📊'} **Trend Direction / 傾向方向**: ${trendAnalysis.trend}

#### Recent Performance Pattern / 最近のパフォーマンスパターン

`;

  // Add recent pattern analysis
  let patternReport = ``;
  const recentIterations = (state.iterations || []).slice(-5);
  
  if (recentIterations.length > 0) {
    patternReport += `Last 5 iterations / 直近5反復:\n\n`;
    recentIterations.forEach((iteration, index) => {
      const status = iteration.status === 'success' ? '✅ Success' : 
                     iteration.status === 'failure' ? '❌ Failure' : '⚠️ Other';
      patternReport += `${index + 1}. Iteration ${iteration.iteration}: ${status}\n`;
    });
  } else {
    patternReport += `No recent iteration data available / 最近の反復データなし\n`;
  }
  
  return `${patternReport}

## 🛠️ Repair Effectiveness / 修復効果

### Auto-Repair Statistics / 自動修復統計

- **Total Fixes Applied / 適用された総修正数**: ${state.total_fixes_applied || 0}
- **Fix Success Rate / 修正成功率**: ${metrics.successRate}%
- **Average Time to Fix / 平均修正時間**: ${metrics.averageIterationTime}s

### Common Issues Detected / 検出された共通問題

Based on iteration patterns, the following issues have been identified:
反復パターンに基づき、以下の問題が特定されました:

${config.ciStatus === 'failure' ? `
- 🔍 **Test Failures**: Unit or integration tests are failing / テスト失敗
- 🏗️ **Build Issues**: Compilation or packaging problems / ビルド問題
- 🔒 **Security Concerns**: Potential security vulnerabilities / セキュリティ懸念
- 📦 **Dependency Conflicts**: Package version mismatches / 依存関係競合
` : `
- ✅ **No Critical Issues**: System is functioning normally / 重大な問題なし
- 🔧 **Maintenance**: Routine maintenance and optimization / 定期メンテナンス
`}

## 🎯 Recommendations / 推奨事項

### Immediate Actions / 即座のアクション

${config.ciStatus === 'success' ? `
✅ **Continue Current Approach**: The system is working well
現在のアプローチを継続: システムは正常に動作中
` : `
🔧 **Focus on Failing Components**: Prioritize fixing recurring failures
失敗コンポーネントに集中: 繰り返し失敗する部分の修正を優先
`}

### Long-term Improvements / 長期的改善

1. **Monitoring Enhancement / 監視強化**
   - Implement more granular metrics collection
   - より細かいメトリクス収集の実装

2. **Predictive Analysis / 予測分析**
   - Add failure prediction based on historical patterns
   - 履歴パターンに基づく障害予測の追加

3. **Automated Recovery / 自動復旧**
   - Enhance auto-repair capabilities
   - 自動修復機能の強化

## 📊 Raw Data / 生データ

### Current State / 現在の状態
\`\`\`json
${JSON.stringify(state, null, 2)}
\`\`\`

### Metrics Summary / メトリクスサマリー
\`\`\`json
${JSON.stringify(metrics, null, 2)}
\`\`\`

---

*Report generated by Auto-Repair Performance Monitor*
*自動修復パフォーマンスモニターにより生成*

**Report ID**: ${config.loopId}-iter-${config.iteration}
**Generated**: ${timestamp}
**Next Update**: Next iteration or manual trigger
`;
}

// Main execution function
function main() {
  log('📊 Starting performance report generation / パフォーマンスレポート生成開始');
  
  parseArgs();
  
  log(`📝 Configuration:
    - Iteration: ${config.iteration}
    - Loop ID: ${config.loopId}
    - CI Status: ${config.ciStatus}
    - Run ID: ${config.runId}`);
  
  // Ensure output directory exists
  ensureDirectory(config.outputDir);
  
  // Load current state
  const state = loadState();
  
  // Calculate performance metrics
  const metrics = calculateMetrics(state);
  
  // Generate detailed report
  const report = generateDetailedReport(state, metrics);
  
  // Save performance report
  const reportFilename = `performance-${config.loopId}-iter-${config.iteration}-${Date.now()}.md`;
  const reportPath = path.join(config.outputDir, reportFilename);
  
  try {
    fs.writeFileSync(reportPath, report);
    log(`📋 Performance report saved: ${reportPath}`);
  } catch (error) {
    log(`❌ Error saving report: ${error.message}`);
    process.exit(1);
  }
  
  // Update state with performance data
  const updatedState = {
    ...state,
    last_performance_check: new Date().toISOString(),
    performance_metrics: metrics
  };
  
  saveState(updatedState);
  
  // Generate summary for console output
  console.log(`
🎯 Performance Report Summary / パフォーマンスレポートサマリー
===============================================

📊 Current Status / 現在のステータス: ${config.ciStatus}
🔢 Iteration / 反復: ${config.iteration}
📈 Success Rate / 成功率: ${metrics.successRate}%
⏱️ Total Runtime / 総実行時間: ${Math.floor(metrics.totalDuration / 60)}分
📋 Report File / レポートファイル: ${reportPath}

===============================================
  `);
  
  log('✅ Performance report generation completed / パフォーマンスレポート生成完了');
}

// Error handling
process.on('uncaughtException', (error) => {
  log(`❌ Uncaught exception: ${error.message}`);
  console.error(error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  log(`❌ Unhandled rejection at: ${promise}, reason: ${reason}`);
  process.exit(1);
});

// Execute main function
if (require.main === module) {
  main();
}

module.exports = {
  generateDetailedReport,
  calculateMetrics,
  generateTrendAnalysis,
  generatePerformanceChart
};