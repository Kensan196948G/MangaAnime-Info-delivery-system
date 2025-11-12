import { EventEmitter } from 'events';
import * as fs from 'fs/promises';
import * as path from 'path';
import { spawn } from 'child_process';
import * as yaml from 'js-yaml';

export interface Hook {
  name: string;
  type: 'pre' | 'post' | 'error';
  script?: string;
  command?: string;
  agent?: string;
  action?: string;
  condition?: string;
  timeout?: number;
  async?: boolean;
}

export interface HookContext {
  workflow?: string;
  trigger?: any;
  error?: any;
  result?: any;
  timestamp: number;
  environment: Record<string, string>;
}

export class HookManager extends EventEmitter {
  private hooks: Map<string, Hook[]> = new Map();
  private globalHooks: Map<string, Hook[]> = new Map();
  private running: Set<string> = new Set();
  
  constructor(private configPath: string = '.claude/hooks') {
    super();
    this.loadHooks();
  }

  async loadHooks(): Promise<void> {
    try {
      // Load global hooks configuration
      const globalConfigPath = path.join(this.configPath, 'hooks.yaml');
      if (await this.fileExists(globalConfigPath)) {
        const content = await fs.readFile(globalConfigPath, 'utf-8');
        const config = yaml.load(content) as any;
        
        if (config.global) {
          Object.entries(config.global).forEach(([event, hooks]) => {
            this.globalHooks.set(event, hooks as Hook[]);
          });
        }
        
        if (config.workflows) {
          Object.entries(config.workflows).forEach(([workflow, events]) => {
            Object.entries(events as any).forEach(([event, hooks]) => {
              const key = `${workflow}:${event}`;
              this.hooks.set(key, hooks as Hook[]);
            });
          });
        }
      }

      // Load individual hook files
      await this.loadHookFiles();
      
      this.emit('hooks:loaded', {
        globalCount: this.globalHooks.size,
        workflowCount: this.hooks.size
      });
    } catch (error) {
      this.emit('error', { message: 'Failed to load hooks', error });
    }
  }

  private async loadHookFiles(): Promise<void> {
    const hookFiles = [
      'pre-init.js',
      'post-init.js',
      'pre-task.js',
      'post-task.js',
      'on-error.js'
    ];

    for (const file of hookFiles) {
      const filePath = path.join(this.configPath, file);
      if (await this.fileExists(filePath)) {
        const eventName = file.replace('.js', '').replace('-', ':');
        await this.createHookFromFile(eventName, filePath);
      }
    }
  }

  private async createHookFromFile(eventName: string, filePath: string): Promise<void> {
    const hook: Hook = {
      name: path.basename(filePath),
      type: eventName.includes('pre') ? 'pre' : eventName.includes('post') ? 'post' : 'error',
      script: filePath,
      async: true
    };

    const existing = this.globalHooks.get(eventName) || [];
    existing.push(hook);
    this.globalHooks.set(eventName, existing);
  }

  async executeHooks(
    event: string,
    context: HookContext,
    workflow?: string
  ): Promise<any[]> {
    const results: any[] = [];
    
    // Execute global hooks
    const globalHooks = this.globalHooks.get(event) || [];
    for (const hook of globalHooks) {
      if (await this.shouldExecute(hook, context)) {
        const result = await this.executeHook(hook, context);
        results.push(result);
      }
    }
    
    // Execute workflow-specific hooks
    if (workflow) {
      const workflowHooks = this.hooks.get(`${workflow}:${event}`) || [];
      for (const hook of workflowHooks) {
        if (await this.shouldExecute(hook, context)) {
          const result = await this.executeHook(hook, context);
          results.push(result);
        }
      }
    }
    
    return results;
  }

  private async shouldExecute(hook: Hook, context: HookContext): Promise<boolean> {
    if (!hook.condition) return true;
    
    try {
      // Evaluate condition
      const conditionFunc = new Function('context', `
        with (context) {
          return ${hook.condition};
        }
      `);
      
      return conditionFunc(context);
    } catch (error) {
      this.emit('error', {
        message: 'Failed to evaluate hook condition',
        hook: hook.name,
        error
      });
      return false;
    }
  }

  private async executeHook(hook: Hook, context: HookContext): Promise<any> {
    const hookId = `${hook.name}-${Date.now()}`;
    this.running.add(hookId);
    
    this.emit('hook:start', { hook: hook.name, context });
    
    try {
      let result: any;
      
      if (hook.script) {
        result = await this.executeScript(hook.script, context, hook.timeout);
      } else if (hook.command) {
        result = await this.executeCommand(hook.command, context, hook.timeout);
      } else if (hook.agent && hook.action) {
        result = await this.executeAgent(hook.agent, hook.action, context);
      }
      
      this.emit('hook:complete', {
        hook: hook.name,
        result,
        duration: Date.now() - context.timestamp
      });
      
      return result;
    } catch (error) {
      this.emit('hook:error', {
        hook: hook.name,
        error,
        context
      });
      
      if (hook.type === 'error') {
        throw error; // Re-throw for error hooks
      }
      
      return { error: error.message };
    } finally {
      this.running.delete(hookId);
    }
  }

  private async executeScript(
    scriptPath: string,
    context: HookContext,
    timeout?: number
  ): Promise<any> {
    const absolutePath = path.isAbsolute(scriptPath) 
      ? scriptPath 
      : path.join(process.cwd(), scriptPath);
    
    return new Promise((resolve, reject) => {
      const child = spawn('node', [absolutePath], {
        env: {
          ...process.env,
          ...context.environment,
          HOOK_CONTEXT: JSON.stringify(context)
        }
      });
      
      let output = '';
      let error = '';
      let timer: NodeJS.Timeout;
      
      if (timeout) {
        timer = setTimeout(() => {
          child.kill('SIGTERM');
          reject(new Error(`Hook timed out after ${timeout}ms`));
        }, timeout);
      }
      
      child.stdout.on('data', (data) => {
        output += data.toString();
      });
      
      child.stderr.on('data', (data) => {
        error += data.toString();
      });
      
      child.on('exit', (code) => {
        if (timer) clearTimeout(timer);
        
        if (code === 0) {
          resolve({ output, code });
        } else {
          reject(new Error(`Script exited with code ${code}: ${error}`));
        }
      });
    });
  }

  private async executeCommand(
    command: string,
    context: HookContext,
    timeout?: number
  ): Promise<any> {
    // Replace variables in command
    const processedCommand = this.processTemplate(command, context);
    
    return new Promise((resolve, reject) => {
      const child = spawn('sh', ['-c', processedCommand], {
        env: {
          ...process.env,
          ...context.environment
        }
      });
      
      let output = '';
      let error = '';
      let timer: NodeJS.Timeout;
      
      if (timeout) {
        timer = setTimeout(() => {
          child.kill('SIGTERM');
          reject(new Error(`Command timed out after ${timeout}ms`));
        }, timeout);
      }
      
      child.stdout.on('data', (data) => {
        output += data.toString();
      });
      
      child.stderr.on('data', (data) => {
        error += data.toString();
      });
      
      child.on('exit', (code) => {
        if (timer) clearTimeout(timer);
        
        if (code === 0) {
          resolve({ output, code });
        } else {
          reject(new Error(`Command exited with code ${code}: ${error}`));
        }
      });
    });
  }

  private async executeAgent(
    agentName: string,
    action: string,
    context: HookContext
  ): Promise<any> {
    // This would integrate with the SubAgent system
    this.emit('agent:execute', { agent: agentName, action, context });
    
    // Simulate agent execution
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          agent: agentName,
          action,
          result: 'Agent action completed'
        });
      }, 100);
    });
  }

  private processTemplate(template: string, context: HookContext): string {
    return template.replace(/\${([^}]+)}/g, (match, path) => {
      const keys = path.split('.');
      let value: any = context;
      
      for (const key of keys) {
        if (value && typeof value === 'object') {
          value = value[key];
        } else {
          return match;
        }
      }
      
      return value !== undefined ? String(value) : match;
    });
  }

  private async fileExists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  registerHook(event: string, hook: Hook, workflow?: string): void {
    const key = workflow ? `${workflow}:${event}` : event;
    const collection = workflow ? this.hooks : this.globalHooks;
    
    const existing = collection.get(key) || [];
    existing.push(hook);
    collection.set(key, existing);
    
    this.emit('hook:registered', { event, hook, workflow });
  }

  unregisterHook(event: string, hookName: string, workflow?: string): void {
    const key = workflow ? `${workflow}:${event}` : event;
    const collection = workflow ? this.hooks : this.globalHooks;
    
    const hooks = collection.get(key) || [];
    const filtered = hooks.filter(h => h.name !== hookName);
    
    if (filtered.length > 0) {
      collection.set(key, filtered);
    } else {
      collection.delete(key);
    }
    
    this.emit('hook:unregistered', { event, hookName, workflow });
  }

  async waitForRunningHooks(): Promise<void> {
    while (this.running.size > 0) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }

  getRegisteredHooks(): { global: Map<string, Hook[]>, workflows: Map<string, Hook[]> } {
    return {
      global: new Map(this.globalHooks),
      workflows: new Map(this.hooks)
    };
  }
}

export default HookManager;