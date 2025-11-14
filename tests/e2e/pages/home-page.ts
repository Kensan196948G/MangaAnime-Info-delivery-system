import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base-page';

/**
 * ホームページのページオブジェクト
 * 
 * ダッシュボード機能のテストを提供します
 */
export class HomePage extends BasePage {
  
  // ページ固有の要素セレクタ
  private readonly statsCards = '.stats-card, .card';
  private readonly recentReleasesSection = '#recent-releases, .recent-releases';
  private readonly systemStatusSection = '#system-status, .system-status';
  private readonly quickActionsSection = '.quick-actions';
  
  // 統計情報の要素
  private readonly totalWorksCount = '[data-stat="total-works"], .total-works-count';
  private readonly todayReleasesCount = '[data-stat="today-releases"], .today-releases-count';
  private readonly upcomingReleasesCount = '[data-stat="upcoming-releases"], .upcoming-releases-count';
  
  // 最近のリリース要素
  private readonly releaseItems = '.release-item, .recent-release';
  private readonly releaseTitle = '.release-title, .title';
  private readonly releaseDate = '.release-date, .date';
  private readonly releasePlatform = '.release-platform, .platform';

  constructor(page: Page) {
    super(page);
  }

  /**
   * ホームページへの遷移
   */
  async navigate(): Promise<void> {
    await this.page.goto('/');
    await this.waitForPageLoad();
  }

  /**
   * ダッシュボードの統計カードが表示されることを確認
   */
  async verifyStatsCards(): Promise<void> {
    const statsCards = this.page.locator(this.statsCards);
    await expect(statsCards).toHaveCount(4, { timeout: 10000 });
    
    // 各統計カードのタイトルと値を確認
    const expectedStats = [
      '登録作品数',
      '本日のリリース',
      '今後のリリース',
      'システム状態'
    ];

    for (let i = 0; i < expectedStats.length; i++) {
      const card = statsCards.nth(i);
      await expect(card).toContainText(expectedStats[i]);
      
      // 数値または状態が表示されていることを確認
      const valueElement = card.locator('.stat-value, .card-value, .value');
      await expect(valueElement).toBeVisible();
    }
  }

  /**
   * 最近のリリース一覧を確認
   */
  async verifyRecentReleases(): Promise<void> {
    const recentSection = this.page.locator(this.recentReleasesSection);
    await expect(recentSection).toBeVisible();

    const releaseItems = this.page.locator(this.releaseItems);
    const itemCount = await releaseItems.count();
    
    if (itemCount > 0) {
      // 最初の数項目の詳細を確認
      const itemsToCheck = Math.min(itemCount, 5);
      
      for (let i = 0; i < itemsToCheck; i++) {
        const item = releaseItems.nth(i);
        
        // タイトルが存在することを確認
        const title = item.locator(this.releaseTitle);
        await expect(title).toBeVisible();
        await expect(title).not.toBeEmpty();
        
        // 日付が存在することを確認
        const date = item.locator(this.releaseDate);
        await expect(date).toBeVisible();
        
        // プラットフォーム情報が存在することを確認
        const platform = item.locator(this.releasePlatform);
        await expect(platform).toBeVisible();
      }
    } else {
      // データがない場合の空状態表示を確認
      const emptyState = recentSection.locator('.empty-state, .no-data');
      await expect(emptyState).toBeVisible();
    }
  }

  /**
   * システム状態の確認
   */
  async verifySystemStatus(): Promise<void> {
    const statusSection = this.page.locator(this.systemStatusSection);
    await expect(statusSection).toBeVisible();

    // システム状態インジケーターを確認
    const statusIndicators = statusSection.locator('.status-indicator, .indicator');
    await expect(statusIndicators.first()).toBeVisible();

    // 各システムコンポーネントの状態を確認
    const components = [
      'データベース',
      'メール送信',
      'カレンダー連携',
      'API収集'
    ];

    for (const component of components) {
      const componentStatus = statusSection.locator(`.component-status:has-text("${component}")`);
      if (await componentStatus.count() > 0) {
        await expect(componentStatus).toBeVisible();
        
        // 状態アイコン（成功/警告/エラー）を確認
        const statusIcon = componentStatus.locator('.status-icon, .icon');
        await expect(statusIcon).toBeVisible();
      }
    }
  }

  /**
   * クイックアクションボタンの確認
   */
  async verifyQuickActions(): Promise<void> {
    const quickActionsSection = this.page.locator(this.quickActionsSection);
    
    if (await quickActionsSection.count() > 0) {
      await expect(quickActionsSection).toBeVisible();

      const expectedActions = [
        '手動収集実行',
        '設定変更',
        'ログ確認',
        'テスト通知'
      ];

      for (const action of expectedActions) {
        const actionButton = quickActionsSection.locator(`button:has-text("${action}"), a:has-text("${action}")`);
        if (await actionButton.count() > 0) {
          await expect(actionButton).toBeVisible();
          await expect(actionButton).toBeEnabled();
        }
      }
    }
  }

  /**
   * 統計数値の取得
   */
  async getStatistics(): Promise<{
    totalWorks: number;
    todayReleases: number;
    upcomingReleases: number;
  }> {
    await this.waitForPageLoad();

    const totalWorks = await this.getStatValue(this.totalWorksCount);
    const todayReleases = await this.getStatValue(this.todayReleasesCount);
    const upcomingReleases = await this.getStatValue(this.upcomingReleasesCount);

    return {
      totalWorks,
      todayReleases,
      upcomingReleases
    };
  }

  /**
   * 統計値を数値として取得するヘルパー
   */
  private async getStatValue(selector: string): Promise<number> {
    const element = this.page.locator(selector);
    if (await element.count() === 0) return 0;
    
    const text = await element.textContent();
    const match = text?.match(/\d+/);
    return match ? parseInt(match[0], 10) : 0;
  }

  /**
   * 最近のリリース一覧からアイテムを選択
   */
  async clickRecentRelease(index: number): Promise<void> {
    const releaseItems = this.page.locator(this.releaseItems);
    await expect(releaseItems).toHaveCount({ gte: index + 1 });
    
    const targetItem = releaseItems.nth(index);
    await targetItem.click();
    await this.waitForPageLoad();
  }

  /**
   * クイックアクションの実行
   */
  async executeQuickAction(actionName: string): Promise<void> {
    const quickActionsSection = this.page.locator(this.quickActionsSection);
    const actionButton = quickActionsSection.locator(`button:has-text("${actionName}"), a:has-text("${actionName}")`);
    
    await expect(actionButton).toBeVisible();
    await actionButton.click();
    
    // アクションによっては確認ダイアログが表示される場合があるので処理
    this.helpers.handleModal('accept');
    
    await this.waitForLoadingToFinish();
  }

  /**
   * リアルタイム更新の確認
   */
  async verifyRealTimeUpdates(): Promise<void> {
    // 初期状態の統計を取得
    const initialStats = await this.getStatistics();
    
    // WebSocketまたはポーリングによるリアルタイム更新を待機
    await this.page.waitForTimeout(5000);
    
    // 統計の更新を確認（実際の更新がある場合）
    const updatedStats = await this.getStatistics();
    
    // 更新があった場合のログ出力
    if (initialStats.totalWorks !== updatedStats.totalWorks ||
        initialStats.todayReleases !== updatedStats.todayReleases ||
        initialStats.upcomingReleases !== updatedStats.upcomingReleases) {
      console.log('リアルタイム統計更新を検出:', { initialStats, updatedStats });
    }
  }

  /**
   * ダッシュボードの完全な動作確認
   */
  async verifyFullDashboard(): Promise<void> {
    await this.verifyStatsCards();
    await this.verifyRecentReleases();
    await this.verifySystemStatus();
    await this.verifyQuickActions();
  }
}