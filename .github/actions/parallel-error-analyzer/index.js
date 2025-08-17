const core = require('@actions/core');
const fs = require('fs').promises;
const path = require('path');

/**
 * Parallel Error Analyzer - SubAgent System
 * Analyzes multiple workflow errors simultaneously using concurrent pattern matching
 */

class ParallelErrorAnalyzer {
  constructor() {
    this.maxConcurrent = parseInt(core.getInput('max-concurrent') || '5');
    this.analysisTimeout = parseInt(core.getInput('analysis-timeout') || '300') * 1000;
    this.patternDbPath = core.getInput('pattern-db-path') || '.github/repair-patterns.json';
    this.errorPatterns = null;
    this.analysisResults = [];
    this.repairStrategies = [];
  }

  async loadErrorPatterns() {
    try {
      const patternData = await fs.readFile(this.patternDbPath, 'utf8');
      this.errorPatterns = JSON.parse(patternData);
      core.info(`Loaded ${Object.keys(this.errorPatterns).length} error patterns`);
    } catch (error) {
      core.warning(`Could not load error patterns: ${error.message}`);
      this.errorPatterns = this.getDefaultPatterns();
    }
  }

  getDefaultPatterns() {
    return {
      "workflow_syntax": {
        patterns: [
          "Invalid workflow file",
          "syntax error",
          "unexpected token",
          "invalid YAML"
        ],
        repairs: [
          "Fix YAML syntax errors",
          "Validate workflow structure",
          "Check indentation and formatting"
        ],
        confidence: 0.9
      },
      "dependency_error": {
        patterns: [
          "module not found",
          "package not installed",
          "import error",
          "cannot resolve"
        ],
        repairs: [
          "Install missing dependencies",
          "Update package.json",
          "Fix import paths"
        ],
        confidence: 0.85
      },
      "permission_error": {
        patterns: [
          "permission denied",
          "access forbidden",
          "unauthorized",
          "token expired"
        ],
        repairs: [
          "Update GitHub token permissions",
          "Check repository access rights",
          "Refresh authentication tokens"
        ],
        confidence: 0.8
      },
      "timeout_error": {
        patterns: [
          "timeout exceeded",
          "operation timed out",
          "job cancelled",
          "runner timeout"
        ],
        repairs: [
          "Increase timeout values",
          "Optimize long-running operations",
          "Split into smaller jobs"
        ],
        confidence: 0.75
      },
      "resource_limit": {
        patterns: [
          "out of memory",
          "disk space",
          "resource limit",
          "quota exceeded"
        ],
        repairs: [
          "Optimize memory usage",
          "Clean up disk space",
          "Use smaller datasets"
        ],
        confidence: 0.7
      }
    };
  }

  async analyzeErrorBatch(errors) {
    const semaphore = new Semaphore(this.maxConcurrent);
    const analysisPromises = errors.map(async (error, index) => {
      return semaphore.acquire(async () => {
        return this.analyzeError(error, index);
      });
    });

    return Promise.all(analysisPromises);
  }

  async analyzeError(errorLog, index) {
    const startTime = Date.now();
    
    try {
      core.info(`Starting analysis ${index + 1} - Error: ${errorLog.type || 'Unknown'}`);
      
      const analysisResult = await Promise.race([
        this.performErrorAnalysis(errorLog),
        this.createTimeoutPromise()
      ]);

      const duration = Date.now() - startTime;
      core.info(`Analysis ${index + 1} completed in ${duration}ms`);
      
      return {
        index,
        success: true,
        duration,
        ...analysisResult
      };
    } catch (error) {
      const duration = Date.now() - startTime;
      core.error(`Analysis ${index + 1} failed after ${duration}ms: ${error.message}`);
      
      return {
        index,
        success: false,
        duration,
        error: error.message,
        repairStrategy: this.getFallbackStrategy()
      };
    }
  }

  async performErrorAnalysis(errorLog) {
    const errorText = this.extractErrorText(errorLog);
    const matchedPatterns = this.findMatchingPatterns(errorText);
    const repairStrategy = this.generateRepairStrategy(matchedPatterns, errorLog);
    
    return {
      errorType: this.categorizeError(matchedPatterns),
      matchedPatterns,
      repairStrategy,
      confidence: this.calculateConfidence(matchedPatterns),
      metadata: {
        errorSource: errorLog.source || 'unknown',
        timestamp: errorLog.timestamp || new Date().toISOString(),
        workflowId: errorLog.workflowId || 'unknown'
      }
    };
  }

  extractErrorText(errorLog) {
    if (typeof errorLog === 'string') return errorLog;
    if (errorLog.message) return errorLog.message;
    if (errorLog.error) return errorLog.error;
    if (errorLog.logs) return errorLog.logs.join(' ');
    return JSON.stringify(errorLog);
  }

  findMatchingPatterns(errorText) {
    const matches = [];
    const lowerErrorText = errorText.toLowerCase();
    
    for (const [patternKey, patternData] of Object.entries(this.errorPatterns)) {
      const patternMatches = patternData.patterns.filter(pattern => 
        lowerErrorText.includes(pattern.toLowerCase())
      );
      
      if (patternMatches.length > 0) {
        matches.push({
          key: patternKey,
          matchedPatterns: patternMatches,
          confidence: patternData.confidence,
          repairs: patternData.repairs
        });
      }
    }
    
    return matches;
  }

  categorizeError(matchedPatterns) {
    if (matchedPatterns.length === 0) return 'unknown';
    
    // Return the pattern with highest confidence
    return matchedPatterns.reduce((best, current) => 
      current.confidence > best.confidence ? current : best
    ).key;
  }

  generateRepairStrategy(matchedPatterns, errorLog) {
    if (matchedPatterns.length === 0) {
      return this.getFallbackStrategy();
    }
    
    // Combine repairs from all matched patterns
    const allRepairs = matchedPatterns.flatMap(pattern => pattern.repairs);
    const uniqueRepairs = [...new Set(allRepairs)];
    
    return {
      primaryActions: uniqueRepairs.slice(0, 3),
      secondaryActions: uniqueRepairs.slice(3),
      priority: this.calculatePriority(matchedPatterns),
      estimatedDuration: this.estimateRepairDuration(matchedPatterns),
      requiredPermissions: this.determineRequiredPermissions(matchedPatterns),
      riskLevel: this.assessRiskLevel(matchedPatterns)
    };
  }

  calculateConfidence(matchedPatterns) {
    if (matchedPatterns.length === 0) return 0.1;
    
    const avgConfidence = matchedPatterns.reduce((sum, pattern) => 
      sum + pattern.confidence, 0) / matchedPatterns.length;
    
    // Boost confidence for multiple pattern matches
    const boostFactor = Math.min(1.2, 1 + (matchedPatterns.length - 1) * 0.1);
    
    return Math.min(1.0, avgConfidence * boostFactor);
  }

  calculatePriority(matchedPatterns) {
    const highPriorityPatterns = ['workflow_syntax', 'permission_error'];
    const hasHighPriority = matchedPatterns.some(pattern => 
      highPriorityPatterns.includes(pattern.key)
    );
    
    return hasHighPriority ? 'high' : 'medium';
  }

  estimateRepairDuration(matchedPatterns) {
    const durationMap = {
      'workflow_syntax': 5,
      'dependency_error': 10,
      'permission_error': 15,
      'timeout_error': 8,
      'resource_limit': 12
    };
    
    const maxDuration = Math.max(...matchedPatterns.map(pattern => 
      durationMap[pattern.key] || 10
    ));
    
    return `${maxDuration} minutes`;
  }

  determineRequiredPermissions(matchedPatterns) {
    const permissionMap = {
      'workflow_syntax': ['contents:write'],
      'dependency_error': ['contents:write'],
      'permission_error': ['admin'],
      'timeout_error': ['contents:write'],
      'resource_limit': ['contents:write']
    };
    
    const allPermissions = matchedPatterns.flatMap(pattern => 
      permissionMap[pattern.key] || ['contents:read']
    );
    
    return [...new Set(allPermissions)];
  }

  assessRiskLevel(matchedPatterns) {
    const riskMap = {
      'workflow_syntax': 'low',
      'dependency_error': 'low',
      'permission_error': 'medium',
      'timeout_error': 'low',
      'resource_limit': 'medium'
    };
    
    const riskLevels = matchedPatterns.map(pattern => riskMap[pattern.key] || 'low');
    
    if (riskLevels.includes('high')) return 'high';
    if (riskLevels.includes('medium')) return 'medium';
    return 'low';
  }

  getFallbackStrategy() {
    return {
      primaryActions: [
        'Review error logs for common patterns',
        'Check workflow syntax and dependencies',
        'Verify repository permissions'
      ],
      secondaryActions: [
        'Contact repository maintainer',
        'Check GitHub status page'
      ],
      priority: 'low',
      estimatedDuration: '15 minutes',
      requiredPermissions: ['contents:read'],
      riskLevel: 'low'
    };
  }

  createTimeoutPromise() {
    return new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Analysis timeout')), this.analysisTimeout);
    });
  }

  async run() {
    try {
      core.info('🔍 Starting Parallel Error Analyzer');
      
      await this.loadErrorPatterns();
      
      const errorLogsInput = core.getInput('error-logs');
      const errorLogs = JSON.parse(errorLogsInput);
      
      core.info(`Analyzing ${errorLogs.length} errors with ${this.maxConcurrent} concurrent workers`);
      
      const results = await this.analyzeErrorBatch(errorLogs);
      
      this.analysisResults = results;
      this.repairStrategies = results.map(result => result.repairStrategy);
      
      // Set outputs
      core.setOutput('repair-strategies', JSON.stringify(this.repairStrategies));
      core.setOutput('analysis-results', JSON.stringify(this.analysisResults));
      core.setOutput('pattern-matches', JSON.stringify(
        results.map(r => r.matchedPatterns || [])
      ));
      core.setOutput('concurrent-count', this.maxConcurrent.toString());
      
      const successCount = results.filter(r => r.success).length;
      core.info(`✅ Analysis complete: ${successCount}/${errorLogs.length} successful`);
      
    } catch (error) {
      core.setFailed(`Parallel Error Analyzer failed: ${error.message}`);
    }
  }
}

// Semaphore class for controlling concurrency
class Semaphore {
  constructor(maxConcurrent) {
    this.maxConcurrent = maxConcurrent;
    this.running = 0;
    this.queue = [];
  }

  async acquire(task) {
    return new Promise((resolve, reject) => {
      this.queue.push({ task, resolve, reject });
      this.tryNext();
    });
  }

  tryNext() {
    if (this.running >= this.maxConcurrent || this.queue.length === 0) {
      return;
    }

    this.running++;
    const { task, resolve, reject } = this.queue.shift();

    task()
      .then(resolve)
      .catch(reject)
      .finally(() => {
        this.running--;
        this.tryNext();
      });
  }
}

// Run the analyzer
const analyzer = new ParallelErrorAnalyzer();
analyzer.run();