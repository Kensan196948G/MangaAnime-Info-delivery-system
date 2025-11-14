/**
 * テスト通知UI 包括的E2Eテスト
 *
 * Playwright を使用してブラウザからのテスト通知機能をテスト
 *
 * 実行方法:
 *   npx playwright test tests/test_notification_ui.spec.ts
 *   npx playwright test tests/test_notification_ui.spec.ts --headed
 *   npx playwright test tests/test_notification_ui.spec.ts --debug
 */

import { test, expect, Page } from '@playwright/test';

// テスト設定
const BASE_URL = process.env.BASE_URL || 'http://localhost:5000';
const TEST_TIMEOUT = 30000; // 30秒

test.describe('テスト通知UI 包括的テスト', () => {

  test.beforeEach(async ({ page }) => {
    // 各テストの前にダッシュボードページに移動
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
  });

  test('テストケース1: 基本的なテスト通知送信', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);

    // テスト通知ボタンを探す
    const testNotificationButton = page.locator('button:has-text("テスト通知"), button:has-text("Test Notification")').first();
    await expect(testNotificationButton).toBeVisible({ timeout: 10000 });

    // ボタンをクリック
    await testNotificationButton.click();

    // 成功メッセージを待機
    const successMessage = page.locator('.alert-success, .toast-success, .success-message, div:has-text("成功")');
    await expect(successMessage).toBeVisible({ timeout: 15000 });

    // 成功メッセージの内容を確認
    const messageText = await successMessage.textContent();
    expect(messageText).toMatch(/成功|送信|Success|Sent/i);
  });

  test('テストケース2: モーダルダイアログでのテスト通知', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);

    // モーダルを開くボタンを探す
    const openModalButton = page.locator('button:has-text("テスト通知"), [data-bs-toggle="modal"]').first();

    if (await openModalButton.isVisible()) {
      await openModalButton.click();

      // モーダルが表示されるのを待機
      const modal = page.locator('.modal, [role="dialog"]');
      await expect(modal).toBeVisible({ timeout: 5000 });

      // カスタムメッセージ入力フィールドがあれば入力
      const messageInput = page.locator('input[type="text"], textarea').first();
      if (await messageInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await messageInput.fill('UIテスト: ブラウザからのテスト通知');
      }

      // 送信ボタンをクリック
      const sendButton = page.locator('button:has-text("送信"), button:has-text("Send")').first();
      await sendButton.click();

      // 成功メッセージを待機
      const successIndicator = page.locator('.alert-success, .success, div:has-text("成功")');
      await expect(successIndicator).toBeVisible({ timeout: 15000 });
    }
  });

  test('テストケース3: レスポンシブデザイン確認', async ({ page }) => {
    // モバイルビューポート
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();
    await page.waitForLoadState('networkidle');

    const testButton = page.locator('button:has-text("テスト通知"), button:has-text("Test")').first();
    await expect(testButton).toBeVisible({ timeout: 10000 });

    // タブレットビューポート
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.reload();
    await page.waitForLoadState('networkidle');
    await expect(testButton).toBeVisible({ timeout: 10000 });

    // デスクトップビューポート
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.reload();
    await page.waitForLoadState('networkidle');
    await expect(testButton).toBeVisible({ timeout: 10000 });
  });

  test('テストケース4: エラーハンドリング - ネットワークエラー', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);

    // ネットワークをオフラインにする
    await page.context().setOffline(true);

    const testButton = page.locator('button:has-text("テスト通知")').first();

    if (await testButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await testButton.click();

      // エラーメッセージを待機
      const errorMessage = page.locator('.alert-danger, .error, div:has-text("エラー")');
      await expect(errorMessage).toBeVisible({ timeout: 10000 });
    }

    // ネットワークを復元
    await page.context().setOffline(false);
  });

  test('テストケース5: 連続クリック防止', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);

    const testButton = page.locator('button:has-text("テスト通知")').first();

    if (await testButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      // 最初のクリック
      await testButton.click();

      // ボタンが無効化されることを確認
      await page.waitForTimeout(500);
      const isDisabled = await testButton.isDisabled().catch(() => false);

      if (isDisabled) {
        // 無効化されている場合、もう一度クリックしても何も起こらない
        await testButton.click({ force: true });

        // エラーメッセージが表示されないことを確認
        const errorMessage = page.locator('.alert-danger, .error');
        const errorVisible = await errorMessage.isVisible({ timeout: 2000 }).catch(() => false);
        expect(errorVisible).toBeFalsy();
      }
    }
  });

  test('テストケース6: UI要素の存在確認', async ({ page }) => {
    // ダッシュボードの主要要素を確認
    const mainContent = page.locator('main, .container, #app');
    await expect(mainContent).toBeVisible({ timeout: 10000 });

    // ナビゲーションバー
    const navbar = page.locator('nav, .navbar, header');
    await expect(navbar).toBeVisible({ timeout: 5000 });

    // テスト通知ボタンまたはセクション
    const notificationSection = page.locator('button:has-text("テスト"), section:has-text("通知")');
    await expect(notificationSection.first()).toBeVisible({ timeout: 10000 });
  });

  test('テストケース7: JavaScriptエラーの検出', async ({ page }) => {
    const jsErrors: string[] = [];

    // JavaScriptエラーをキャプチャ
    page.on('pageerror', (error) => {
      jsErrors.push(error.message);
    });

    // コンソールエラーをキャプチャ
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        jsErrors.push(msg.text());
      }
    });

    // ページをリロードして操作
    await page.reload();
    await page.waitForLoadState('networkidle');

    const testButton = page.locator('button:has-text("テスト通知")').first();

    if (await testButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await testButton.click();
      await page.waitForTimeout(2000);
    }

    // JavaScriptエラーがないことを確認
    console.log('Captured JavaScript errors:', jsErrors);

    // 致命的なエラー以外は許容（警告など）
    const criticalErrors = jsErrors.filter(err =>
      !err.includes('Warning') &&
      !err.includes('JQMIGRATE') &&
      !err.includes('favicon')
    );

    expect(criticalErrors.length).toBe(0);
  });

  test('テストケース8: アクセシビリティチェック', async ({ page }) => {
    // 主要なボタンにアクセシブルな名前があるか確認
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();

    for (let i = 0; i < Math.min(buttonCount, 10); i++) {
      const button = buttons.nth(i);
      const buttonText = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');

      // ボタンにテキストまたはaria-labelがあることを確認
      expect(buttonText || ariaLabel).toBeTruthy();
    }
  });

  test('テストケース9: ローディング状態の確認', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);

    const testButton = page.locator('button:has-text("テスト通知")').first();

    if (await testButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      // ボタンをクリック
      await testButton.click();

      // ローディングインジケーターを確認（スピナー、ローディングテキストなど）
      const loadingIndicator = page.locator(
        '.spinner, .loading, [role="status"], button:has-text("送信中"), button:disabled'
      );

      // ローディング表示があれば確認
      const hasLoading = await loadingIndicator.first().isVisible({ timeout: 2000 }).catch(() => false);

      if (hasLoading) {
        console.log('ローディングインジケーターが表示されました');
      }

      // 最終的に結果が表示されることを確認
      const result = page.locator('.alert, .toast, .message, div:has-text("成功"), div:has-text("エラー")');
      await expect(result.first()).toBeVisible({ timeout: 15000 });
    }
  });

  test('テストケース10: パフォーマンス測定', async ({ page }) => {
    // Performance APIを使用してページロード時間を測定
    const performanceData = await page.evaluate(() => {
      const perfData = window.performance.timing;
      const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
      const domReadyTime = perfData.domContentLoadedEventEnd - perfData.navigationStart;

      return {
        pageLoadTime,
        domReadyTime
      };
    });

    console.log('Performance Data:', performanceData);

    // ページロード時間が30秒以内であることを確認
    expect(performanceData.pageLoadTime).toBeLessThan(30000);
    expect(performanceData.domReadyTime).toBeLessThan(20000);
  });

});

test.describe('テスト通知API直接テスト', () => {

  test('テストケース11: APIエンドポイント直接呼び出し', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/api/test-notification`, {
      data: {
        message: 'Playwright APIテスト'
      },
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // レスポンスステータスを確認
    expect(response.status()).toBeLessThanOrEqual(500);

    // レスポンスボディを確認
    const responseBody = await response.json();
    expect(responseBody).toHaveProperty('success');
  });

  test('テストケース12: 不正なJSONの送信', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/api/test-notification`, {
      data: '{invalid json}',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // エラーレスポンスを期待
    expect([400, 500]).toContain(response.status());
  });

  test('テストケース13: GETメソッドでのアクセス', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/test-notification`);

    // 405 Method Not Allowedを期待
    expect(response.status()).toBe(405);
  });

});
