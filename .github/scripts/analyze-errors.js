#!/usr/bin/env node

/**
 * エラー分析・分類スクリプト (Error Analysis & Classification)
 * 
 * 機能:
 * - ワークフローログを解析してエラーパターンを特定
 * - エラータイプに応じて適切な修復SubAgentを選択
 * - 並列処理でエラー分析を高速化
 * - JSON形式で修復戦略を出力
 */

const fs = require('fs');
const path = require('path');

// エラーパターン定義 (Error Pattern Definitions)
const ERROR_PATTERNS = {
  test: {
    patterns: [
      /Test failed:|test failed/i,
      /AssertionError/i,
      /Expected.*but got/i,
      /Cannot find module.*test/i,
      /jest.*failed/i,
      /npm test.*failed/i,
      /pytest.*failed/i,
      /unittest.*failed/i
    ],
    subagent: 'repair-test-failures.sh',
    priority: 'high',
    timeLimit: 15
  },
  
  build: {
    patterns: [
      /Build failed|build failed/i,
      /TypeScript error|TS\d+:/i,
      /Cannot find module/i,
      /Unexpected token/i,
      /SyntaxError/i,
      /Module not found/i,
      /npm run build.*failed/i,
      /webpack.*failed/i,
      /tsc.*error/i
    ],
    subagent: 'repair-build-failures.sh',
    priority: 'critical',
    timeLimit: 20
  },
  
  lint: {
    patterns: [
      /Lint failed|lint failed/i,
      /ESLint.*error/i,
      /Prettier.*error/i,
      /\d+ problems? \(\d+ errors?/i,
      /npm run lint.*failed/i,
      /Linting errors found/i,
      /Code style violations/i
    ],
    subagent: 'repair-lint-failures.sh',
    priority: 'medium',
    timeLimit: 10
  },
  
  dependency: {
    patterns: [
      /peer dep.*warning/i,
      /ERESOLVE.*dependency/i,
      /npm ERR!.*peer/i,
      /Package.*not found/i,
      /Version conflict/i,
      /Dependency.*missing/i,
      /npm install.*failed/i,
      /yarn install.*failed/i
    ],
    subagent: 'repair-dependency-issues.sh',
    priority: 'high',
    timeLimit: 12
  }
};

/**
 * ログファイルからエラーを抽出 (Extract errors from log files)
 */
function extractErrors(logContent) {
  const lines = logContent.split('\n');
  const errors = [];
  
  lines.forEach((line, index) => {
    if (line.includes('Error') || line.includes('Failed') || line.includes('error')) {
      errors.push({
        line: index + 1,
        content: line.trim(),
        context: lines.slice(Math.max(0, index - 2), index + 3)
      });
    }
  });
  
  return errors;
}

/**
 * エラーパターンをマッチング (Match error patterns)
 */
function classifyErrors(errors) {
  const classification = {
    test: [],
    build: [],
    lint: [],
    dependency: [],
    unknown: []
  };
  
  errors.forEach(error => {
    let classified = false;
    
    for (const [type, config] of Object.entries(ERROR_PATTERNS)) {
      if (config.patterns.some(pattern => pattern.test(error.content))) {
        classification[type].push({
          ...error,
          type,
          subagent: config.subagent,
          priority: config.priority,
          timeLimit: config.timeLimit
        });
        classified = true;
        break;
      }
    }
    
    if (!classified) {
      classification.unknown.push(error);
    }
  });
  
  return classification;
}

/**
 * 修復戦略を生成 (Generate repair strategy)
 */
function generateRepairStrategy(classification) {
  const strategy = {
    timestamp: new Date().toISOString(),
    totalErrors: 0,
    repairPlan: [],
    estimatedTime: 0
  };
  
  // 優先度順でソート (Sort by priority)
  const priorityOrder = { critical: 1, high: 2, medium: 3, low: 4 };
  
  Object.entries(classification).forEach(([type, errors]) => {
    if (errors.length > 0 && type !== 'unknown') {
      const config = ERROR_PATTERNS[type];
      strategy.totalErrors += errors.length;
      strategy.estimatedTime += config.timeLimit;
      
      strategy.repairPlan.push({
        type,
        errorCount: errors.length,
        subagent: config.subagent,
        priority: config.priority,
        timeLimit: config.timeLimit,
        errors: errors.slice(0, 5) // 最初の5個のエラーのみ記録
      });
    }
  });
  
  // 優先度でソート
  strategy.repairPlan.sort((a, b) => 
    priorityOrder[a.priority] - priorityOrder[b.priority]
  );
  
  return strategy;
}

/**
 * 並列エラー分析 (Parallel error analysis)
 */
async function analyzeErrorsParallel(logFiles) {
  const results = await Promise.all(
    logFiles.map(async logFile => {
      try {
        const content = fs.readFileSync(logFile, 'utf8');
        const errors = extractErrors(content);
        const classification = classifyErrors(errors);
        
        return {
          file: logFile,
          classification,
          success: true
        };
      } catch (error) {
        return {
          file: logFile,
          error: error.message,
          success: false
        };
      }
    })
  );
  
  return results;
}

/**
 * メイン分析処理 (Main analysis process)
 */
async function main() {
  try {
    console.log('🔍 エラー分析を開始... (Starting error analysis...)');
    
    // ログファイルを検索
    const logFiles = [
      '.github/workflows/logs/build.log',
      '.github/workflows/logs/test.log',
      '.github/workflows/logs/lint.log',
      'npm-debug.log',
      'yarn-error.log'
    ].filter(file => fs.existsSync(file));
    
    if (logFiles.length === 0) {
      console.log('⚠️  ログファイルが見つかりません');
      process.exit(0);
    }
    
    // 並列分析実行
    const analysisResults = await analyzeErrorsParallel(logFiles);
    
    // 結果を統合
    const combinedClassification = {
      test: [],
      build: [],
      lint: [],
      dependency: [],
      unknown: []
    };
    
    analysisResults.forEach(result => {
      if (result.success) {
        Object.keys(combinedClassification).forEach(type => {
          combinedClassification[type].push(...result.classification[type]);
        });
      }
    });
    
    // 修復戦略生成
    const strategy = generateRepairStrategy(combinedClassification);
    
    // 結果出力
    const outputPath = '.github/outputs/error-analysis.json';
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, JSON.stringify(strategy, null, 2));
    
    console.log(`✅ エラー分析完了: ${strategy.totalErrors}個のエラーを検出`);
    console.log(`📋 修復計画: ${strategy.repairPlan.length}個のSubAgentを実行予定`);
    console.log(`⏱️  推定修復時間: ${strategy.estimatedTime}分`);
    
    // 修復が必要な場合は終了コード1を返す
    process.exit(strategy.totalErrors > 0 ? 1 : 0);
    
  } catch (error) {
    console.error('❌ エラー分析に失敗:', error.message);
    process.exit(2);
  }
}

// スクリプト実行
if (require.main === module) {
  main();
}

module.exports = {
  extractErrors,
  classifyErrors,
  generateRepairStrategy,
  analyzeErrorsParallel
};