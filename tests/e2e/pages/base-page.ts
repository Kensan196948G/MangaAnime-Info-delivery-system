import { Page, Locator, expect } from '@playwright/test';
import { TestHelpers } from '../utils/test-helpers';

/**
 * ベースページクラス
 * 
 * 全ページ共通の機能を提供します
 */
export abstract class BasePage {
  protected helpers: TestHelpers;
  
  // 共通要素のセレクタ
  protected readonly navigationMenu = 'nav, .navbar';
  protected readonly pageTitle = 'h1, .page-title';
  protected readonly loadingSpinner = '.loading, .spinner';
  protected readonly errorMessage = '.alert-danger, .error';
  protected readonly successMessage = '.alert-success, .success';

  constructor(protected page: Page) {
    this.helpers = new TestHelpers(page);
  }

  /**
   * ページの基本的な読み込み確認
   */
  async waitForPageLoad(): Promise<void> {
    await this.helpers.waitForPageLoad();
    // ナビゲーションメニューが表示されることを確認
    await this.helpers.waitForElement(this.navigationMenu);
  }

  /**
   * ページタイトルの取得
   */
  async getPageTitle(): Promise<string> {
    const titleElement = this.page.locator(this.pageTitle);
    return await titleElement.textContent() || '';
  }

  /**
   * ナビゲーションメニューのリンクをクリック
   */
  async clickNavLink(linkText: string): Promise<void> {
    const navLink = this.page.locator(`${this.navigationMenu} a`).filter({
      hasText: linkText
    });
    await navLink.click();
    await this.waitForPageLoad();
  }

  /**
   * エラーメッセージの確認
   */
  async verifyErrorMessage(expectedMessage: string): Promise<void> {
    await this.helpers.verifyNotification(expectedMessage, 'error');
  }

  /**
   * 成功メッセージの確認
   */
  async verifySuccessMessage(expectedMessage: string): Promise<void> {
    await this.helpers.verifyNotification(expectedMessage, 'success');
  }

  /**
   * ローディング状態の待機
   */
  async waitForLoadingToFinish(): Promise<void> {
    await this.helpers.waitForLoadingToFinish();
  }

  /**
   * フッター情報の確認
   */
  async verifyFooter(): Promise<void> {
    const footer = this.page.locator('footer');
    await expect(footer).toBeVisible();
  }

  /**
   * レスポンシブデザインの確認
   */
  async verifyResponsiveLayout(viewport: { width: number; height: number }): Promise<void> {
    await this.page.setViewportSize(viewport);
    await this.waitForPageLoad();
    
    // モバイル表示時のハンバーガーメニュー確認
    if (viewport.width < 768) {
      const mobileMenuToggle = this.page.locator('.navbar-toggler, .mobile-menu-toggle');
      await expect(mobileMenuToggle).toBeVisible();
    }
  }

  /**
   * アクセシビリティの基本チェック
   */
  async verifyAccessibility(): Promise<void> {
    // フォーカス可能な要素にtabindex属性があることを確認
    const focusableElements = this.page.locator('input, button, select, textarea, a[href]');
    const count = await focusableElements.count();
    
    for (let i = 0; i < count; i++) {
      const element = focusableElements.nth(i);
      // 要素にラベルまたはaria-label属性があることを確認
      const hasLabel = await element.getAttribute('aria-label') !== null ||
                      await element.getAttribute('aria-labelledby') !== null ||
                      await this.page.locator(`label[for="${await element.getAttribute('id')}"]`).count() > 0;
      
      if (!hasLabel && await element.getAttribute('type') !== 'hidden') {
        console.warn(`アクセシビリティ警告: 要素にラベルがありません - ${await element.innerHTML()}`);
      }
    }
  }

  /**
   * パフォーマンスメトリクスの取得
   */
  async getPerformanceMetrics(): Promise<any> {
    return await this.page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.navigationStart,
        loadComplete: navigation.loadEventEnd - navigation.navigationStart,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
      };
    });
  }

  /**
   * コンソールエラーの監視
   */
  enableConsoleErrorTracking(): void {
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error('ブラウザコンソールエラー:', msg.text());
      }
    });

    this.page.on('pageerror', error => {
      console.error('ページエラー:', error.message);
    });
  }

  /**
   * ネットワークリクエストの監視
   */
  async monitorNetworkRequests(): Promise<void> {
    this.page.on('request', request => {
      console.log('リクエスト:', request.method(), request.url());
    });

    this.page.on('response', response => {
      if (response.status() >= 400) {
        console.error('HTTPエラーレスポンス:', response.status(), response.url());
      }
    });
  }
}