import { test as base, Page } from '@playwright/test';
import { testWorks, testReleases } from './test-data';

/**
 * カスタムフィクスチャ定義
 * 共通テストユーティリティを提供
 */

type CustomFixtures = {
  authenticatedPage: Page;
  testDataSetup: void;
};

export const test = base.extend<CustomFixtures>({
  /**
   * 認証済みページフィクスチャ
   */
  authenticatedPage: async ({ page }, use) => {
    // 認証処理（セッション確立）
    await page.goto('/');
    // 必要に応じてログイン処理を追加
    await use(page);
  },

  /**
   * テストデータセットアップフィクスチャ
   */
  testDataSetup: async ({ page }, use) => {
    // テストデータの準備
    await page.request.post('/api/test/setup', {
      data: {
        works: [testWorks.anime, testWorks.manga],
        releases: [testReleases.episode, testReleases.volume],
      },
    });

    await use();

    // クリーンアップ
    await page.request.post('/api/test/cleanup');
  },
});

export { expect } from '@playwright/test';

/**
 * ページオブジェクトモデル用ヘルパー
 */
export class PageHelper {
  constructor(private page: Page) {}

  /**
   * 要素が表示されるまで待機
   */
  async waitForVisible(selector: string, timeout = 5000) {
    await this.page.waitForSelector(selector, { state: 'visible', timeout });
  }

  /**
   * テキスト内容を確認
   */
  async expectText(selector: string, text: string) {
    const element = await this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    const content = await element.textContent();
    return content?.includes(text);
  }

  /**
   * フォーム送信ヘルパー
   */
  async submitForm(formSelector: string, data: Record<string, string>) {
    for (const [name, value] of Object.entries(data)) {
      await this.page.fill(`${formSelector} [name="${name}"]`, value);
    }
    await this.page.click(`${formSelector} button[type="submit"]`);
  }

  /**
   * API応答待機
   */
  async waitForApiResponse(urlPattern: string | RegExp, timeout = 10000) {
    return await this.page.waitForResponse(
      response => {
        const url = response.url();
        if (typeof urlPattern === 'string') {
          return url.includes(urlPattern);
        }
        return urlPattern.test(url);
      },
      { timeout }
    );
  }

  /**
   * スクリーンショット撮影
   */
  async captureScreenshot(name: string) {
    await this.page.screenshot({
      path: `screenshots/${name}-${Date.now()}.png`,
      fullPage: true,
    });
  }
}
