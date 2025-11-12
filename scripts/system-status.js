#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const GLOBAL_HOME = '/mnt/Linux-ExHDD/Claude-GlobalSettings';

// カラーコード
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  purple: '\x1b[35m',
  cyan: '\x1b[36m'
};

console.log(`${colors.purple}═══════════════════════════════════════════════════════${colors.reset}`);
console.log(`${colors.purple}     Claude AI Development Environment - Status${colors.reset}`);
console.log(`${colors.purple}═══════════════════════════════════════════════════════${colors.reset}`);
console.log('');

// グローバル設定の確認
console.log(`${colors.cyan}📍 Global Settings${colors.reset}`);
console.log(`   Location: ${colors.blue}${GLOBAL_HOME}${colors.reset}`);
console.log(`   User Config: ${colors.blue}${process.env.HOME}/.claude${colors.reset}`);
console.log('');

// コンポーネント状態確認
console.log(`${colors.cyan}📊 Components Status${colors.reset}`);

const components = [
  {
    name: 'SubAgent',
    check: () => fs.existsSync(path.join(GLOBAL_HOME, '.claude/agents/agent-config.yaml')),
    path: '.claude/agents/'
  },
  {
    name: 'Claude-Flow',
    check: () => fs.existsSync(path.join(GLOBAL_HOME, '.claude/flow-config/claude-flow.config.js')),
    path: '.claude/flow-config/'
  },
  {
    name: 'Context7',
    check: () => fs.existsSync(path.join(GLOBAL_HOME, '.claude/context7/context7.config.json')),
    path: '.claude/context7/'
  },
  {
    name: 'SerenaMCP',
    check: () => fs.existsSync(path.join(GLOBAL_HOME, '.claude/serena/serena-mcp.yaml')),
    path: '.claude/serena/'
  },
  {
    name: 'Hive-Mind',
    check: () => fs.existsSync(path.join(GLOBAL_HOME, 'config/hive-mind/hive-mind.config.ts')),
    path: 'config/hive-mind/'
  },
  {
    name: 'Workflows',
    check: () => fs.existsSync(path.join(GLOBAL_HOME, '.claude/workflows/workflow.yaml')),
    path: '.claude/workflows/'
  },
  {
    name: 'Hooks',
    check: () => fs.existsSync(path.join(GLOBAL_HOME, '.claude/hooks/hook-manager.ts')),
    path: '.claude/hooks/'
  }
];

components.forEach(comp => {
  const status = comp.check();
  const icon = status ? `${colors.green}✓${colors.reset}` : `${colors.red}✗${colors.reset}`;
  const statusText = status ? `${colors.green}Configured${colors.reset}` : `${colors.red}Not Found${colors.reset}`;
  console.log(`   ${icon} ${comp.name.padEnd(15)} ${statusText}`);
});

// プロセス状態確認
console.log('');
console.log(`${colors.cyan}🔄 Running Processes${colors.reset}`);

try {
  const claudeFlowRunning = execSync('pgrep -f "claude-flow"', { encoding: 'utf-8' }).trim();
  if (claudeFlowRunning) {
    console.log(`   ${colors.green}✓${colors.reset} Claude-Flow    ${colors.green}Running (PID: ${claudeFlowRunning.split('\n')[0]})${colors.reset}`);
  } else {
    console.log(`   ${colors.yellow}○${colors.reset} Claude-Flow    ${colors.yellow}Not Running${colors.reset}`);
  }
} catch (e) {
  console.log(`   ${colors.yellow}○${colors.reset} Claude-Flow    ${colors.yellow}Not Running${colors.reset}`);
}

// 依存関係の確認
console.log('');
console.log(`${colors.cyan}📦 Dependencies${colors.reset}`);

const packageJsonPath = path.join(GLOBAL_HOME, 'package.json');
if (fs.existsSync(packageJsonPath)) {
  const pkg = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
  const deps = Object.keys(pkg.dependencies || {}).length;
  const devDeps = Object.keys(pkg.devDependencies || {}).length;
  const optDeps = Object.keys(pkg.optionalDependencies || {}).length;
  
  console.log(`   Dependencies: ${deps}`);
  console.log(`   Dev Dependencies: ${devDeps}`);
  console.log(`   Optional Dependencies: ${optDeps}`);
}

// Node.jsバージョン
console.log('');
console.log(`${colors.cyan}⚙️  Environment${colors.reset}`);
const nodeVersion = process.version;
console.log(`   Node.js: ${nodeVersion}`);

try {
  const npmVersion = execSync('npm -v', { encoding: 'utf-8' }).trim();
  console.log(`   npm: v${npmVersion}`);
} catch (e) {
  console.log(`   npm: ${colors.red}Not Found${colors.reset}`);
}

// 使用可能なコマンド
console.log('');
console.log(`${colors.cyan}💡 Available Commands${colors.reset}`);
console.log('   claude-new-project <name>  - Create new AI project');
console.log('   claude-enable              - Enable AI in current project');
console.log('   claude-init                - Initialize AI environment');
console.log('   claude-flow                - Start Claude-Flow swarm');
console.log('   claude-start               - Start integrated system');
console.log('   claude-status              - Show this status');
console.log('   claude-update              - Update global settings');
console.log('   claude-help                - Show detailed help');

console.log('');
console.log(`${colors.purple}═══════════════════════════════════════════════════════${colors.reset}`);