import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base-page';

/**
 * 設定ページのページオブジェクト
 * 
 * システム設定機能のテストを提供します
 */
export class ConfigPage extends BasePage {
  
  // フォーム要素のセレクタ
  private readonly configForm = '#config-form, form[name="config"]';
  private readonly saveButton = 'button[type="submit"], .save-button';
  private readonly resetButton = '.reset-button, button:has-text("リセット")';
  
  // NGワード設定
  private readonly ngKeywordsTextarea = '#ng_keywords, textarea[name="ng_keywords"]';
  private readonly addNgKeywordButton = '.add-ng-keyword, button:has-text("追加")';
  private readonly ngKeywordInput = '#new-ng-keyword, input[name="new_ng_keyword"]';
  private readonly ngKeywordsList = '.ng-keywords-list, #ng-keywords-list';
  private readonly removeNgKeywordButton = '.remove-ng-keyword';
  
  // メール設定
  private readonly emailEnabledCheckbox = '#email_enabled, input[name="email_enabled"]';
  private readonly emailAddressInput = '#email_address, input[name="email_address"]';
  private readonly emailAppPasswordInput = '#email_app_password, input[name="email_app_password"]';
  private readonly testEmailButton = '.test-email-button, button:has-text("テストメール送信")';
  
  // カレンダー設定
  private readonly calendarEnabledCheckbox = '#calendar_enabled, input[name="calendar_enabled"]';
  private readonly calendarIdInput = '#calendar_id, input[name="calendar_id"]';
  private readonly testCalendarButton = '.test-calendar-button, button:has-text("カレンダーテスト")';
  
  // 収集設定
  private readonly autoCollectionEnabledCheckbox = '#auto_collection_enabled, input[name="auto_collection_enabled"]';
  private readonly collectionIntervalSelect = '#collection_interval, select[name="collection_interval"]';
  private readonly maxResultsInput = '#max_results, input[name="max_results"]';
  
  // 通知設定
  private readonly notificationEnabledCheckbox = '#notification_enabled, input[name="notification_enabled"]';
  private readonly notificationTypesCheckboxes = 'input[name="notification_types"]';
  
  // フィルタリング設定
  private readonly filterByGenreCheckbox = '#filter_by_genre, input[name="filter_by_genre"]';
  private readonly allowedGenresSelect = '#allowed_genres, select[name="allowed_genres"]';

  constructor(page: Page) {
    super(page);
  }

  /**
   * 設定ページへの遷移
   */
  async navigate(): Promise<void> {
    await this.page.goto('/config');
    await this.waitForPageLoad();
  }

  /**
   * NGワードの追加
   */
  async addNgKeyword(keyword: string): Promise<void> {
    // 入力フィールドにキーワードを入力
    const input = this.page.locator(this.ngKeywordInput);
    await expect(input).toBeVisible();
    await input.fill(keyword);
    
    // 追加ボタンをクリック
    const addButton = this.page.locator(this.addNgKeywordButton);
    await addButton.click();
    
    // キーワードがリストに追加されることを確認
    const keywordsList = this.page.locator(this.ngKeywordsList);
    await expect(keywordsList).toContainText(keyword);
    
    await this.waitForLoadingToFinish();
  }

  /**
   * NGワードの削除
   */
  async removeNgKeyword(keyword: string): Promise<void> {
    const keywordsList = this.page.locator(this.ngKeywordsList);
    const keywordItem = keywordsList.locator('.ng-keyword-item').filter({
      hasText: keyword
    });
    
    await expect(keywordItem).toBeVisible();
    
    const removeButton = keywordItem.locator(this.removeNgKeywordButton);
    await removeButton.click();
    
    // 確認ダイアログがある場合は承認
    this.helpers.handleModal('accept');
    
    // キーワードがリストから削除されることを確認
    await expect(keywordItem).not.toBeVisible();
  }

  /**
   * NGワード一覧の確認
   */
  async verifyNgKeywords(expectedKeywords: string[]): Promise<void> {
    const keywordsList = this.page.locator(this.ngKeywordsList);
    await expect(keywordsList).toBeVisible();
    
    for (const keyword of expectedKeywords) {
      await expect(keywordsList).toContainText(keyword);
    }
  }

  /**
   * メール設定の更新
   */
  async updateEmailSettings(config: {
    enabled: boolean;
    email?: string;
    appPassword?: string;
  }): Promise<void> {
    // メール有効化の設定
    await this.helpers.toggleCheckbox(this.emailEnabledCheckbox, config.enabled);
    
    if (config.enabled) {
      // メールアドレスの設定
      if (config.email) {
        await this.page.fill(this.emailAddressInput, config.email);
      }
      
      // アプリパスワードの設定
      if (config.appPassword) {
        await this.page.fill(this.emailAppPasswordInput, config.appPassword);
      }
    }
  }

  /**
   * テストメールの送信
   */
  async sendTestEmail(): Promise<void> {
    const testButton = this.page.locator(this.testEmailButton);
    await expect(testButton).toBeVisible();
    await expect(testButton).toBeEnabled();
    
    await testButton.click();
    await this.waitForLoadingToFinish();
    
    // 成功またはエラーメッセージを確認
    const notification = this.page.locator('.alert, .notification');
    await expect(notification).toBeVisible();
  }

  /**
   * カレンダー設定の更新
   */
  async updateCalendarSettings(config: {
    enabled: boolean;
    calendarId?: string;
  }): Promise<void> {
    // カレンダー有効化の設定
    await this.helpers.toggleCheckbox(this.calendarEnabledCheckbox, config.enabled);
    
    if (config.enabled && config.calendarId) {
      await this.page.fill(this.calendarIdInput, config.calendarId);
    }
  }

  /**
   * カレンダーテストの実行
   */
  async testCalendarConnection(): Promise<void> {
    const testButton = this.page.locator(this.testCalendarButton);
    await expect(testButton).toBeVisible();
    await expect(testButton).toBeEnabled();
    
    await testButton.click();
    await this.waitForLoadingToFinish();
    
    // テスト結果の確認
    const result = this.page.locator('.test-result, .alert');
    await expect(result).toBeVisible();
  }

  /**
   * 自動収集設定の更新
   */
  async updateCollectionSettings(config: {
    autoCollectionEnabled: boolean;
    intervalHours?: number;
    maxResults?: number;
  }): Promise<void> {
    // 自動収集の有効化
    await this.helpers.toggleCheckbox(this.autoCollectionEnabledCheckbox, config.autoCollectionEnabled);
    
    if (config.autoCollectionEnabled) {
      // 収集間隔の設定
      if (config.intervalHours) {
        await this.helpers.selectOption(this.collectionIntervalSelect, config.intervalHours.toString());
      }
      
      // 最大結果数の設定
      if (config.maxResults) {
        await this.page.fill(this.maxResultsInput, config.maxResults.toString());
      }
    }
  }

  /**
   * 通知設定の更新
   */
  async updateNotificationSettings(config: {
    enabled: boolean;
    types?: string[];
  }): Promise<void> {
    // 通知有効化の設定
    await this.helpers.toggleCheckbox(this.notificationEnabledCheckbox, config.enabled);
    
    if (config.enabled && config.types) {
      // 通知タイプの選択
      for (const type of config.types) {
        const checkbox = this.page.locator(`${this.notificationTypesCheckboxes}[value="${type}"]`);
        await this.helpers.toggleCheckbox(`${this.notificationTypesCheckboxes}[value="${type}"]`, true);
      }
    }
  }

  /**
   * 設定の保存
   */
  async saveConfiguration(): Promise<void> {
    const saveButton = this.page.locator(this.saveButton);
    await expect(saveButton).toBeVisible();
    await expect(saveButton).toBeEnabled();
    
    await saveButton.click();
    await this.waitForLoadingToFinish();
    
    // 保存成功メッセージの確認
    await this.verifySuccessMessage('設定を保存しました');
  }

  /**
   * 設定のリセット
   */
  async resetConfiguration(): Promise<void> {
    const resetButton = this.page.locator(this.resetButton);
    if (await resetButton.count() > 0) {
      await resetButton.click();
      
      // 確認ダイアログの処理
      this.helpers.handleModal('accept');
      
      await this.waitForLoadingToFinish();
      
      // リセット成功メッセージの確認
      await this.verifySuccessMessage('設定をリセットしました');
    }
  }

  /**
   * フォームバリデーションの確認
   */
  async verifyFormValidation(): Promise<void> {
    // メール設定を有効にして無効なメールアドレスを入力
    await this.helpers.toggleCheckbox(this.emailEnabledCheckbox, true);
    await this.page.fill(this.emailAddressInput, 'invalid-email');
    
    await this.page.locator(this.saveButton).click();
    
    // バリデーションエラーメッセージの確認
    const emailError = this.page.locator('.email-error, .error:has-text("メール")');
    if (await emailError.count() > 0) {
      await expect(emailError).toBeVisible();
    }
    
    // HTML5バリデーションの確認
    const emailInput = this.page.locator(this.emailAddressInput);
    const validationMessage = await emailInput.evaluate((input: HTMLInputElement) => {
      return input.validationMessage;
    });
    
    expect(validationMessage).toBeTruthy();
  }

  /**
   * 設定の完全なワークフローテスト
   */
  async performCompleteConfigurationWorkflow(): Promise<void> {
    // NGワードの追加
    await this.addNgKeyword('テストNG');
    
    // メール設定の更新
    await this.updateEmailSettings({
      enabled: true,
      email: 'test@example.com',
      appPassword: 'test_password'
    });
    
    // カレンダー設定の更新
    await this.updateCalendarSettings({
      enabled: true,
      calendarId: 'test_calendar@gmail.com'
    });
    
    // 収集設定の更新
    await this.updateCollectionSettings({
      autoCollectionEnabled: true,
      intervalHours: 6,
      maxResults: 50
    });
    
    // 通知設定の更新
    await this.updateNotificationSettings({
      enabled: true,
      types: ['email', 'calendar']
    });
    
    // 設定の保存
    await this.saveConfiguration();
    
    // 保存後の確認
    await this.page.reload();
    await this.waitForPageLoad();
    
    // 設定が保持されていることを確認
    await this.verifyNgKeywords(['テストNG']);
  }
}