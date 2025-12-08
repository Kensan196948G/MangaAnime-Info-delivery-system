import { test, expect } from '../fixtures/custom-fixtures';
import { PageHelper } from '../fixtures/custom-fixtures';

/**
 * ホームページE2Eテスト
 */
test.describe('ホームページ', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('ページタイトルが正しく表示される', async ({ page }) => {
    await expect(page).toHaveTitle(/アニメ・マンガ最新情報配信システム/);
  });

  test('ナビゲーションバーが表示される', async ({ page }) => {
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();

    // ナビゲーションリンクの確認
    await expect(page.locator('nav a:has-text("ホーム")')).toBeVisible();
    await expect(page.locator('nav a:has-text("作品一覧")')).toBeVisible();
    await expect(page.locator('nav a:has-text("リリース情報")')).toBeVisible();
  });

  test('メインコンテンツが表示される', async ({ page }) => {
    const main = page.locator('main');
    await expect(main).toBeVisible();
  });

  test('最新リリース情報が表示される', async ({ page, testDataSetup }) => {
    const helper = new PageHelper(page);

    // API応答待機
    await helper.waitForApiResponse('/api/releases/latest');

    // リリース情報カードの確認
    const releaseCards = page.locator('.release-card');
    await expect(releaseCards).toHaveCountGreaterThan(0);

    // 最初のカードの内容確認
    const firstCard = releaseCards.first();
    await expect(firstCard.locator('.release-title')).toBeVisible();
    await expect(firstCard.locator('.release-date')).toBeVisible();
    await expect(firstCard.locator('.release-platform')).toBeVisible();
  });

  test('検索フォームが機能する', async ({ page }) => {
    const helper = new PageHelper(page);

    // 検索フォームに入力
    await page.fill('input[name="search"]', 'テストアニメ');
    await page.click('button[type="submit"]');

    // 検索結果待機
    await helper.waitForApiResponse('/api/search');

    // 検索結果が表示される
    const results = page.locator('.search-results');
    await expect(results).toBeVisible();
  });

  test('フィルター機能が動作する', async ({ page }) => {
    // タイプフィルター
    await page.selectOption('select[name="type"]', 'anime');
    await page.waitForTimeout(500);

    // アニメのみ表示されることを確認
    const animeCards = page.locator('.release-card[data-type="anime"]');
    await expect(animeCards).toHaveCountGreaterThan(0);

    const mangaCards = page.locator('.release-card[data-type="manga"]');
    await expect(mangaCards).toHaveCount(0);
  });

  test('レスポンシブデザインが機能する', async ({ page }) => {
    // デスクトップビュー
    await page.setViewportSize({ width: 1280, height: 720 });
    await expect(page.locator('.desktop-nav')).toBeVisible();

    // モバイルビュー
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('.mobile-nav')).toBeVisible();

    // ハンバーガーメニュー
    await page.click('.hamburger-menu');
    await expect(page.locator('.mobile-menu')).toBeVisible();
  });

  test('ページネーションが機能する', async ({ page, testDataSetup }) => {
    const helper = new PageHelper(page);

    // 2ページ目に移動
    await page.click('a[aria-label="次のページ"]');
    await helper.waitForApiResponse('/api/releases');

    // URLパラメータ確認
    expect(page.url()).toContain('page=2');

    // コンテンツが更新される
    await expect(page.locator('.release-card')).toHaveCountGreaterThan(0);
  });

  test('エラー処理が適切に行われる', async ({ page }) => {
    // API エラーをシミュレート
    await page.route('**/api/releases/latest', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal Server Error' }),
      });
    });

    await page.reload();

    // エラーメッセージが表示される
    const errorMessage = page.locator('.error-message');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText('エラーが発生しました');
  });

  test('アクセシビリティ対応', async ({ page }) => {
    // キーボードナビゲーション
    await page.keyboard.press('Tab');
    const focusedElement = await page.locator(':focus');
    await expect(focusedElement).toBeVisible();

    // ARIA属性の確認
    await expect(page.locator('[role="navigation"]')).toBeVisible();
    await expect(page.locator('[role="main"]')).toBeVisible();

    // alt属性の確認
    const images = await page.locator('img').all();
    for (const img of images) {
      await expect(img).toHaveAttribute('alt');
    }
  });

  test('パフォーマンステスト', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    // 3秒以内にロード完了
    expect(loadTime).toBeLessThan(3000);

    // First Contentful Paint (FCP) チェック
    const performanceMetrics = await page.evaluate(() => {
      const perfData = performance.getEntriesByType('paint');
      const fcp = perfData.find(entry => entry.name === 'first-contentful-paint');
      return fcp ? fcp.startTime : null;
    });

    if (performanceMetrics) {
      expect(performanceMetrics).toBeLessThan(1500);
    }
  });
});
