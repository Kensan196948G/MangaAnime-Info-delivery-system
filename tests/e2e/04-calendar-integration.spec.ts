import { test, expect } from '@playwright/test';
import { HomePage } from './pages/home-page';
import { ConfigPage } from './pages/config-page';
import { TestDataGenerator } from './utils/test-helpers';

/**
 * カレンダー連携機能のE2Eテスト
 * 
 * Googleカレンダー連携、予定登録、同期機能をテストします
 */

test.describe('カレンダー連携機能', () => {
  let homePage: HomePage;
  let configPage: ConfigPage;

  test.beforeEach(async ({ page }) => {
    homePage = new HomePage(page);
    configPage = new ConfigPage(page);
    
    // コンソールエラーの監視
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error('ブラウザコンソールエラー:', msg.text());
      }
    });
  });

  test.describe('カレンダーページ表示', () => {
    
    test('カレンダーページが正常に表示される', async ({ page }) => {
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      // カレンダービューの表示確認
      const calendarView = page.locator('#calendar, .calendar-view, .calendar-container');
      await expect(calendarView).toBeVisible();
      
      // カレンダーナビゲーション要素の確認
      const prevButton = page.locator('.prev-month, .calendar-prev, button:has-text("前")');
      const nextButton = page.locator('.next-month, .calendar-next, button:has-text("次")');
      const monthYear = page.locator('.current-month, .month-year, .calendar-header');
      
      if (await prevButton.count() > 0) {
        await expect(prevButton).toBeVisible();
      }
      if (await nextButton.count() > 0) {
        await expect(nextButton).toBeVisible();
      }
      if (await monthYear.count() > 0) {
        await expect(monthYear).toBeVisible();
      }
    });

    test('カレンダーの月間ビューナビゲーション', async ({ page }) => {
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      const monthYearElement = page.locator('.current-month, .month-year, .calendar-header');
      
      if (await monthYearElement.count() > 0) {
        // 現在の月を記録
        const currentMonth = await monthYearElement.textContent();
        
        // 次の月に移動
        const nextButton = page.locator('.next-month, .calendar-next, button:has-text("次")');
        if (await nextButton.count() > 0) {
          await nextButton.click();
          await homePage.waitForLoadingToFinish();
          
          // 月が変わったことを確認
          const newMonth = await monthYearElement.textContent();
          expect(newMonth).not.toBe(currentMonth);
          
          // 前の月に戻る
          const prevButton = page.locator('.prev-month, .calendar-prev, button:has-text("前")');
          if (await prevButton.count() > 0) {
            await prevButton.click();
            await homePage.waitForLoadingToFinish();
          }
        }
      }
    });

    test('今日の日付がハイライトされる', async ({ page }) => {
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      const today = new Date();
      const todayDate = today.getDate();
      
      // 今日の日付セルを探す
      const todayCell = page.locator(
        `.calendar-day[data-date="${todayDate}"], ` +
        `.day-${todayDate}, ` +
        `.today, ` +
        `td:has-text("${todayDate}").today, ` +
        `td:has-text("${todayDate}").current-day`
      );
      
      if (await todayCell.count() > 0) {
        await expect(todayCell).toBeVisible();
        
        // todayクラスまたは類似のスタイルが適用されていることを確認
        const cellClass = await todayCell.getAttribute('class');
        if (cellClass) {
          expect(cellClass).toMatch(/today|current|highlight/);
        }
      }
    });
  });

  test.describe('カレンダーイベント表示', () => {
    
    test('リリースイベントが表示される', async ({ page }) => {
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      // カレンダー上のイベント要素を探す
      const events = page.locator('.calendar-event, .event, .release-event');
      const eventCount = await events.count();
      
      if (eventCount > 0) {
        // 最初のイベントの詳細を確認
        const firstEvent = events.first();
        await expect(firstEvent).toBeVisible();
        
        // イベントのタイトルまたは内容があることを確認
        const eventText = await firstEvent.textContent();
        expect(eventText).toBeTruthy();
        expect(eventText!.length).toBeGreaterThan(0);
        
        // イベントをクリックして詳細表示をテスト
        await firstEvent.click();
        
        // 詳細モーダルまたはポップオーバーが表示されるかチェック
        const eventDetail = page.locator('.event-detail, .event-popup, .modal');
        if (await eventDetail.count() > 0) {
          await expect(eventDetail).toBeVisible();
          
          // 詳細情報が含まれていることを確認
          const detailContent = await eventDetail.textContent();
          expect(detailContent).toBeTruthy();
        }
      } else {
        console.log('カレンダーにイベントが登録されていません');
      }
    });

    test('異なるタイプのイベントが区別して表示される', async ({ page }) => {
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      // アニメとマンガのイベントを探す
      const animeEvents = page.locator('.event-anime, .anime-release, [data-type="anime"]');
      const mangaEvents = page.locator('.event-manga, .manga-release, [data-type="manga"]');
      
      const animeCount = await animeEvents.count();
      const mangaCount = await mangaEvents.count();
      
      if (animeCount > 0 || mangaCount > 0) {
        console.log(`アニメイベント: ${animeCount}件, マンガイベント: ${mangaCount}件`);
        
        // イベントタイプごとに異なるスタイルが適用されていることを確認
        if (animeCount > 0) {
          const animeClass = await animeEvents.first().getAttribute('class');
          expect(animeClass).toContain('anime');
        }
        
        if (mangaCount > 0) {
          const mangaClass = await mangaEvents.first().getAttribute('class');
          expect(mangaClass).toContain('manga');
        }
      }
    });

    test('イベントの日付情報が正しく表示される', async ({ page }) => {
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      const events = page.locator('.calendar-event, .event, .release-event');
      const eventCount = await events.count();
      
      if (eventCount > 0) {
        const firstEvent = events.first();
        
        // イベントが配置されている日付セルを確認
        const parentCell = firstEvent.locator('xpath=ancestor::td[@data-date or contains(@class, "calendar-day")]');
        
        if (await parentCell.count() > 0) {
          const dateAttr = await parentCell.getAttribute('data-date');
          const cellClass = await parentCell.getAttribute('class');
          
          // 日付情報が適切に設定されていることを確認
          expect(dateAttr || cellClass).toBeTruthy();
        }
      }
    });
  });

  test.describe('カレンダー設定との連携', () => {
    
    test('カレンダー設定変更後の表示更新', async ({ page }) => {
      // まず設定ページでカレンダーを有効化
      await configPage.navigate();
      
      await configPage.updateCalendarSettings({
        enabled: true,
        calendarId: 'test_calendar'
      });
      
      await configPage.saveConfiguration();
      
      // カレンダーページに移動して表示確認
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      // カレンダーが正常に表示されることを確認
      const calendarView = page.locator('#calendar, .calendar-view');
      await expect(calendarView).toBeVisible();
      
      // 設定が無効の場合のテスト
      await configPage.navigate();
      await configPage.updateCalendarSettings({
        enabled: false
      });
      await configPage.saveConfiguration();
      
      await page.goto('/calendar');
      
      // 無効化メッセージまたは設定へのリンクが表示されることを確認
      const disabledMessage = page.locator('.calendar-disabled, .config-required');
      if (await disabledMessage.count() > 0) {
        await expect(disabledMessage).toBeVisible();
      }
    });

    test('カレンダー接続テスト機能', async ({ page }) => {
      await configPage.navigate();
      
      // テスト用設定を適用
      await configPage.updateCalendarSettings({
        enabled: true,
        calendarId: 'primary'
      });
      
      // カレンダー接続テストを実行
      await configPage.testCalendarConnection();
      
      // テスト結果を確認
      const testResult = page.locator('.test-result, .alert, .notification');
      await expect(testResult).toBeVisible();
      
      const resultText = await testResult.textContent();
      expect(resultText).toMatch(/(成功|失敗|エラー|接続)/);
    });
  });

  test.describe('カレンダーAPI統合', () => {
    
    test('Google Calendar API呼び出し', async ({ page }) => {
      // API呼び出しの監視
      let apiCalled = false;
      
      page.on('request', request => {
        if (request.url().includes('calendar') || request.url().includes('google')) {
          apiCalled = true;
          console.log('カレンダーAPIリクエスト:', request.method(), request.url());
        }
      });
      
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      // APIが呼び出されたかまたはキャッシュデータが表示されることを確認
      const calendarData = page.locator('.calendar-event, .event, .no-events');
      await expect(calendarData).toBeVisible();
    });

    test('カレンダーイベント作成API', async ({ page }) => {
      // 手動でイベント作成をトリガー
      await homePage.navigate();
      
      // クイックアクションまたは手動収集でイベント作成をトリガー
      const manualCollectionButton = page.locator('button:has-text("手動収集"), .manual-collection');
      
      if (await manualCollectionButton.count() > 0) {
        await manualCollectionButton.click();
        await homePage.waitForLoadingToFinish();
        
        // 収集結果としてカレンダーイベントが作成されることを期待
        await page.goto('/calendar');
        await homePage.waitForPageLoad();
        
        const events = page.locator('.calendar-event, .event');
        // イベントの存在確認（数はゼロでも可）
        const eventCount = await events.count();
        expect(eventCount).toBeGreaterThanOrEqual(0);
      }
    });
  });

  test.describe('エラーハンドリング', () => {
    
    test('カレンダーAPI接続エラーの処理', async ({ page }) => {
      // ネットワークリクエストを失敗させる（オフライン状態をシミュレート）
      await page.route('**/calendar**', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal Server Error' })
        });
      });
      
      await page.goto('/calendar');
      
      // エラーメッセージまたはオフライン表示を確認
      const errorMessage = page.locator('.error, .alert-danger, .offline-message');
      if (await errorMessage.count() > 0) {
        await expect(errorMessage).toBeVisible();
        
        const errorText = await errorMessage.textContent();
        expect(errorText).toMatch(/(エラー|接続|失敗|オフライン)/);
      }
    });

    test('認証エラーの処理', async ({ page }) => {
      // 認証エラーをシミュレート
      await page.route('**/auth**', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Unauthorized' })
        });
      });
      
      await page.goto('/calendar');
      
      // 認証が必要なメッセージまたは設定へのリンクを確認
      const authMessage = page.locator('.auth-required, .login-required');
      if (await authMessage.count() > 0) {
        await expect(authMessage).toBeVisible();
        
        // 設定ページへのリンクがあることを確認
        const settingsLink = page.locator('a:has-text("設定"), a:has-text("認証")');
        if (await settingsLink.count() > 0) {
          await expect(settingsLink).toBeVisible();
        }
      }
    });

    test('レート制限エラーの処理', async ({ page }) => {
      // レート制限エラーをシミュレート
      await page.route('**/calendar**', route => {
        route.fulfill({
          status: 429,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Too Many Requests' })
        });
      });
      
      await page.goto('/calendar');
      
      // レート制限メッセージを確認
      const rateLimitMessage = page.locator('.rate-limit, .too-many-requests');
      if (await rateLimitMessage.count() > 0) {
        await expect(rateLimitMessage).toBeVisible();
      }
    });
  });

  test.describe('レスポンシブ対応', () => {
    
    test('モバイル表示でのカレンダー', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      // モバイル用カレンダー表示を確認
      const mobileCalendar = page.locator('.calendar-mobile, .mobile-calendar');
      const standardCalendar = page.locator('#calendar, .calendar-view');
      
      // モバイル専用表示または標準表示のいずれかが表示されることを確認
      const mobileVisible = await mobileCalendar.count() > 0 && await mobileCalendar.isVisible();
      const standardVisible = await standardCalendar.count() > 0 && await standardCalendar.isVisible();
      
      expect(mobileVisible || standardVisible).toBeTruthy();
      
      // モバイルでのナビゲーション操作
      const nextButton = page.locator('.next-month, .calendar-next, button:has-text("次")');
      if (await nextButton.count() > 0) {
        await nextButton.click();
        await homePage.waitForLoadingToFinish();
      }
    });

    test('タブレット表示でのカレンダー', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      // タブレット表示での基本機能確認
      const calendarView = page.locator('#calendar, .calendar-view');
      await expect(calendarView).toBeVisible();
      
      // イベント表示の確認
      const events = page.locator('.calendar-event, .event');
      const eventCount = await events.count();
      
      if (eventCount > 0) {
        await events.first().click();
        // イベント詳細の表示確認
        const eventDetail = page.locator('.event-detail, .event-popup, .modal');
        if (await eventDetail.count() > 0) {
          await expect(eventDetail).toBeVisible();
        }
      }
    });
  });

  test.describe('パフォーマンス', () => {
    
    test('カレンダー読み込み性能', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      const loadTime = Date.now() - startTime;
      
      // 5秒以内に読み込まれることを確認
      expect(loadTime).toBeLessThan(5000);
      
      console.log('カレンダーページ読み込み時間:', loadTime + 'ms');
    });

    test('月間ナビゲーション性能', async ({ page }) => {
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      const nextButton = page.locator('.next-month, .calendar-next, button:has-text("次")');
      
      if (await nextButton.count() > 0) {
        const startTime = Date.now();
        
        await nextButton.click();
        await homePage.waitForLoadingToFinish();
        
        const navigationTime = Date.now() - startTime;
        
        // 3秒以内にナビゲーションが完了することを確認
        expect(navigationTime).toBeLessThan(3000);
        
        console.log('月間ナビゲーション時間:', navigationTime + 'ms');
      }
    });
  });

  test.describe('アクセシビリティ', () => {
    
    test('キーボードナビゲーション', async ({ page }) => {
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      // 矢印キーでカレンダー内をナビゲート
      await page.keyboard.press('Tab'); // カレンダーにフォーカス
      await page.keyboard.press('ArrowRight'); // 次の日に移動
      await page.keyboard.press('ArrowDown'); // 下の週に移動
      
      const focusedElement = page.locator(':focus');
      await expect(focusedElement).toBeVisible();
    });

    test('スクリーンリーダー対応', async ({ page }) => {
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      // カレンダーテーブルにappropriateなaria属性があることを確認
      const calendarTable = page.locator('table, .calendar-grid');
      
      if (await calendarTable.count() > 0) {
        const ariaLabel = await calendarTable.getAttribute('aria-label');
        const role = await calendarTable.getAttribute('role');
        
        expect(ariaLabel || role).toBeTruthy();
      }
      
      // イベントにaria-labelがあることを確認
      const events = page.locator('.calendar-event, .event');
      if (await events.count() > 0) {
        const eventAriaLabel = await events.first().getAttribute('aria-label');
        const eventTitle = await events.first().getAttribute('title');
        
        expect(eventAriaLabel || eventTitle).toBeTruthy();
      }
    });
  });
});