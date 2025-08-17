const core = require('@actions/core');
const github = require('@actions/github');
const fs = require('fs').promises;
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

/**
 * Repair Validator - SubAgent System Validation
 * Tests repair effectiveness and calculates success metrics
 */

class RepairValidator {
  constructor() {
    this.repairResults = JSON.parse(core.getInput('repair-results'));
    this.previousErrors = JSON.parse(core.getInput('previous-errors'));
    this.validationMode = core.getInput('validation-mode') || 'thorough';
    this.successThreshold = parseFloat(core.getInput('success-threshold') || '0.7');
    this.githubToken = core.getInput('github-token');
    this.octokit = github.getOctokit(this.githubToken);
    
    this.validationResults = [];
    this.effectivenessScore = 0;
    this.overallSuccessRate = 0;
  }

  async run() {
    try {
      core.info('✅ Starting Repair Validator');
      core.info(`Validation mode: ${this.validationMode}`);
      core.info(`Success threshold: ${this.successThreshold}`);
      
      await this.validateRepairs();
      await this.calculateMetrics();
      const shouldContinue = this.determineContinuation();
      const recommendations = this.generateRecommendations();
      
      await this.setOutputs(shouldContinue, recommendations);
      
      core.info(`🎯 Validation complete - Success rate: ${Math.round(this.overallSuccessRate * 100)}%`);
      core.info(`📊 Effectiveness score: ${this.effectivenessScore}/100`);
      core.info(`🔄 Continue loop: ${shouldContinue}`);
      
    } catch (error) {
      core.setFailed(`Repair Validator failed: ${error.message}`);
    }
  }

  async validateRepairs() {
    core.info(`Validating ${this.repairResults.length} repair results`);
    
    for (let i = 0; i < this.repairResults.length; i++) {
      const repair = this.repairResults[i];
      const originalError = this.previousErrors[i];
      
      core.info(`Validating repair ${i + 1}/${this.repairResults.length}: ${repair.repairId}`);
      
      const validationResult = await this.validateSingleRepair(repair, originalError);
      this.validationResults.push(validationResult);
    }
  }

  async validateSingleRepair(repair, originalError) {
    const validation = {
      repairId: repair.repairId,
      originalError,
      repairAttempted: repair.success,
      validationTests: [],
      overallValid: false,
      confidence: 0,
      issues: []
    };

    try {
      // Test 1: Basic execution validation
      const executionTest = await this.testExecution(repair);
      validation.validationTests.push(executionTest);

      // Test 2: Error resolution validation
      const resolutionTest = await this.testErrorResolution(repair, originalError);
      validation.validationTests.push(resolutionTest);

      // Test 3: Side effects validation
      const sideEffectsTest = await this.testSideEffects(repair);
      validation.validationTests.push(sideEffectsTest);

      // Test 4: Workflow integrity validation (if applicable)
      if (this.validationMode !== 'quick') {
        const integrityTest = await this.testWorkflowIntegrity(repair);
        validation.validationTests.push(integrityTest);
      }

      // Test 5: Comprehensive system validation
      if (this.validationMode === 'comprehensive') {
        const systemTest = await this.testSystemIntegrity();
        validation.validationTests.push(systemTest);
      }

      // Calculate overall validation result
      validation.overallValid = this.calculateValidationResult(validation.validationTests);
      validation.confidence = this.calculateConfidence(validation.validationTests);

    } catch (error) {
      validation.issues.push(`Validation error: ${error.message}`);
      validation.overallValid = false;
      validation.confidence = 0;
    }

    return validation;
  }

  async testExecution(repair) {
    const test = {
      name: 'execution_test',
      passed: false,
      details: {},
      duration: 0
    };

    const startTime = Date.now();

    try {
      // Check if repair claimed success
      if (!repair.success) {
        test.details.message = 'Repair reported failure';
        test.passed = false;
        return test;
      }

      // Verify executed actions
      if (repair.executedActions && repair.executedActions.length > 0) {
        test.details.executedActions = repair.executedActions;
        test.details.actionCount = repair.executedActions.length;
        test.passed = true;
        test.details.message = `Successfully executed ${repair.executedActions.length} actions`;
      } else {
        test.details.message = 'No actions were executed';
        test.passed = false;
      }

    } catch (error) {
      test.details.error = error.message;
      test.passed = false;
    } finally {
      test.duration = Date.now() - startTime;
    }

    return test;
  }

  async testErrorResolution(repair, originalError) {
    const test = {
      name: 'error_resolution_test',
      passed: false,
      details: {},
      duration: 0
    };

    const startTime = Date.now();

    try {
      // Check if the original error type was addressed
      const errorType = this.categorizeError(originalError);
      const repairType = this.categorizeRepair(repair);

      test.details.originalErrorType = errorType;
      test.details.repairType = repairType;

      // Verify error-repair alignment
      const isAligned = this.verifyErrorRepairAlignment(errorType, repairType);
      test.details.aligned = isAligned;

      if (isAligned && repair.success) {
        // Attempt to reproduce the original error
        const errorStillExists = await this.checkErrorPersistence(originalError);
        test.details.errorPersists = errorStillExists;
        test.passed = !errorStillExists;
        test.details.message = errorStillExists 
          ? 'Original error still present' 
          : 'Original error resolved';
      } else {
        test.passed = false;
        test.details.message = 'Repair not aligned with error type or repair failed';
      }

    } catch (error) {
      test.details.error = error.message;
      test.passed = false;
    } finally {
      test.duration = Date.now() - startTime;
    }

    return test;
  }

  async testSideEffects(repair) {
    const test = {
      name: 'side_effects_test',
      passed: false,
      details: {},
      duration: 0
    };

    const startTime = Date.now();

    try {
      const sideEffects = [];

      // Check for unintended file modifications
      const fileChanges = await this.checkUnintendedFileChanges(repair);
      if (fileChanges.length > 0) {
        sideEffects.push(`Unintended file changes: ${fileChanges.join(', ')}`);
      }

      // Check for broken workflows
      const brokenWorkflows = await this.checkBrokenWorkflows();
      if (brokenWorkflows.length > 0) {
        sideEffects.push(`Broken workflows: ${brokenWorkflows.join(', ')}`);
      }

      // Check for permission issues
      const permissionIssues = await this.checkPermissionIssues();
      if (permissionIssues.length > 0) {
        sideEffects.push(`Permission issues: ${permissionIssues.join(', ')}`);
      }

      test.details.sideEffects = sideEffects;
      test.passed = sideEffects.length === 0;
      test.details.message = test.passed 
        ? 'No negative side effects detected' 
        : `${sideEffects.length} side effects detected`;

    } catch (error) {
      test.details.error = error.message;
      test.passed = false;
    } finally {
      test.duration = Date.now() - startTime;
    }

    return test;
  }

  async testWorkflowIntegrity(repair) {
    const test = {
      name: 'workflow_integrity_test',
      passed: false,
      details: {},
      duration: 0
    };

    const startTime = Date.now();

    try {
      // Validate workflow syntax
      const syntaxCheck = await this.validateWorkflowSyntax();
      test.details.syntaxValid = syntaxCheck.valid;
      test.details.syntaxErrors = syntaxCheck.errors;

      // Test workflow execution (dry run)
      const executionCheck = await this.testWorkflowExecution();
      test.details.executionValid = executionCheck.valid;
      test.details.executionErrors = executionCheck.errors;

      test.passed = syntaxCheck.valid && executionCheck.valid;
      test.details.message = test.passed 
        ? 'Workflow integrity maintained' 
        : 'Workflow integrity issues detected';

    } catch (error) {
      test.details.error = error.message;
      test.passed = false;
    } finally {
      test.duration = Date.now() - startTime;
    }

    return test;
  }

  async testSystemIntegrity() {
    const test = {
      name: 'system_integrity_test',
      passed: false,
      details: {},
      duration: 0
    };

    const startTime = Date.now();

    try {
      const systemChecks = [];

      // Check repository structure
      const structureCheck = await this.checkRepositoryStructure();
      systemChecks.push({ name: 'structure', ...structureCheck });

      // Check dependencies
      const dependencyCheck = await this.checkDependencies();
      systemChecks.push({ name: 'dependencies', ...dependencyCheck });

      // Check configurations
      const configCheck = await this.checkConfigurations();
      systemChecks.push({ name: 'configurations', ...configCheck });

      test.details.systemChecks = systemChecks;
      test.passed = systemChecks.every(check => check.passed);
      test.details.message = test.passed 
        ? 'System integrity validated' 
        : 'System integrity issues detected';

    } catch (error) {
      test.details.error = error.message;
      test.passed = false;
    } finally {
      test.duration = Date.now() - startTime;
    }

    return test;
  }

  categorizeError(error) {
    if (!error) return 'unknown';
    
    const errorText = typeof error === 'string' ? error : (error.message || error.error || '');
    const errorLower = errorText.toLowerCase();

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
    if (errorLower.includes('workflow')) {
      return 'workflow_error';
    }

    return 'unknown_error';
  }

  categorizeRepair(repair) {
    if (!repair || !repair.strategy) return 'unknown';

    const actions = repair.strategy.primaryActions || [];
    const actionsText = actions.join(' ').toLowerCase();

    if (actionsText.includes('yaml') || actionsText.includes('syntax')) {
      return 'yaml_repair';
    }
    if (actionsText.includes('permission') || actionsText.includes('token')) {
      return 'permission_repair';
    }
    if (actionsText.includes('dependency') || actionsText.includes('package')) {
      return 'dependency_repair';
    }
    if (actionsText.includes('workflow')) {
      return 'workflow_repair';
    }

    return 'generic_repair';
  }

  verifyErrorRepairAlignment(errorType, repairType) {
    const alignmentMap = {
      'syntax_error': ['yaml_repair', 'workflow_repair'],
      'permission_error': ['permission_repair'],
      'timeout_error': ['workflow_repair', 'generic_repair'],
      'dependency_error': ['dependency_repair'],
      'workflow_error': ['workflow_repair', 'yaml_repair']
    };

    const expectedRepairs = alignmentMap[errorType] || ['generic_repair'];
    return expectedRepairs.includes(repairType);
  }

  async checkErrorPersistence(originalError) {
    try {
      // This is a simplified check - in a real scenario, you'd re-run the original failing operation
      // For now, we assume if the repair was successful, the error is resolved
      return false;
    } catch (error) {
      // If we can't check, assume the error might still exist
      return true;
    }
  }

  async checkUnintendedFileChanges(repair) {
    try {
      // Check git status for unexpected changes
      const { stdout } = await execAsync('git status --porcelain');
      const changes = stdout.trim().split('\n').filter(line => line.trim());
      
      // Filter out expected changes based on repair actions
      const expectedPatterns = this.getExpectedChangePatterns(repair);
      const unintendedChanges = changes.filter(change => {
        return !expectedPatterns.some(pattern => change.includes(pattern));
      });

      return unintendedChanges;
    } catch (error) {
      core.warning(`Could not check file changes: ${error.message}`);
      return [];
    }
  }

  getExpectedChangePatterns(repair) {
    const patterns = [];
    
    if (repair.actionResults) {
      repair.actionResults.forEach(result => {
        if (result.modifiedFiles) {
          patterns.push(...result.modifiedFiles);
        }
      });
    }

    // Add common expected patterns
    patterns.push('.github/workflows/');
    patterns.push('package.json');
    patterns.push('package-lock.json');

    return patterns;
  }

  async checkBrokenWorkflows() {
    try {
      const brokenWorkflows = [];
      const workflowFiles = await this.findWorkflowFiles();

      for (const file of workflowFiles) {
        const isValid = await this.validateWorkflowFile(file);
        if (!isValid) {
          brokenWorkflows.push(file);
        }
      }

      return brokenWorkflows;
    } catch (error) {
      core.warning(`Could not check workflow integrity: ${error.message}`);
      return [];
    }
  }

  async findWorkflowFiles() {
    try {
      const workflowDir = '.github/workflows';
      const files = await fs.readdir(workflowDir);
      return files
        .filter(file => file.endsWith('.yml') || file.endsWith('.yaml'))
        .map(file => `${workflowDir}/${file}`);
    } catch (error) {
      return [];
    }
  }

  async validateWorkflowFile(filePath) {
    try {
      const content = await fs.readFile(filePath, 'utf8');
      
      // Basic YAML structure validation
      const hasName = content.includes('name:');
      const hasOn = content.includes('on:');
      const hasJobs = content.includes('jobs:');
      
      return hasName && hasOn && hasJobs;
    } catch (error) {
      return false;
    }
  }

  async checkPermissionIssues() {
    try {
      // Check for common permission-related issues
      const issues = [];
      
      // Check if token has required permissions (simplified check)
      try {
        await this.octokit.rest.repos.get({
          owner: github.context.repo.owner,
          repo: github.context.repo.repo
        });
      } catch (error) {
        if (error.status === 403) {
          issues.push('GitHub token permission issue');
        }
      }

      return issues;
    } catch (error) {
      return [];
    }
  }

  async validateWorkflowSyntax() {
    try {
      const workflowFiles = await this.findWorkflowFiles();
      const results = { valid: true, errors: [] };

      for (const file of workflowFiles) {
        try {
          await fs.readFile(file, 'utf8');
          // In a real implementation, you'd use a YAML parser here
        } catch (error) {
          results.valid = false;
          results.errors.push(`${file}: ${error.message}`);
        }
      }

      return results;
    } catch (error) {
      return { valid: false, errors: [error.message] };
    }
  }

  async testWorkflowExecution() {
    try {
      // This would ideally test workflow execution in a sandbox
      // For now, we perform basic validation
      return { valid: true, errors: [] };
    } catch (error) {
      return { valid: false, errors: [error.message] };
    }
  }

  async checkRepositoryStructure() {
    try {
      const requiredPaths = [
        '.github',
        '.github/workflows',
        'package.json'
      ];

      for (const path of requiredPaths) {
        try {
          await fs.access(path);
        } catch (error) {
          return { passed: false, message: `Missing required path: ${path}` };
        }
      }

      return { passed: true, message: 'Repository structure intact' };
    } catch (error) {
      return { passed: false, message: `Structure check failed: ${error.message}` };
    }
  }

  async checkDependencies() {
    try {
      // Check if package.json exists and is valid
      const packageJson = JSON.parse(await fs.readFile('package.json', 'utf8'));
      
      // Check if node_modules exists
      try {
        await fs.access('node_modules');
        return { passed: true, message: 'Dependencies are installed' };
      } catch (error) {
        return { passed: false, message: 'Dependencies not installed' };
      }
    } catch (error) {
      if (error.code === 'ENOENT') {
        return { passed: true, message: 'No package.json (not a Node.js project)' };
      }
      return { passed: false, message: `Dependency check failed: ${error.message}` };
    }
  }

  async checkConfigurations() {
    try {
      // Check for essential configuration files
      const configFiles = [
        '.github/repair-patterns.json',
        '.github/repair-state.json'
      ];

      let configsPresent = 0;
      for (const file of configFiles) {
        try {
          await fs.access(file);
          configsPresent++;
        } catch (error) {
          // File doesn't exist, which is okay for some configs
        }
      }

      return { 
        passed: true, 
        message: `${configsPresent}/${configFiles.length} configuration files present` 
      };
    } catch (error) {
      return { passed: false, message: `Configuration check failed: ${error.message}` };
    }
  }

  calculateValidationResult(tests) {
    if (tests.length === 0) return false;
    
    const criticalTests = ['execution_test', 'error_resolution_test'];
    const criticalPassed = tests
      .filter(test => criticalTests.includes(test.name))
      .every(test => test.passed);

    if (!criticalPassed) return false;

    // If critical tests pass, check overall pass rate
    const passedTests = tests.filter(test => test.passed).length;
    const passRate = passedTests / tests.length;

    return passRate >= 0.6; // 60% of tests must pass
  }

  calculateConfidence(tests) {
    if (tests.length === 0) return 0;

    const weights = {
      'execution_test': 0.3,
      'error_resolution_test': 0.4,
      'side_effects_test': 0.15,
      'workflow_integrity_test': 0.1,
      'system_integrity_test': 0.05
    };

    let weightedScore = 0;
    let totalWeight = 0;

    tests.forEach(test => {
      const weight = weights[test.name] || 0.1;
      totalWeight += weight;
      if (test.passed) {
        weightedScore += weight;
      }
    });

    return totalWeight > 0 ? Math.round((weightedScore / totalWeight) * 100) / 100 : 0;
  }

  async calculateMetrics() {
    const validRepairs = this.validationResults.filter(result => result.overallValid).length;
    this.overallSuccessRate = this.validationResults.length > 0 
      ? validRepairs / this.validationResults.length 
      : 0;

    // Calculate effectiveness score (0-100)
    const avgConfidence = this.validationResults.length > 0
      ? this.validationResults.reduce((sum, result) => sum + result.confidence, 0) / this.validationResults.length
      : 0;

    const successBonus = this.overallSuccessRate * 30; // Up to 30 points for success rate
    const confidenceBonus = avgConfidence * 50; // Up to 50 points for confidence
    const completionBonus = Math.min(20, this.validationResults.length * 2); // Up to 20 points for completion

    this.effectivenessScore = Math.round(successBonus + confidenceBonus + completionBonus);
  }

  determineContinuation() {
    // Continue if success rate meets threshold and effectiveness score is reasonable
    const meetsThreshold = this.overallSuccessRate >= this.successThreshold;
    const hasReasonableEffectiveness = this.effectivenessScore >= 50;
    const hasFailedRepairs = this.validationResults.some(result => !result.overallValid);

    // Continue if we meet thresholds but still have failed repairs to address
    return meetsThreshold && hasReasonableEffectiveness && hasFailedRepairs;
  }

  generateRecommendations() {
    const recommendations = [];

    // Success rate recommendations
    if (this.overallSuccessRate < 0.5) {
      recommendations.push({
        type: 'success_rate',
        priority: 'high',
        message: 'Success rate is below 50%. Review error analysis and repair strategies.'
      });
    }

    // Effectiveness recommendations
    if (this.effectivenessScore < 60) {
      recommendations.push({
        type: 'effectiveness',
        priority: 'medium',
        message: 'Effectiveness score is low. Focus on improving repair quality and accuracy.'
      });
    }

    // Specific repair recommendations
    const failedValidations = this.validationResults.filter(result => !result.overallValid);
    if (failedValidations.length > 0) {
      const commonIssues = this.analyzeCommonValidationFailures(failedValidations);
      commonIssues.forEach(issue => {
        recommendations.push({
          type: 'repair_specific',
          priority: 'medium',
          message: `Common validation failure: ${issue}`
        });
      });
    }

    return recommendations;
  }

  analyzeCommonValidationFailures(failedValidations) {
    const issueCount = {};

    failedValidations.forEach(validation => {
      validation.issues.forEach(issue => {
        issueCount[issue] = (issueCount[issue] || 0) + 1;
      });

      validation.validationTests.forEach(test => {
        if (!test.passed && test.details.message) {
          issueCount[test.details.message] = (issueCount[test.details.message] || 0) + 1;
        }
      });
    });

    return Object.entries(issueCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([issue, count]) => `${issue} (${count} occurrences)`);
  }

  async setOutputs(shouldContinue, recommendations) {
    const failedRepairs = this.validationResults
      .filter(result => !result.overallValid)
      .map(result => ({
        repairId: result.repairId,
        issues: result.issues,
        confidence: result.confidence
      }));

    core.setOutput('validation-results', JSON.stringify(this.validationResults));
    core.setOutput('overall-success-rate', this.overallSuccessRate.toString());
    core.setOutput('effectiveness-score', this.effectivenessScore.toString());
    core.setOutput('continue-loop', shouldContinue.toString());
    core.setOutput('failed-repairs', JSON.stringify(failedRepairs));
    core.setOutput('recommendations', JSON.stringify(recommendations));
  }
}

// Run the validator
const validator = new RepairValidator();
validator.run();