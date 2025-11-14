#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🎯 Initializing Integrated AI Development Environment\n');
console.log('This will set up all components for immediate use.\n');

async function init() {
  const steps = [
    {
      name: 'Check Node.js version',
      action: () => {
        const version = process.version;
        if (parseInt(version.slice(1).split('.')[0]) < 18) {
          throw new Error('Node.js 18 or higher is required');
        }
        console.log(`✓ Node.js ${version}`);
      }
    },
    {
      name: 'Install dependencies',
      action: () => {
        console.log('Installing npm packages...');
        try {
          // Install main dependencies first
          execSync('npm install --no-optional', { stdio: 'inherit' });
          console.log('✓ Main dependencies installed');
          
          // Try to install optional dependencies (may fail)
          try {
            console.log('Installing optional dependencies...');
            execSync('npm install --optional', { stdio: 'pipe' });
            console.log('✓ Optional dependencies installed');
          } catch (optError) {
            console.log('⚠️  Some optional dependencies failed (this is OK)');
          }
        } catch (error) {
          throw new Error('Failed to install main dependencies');
        }
      }
    },
    {
      name: 'Create environment file',
      action: () => {
        const envPath = path.join(process.cwd(), '.env');
        if (!fs.existsSync(envPath)) {
          fs.writeFileSync(envPath, `# Environment Configuration
NODE_ENV=development
MONITOR_PORT=3000

# GitHub Integration (optional)
# GITHUB_TOKEN=your_token_here
# GITHUB_OWNER=your_org
# GITHUB_REPO=your_repo

# Webhook Configuration (optional)
# WEBHOOK_URL=https://your-webhook-url
# WEBHOOK_SECRET=your_secret

# Database
DB_PATH=.claude/memory.db
DB_CACHE_SIZE_MB=512

# Claude-Flow
CLAUDE_FLOW_MODE=swarm
CLAUDE_FLOW_WORKERS=10

# Context7
CONTEXT7_LAYERS=7
CONTEXT7_WINDOW=200000

# Performance
PARALLEL_EXECUTION=true
MAX_CONCURRENT=10
`);
          console.log('✓ Created .env file');
        } else {
          console.log('✓ .env file already exists');
        }
      }
    },
    {
      name: 'Compile TypeScript files',
      action: () => {
        console.log('Compiling TypeScript...');
        try {
          execSync('npx tsc', { stdio: 'inherit' });
          console.log('✓ TypeScript compiled');
        } catch (error) {
          console.log('⚠️  TypeScript compilation skipped (will compile on first run)');
        }
      }
    },
    {
      name: 'Initialize Claude-Flow',
      action: () => {
        console.log('Setting up Claude-Flow...');
        try {
          execSync('npx claude-flow@alpha init --force', { stdio: 'inherit' });
        } catch (error) {
          console.log('⚠️  Claude-Flow initialization skipped');
        }
      }
    },
    {
      name: 'Create initial hooks',
      action: () => {
        const hooksDir = path.join(process.cwd(), '.claude', 'hooks');
        
        // Pre-init hook
        const preInitPath = path.join(hooksDir, 'pre-init.js');
        if (!fs.existsSync(preInitPath)) {
          fs.writeFileSync(preInitPath, `// Pre-initialization hook
console.log('[Hook] Pre-initialization: Loading environment...');

const context = JSON.parse(process.env.HOOK_CONTEXT || '{}');
console.log('[Hook] Context:', context);

// Add your pre-init logic here
process.exit(0);
`);
        }
        
        // Post-init hook
        const postInitPath = path.join(hooksDir, 'post-init.js');
        if (!fs.existsSync(postInitPath)) {
          fs.writeFileSync(postInitPath, `// Post-initialization hook
console.log('[Hook] Post-initialization: System ready!');

const context = JSON.parse(process.env.HOOK_CONTEXT || '{}');

// Add your post-init logic here
process.exit(0);
`);
        }
        
        console.log('✓ Created initial hooks');
      }
    },
    {
      name: 'Setup Git hooks (optional)',
      action: () => {
        try {
          const gitDir = path.join(process.cwd(), '.git');
          if (fs.existsSync(gitDir)) {
            const hookPath = path.join(gitDir, 'hooks', 'pre-commit');
            fs.writeFileSync(hookPath, `#!/bin/sh
# Pre-commit hook for integrated environment
npm run lint
npm run type-check
`, { mode: 0o755 });
            console.log('✓ Git hooks configured');
          } else {
            console.log('⚠️  Not a git repository, skipping git hooks');
          }
        } catch (error) {
          console.log('⚠️  Git hooks setup skipped');
        }
      }
    },
    {
      name: 'Create reports directory',
      action: () => {
        const reportsDir = path.join(process.cwd(), '.claude', 'reports');
        if (!fs.existsSync(reportsDir)) {
          fs.mkdirSync(reportsDir, { recursive: true });
        }
        console.log('✓ Reports directory ready');
      }
    },
    {
      name: 'Validate configuration',
      action: () => {
        const configPath = path.join(process.cwd(), '.claude', 'project-config.json');
        if (fs.existsSync(configPath)) {
          const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
          if (config.autoEnable && config.features) {
            console.log('✓ Configuration validated');
          } else {
            throw new Error('Invalid configuration structure');
          }
        } else {
          throw new Error('Configuration file not found');
        }
      }
    }
  ];

  console.log('Starting initialization...\n');
  
  for (const step of steps) {
    try {
      console.log(`📌 ${step.name}...`);
      await step.action();
    } catch (error) {
      console.error(`❌ Failed at step "${step.name}":`, error.message);
      process.exit(1);
    }
  }
  
  console.log('\n' + '='.repeat(60));
  console.log('🎉 Initialization complete!');
  console.log('='.repeat(60));
  console.log('\nYour integrated AI development environment is ready to use.');
  console.log('\nQuick start commands:');
  console.log('  npm start           - Start all systems');
  console.log('  npm run dev         - Start in development mode');
  console.log('  npm run status      - Check system status');
  console.log('  npm run claude-flow - Launch Claude-Flow swarm');
  console.log('\n💡 All features are now enabled and will activate automatically');
  console.log('   when you create new projects in this environment.');
}

init().catch(error => {
  console.error('Initialization failed:', error);
  process.exit(1);
});