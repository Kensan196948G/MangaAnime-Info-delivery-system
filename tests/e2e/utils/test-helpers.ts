import { Page, Locator, expect } from '@playwright/test';

/**
 * E2Eテスト用ヘルパー関数
 * 
 * 共通のテスト操作とアサーションを提供します
 */

export class TestHelpers {
  constructor(private page: Page) {}

  /**
   * 指定した時間待機
   */
  async wait(ms: number): Promise<void> {
    await this.page.waitForTimeout(ms);
  }

  /**
   * ページが完全に読み込まれるまで待機
   */
  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 要素が表示されるまで待機
   */
  async waitForElement(selector: string, timeout = 10000): Promise<Locator> {
    const element = this.page.locator(selector);
    await expect(element).toBeVisible({ timeout });
    return element;
  }

  /**
   * APIレスポンスを待機
   */
  async waitForAPIResponse(urlPattern: string | RegExp, timeout = 15000): Promise<void> {
    await this.page.waitForResponse(response => 
      typeof urlPattern === 'string' 
        ? response.url().includes(urlPattern)
        : urlPattern.test(response.url()),
      { timeout }
    );
  }

  /**
   * フォーム入力
   */
  async fillForm(formData: Record<string, string>): Promise<void> {
    for (const [selector, value] of Object.entries(formData)) {
      await this.page.fill(selector, value);
    }
  }

  /**
   * Select要素の選択
   */
  async selectOption(selector: string, value: string): Promise<void> {
    await this.page.selectOption(selector, value);
  }

  /**
   * チェックボックスの状態変更
   */
  async toggleCheckbox(selector: string, checked: boolean): Promise<void> {
    const checkbox = this.page.locator(selector);
    const currentState = await checkbox.isChecked();
    if (currentState !== checked) {
      await checkbox.click();
    }
  }

  /**
   * テーブル内のデータ確認
   */
  async verifyTableData(tableSelector: string, expectedData: string[][]): Promise<void> {
    const table = this.page.locator(tableSelector);
    await expect(table).toBeVisible();

    for (let i = 0; i < expectedData.length; i++) {
      for (let j = 0; j < expectedData[i].length; j++) {
        const cell = table.locator(`tr:nth-child(${i + 1}) td:nth-child(${j + 1})`);
        await expect(cell).toContainText(expectedData[i][j]);
      }
    }
  }

  /**
   * 通知メッセージの確認
   */
  async verifyNotification(message: string, type: 'success' | 'error' | 'warning' = 'success'): Promise<void> {
    const notification = this.page.locator(`.alert-${type}, .notification-${type}, .flash-${type}`);
    await expect(notification).toBeVisible();
    await expect(notification).toContainText(message);
  }

  /**
   * ページタイトルの確認
   */
  async verifyPageTitle(expectedTitle: string): Promise<void> {
    await expect(this.page).toHaveTitle(expectedTitle);
  }

  /**
   * URLの確認
   */
  async verifyURL(expectedURL: string | RegExp): Promise<void> {
    if (typeof expectedURL === 'string') {
      await expect(this.page).toHaveURL(expectedURL);
    } else {
      await expect(this.page).toHaveURL(expectedURL);
    }
  }

  /**
   * ローディング状態の待機
   */
  async waitForLoadingToFinish(): Promise<void> {
    // スピナーやローディングインジケーターが消えるまで待機
    await this.page.waitForSelector('.loading, .spinner, [data-loading="true"]', {
      state: 'hidden',
      timeout: 30000
    }).catch(() => {
      // ローディング要素が存在しない場合は無視
    });
  }

  /**
   * モーダルダイアログの操作
   */
  async handleModal(action: 'accept' | 'dismiss' = 'accept'): Promise<void> {
    this.page.on('dialog', async dialog => {
      if (action === 'accept') {
        await dialog.accept();
      } else {
        await dialog.dismiss();
      }
    });
  }

  /**
   * ファイルアップロード
   */
  async uploadFile(selector: string, filePath: string): Promise<void> {
    await this.page.setInputFiles(selector, filePath);
  }

  /**
   * スクロール操作
   */
  async scrollTo(selector: string): Promise<void> {
    await this.page.locator(selector).scrollIntoViewIfNeeded();
  }

  /**
   * 要素のスクリーンショット
   */
  async screenshotElement(selector: string, filename: string): Promise<void> {
    await this.page.locator(selector).screenshot({ 
      path: `tests/e2e/screenshots/${filename}` 
    });
  }

  /**
   * カスタムコマンドの実行
   */
  async executeScript(script: string): Promise<any> {
    return await this.page.evaluate(script);
  }

  /**
   * ローカルストレージの操作
   */
  async setLocalStorage(key: string, value: string): Promise<void> {
    await this.page.evaluate(([key, value]) => {
      localStorage.setItem(key, value);
    }, [key, value]);
  }

  async getLocalStorage(key: string): Promise<string | null> {
    return await this.page.evaluate((key) => {
      return localStorage.getItem(key);
    }, key);
  }

  /**
   * セッションストレージの操作
   */
  async setSessionStorage(key: string, value: string): Promise<void> {
    await this.page.evaluate(([key, value]) => {
      sessionStorage.setItem(key, value);
    }, [key, value]);
  }
}

/**
 * テストデータ生成ヘルパー
 */
export class TestDataGenerator {
  /**
   * ランダムな文字列生成
   */
  static randomString(length = 8): string {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  /**
   * テスト用アニメタイトル生成
   */
  static generateAnimeTitle(): string {
    const prefixes = ['魔法の', '勇者の', '異世界', '学園', '戦闘', '恋愛'];
    const suffixes = ['物語', 'アドベンチャー', 'ファンタジー', '学院', 'バトル', 'ロマンス'];
    const prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
    const suffix = suffixes[Math.floor(Math.random() * suffixes.length)];
    return `${prefix}${suffix} ${this.randomString(4)}`;
  }

  /**
   * テスト用マンガタイトル生成
   */
  static generateMangaTitle(): string {
    const prefixes = ['新世紀', '超人', '神秘の', '古代', '未来', '伝説の'];
    const suffixes = ['戦記', 'クロニクル', 'サーガ', 'ストーリー', 'テイル', 'エピック'];
    const prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
    const suffix = suffixes[Math.floor(Math.random() * suffixes.length)];
    return `${prefix}${suffix} 第${Math.floor(Math.random() * 20) + 1}巻`;
  }

  /**
   * テスト用日付生成
   */
  static generateFutureDate(daysFromNow = 30): string {
    const date = new Date();
    date.setDate(date.getDate() + Math.floor(Math.random() * daysFromNow));
    return date.toISOString().split('T')[0];
  }
}