const core = require('@actions/core');
const fs = require('fs').promises;
const path = require('path');

/**
 * Repair State Manager - SubAgent System State Management
 * Manages loop iteration tracking, repair history, and pattern learning
 */

class RepairStateManager {
  constructor() {
    this.operation = core.getInput('operation');
    this.stateFilePath = core.getInput('state-file-path') || '.github/repair-state.json';
    this.iterationNumber = parseInt(core.getInput('iteration-number')) || 0;
    this.currentState = null;
    this.defaultState = this.createDefaultState();
  }

  createDefaultState() {
    return {
      version: '1.0',
      created: new Date().toISOString(),
      updated: new Date().toISOString(),
      currentIteration: 0,
      maxIterations: 210, // 7 cycles × 30 iterations
      cycleConfiguration: {
        iterationsPerCycle: 30,
        totalCycles: 7,
        currentCycle: 1
      },
      repairHistory: [],
      errorPatterns: {},
      successPatterns: {},
      statistics: {
        totalRepairs: 0,
        successfulRepairs: 0,
        failedRepairs: 0,
        averageRepairTime: 0,
        mostCommonErrors: [],
        mostEffectiveRepairs: []
      },
      learningData: {
        patternAccuracy: {},
        repairEffectiveness: {},
        timeoutPatterns: [],
        riskAssessments: {}
      },
      recommendations: [],
      lastAnalysis: null
    };
  }

  async run() {
    try {
      core.info(`🗄️ Running Repair State Manager - Operation: ${this.operation}`);
      
      switch (this.operation) {
        case 'save':
          await this.saveState();
          break;
        case 'load':
          await this.loadState();
          break;
        case 'update':
          await this.updateState();
          break;
        case 'analyze':
          await this.analyzeState();
          break;
        default:
          throw new Error(`Unknown operation: ${this.operation}`);
      }
      
      await this.generateOutputs();
      core.info('✅ Repair State Manager completed successfully');
      
    } catch (error) {
      core.setFailed(`Repair State Manager failed: ${error.message}`);
    }
  }

  async saveState() {
    try {
      const stateDataInput = core.getInput('state-data');
      const stateData = stateDataInput ? JSON.parse(stateDataInput) : this.defaultState;
      
      // Merge with existing state if it exists
      const existingState = await this.loadExistingState();
      this.currentState = this.mergeStates(existingState, stateData);
      
      // Update timestamps and iteration
      this.currentState.updated = new Date().toISOString();
      if (this.iterationNumber > 0) {
        this.currentState.currentIteration = this.iterationNumber;
        this.updateCycleInfo();
      }
      
      await this.writeStateFile();
      core.info(`State saved to ${this.stateFilePath}`);
      
    } catch (error) {
      throw new Error(`Failed to save state: ${error.message}`);
    }
  }

  async loadState() {
    try {
      this.currentState = await this.loadExistingState();
      core.info(`State loaded from ${this.stateFilePath}`);
      
    } catch (error) {
      core.warning(`Could not load existing state: ${error.message}`);
      this.currentState = this.defaultState;
    }
  }

  async updateState() {
    try {
      await this.loadState();
      
      const repairResultsInput = core.getInput('repair-results');
      if (repairResultsInput) {
        const repairResults = JSON.parse(repairResultsInput);
        await this.processRepairResults(repairResults);
      }
      
      await this.saveState();
      core.info('State updated with latest repair results');
      
    } catch (error) {
      throw new Error(`Failed to update state: ${error.message}`);
    }
  }

  async analyzeState() {
    try {
      await this.loadState();
      
      const analysis = this.performStateAnalysis();
      const recommendations = this.generateRecommendations(analysis);
      const patternUpdates = this.updatePatterns(analysis);
      
      // Update state with analysis results
      this.currentState.lastAnalysis = {
        timestamp: new Date().toISOString(),
        analysis,
        recommendations
      };
      this.currentState.recommendations = recommendations;
      
      await this.saveState();
      core.info('State analysis completed');
      
    } catch (error) {
      throw new Error(`Failed to analyze state: ${error.message}`);
    }
  }

  async loadExistingState() {
    try {
      const stateContent = await fs.readFile(this.stateFilePath, 'utf8');
      return JSON.parse(stateContent);
    } catch (error) {
      if (error.code === 'ENOENT') {
        core.info('No existing state file found, using default state');
        return this.defaultState;
      }
      throw error;
    }
  }

  mergeStates(existing, newData) {
    const merged = { ...existing, ...newData };
    
    // Preserve certain fields from existing state
    if (existing) {
      merged.created = existing.created;
      merged.repairHistory = [...(existing.repairHistory || [])];
      merged.statistics = { ...existing.statistics, ...newData.statistics };
      merged.learningData = { ...existing.learningData, ...newData.learningData };
    }
    
    return merged;
  }

  updateCycleInfo() {
    const { iterationsPerCycle } = this.currentState.cycleConfiguration;
    const currentCycle = Math.floor(this.currentState.currentIteration / iterationsPerCycle) + 1;
    
    this.currentState.cycleConfiguration.currentCycle = Math.min(currentCycle, 7);
  }

  async processRepairResults(repairResults) {
    const timestamp = new Date().toISOString();
    
    // Add to repair history
    const historyEntry = {
      iteration: this.currentState.currentIteration,
      timestamp,
      results: repairResults,
      summary: this.summarizeResults(repairResults)
    };
    
    this.currentState.repairHistory.push(historyEntry);
    
    // Update statistics
    this.updateStatistics(repairResults);
    
    // Update learning data
    this.updateLearningData(repairResults);
    
    // Prune old history if needed
    this.pruneHistory();
  }

  summarizeResults(repairResults) {
    const successful = repairResults.filter(r => r.success).length;
    const failed = repairResults.filter(r => !r.success).length;
    const totalDuration = repairResults.reduce((sum, r) => sum + (r.duration || 0), 0);
    
    return {
      totalRepairs: repairResults.length,
      successful,
      failed,
      successRate: successful / repairResults.length,
      averageDuration: totalDuration / repairResults.length,
      totalDuration
    };
  }

  updateStatistics(repairResults) {
    const stats = this.currentState.statistics;
    
    stats.totalRepairs += repairResults.length;
    stats.successfulRepairs += repairResults.filter(r => r.success).length;
    stats.failedRepairs += repairResults.filter(r => !r.success).length;
    
    // Update average repair time
    const totalDuration = repairResults.reduce((sum, r) => sum + (r.duration || 0), 0);
    const newAverage = (stats.averageRepairTime * (stats.totalRepairs - repairResults.length) + totalDuration) / stats.totalRepairs;
    stats.averageRepairTime = Math.round(newAverage);
    
    // Update most common errors
    this.updateMostCommonErrors(repairResults);
    
    // Update most effective repairs
    this.updateMostEffectiveRepairs(repairResults);
  }

  updateMostCommonErrors(repairResults) {
    const errorCounts = {};
    
    repairResults.forEach(result => {
      if (!result.success && result.error) {
        const errorType = this.categorizeError(result.error);
        errorCounts[errorType] = (errorCounts[errorType] || 0) + 1;
      }
    });
    
    // Merge with existing counts
    const existingErrors = this.currentState.statistics.mostCommonErrors || [];
    const errorMap = {};
    
    existingErrors.forEach(item => {
      errorMap[item.type] = item.count;
    });
    
    Object.entries(errorCounts).forEach(([type, count]) => {
      errorMap[type] = (errorMap[type] || 0) + count;
    });
    
    // Sort and keep top 10
    this.currentState.statistics.mostCommonErrors = Object.entries(errorMap)
      .map(([type, count]) => ({ type, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }

  updateMostEffectiveRepairs(repairResults) {
    const repairEffectiveness = {};
    
    repairResults.forEach(result => {
      if (result.success && result.strategy) {
        const repairType = this.categorizeRepair(result.strategy);
        if (!repairEffectiveness[repairType]) {
          repairEffectiveness[repairType] = { successes: 0, attempts: 0 };
        }
        repairEffectiveness[repairType].successes += 1;
        repairEffectiveness[repairType].attempts += 1;
      }
    });
    
    // Update existing effectiveness data
    const existingRepairs = this.currentState.statistics.mostEffectiveRepairs || [];
    const repairMap = {};
    
    existingRepairs.forEach(item => {
      repairMap[item.type] = {
        successes: item.successes,
        attempts: item.attempts
      };
    });
    
    Object.entries(repairEffectiveness).forEach(([type, data]) => {
      if (!repairMap[type]) {
        repairMap[type] = { successes: 0, attempts: 0 };
      }
      repairMap[type].successes += data.successes;
      repairMap[type].attempts += data.attempts;
    });
    
    // Calculate effectiveness and sort
    this.currentState.statistics.mostEffectiveRepairs = Object.entries(repairMap)
      .map(([type, data]) => ({
        type,
        successes: data.successes,
        attempts: data.attempts,
        effectiveness: data.attempts > 0 ? data.successes / data.attempts : 0
      }))
      .sort((a, b) => b.effectiveness - a.effectiveness)
      .slice(0, 10);
  }

  updateLearningData(repairResults) {
    const learningData = this.currentState.learningData;
    
    // Update pattern accuracy
    repairResults.forEach(result => {
      if (result.strategy && result.strategy.matchedPatterns) {
        result.strategy.matchedPatterns.forEach(pattern => {
          if (!learningData.patternAccuracy[pattern.key]) {
            learningData.patternAccuracy[pattern.key] = {
              predictions: 0,
              correct: 0
            };
          }
          
          learningData.patternAccuracy[pattern.key].predictions += 1;
          if (result.success) {
            learningData.patternAccuracy[pattern.key].correct += 1;
          }
        });
      }
    });
    
    // Update repair effectiveness
    repairResults.forEach(result => {
      if (result.strategy) {
        const repairType = this.categorizeRepair(result.strategy);
        if (!learningData.repairEffectiveness[repairType]) {
          learningData.repairEffectiveness[repairType] = {
            attempts: 0,
            successes: 0,
            averageDuration: 0
          };
        }
        
        const effectiveness = learningData.repairEffectiveness[repairType];
        effectiveness.attempts += 1;
        if (result.success) {
          effectiveness.successes += 1;
        }
        effectiveness.averageDuration = (effectiveness.averageDuration * (effectiveness.attempts - 1) + (result.duration || 0)) / effectiveness.attempts;
      }
    });
  }

  categorizeError(error) {
    const errorLower = error.toLowerCase();
    
    if (errorLower.includes('syntax') || errorLower.includes('yaml')) {
      return 'syntax_error';
    }
    if (errorLower.includes('permission') || errorLower.includes('unauthorized')) {
      return 'permission_error';
    }
    if (errorLower.includes('timeout')) {
      return 'timeout_error';
    }
    if (errorLower.includes('dependency') || errorLower.includes('module')) {
      return 'dependency_error';
    }
    
    return 'unknown_error';
  }

  categorizeRepair(strategy) {
    if (strategy.primaryActions) {
      const actions = strategy.primaryActions.join(' ').toLowerCase();
      
      if (actions.includes('yaml') || actions.includes('syntax')) {
        return 'yaml_repair';
      }
      if (actions.includes('dependency') || actions.includes('package')) {
        return 'dependency_repair';
      }
      if (actions.includes('permission') || actions.includes('token')) {
        return 'permission_repair';
      }
    }
    
    return 'generic_repair';
  }

  pruneHistory() {
    // Keep only last 100 entries to prevent file from growing too large
    if (this.currentState.repairHistory.length > 100) {
      this.currentState.repairHistory = this.currentState.repairHistory.slice(-100);
    }
  }

  performStateAnalysis() {
    const stats = this.currentState.statistics;
    const history = this.currentState.repairHistory;
    
    const analysis = {
      overallPerformance: this.analyzeOverallPerformance(stats),
      trendAnalysis: this.analyzeTrends(history),
      errorPatternAnalysis: this.analyzeErrorPatterns(),
      repairEfficiencyAnalysis: this.analyzeRepairEfficiency(),
      cycleProgressAnalysis: this.analyzeCycleProgress()
    };
    
    return analysis;
  }

  analyzeOverallPerformance(stats) {
    const successRate = stats.totalRepairs > 0 ? stats.successfulRepairs / stats.totalRepairs : 0;
    
    let performance = 'poor';
    if (successRate >= 0.8) performance = 'excellent';
    else if (successRate >= 0.6) performance = 'good';
    else if (successRate >= 0.4) performance = 'fair';
    
    return {
      successRate,
      performance,
      totalRepairs: stats.totalRepairs,
      averageRepairTime: stats.averageRepairTime
    };
  }

  analyzeTrends(history) {
    if (history.length < 2) {
      return { trend: 'insufficient_data' };
    }
    
    const recentHistory = history.slice(-10);
    const successRates = recentHistory.map(h => h.summary.successRate);
    
    const trend = this.calculateTrend(successRates);
    const stability = this.calculateStability(successRates);
    
    return { trend, stability, recentSuccessRates: successRates };
  }

  calculateTrend(values) {
    if (values.length < 2) return 'stable';
    
    const firstHalf = values.slice(0, Math.floor(values.length / 2));
    const secondHalf = values.slice(Math.floor(values.length / 2));
    
    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
    
    const difference = secondAvg - firstAvg;
    
    if (difference > 0.1) return 'improving';
    if (difference < -0.1) return 'declining';
    return 'stable';
  }

  calculateStability(values) {
    if (values.length < 2) return 'stable';
    
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const variance = values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / values.length;
    const standardDeviation = Math.sqrt(variance);
    
    if (standardDeviation < 0.1) return 'stable';
    if (standardDeviation < 0.2) return 'moderate';
    return 'unstable';
  }

  analyzeErrorPatterns() {
    const errorPatterns = this.currentState.statistics.mostCommonErrors || [];
    const totalErrors = errorPatterns.reduce((sum, pattern) => sum + pattern.count, 0);
    
    return {
      dominantErrors: errorPatterns.slice(0, 3),
      errorDiversity: errorPatterns.length,
      totalErrors,
      recommendations: this.getErrorPatternRecommendations(errorPatterns)
    };
  }

  analyzeRepairEfficiency() {
    const effectiveRepairs = this.currentState.statistics.mostEffectiveRepairs || [];
    const avgEffectiveness = effectiveRepairs.length > 0 
      ? effectiveRepairs.reduce((sum, repair) => sum + repair.effectiveness, 0) / effectiveRepairs.length 
      : 0;
    
    return {
      mostEffectiveRepairs: effectiveRepairs.slice(0, 5),
      averageEffectiveness: avgEffectiveness,
      recommendations: this.getEfficiencyRecommendations(effectiveRepairs)
    };
  }

  analyzeCycleProgress() {
    const { currentIteration, maxIterations, cycleConfiguration } = this.currentState;
    const progress = currentIteration / maxIterations;
    const cycleProgress = (currentIteration % cycleConfiguration.iterationsPerCycle) / cycleConfiguration.iterationsPerCycle;
    
    return {
      overallProgress: progress,
      cycleProgress,
      currentCycle: cycleConfiguration.currentCycle,
      remainingIterations: maxIterations - currentIteration,
      onTrack: progress <= (Date.now() - new Date(this.currentState.created)) / (30 * 24 * 60 * 60 * 1000) // Rough calculation
    };
  }

  generateRecommendations(analysis) {
    const recommendations = [];
    
    // Performance recommendations
    if (analysis.overallPerformance.successRate < 0.5) {
      recommendations.push({
        type: 'performance',
        priority: 'high',
        message: 'Success rate is below 50%. Consider reviewing error patterns and repair strategies.'
      });
    }
    
    // Trend recommendations
    if (analysis.trendAnalysis.trend === 'declining') {
      recommendations.push({
        type: 'trend',
        priority: 'medium',
        message: 'Performance is declining. Review recent changes and adjust strategies.'
      });
    }
    
    // Error pattern recommendations
    if (analysis.errorPatternAnalysis.dominantErrors.length > 0) {
      const topError = analysis.errorPatternAnalysis.dominantErrors[0];
      recommendations.push({
        type: 'error_pattern',
        priority: 'medium',
        message: `Most common error: ${topError.type} (${topError.count} occurrences). Focus on improving this repair pattern.`
      });
    }
    
    return recommendations;
  }

  getErrorPatternRecommendations(errorPatterns) {
    const recommendations = [];
    
    errorPatterns.forEach(pattern => {
      switch (pattern.type) {
        case 'syntax_error':
          recommendations.push('Implement automated syntax validation');
          break;
        case 'permission_error':
          recommendations.push('Review and update token permissions');
          break;
        case 'timeout_error':
          recommendations.push('Optimize long-running operations');
          break;
      }
    });
    
    return recommendations;
  }

  getEfficiencyRecommendations(effectiveRepairs) {
    const recommendations = [];
    
    const lowEfficiency = effectiveRepairs.filter(repair => repair.effectiveness < 0.5);
    if (lowEfficiency.length > 0) {
      recommendations.push(`Improve low-efficiency repairs: ${lowEfficiency.map(r => r.type).join(', ')}`);
    }
    
    const highEfficiency = effectiveRepairs.filter(repair => repair.effectiveness > 0.8);
    if (highEfficiency.length > 0) {
      recommendations.push(`Prioritize high-efficiency repairs: ${highEfficiency.map(r => r.type).join(', ')}`);
    }
    
    return recommendations;
  }

  updatePatterns(analysis) {
    const patternUpdates = {};
    
    // Update error patterns based on learning data
    const learningData = this.currentState.learningData;
    
    Object.entries(learningData.patternAccuracy).forEach(([patternKey, data]) => {
      const accuracy = data.predictions > 0 ? data.correct / data.predictions : 0;
      
      patternUpdates[patternKey] = {
        accuracy,
        confidence: Math.min(0.9, accuracy * 1.1), // Boost confidence for accurate patterns
        lastUpdated: new Date().toISOString()
      };
    });
    
    return patternUpdates;
  }

  async writeStateFile() {
    try {
      // Ensure directory exists
      const dir = path.dirname(this.stateFilePath);
      await fs.mkdir(dir, { recursive: true });
      
      // Write state file with pretty formatting
      await fs.writeFile(
        this.stateFilePath, 
        JSON.stringify(this.currentState, null, 2)
      );
    } catch (error) {
      throw new Error(`Failed to write state file: ${error.message}`);
    }
  }

  async generateOutputs() {
    // Set outputs
    core.setOutput('current-state', JSON.stringify(this.currentState));
    core.setOutput('iteration-count', this.currentState.currentIteration.toString());
    core.setOutput('repair-history', JSON.stringify(this.currentState.repairHistory));
    
    if (this.currentState.lastAnalysis) {
      core.setOutput('pattern-updates', JSON.stringify(this.currentState.lastAnalysis.analysis));
      core.setOutput('recommendations', JSON.stringify(this.currentState.recommendations));
    }
  }
}

// Run the state manager
const stateManager = new RepairStateManager();
stateManager.run();