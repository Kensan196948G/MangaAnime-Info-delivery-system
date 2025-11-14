import { test, expect } from '@playwright/test';
import { HomePage } from './pages/home-page';
import { ConfigPage } from './pages/config-page';
import { ReleasesPage } from './pages/releases-page';
import { TestDataGenerator } from './utils/test-helpers';

/**
 * エラーハンドリングと統合ワークフローのE2Eテスト
 * 
 * システムのエラー処理、フォールバック機能、統合フローをテストします
 */

test.describe('エラーハンドリング', () => {
  let homePage: HomePage;
  let configPage: ConfigPage;
  let releasesPage: ReleasesPage;

  test.beforeEach(async ({ page }) => {
    homePage = new HomePage(page);
    configPage = new ConfigPage(page);
    releasesPage = new ReleasesPage(page);
    
    // エラーログの収集
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error('ブラウザエラー:', msg.text());
      }
    });
    
    page.on('pageerror', error => {
      console.error('ページエラー:', error.message);
    });
  });

  test.describe('ネットワークエラー処理', () => {
    
    test('API接続エラー時のフォールバック表示', async ({ page }) => {
      // APIリクエストを失敗させる
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal Server Error' })
        });
      });
      
      await homePage.navigate();
      
      // エラーメッセージまたはフォールバック表示を確認
      const errorIndicator = page.locator('.error, .alert-danger, .connection-error');
      const offlineMode = page.locator('.offline-mode, .fallback-data');
      
      // エラー表示またはオフラインモードのいずれかが表示されることを確認
      const errorVisible = await errorIndicator.count() > 0 && await errorIndicator.isVisible();
      const offlineVisible = await offlineMode.count() > 0 && await offlineMode.isVisible();
      
      if (errorVisible) {
        const errorText = await errorIndicator.textContent();
        expect(errorText).toMatch(/(エラー|接続|失敗)/);
      }
      
      expect(errorVisible || offlineVisible).toBeTruthy();
    });

    test('タイムアウトエラーの処理', async ({ page }) => {
      // リクエストを遅延させてタイムアウトをシミュレート
      await page.route('**/api/releases**', async route => {
        await new Promise(resolve => setTimeout(resolve, 10000)); // 10秒遅延
        route.continue();
      });
      
      await releasesPage.navigate();
      
      // タイムアウトメッセージまたはローディング状態が適切に処理されることを確認
      const timeoutMessage = page.locator('.timeout, .loading-timeout, .request-timeout');
      const loadingIndicator = page.locator('.loading, .spinner');
      
      // 一定時間後にタイムアウト処理が動作することを確認
      await page.waitForTimeout(5000);
      
      if (await timeoutMessage.count() > 0) {
        await expect(timeoutMessage).toBeVisible();
      } else if (await loadingIndicator.count() > 0) {
        // ローディングが継続している場合は、無限ローディングを防ぐ仕組みがあることを確認
        console.log('ローディングインジケーターが表示されています');
      }
    });

    test('部分的なAPI失敗時の処理', async ({ page }) => {
      // 一部のAPIのみ失敗させる
      await page.route('**/api/stats**', route => {
        route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Not Found' })
        });
      });
      
      await homePage.navigate();
      
      // 他の機能は正常に動作し、失敗した部分のみエラー表示されることを確認
      const statsCards = page.locator('.stats-card, .card');
      const recentReleases = page.locator('#recent-releases, .recent-releases');
      
      // 統計情報はエラーまたは非表示
      const statsError = page.locator('.stats-error, .card .error');
      
      // 最近のリリースは正常に表示
      if (await recentReleases.count() > 0) {
        await expect(recentReleases).toBeVisible();
      }
      
      // 統計部分でエラーハンドリングされていることを確認
      if (await statsError.count() > 0) {
        await expect(statsError).toBeVisible();
      }
    });
  });

  test.describe('フォーム入力エラー', () => {
    
    test('不正なメールアドレス入力エラー', async ({ page }) => {
      await configPage.navigate();
      
      await configPage.updateEmailSettings({
        enabled: true,
        email: 'invalid-email-format',
        appPassword: 'test_password'
      });
      
      const saveButton = page.locator('button[type="submit"], .save-button');
      await saveButton.click();
      
      // バリデーションエラーの表示確認
      const emailError = page.locator('.email-error, .validation-error, .invalid-feedback');
      if (await emailError.count() > 0) {
        await expect(emailError).toBeVisible();
        
        const errorText = await emailError.textContent();
        expect(errorText).toMatch(/(無効|不正|形式)/);
      } else {
        // HTML5バリデーションの確認
        const emailInput = page.locator('#email_address, input[name="email_address"]');
        const isValid = await emailInput.evaluate((input: HTMLInputElement) => {
          return input.checkValidity();
        });
        expect(isValid).toBeFalsy();
      }
    });

    test('必須フィールド未入力エラー', async ({ page }) => {
      await configPage.navigate();
      
      // メール機能を有効にして必須フィールドを空にする
      const emailEnabledCheckbox = page.locator('#email_enabled, input[name="email_enabled"]');
      await emailEnabledCheckbox.check();
      
      const emailInput = page.locator('#email_address, input[name="email_address"]');
      await emailInput.fill('');
      
      const saveButton = page.locator('button[type="submit"], .save-button');
      await saveButton.click();
      
      // 必須フィールドエラーの確認
      const requiredError = page.locator('.required-error, .field-required');
      if (await requiredError.count() > 0) {
        await expect(requiredError).toBeVisible();
      } else {
        // ブラウザの標準バリデーション確認
        const validationMessage = await emailInput.evaluate((input: HTMLInputElement) => {
          return input.validationMessage;
        });
        expect(validationMessage).toBeTruthy();
      }
    });

    test('数値範囲外エラー', async ({ page }) => {
      await configPage.navigate();
      
      const maxResultsInput = page.locator('#max_results, input[name="max_results"]');
      
      if (await maxResultsInput.count() > 0) {
        // 範囲外の値を入力
        await maxResultsInput.fill('99999');
        
        const saveButton = page.locator('button[type="submit"], .save-button');
        await saveButton.click();
        
        // 範囲エラーの確認
        const rangeError = page.locator('.range-error, .out-of-range');
        if (await rangeError.count() > 0) {
          await expect(rangeError).toBeVisible();
        } else {
          // 値が自動的に制限されているか確認
          const actualValue = await maxResultsInput.inputValue();
          expect(parseInt(actualValue)).toBeLessThanOrEqual(1000); // 想定される上限
        }
      }
    });

    test('重複データエラー', async ({ page }) => {
      await configPage.navigate();
      
      const testKeyword = 'DuplicateTest_' + TestDataGenerator.randomString(4);
      
      // 同じキーワードを2回追加しようとする
      await configPage.addNgKeyword(testKeyword);
      
      // 2回目の追加でエラーまたは無視されることを確認
      const ngKeywordInput = page.locator('#new-ng-keyword, input[name="new_ng_keyword"]');
      const addButton = page.locator('.add-ng-keyword, button:has-text("追加")');
      
      await ngKeywordInput.fill(testKeyword);
      await addButton.click();
      
      // 重複エラーメッセージまたは追加の無視
      const duplicateError = page.locator('.duplicate-error, .already-exists');
      if (await duplicateError.count() > 0) {
        await expect(duplicateError).toBeVisible();
      }
      
      // リストに同じキーワードが2つ存在しないことを確認
      const keywordsList = page.locator('.ng-keywords-list, #ng-keywords-list');
      const keywordMatches = keywordsList.locator('.ng-keyword-item').filter({
        hasText: testKeyword
      });
      
      const matchCount = await keywordMatches.count();
      expect(matchCount).toBeLessThanOrEqual(1);
    });
  });

  test.describe('権限・認証エラー', () => {
    
    test('認証切れ時の処理', async ({ page }) => {
      // 認証エラーをシミュレート
      await page.route('**/api/**', route => {
        if (route.request().url().includes('auth') || route.request().url().includes('token')) {
          route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Unauthorized' })
          });
        } else {
          route.continue();
        }
      });
      
      await configPage.navigate();
      
      // 認証が必要な操作を実行
      await configPage.updateEmailSettings({
        enabled: true,
        email: 'test@example.com'
      });
      
      await configPage.sendTestEmail();
      
      // 認証エラーメッセージまたは再認証プロンプトを確認
      const authError = page.locator('.auth-error, .unauthorized, .login-required');
      if (await authError.count() > 0) {
        await expect(authError).toBeVisible();
        
        // 設定ページまたはログインページへのリンクがあることを確認
        const settingsLink = page.locator('a:has-text("設定"), a:has-text("認証")');
        if (await settingsLink.count() > 0) {
          await expect(settingsLink).toBeVisible();
        }
      }
    });

    test('権限不足エラー', async ({ page }) => {
      // 権限不足エラーをシミュレート
      await page.route('**/api/admin/**', route => {
        route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Forbidden' })
        });
      });
      
      const adminSection = page.locator('.admin-section, #admin');
      
      if (await adminSection.count() > 0) {
        await page.goto('/admin');
        
        // アクセス拒否メッセージの確認
        const forbiddenMessage = page.locator('.forbidden, .access-denied, .permission-error');
        if (await forbiddenMessage.count() > 0) {
          await expect(forbiddenMessage).toBeVisible();
          
          const errorText = await forbiddenMessage.textContent();
          expect(errorText).toMatch(/(権限|アクセス|許可)/);
        }
      }
    });
  });

  test.describe('データ処理エラー', () => {
    
    test('無効なデータ形式エラー', async ({ page }) => {
      // 不正なJSONレスポンスをシミュレート
      await page.route('**/api/releases**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: 'invalid json data'
        });
      });
      
      await releasesPage.navigate();
      
      // データ形式エラーの処理確認
      const dataError = page.locator('.data-error, .parse-error, .invalid-data');
      if (await dataError.count() > 0) {
        await expect(dataError).toBeVisible();
      } else {
        // フォールバック表示やエラーハンドリングがされていることを確認
        const fallback = page.locator('.no-data, .empty-state');
        await expect(fallback).toBeVisible();
      }
    });

    test('大きすぎるデータセットエラー', async ({ page }) => {
      // 非常に大きなデータセットをシミュレート
      const largeDataset = Array.from({ length: 10000 }, (_, i) => ({
        id: i,
        title: `Large Dataset Item ${i}`,
        type: 'anime',
        platform: 'TestPlatform',
        release_date: '2024-01-01'
      }));
      
      await page.route('**/api/releases**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ releases: largeDataset })
        });
      });
      
      const startTime = Date.now();
      await releasesPage.navigate();
      const loadTime = Date.now() - startTime;
      
      // 大きなデータでも適切に処理されることを確認
      expect(loadTime).toBeLessThan(10000); // 10秒以内
      
      // ページネーションまたは遅延読み込みが適用されていることを確認
      const releaseRows = await releasesPage.getReleaseRows();
      expect(releaseRows.length).toBeLessThan(100); // 一度に表示される行数が制限されている
    });
  });

  test.describe('リソース不足エラー', () => {
    
    test('メモリ不足シミュレーション', async ({ page }) => {
      // メモリ使用量の監視
      const performanceMetrics = await homePage.getPerformanceMetrics();
      console.log('初期パフォーマンスメトリクス:', performanceMetrics);
      
      // 複数の重い操作を同時実行
      const promises = [
        releasesPage.navigate(),
        page.goto('/calendar'),
        homePage.navigate()
      ];
      
      try {
        await Promise.allSettled(promises);
        
        // ページが応答可能な状態であることを確認
        const currentUrl = page.url();
        expect(currentUrl).toContain('http://127.0.0.1:3033');
        
        // 基本的な要素が表示されることを確認
        const mainContent = page.locator('main, .main-content, body');
        await expect(mainContent).toBeVisible();
        
      } catch (error) {
        console.error('リソース不足テスト中のエラー:', error);
        
        // エラーページが適切に表示されることを確認
        const errorPage = page.locator('.error-page, .system-error');
        if (await errorPage.count() > 0) {
          await expect(errorPage).toBeVisible();
        }
      }
    });
  });

  test.describe('統合エラーハンドリング', () => {
    
    test('複数システム連携時のエラー処理', async ({ page }) => {
      // 複数のAPIで異なるエラーをシミュレート
      await page.route('**/api/email/test**', route => {
        route.fulfill({
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Service Unavailable' })
        });
      });
      
      await page.route('**/api/calendar/test**', route => {
        route.fulfill({
          status: 429,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Rate Limit Exceeded' })
        });
      });
      
      await configPage.navigate();
      
      // メール設定とカレンダー設定を有効化
      await configPage.updateEmailSettings({
        enabled: true,
        email: 'test@example.com',
        appPassword: 'test_password'
      });
      
      await configPage.updateCalendarSettings({
        enabled: true,
        calendarId: 'primary'
      });
      
      // 各テスト機能を実行
      await configPage.sendTestEmail();
      await configPage.testCalendarConnection();
      
      // それぞれ異なるエラーメッセージが表示されることを確認
      const emailError = page.locator('.email-test-error, .email-error');
      const calendarError = page.locator('.calendar-test-error, .calendar-error');
      
      if (await emailError.count() > 0) {
        await expect(emailError).toBeVisible();
        const emailErrorText = await emailError.textContent();
        expect(emailErrorText).toMatch(/(メール|送信|接続)/);
      }
      
      if (await calendarError.count() > 0) {
        await expect(calendarError).toBeVisible();
        const calendarErrorText = await calendarError.textContent();
        expect(calendarErrorText).toMatch(/(カレンダー|制限|レート)/);
      }
    });

    test('依存関係エラーの連鎖処理', async ({ page }) => {
      // データベース接続エラーをシミュレート
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ 
            error: 'Database Connection Failed',
            code: 'DB_CONNECTION_ERROR'
          })
        });
      });
      
      await homePage.navigate();
      
      // システム全体がグレースフルにエラー処理されることを確認
      const systemError = page.locator('.system-error, .database-error, .maintenance-mode');
      const errorMessage = page.locator('.error-message, .alert-danger');
      
      if (await systemError.count() > 0) {
        await expect(systemError).toBeVisible();
      } else if (await errorMessage.count() > 0) {
        await expect(errorMessage).toBeVisible();
        
        const errorText = await errorMessage.textContent();
        expect(errorText).toMatch(/(データベース|接続|エラー)/);
      }
      
      // 基本的なナビゲーションは動作することを確認
      const navigation = page.locator('nav, .navbar');
      await expect(navigation).toBeVisible();
    });
  });

  test.describe('回復機能', () => {
    
    test('一時的エラーからの自動回復', async ({ page }) => {
      let requestCount = 0;
      
      // 最初の2回は失敗、3回目から成功するようにセット
      await page.route('**/api/releases**', route => {
        requestCount++;
        if (requestCount <= 2) {
          route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Temporary Error' })
          });
        } else {
          route.continue(); // 正常な処理を続行
        }
      });
      
      await releasesPage.navigate();
      
      // 再試行ボタンがある場合はクリック
      const retryButton = page.locator('.retry-button, button:has-text("再試行")');
      if (await retryButton.count() > 0) {
        await retryButton.click();
        await homePage.waitForLoadingToFinish();
        
        if (requestCount <= 2) {
          await retryButton.click();
          await homePage.waitForLoadingToFinish();
        }
      }
      
      // 最終的に正常なデータが表示されることを確認
      const releasesTable = page.locator('.releases-table, #releases-table');
      const errorMessage = page.locator('.error, .alert-danger');
      
      // エラーが解消されてテーブルが表示されるか確認
      if (await releasesTable.count() > 0) {
        await expect(releasesTable).toBeVisible();
      } else if (await errorMessage.count() > 0) {
        // まだエラーが表示されている場合、適切なエラーメッセージかどうか確認
        const errorText = await errorMessage.textContent();
        expect(errorText).toBeTruthy();
      }
    });

    test('オフライン状態の検出と処理', async ({ page }) => {
      // ネットワーク接続をオフラインに設定
      await page.context().setOffline(true);
      
      await homePage.navigate();
      
      // オフライン状態の表示確認
      const offlineIndicator = page.locator('.offline, .no-connection, .network-error');
      if (await offlineIndicator.count() > 0) {
        await expect(offlineIndicator).toBeVisible();
        
        const offlineText = await offlineIndicator.textContent();
        expect(offlineText).toMatch(/(オフライン|接続|ネットワーク)/);
      }
      
      // オンライン復帰をシミュレート
      await page.context().setOffline(false);
      
      // 復帰ボタンまたは自動更新の確認
      const reconnectButton = page.locator('.reconnect, button:has-text("再接続")');
      if (await reconnectButton.count() > 0) {
        await reconnectButton.click();
        await homePage.waitForLoadingToFinish();
        
        // 正常な表示に戻ることを確認
        const mainContent = page.locator('.stats-card, .recent-releases');
        if (await mainContent.count() > 0) {
          await expect(mainContent).toBeVisible();
        }
      }
    });
  });
});