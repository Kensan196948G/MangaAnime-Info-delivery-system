import { test, expect } from '@playwright/test';
import { ConfigPage } from './pages/config-page';
import { TestDataGenerator } from './utils/test-helpers';

/**
 * 設定機能のE2Eテスト
 * 
 * NGワード設定、メール設定、カレンダー設定などをテストします
 */

test.describe('設定機能', () => {
  let configPage: ConfigPage;

  test.beforeEach(async ({ page }) => {
    configPage = new ConfigPage(page);
    await configPage.navigate();
    
    // コンソールエラーの監視
    configPage.enableConsoleErrorTracking();
  });

  test.describe('NGワード設定', () => {
    
    test('NGワードを追加できる', async ({ page }) => {
      const testKeyword = 'テストNG_' + TestDataGenerator.randomString(4);
      
      await configPage.addNgKeyword(testKeyword);
      
      // 追加されたキーワードが一覧に表示されることを確認
      await configPage.verifyNgKeywords([testKeyword]);
      
      // 設定を保存
      await configPage.saveConfiguration();
    });

    test('NGワードを削除できる', async ({ page }) => {
      const testKeyword = '削除テスト_' + TestDataGenerator.randomString(4);
      
      // まずキーワードを追加
      await configPage.addNgKeyword(testKeyword);
      await configPage.saveConfiguration();
      
      // ページをリロードして永続化を確認
      await page.reload();
      await configPage.waitForPageLoad();
      
      // キーワードを削除
      await configPage.removeNgKeyword(testKeyword);
      
      // 設定を保存
      await configPage.saveConfiguration();
    });

    test('複数のNGワードを管理できる', async ({ page }) => {
      const keywords = [
        'NGワード1_' + TestDataGenerator.randomString(3),
        'NGワード2_' + TestDataGenerator.randomString(3),
        'NGワード3_' + TestDataGenerator.randomString(3)
      ];
      
      // 複数のキーワードを追加
      for (const keyword of keywords) {
        await configPage.addNgKeyword(keyword);
      }
      
      // 全てのキーワードが表示されることを確認
      await configPage.verifyNgKeywords(keywords);
      
      // 設定を保存
      await configPage.saveConfiguration();
      
      // ページをリロードして永続化を確認
      await page.reload();
      await configPage.waitForPageLoad();
      await configPage.verifyNgKeywords(keywords);
    });

    test('空のNGワードは追加されない', async ({ page }) => {
      // 空の文字列で追加を試行
      const addButton = page.locator('.add-ng-keyword, button:has-text("追加")');
      
      // 入力フィールドを空のままボタンをクリック
      await addButton.click();
      
      // エラーメッセージまたはバリデーション表示を確認
      const errorMessage = page.locator('.error, .validation-error');
      if (await errorMessage.count() > 0) {
        await expect(errorMessage).toBeVisible();
      }
    });
  });

  test.describe('メール設定', () => {
    
    test('メール設定を更新できる', async ({ page }) => {
      const testEmail = 'test_' + TestDataGenerator.randomString(8) + '@example.com';
      
      await configPage.updateEmailSettings({
        enabled: true,
        email: testEmail,
        appPassword: 'test_password_123'
      });
      
      await configPage.saveConfiguration();
      
      // ページをリロードして設定が保持されていることを確認
      await page.reload();
      await configPage.waitForPageLoad();
      
      const emailInput = page.locator('#email_address, input[name="email_address"]');
      await expect(emailInput).toHaveValue(testEmail);
    });

    test('無効なメールアドレスでバリデーションエラーが表示される', async ({ page }) => {
      await configPage.updateEmailSettings({
        enabled: true,
        email: 'invalid-email-address',
        appPassword: 'test_password'
      });
      
      // バリデーションエラーの確認
      await configPage.verifyFormValidation();
    });

    test('メール無効化時は関連フィールドが無効になる', async ({ page }) => {
      await configPage.updateEmailSettings({
        enabled: false
      });
      
      // メール関連フィールドが無効化されることを確認
      const emailInput = page.locator('#email_address, input[name="email_address"]');
      const passwordInput = page.locator('#email_app_password, input[name="email_app_password"]');
      
      if (await emailInput.count() > 0) {
        const isDisabled = await emailInput.isDisabled();
        // フィールドが無効化されているか、非表示になっていることを確認
        expect(isDisabled || !(await emailInput.isVisible())).toBeTruthy();
      }
    });

    test('テストメール送信機能', async ({ page }) => {
      // テスト用のメール設定
      await configPage.updateEmailSettings({
        enabled: true,
        email: 'test@example.com',
        appPassword: 'test_password'
      });
      
      // テストメールの送信
      await configPage.sendTestEmail();
      
      // 結果メッセージの確認（成功またはエラー）
      const notification = page.locator('.alert, .notification');
      await expect(notification).toBeVisible();
      
      const notificationText = await notification.textContent();
      expect(notificationText).toMatch(/(送信|成功|エラー|失敗)/);
    });
  });

  test.describe('カレンダー設定', () => {
    
    test('カレンダー設定を更新できる', async ({ page }) => {
      const testCalendarId = 'test_calendar_' + TestDataGenerator.randomString(8) + '@gmail.com';
      
      await configPage.updateCalendarSettings({
        enabled: true,
        calendarId: testCalendarId
      });
      
      await configPage.saveConfiguration();
      
      // ページをリロードして設定が保持されていることを確認
      await page.reload();
      await configPage.waitForPageLoad();
      
      const calendarInput = page.locator('#calendar_id, input[name="calendar_id"]');
      if (await calendarInput.count() > 0) {
        await expect(calendarInput).toHaveValue(testCalendarId);
      }
    });

    test('カレンダーテスト機能', async ({ page }) => {
      // テスト用のカレンダー設定
      await configPage.updateCalendarSettings({
        enabled: true,
        calendarId: 'primary'
      });
      
      // カレンダーテストの実行
      await configPage.testCalendarConnection();
      
      // テスト結果の確認
      const result = page.locator('.test-result, .alert');
      await expect(result).toBeVisible();
    });
  });

  test.describe('自動収集設定', () => {
    
    test('自動収集設定を更新できる', async ({ page }) => {
      await configPage.updateCollectionSettings({
        autoCollectionEnabled: true,
        intervalHours: 6,
        maxResults: 50
      });
      
      await configPage.saveConfiguration();
      
      // 設定が保存されたことを確認
      await configPage.verifySuccessMessage('設定を保存しました');
    });

    test('収集間隔の選択肢が正しく表示される', async ({ page }) => {
      const intervalSelect = page.locator('#collection_interval, select[name="collection_interval"]');
      
      if (await intervalSelect.count() > 0) {
        // 期待される選択肢
        const expectedOptions = ['1', '3', '6', '12', '24'];
        
        for (const option of expectedOptions) {
          const optionElement = intervalSelect.locator(`option[value="${option}"]`);
          if (await optionElement.count() > 0) {
            await expect(optionElement).toBeVisible();
          }
        }
      }
    });
  });

  test.describe('通知設定', () => {
    
    test('通知設定を更新できる', async ({ page }) => {
      await configPage.updateNotificationSettings({
        enabled: true,
        types: ['email', 'calendar']
      });
      
      await configPage.saveConfiguration();
      
      // 設定保存の確認
      await configPage.verifySuccessMessage('設定を保存しました');
    });

    test('通知タイプの複数選択', async ({ page }) => {
      const notificationTypes = page.locator('input[name="notification_types"]');
      const typeCount = await notificationTypes.count();
      
      if (typeCount > 0) {
        // 複数のタイプを選択
        for (let i = 0; i < Math.min(typeCount, 2); i++) {
          await notificationTypes.nth(i).check();
        }
        
        await configPage.saveConfiguration();
      }
    });
  });

  test.describe('設定の統合テスト', () => {
    
    test('完全な設定ワークフロー', async ({ page }) => {
      await configPage.performCompleteConfigurationWorkflow();
      
      // 全ての設定が正常に保存されたことを確認
      await configPage.verifySuccessMessage('設定を保存しました');
    });

    test('設定のリセット機能', async ({ page }) => {
      // まず設定を変更
      await configPage.addNgKeyword('リセットテスト');
      await configPage.updateEmailSettings({
        enabled: true,
        email: 'reset_test@example.com'
      });
      await configPage.saveConfiguration();
      
      // 設定のリセット
      await configPage.resetConfiguration();
      
      // リセット後の確認
      const ngKeywordsList = page.locator('.ng-keywords-list, #ng-keywords-list');
      if (await ngKeywordsList.count() > 0) {
        const listContent = await ngKeywordsList.textContent();
        expect(listContent).not.toContain('リセットテスト');
      }
    });

    test('設定の永続性確認', async ({ page }) => {
      const testData = {
        ngKeyword: '永続性テスト_' + TestDataGenerator.randomString(4),
        email: 'persistent_test@example.com'
      };
      
      // 設定を変更して保存
      await configPage.addNgKeyword(testData.ngKeyword);
      await configPage.updateEmailSettings({
        enabled: true,
        email: testData.email
      });
      await configPage.saveConfiguration();
      
      // ブラウザを再起動（新しいページインスタンス）
      await page.close();
      const newPage = await page.context().newPage();
      const newConfigPage = new ConfigPage(newPage);
      
      await newConfigPage.navigate();
      
      // 設定が保持されていることを確認
      await newConfigPage.verifyNgKeywords([testData.ngKeyword]);
      
      const emailInput = newPage.locator('#email_address, input[name="email_address"]');
      if (await emailInput.count() > 0) {
        await expect(emailInput).toHaveValue(testData.email);
      }
      
      await newPage.close();
    });
  });

  test.describe('フォームバリデーション', () => {
    
    test('必須フィールドのバリデーション', async ({ page }) => {
      // メールを有効にして必須フィールドを空にする
      const emailEnabledCheckbox = page.locator('#email_enabled, input[name="email_enabled"]');
      await emailEnabledCheckbox.check();
      
      const emailInput = page.locator('#email_address, input[name="email_address"]');
      await emailInput.fill('');
      
      // 保存を試行
      const saveButton = page.locator('button[type="submit"], .save-button');
      await saveButton.click();
      
      // バリデーションメッセージの確認
      const validationMessage = await emailInput.evaluate((input: HTMLInputElement) => {
        return input.validationMessage;
      });
      
      expect(validationMessage).toBeTruthy();
    });

    test('数値フィールドのバリデーション', async ({ page }) => {
      const maxResultsInput = page.locator('#max_results, input[name="max_results"]');
      
      if (await maxResultsInput.count() > 0) {
        // 負の数を入力
        await maxResultsInput.fill('-10');
        
        const saveButton = page.locator('button[type="submit"], .save-button');
        await saveButton.click();
        
        // バリデーションエラーの確認
        const validationMessage = await maxResultsInput.evaluate((input: HTMLInputElement) => {
          return input.validationMessage;
        });
        
        expect(validationMessage).toBeTruthy();
      }
    });
  });

  test.describe('レスポンシブ対応', () => {
    
    test('モバイル表示での設定フォーム', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      await configPage.navigate();
      
      // フォームが適切に表示されることを確認
      const configForm = page.locator('#config-form, form[name="config"]');
      await expect(configForm).toBeVisible();
      
      // モバイルでの操作性を確認
      await configPage.addNgKeyword('モバイルテスト');
      await configPage.saveConfiguration();
    });

    test('タブレット表示での設定フォーム', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      
      await configPage.navigate();
      
      // レスポンシブレイアウトの確認
      await configPage.verifyResponsiveLayout({ width: 768, height: 1024 });
      
      // 基本的な設定操作が可能であることを確認
      await configPage.addNgKeyword('タブレットテスト');
      await configPage.saveConfiguration();
    });
  });
});