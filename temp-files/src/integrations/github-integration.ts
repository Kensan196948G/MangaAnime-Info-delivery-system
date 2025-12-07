import { Octokit } from '@octokit/rest';
import { createAppAuth } from '@octokit/auth-app';
import { webhooks, EmitterWebhookEvent } from '@octokit/webhooks';
import EventEmitter from 'events';

export interface GitHubConfig {
  auth: {
    type: 'token' | 'app' | 'oauth';
    token?: string;
    appId?: number;
    privateKey?: string;
    clientId?: string;
    clientSecret?: string;
  };
  owner: string;
  repo: string;
  autoSync: boolean;
  webhooks: {
    enabled: boolean;
    secret?: string;
    events: string[];
  };
}

export interface SyncOptions {
  branches?: string[];
  paths?: string[];
  includeIssues?: boolean;
  includePRs?: boolean;
  includeReleases?: boolean;
}

export class GitHubIntegration extends EventEmitter {
  private octokit: Octokit;
  private config: GitHubConfig;
  private webhookHandler: any;
  private syncInterval: NodeJS.Timeout | null = null;

  constructor(config: GitHubConfig) {
    super();
    this.config = config;
    this.octokit = this.createOctokit();
    
    if (config.webhooks.enabled) {
      this.setupWebhooks();
    }
    
    if (config.autoSync) {
      this.startAutoSync();
    }
  }

  private createOctokit(): Octokit {
    switch (this.config.auth.type) {
      case 'token':
        return new Octokit({
          auth: this.config.auth.token
        });
      
      case 'app':
        return new Octokit({
          authStrategy: createAppAuth,
          auth: {
            appId: this.config.auth.appId,
            privateKey: this.config.auth.privateKey
          }
        });
      
      case 'oauth':
        return new Octokit({
          auth: {
            clientId: this.config.auth.clientId,
            clientSecret: this.config.auth.clientSecret
          }
        });
      
      default:
        return new Octokit();
    }
  }

  private setupWebhooks(): void {
    this.webhookHandler = new webhooks({
      secret: this.config.webhooks.secret || ''
    });

    // Register webhook handlers
    this.webhookHandler.on('push', this.handlePush.bind(this));
    this.webhookHandler.on('pull_request', this.handlePullRequest.bind(this));
    this.webhookHandler.on('issues', this.handleIssue.bind(this));
    this.webhookHandler.on('release', this.handleRelease.bind(this));
    this.webhookHandler.on('workflow_run', this.handleWorkflowRun.bind(this));
  }

  private async handlePush(event: EmitterWebhookEvent<'push'>): Promise<void> {
    this.emit('push', {
      ref: event.payload.ref,
      commits: event.payload.commits,
      pusher: event.payload.pusher,
      repository: event.payload.repository.name
    });

    // Auto-sync on push
    if (this.config.autoSync) {
      await this.syncRepository();
    }
  }

  private async handlePullRequest(event: EmitterWebhookEvent<'pull_request'>): Promise<void> {
    this.emit('pull_request', {
      action: event.payload.action,
      number: event.payload.pull_request.number,
      title: event.payload.pull_request.title,
      state: event.payload.pull_request.state,
      user: event.payload.pull_request.user.login
    });
  }

  private async handleIssue(event: EmitterWebhookEvent<'issues'>): Promise<void> {
    this.emit('issue', {
      action: event.payload.action,
      number: event.payload.issue.number,
      title: event.payload.issue.title,
      state: event.payload.issue.state,
      user: event.payload.issue.user.login
    });
  }

  private async handleRelease(event: EmitterWebhookEvent<'release'>): Promise<void> {
    this.emit('release', {
      action: event.payload.action,
      tag: event.payload.release.tag_name,
      name: event.payload.release.name,
      prerelease: event.payload.release.prerelease
    });
  }

  private async handleWorkflowRun(event: EmitterWebhookEvent<'workflow_run'>): Promise<void> {
    this.emit('workflow_run', {
      action: event.payload.action,
      name: event.payload.workflow_run.name,
      status: event.payload.workflow_run.status,
      conclusion: event.payload.workflow_run.conclusion
    });
  }

  async syncRepository(options: SyncOptions = {}): Promise<void> {
    try {
      // Sync branches
      const branches = options.branches || ['main', 'develop'];
      for (const branch of branches) {
        await this.syncBranch(branch);
      }

      // Sync issues
      if (options.includeIssues) {
        await this.syncIssues();
      }

      // Sync pull requests
      if (options.includePRs) {
        await this.syncPullRequests();
      }

      // Sync releases
      if (options.includeReleases) {
        await this.syncReleases();
      }

      this.emit('sync:complete', { timestamp: Date.now() });
    } catch (error) {
      this.emit('sync:error', error);
      throw error;
    }
  }

  private async syncBranch(branch: string): Promise<void> {
    const { data: ref } = await this.octokit.git.getRef({
      owner: this.config.owner,
      repo: this.config.repo,
      ref: `heads/${branch}`
    });

    const { data: commit } = await this.octokit.git.getCommit({
      owner: this.config.owner,
      repo: this.config.repo,
      commit_sha: ref.object.sha
    });

    this.emit('branch:synced', {
      branch,
      sha: ref.object.sha,
      message: commit.message,
      author: commit.author
    });
  }

  private async syncIssues(): Promise<void> {
    const { data: issues } = await this.octokit.issues.listForRepo({
      owner: this.config.owner,
      repo: this.config.repo,
      state: 'all',
      per_page: 100
    });

    this.emit('issues:synced', {
      count: issues.length,
      issues: issues.map(issue => ({
        number: issue.number,
        title: issue.title,
        state: issue.state,
        labels: issue.labels
      }))
    });
  }

  private async syncPullRequests(): Promise<void> {
    const { data: prs } = await this.octokit.pulls.list({
      owner: this.config.owner,
      repo: this.config.repo,
      state: 'all',
      per_page: 100
    });

    this.emit('prs:synced', {
      count: prs.length,
      pullRequests: prs.map(pr => ({
        number: pr.number,
        title: pr.title,
        state: pr.state,
        mergeable: pr.mergeable
      }))
    });
  }

  private async syncReleases(): Promise<void> {
    const { data: releases } = await this.octokit.repos.listReleases({
      owner: this.config.owner,
      repo: this.config.repo,
      per_page: 100
    });

    this.emit('releases:synced', {
      count: releases.length,
      releases: releases.map(release => ({
        tag: release.tag_name,
        name: release.name,
        prerelease: release.prerelease,
        published_at: release.published_at
      }))
    });
  }

  async getFileContent(path: string, branch: string = 'main'): Promise<string> {
    const { data } = await this.octokit.repos.getContent({
      owner: this.config.owner,
      repo: this.config.repo,
      path,
      ref: branch
    });

    if ('content' in data) {
      return Buffer.from(data.content, 'base64').toString('utf-8');
    }

    throw new Error('File not found or is a directory');
  }

  async updateFile(
    path: string,
    content: string,
    message: string,
    branch: string = 'main'
  ): Promise<void> {
    // Get current file to get its SHA
    let sha: string | undefined;
    try {
      const { data: currentFile } = await this.octokit.repos.getContent({
        owner: this.config.owner,
        repo: this.config.repo,
        path,
        ref: branch
      });

      if ('sha' in currentFile) {
        sha = currentFile.sha;
      }
    } catch (error) {
      // File doesn't exist, will create it
    }

    await this.octokit.repos.createOrUpdateFileContents({
      owner: this.config.owner,
      repo: this.config.repo,
      path,
      message,
      content: Buffer.from(content).toString('base64'),
      branch,
      sha
    });

    this.emit('file:updated', { path, branch, message });
  }

  async createIssue(title: string, body: string, labels?: string[]): Promise<number> {
    const { data: issue } = await this.octokit.issues.create({
      owner: this.config.owner,
      repo: this.config.repo,
      title,
      body,
      labels
    });

    this.emit('issue:created', {
      number: issue.number,
      title: issue.title,
      url: issue.html_url
    });

    return issue.number;
  }

  async createPullRequest(
    title: string,
    head: string,
    base: string,
    body?: string
  ): Promise<number> {
    const { data: pr } = await this.octokit.pulls.create({
      owner: this.config.owner,
      repo: this.config.repo,
      title,
      head,
      base,
      body
    });

    this.emit('pr:created', {
      number: pr.number,
      title: pr.title,
      url: pr.html_url
    });

    return pr.number;
  }

  async runWorkflow(workflowId: string | number, ref: string = 'main'): Promise<void> {
    await this.octokit.actions.createWorkflowDispatch({
      owner: this.config.owner,
      repo: this.config.repo,
      workflow_id: workflowId,
      ref
    });

    this.emit('workflow:triggered', { workflowId, ref });
  }

  async getWorkflowRuns(workflowId?: string | number): Promise<any[]> {
    const params: any = {
      owner: this.config.owner,
      repo: this.config.repo,
      per_page: 100
    };

    if (workflowId) {
      params.workflow_id = workflowId;
    }

    const { data } = await this.octokit.actions.listWorkflowRuns(params);
    return data.workflow_runs;
  }

  private startAutoSync(): void {
    this.syncInterval = setInterval(async () => {
      await this.syncRepository();
    }, 300000); // Sync every 5 minutes
  }

  async processWebhook(headers: any, body: string): Promise<void> {
    if (!this.webhookHandler) {
      throw new Error('Webhooks not enabled');
    }

    await this.webhookHandler.verifyAndReceive({
      id: headers['x-github-delivery'],
      name: headers['x-github-event'],
      payload: body,
      signature: headers['x-hub-signature-256']
    });
  }

  dispose(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
    this.removeAllListeners();
  }
}

export default GitHubIntegration;