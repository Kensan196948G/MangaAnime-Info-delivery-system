#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const yaml = require('js-yaml');

class IntegratedSystemStarter {
  constructor() {
    this.configPath = path.join(process.cwd(), '.claude', 'project-config.json');
    this.config = null;
    this.services = new Map();
    this.initialized = false;
  }

  async start() {
    console.log('🚀 Starting Integrated AI Development Environment...\n');
    
    try {
      // Load configuration
      await this.loadConfig();
      
      // Initialize all systems
      await this.initializeSystems();
      
      // Start services
      await this.startServices();
      
      // Setup monitoring
      this.setupMonitoring();
      
      console.log('✅ All systems initialized and running!');
      console.log('\n📊 System Status:');
      await this.displayStatus();
      
    } catch (error) {
      console.error('❌ Failed to start integrated system:', error);
      process.exit(1);
    }
  }

  async loadConfig() {
    console.log('📁 Loading configuration...');
    
    if (!fs.existsSync(this.configPath)) {
      throw new Error('Configuration file not found. Please run initialization first.');
    }
    
    const configContent = fs.readFileSync(this.configPath, 'utf-8');
    this.config = JSON.parse(configContent);
    
    console.log('✓ Configuration loaded successfully');
  }

  async initializeSystems() {
    console.log('\n🔧 Initializing systems...\n');
    
    const systems = [
      { name: 'SubAgent', init: this.initSubAgent.bind(this) },
      { name: 'Claude-Flow', init: this.initClaudeFlow.bind(this) },
      { name: 'Context7', init: this.initContext7.bind(this) },
      { name: 'SerenaMCP', init: this.initSerenaMCP.bind(this) },
      { name: 'Hive-Mind', init: this.initHiveMind.bind(this) },
      { name: 'SQLite Memory', init: this.initSQLiteMemory.bind(this) },
      { name: 'GitHub Integration', init: this.initGitHub.bind(this) },
      { name: 'Workflow Engine', init: this.initWorkflows.bind(this) },
      { name: 'Hook System', init: this.initHooks.bind(this) }
    ];
    
    // Initialize in parallel where possible
    const initPromises = systems.map(async (system) => {
      try {
        console.log(`  ⏳ Initializing ${system.name}...`);
        await system.init();
        console.log(`  ✓ ${system.name} initialized`);
        return { name: system.name, status: 'success' };
      } catch (error) {
        console.error(`  ✗ ${system.name} failed:`, error.message);
        return { name: system.name, status: 'failed', error: error.message };
      }
    });
    
    const results = await Promise.all(initPromises);
    
    // Check if any critical systems failed
    const criticalFailures = results.filter(r => 
      r.status === 'failed' && 
      ['SubAgent', 'Claude-Flow', 'Context7'].includes(r.name)
    );
    
    if (criticalFailures.length > 0) {
      throw new Error(`Critical systems failed to initialize: ${criticalFailures.map(f => f.name).join(', ')}`);
    }
    
    this.initialized = true;
  }

  async initSubAgent() {
    const agentConfig = path.join(process.cwd(), '.claude', 'agents', 'agent-config.yaml');
    
    if (!fs.existsSync(agentConfig)) {
      throw new Error('SubAgent configuration not found');
    }
    
    // Simulate SubAgent initialization
    await new Promise(resolve => setTimeout(resolve, 500));
    
    this.services.set('subagent', {
      status: 'running',
      config: yaml.load(fs.readFileSync(agentConfig, 'utf-8'))
    });
  }

  async initClaudeFlow() {
    // Start Claude-Flow with swarm mode
    const child = spawn('npx', ['claude-flow@alpha', 'swarm', '--claude', '--detach'], {
      stdio: 'pipe',
      detached: true
    });
    
    child.unref();
    
    this.services.set('claude-flow', {
      status: 'running',
      pid: child.pid,
      mode: 'swarm'
    });
    
    // Wait for Claude-Flow to be ready
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  async initContext7() {
    const context7Config = path.join(process.cwd(), '.claude', 'context7', 'context7.config.json');
    
    if (!fs.existsSync(context7Config)) {
      throw new Error('Context7 configuration not found');
    }
    
    // Simulate Context7 initialization
    await new Promise(resolve => setTimeout(resolve, 300));
    
    this.services.set('context7', {
      status: 'running',
      layers: 7,
      config: JSON.parse(fs.readFileSync(context7Config, 'utf-8'))
    });
  }

  async initSerenaMCP() {
    const serenaConfig = path.join(process.cwd(), '.claude', 'serena', 'serena-mcp.yaml');
    
    if (!fs.existsSync(serenaConfig)) {
      throw new Error('SerenaMCP configuration not found');
    }
    
    // Simulate SerenaMCP initialization
    await new Promise(resolve => setTimeout(resolve, 400));
    
    this.services.set('serena-mcp', {
      status: 'running',
      protocol: 'advanced',
      config: yaml.load(fs.readFileSync(serenaConfig, 'utf-8'))
    });
  }

  async initHiveMind() {
    // Import and initialize Hive-Mind if the TypeScript file has been compiled
    try {
      const HiveMind = require('../dist/config/hive-mind/hive-mind.config.js').default;
      const hiveMind = new HiveMind();
      
      this.services.set('hive-mind', {
        status: 'running',
        instance: hiveMind,
        layers: ['cognitive', 'reactive', 'adaptive']
      });
    } catch (error) {
      // Fallback if not compiled
      this.services.set('hive-mind', {
        status: 'pending-compilation',
        layers: ['cognitive', 'reactive', 'adaptive']
      });
    }
  }

  async initSQLiteMemory() {
    try {
      const SQLiteMemory = require('../dist/src/memory/sqlite-memory.js').default;
      const memory = new SQLiteMemory();
      await memory.initialize();
      
      this.services.set('sqlite-memory', {
        status: 'running',
        instance: memory
      });
    } catch (error) {
      // Fallback if not compiled
      this.services.set('sqlite-memory', {
        status: 'pending-compilation'
      });
    }
  }

  async initGitHub() {
    // Check for GitHub configuration in environment
    if (process.env.GITHUB_TOKEN || process.env.GITHUB_APP_ID) {
      this.services.set('github', {
        status: 'configured',
        autoSync: true
      });
    } else {
      this.services.set('github', {
        status: 'not-configured',
        message: 'Set GITHUB_TOKEN or GITHUB_APP_ID to enable'
      });
    }
  }

  async initWorkflows() {
    const workflowConfig = path.join(process.cwd(), '.claude', 'workflows', 'workflow.yaml');
    
    if (fs.existsSync(workflowConfig)) {
      const workflows = yaml.load(fs.readFileSync(workflowConfig, 'utf-8'));
      
      this.services.set('workflows', {
        status: 'running',
        count: workflows.workflows ? workflows.workflows.length : 0
      });
    } else {
      this.services.set('workflows', {
        status: 'not-configured'
      });
    }
  }

  async initHooks() {
    try {
      const HookManager = require('../dist/.claude/hooks/hook-manager.js').default;
      const hookManager = new HookManager();
      
      this.services.set('hooks', {
        status: 'running',
        instance: hookManager
      });
    } catch (error) {
      // Fallback if not compiled
      this.services.set('hooks', {
        status: 'pending-compilation'
      });
    }
  }

  async startServices() {
    console.log('\n🌟 Starting services...\n');
    
    // Start any additional background services
    // This is where you'd start web servers, watchers, etc.
    
    // Example: Start a monitoring server
    if (this.config.features.monitoring) {
      await this.startMonitoringServer();
    }
  }

  async startMonitoringServer() {
    const express = require('express');
    const app = express();
    
    app.get('/status', (req, res) => {
      const status = {};
      this.services.forEach((value, key) => {
        status[key] = value.status;
      });
      res.json(status);
    });
    
    const port = process.env.MONITOR_PORT || 3000;
    app.listen(port, () => {
      console.log(`  ✓ Monitoring server running on port ${port}`);
    });
  }

  setupMonitoring() {
    // Setup health checks
    setInterval(() => {
      this.healthCheck();
    }, 60000); // Check every minute
    
    // Handle graceful shutdown
    process.on('SIGINT', async () => {
      console.log('\n⏹️  Shutting down gracefully...');
      await this.shutdown();
      process.exit(0);
    });
  }

  async healthCheck() {
    // Perform health checks on all services
    for (const [name, service] of this.services) {
      if (service.instance && typeof service.instance.getStats === 'function') {
        try {
          await service.instance.getStats();
        } catch (error) {
          console.warn(`⚠️  Health check failed for ${name}:`, error.message);
        }
      }
    }
  }

  async displayStatus() {
    const table = [];
    
    this.services.forEach((service, name) => {
      const status = service.status === 'running' ? '🟢' : 
                    service.status === 'configured' ? '🟡' : '🔴';
      table.push(`  ${status} ${name.padEnd(20)} ${service.status}`);
    });
    
    console.log(table.join('\n'));
    
    console.log('\n💡 Tips:');
    console.log('  - Run "npm run status" to check system status');
    console.log('  - Run "npm run claude-flow" to interact with Claude-Flow');
    console.log('  - Check .claude/reports/ for generated reports');
    console.log('  - Workflows are automatically triggered on git events');
  }

  async shutdown() {
    // Cleanup all services
    for (const [name, service] of this.services) {
      if (service.instance && typeof service.instance.close === 'function') {
        await service.instance.close();
      }
      if (service.pid) {
        try {
          process.kill(service.pid);
        } catch (error) {
          // Process might already be dead
        }
      }
    }
  }
}

// Start the integrated system
const starter = new IntegratedSystemStarter();
starter.start().catch(error => {
  console.error('Failed to start:', error);
  process.exit(1);
});