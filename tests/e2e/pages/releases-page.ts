import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base-page';

/**
 * リリース一覧ページのページオブジェクト
 * 
 * 作品リスト表示・フィルタリング機能のテストを提供します
 */
export class ReleasesPage extends BasePage {
  
  // ページ要素のセレクタ
  private readonly releasesTable = '#releases-table, .releases-table';
  private readonly releaseRows = 'tbody tr, .release-row';
  private readonly releaseTitle = '.release-title, td:first-child';
  private readonly releaseDate = '.release-date, .date';
  private readonly releasePlatform = '.release-platform, .platform';
  private readonly releaseType = '.release-type, .type';
  
  // フィルタリング要素
  private readonly filterForm = '#filter-form, .filter-form';
  private readonly typeFilter = '#type-filter, select[name="type"]';
  private readonly platformFilter = '#platform-filter, select[name="platform"]';
  private readonly dateFromInput = '#date-from, input[name="date_from"]';
  private readonly dateToInput = '#date-to, input[name="date_to"]';
  private readonly searchInput = '#search, input[name="search"]';
  private readonly applyFilterButton = '.apply-filter, button:has-text("適用")';
  private readonly clearFilterButton = '.clear-filter, button:has-text("クリア")';
  
  // ページネーション要素
  private readonly paginationNav = '.pagination, nav[aria-label="pagination"]';
  private readonly pageNumbers = '.page-item a, .page-link';
  private readonly nextPageButton = '.next-page, a:has-text("次へ")';
  private readonly prevPageButton = '.prev-page, a:has-text("前へ")';
  private readonly currentPageInfo = '.page-info, .current-page';
  
  // ソート要素
  private readonly sortHeaders = 'th[data-sort], .sortable';
  private readonly sortIndicator = '.sort-indicator, .sort-arrow';
  
  // アクション要素
  private readonly viewDetailsButtons = '.view-details, button:has-text("詳細")';
  private readonly addToWatchlistButtons = '.add-watchlist, button:has-text("ウォッチリスト")';
  private readonly bulkActionCheckboxes = 'input[type="checkbox"][name="selected_releases"]';
  private readonly bulkActionButton = '#bulk-action, .bulk-action';
  
  // 統計情報
  private readonly totalCountInfo = '.total-count, .results-info';
  private readonly filteredCountInfo = '.filtered-count, .showing-info';

  constructor(page: Page) {
    super(page);
  }

  /**
   * リリース一覧ページへの遷移
   */
  async navigate(): Promise<void> {
    await this.page.goto('/releases');
    await this.waitForPageLoad();
  }

  /**
   * リリース一覧テーブルの表示確認
   */
  async verifyReleasesTable(): Promise<void> {
    const table = this.page.locator(this.releasesTable);
    await expect(table).toBeVisible();
    
    // テーブルヘッダーの確認
    const expectedHeaders = ['タイトル', '種別', 'プラットフォーム', 'リリース日', 'アクション'];
    for (const header of expectedHeaders) {
      const headerElement = table.locator(`th:has-text("${header}")`);
      await expect(headerElement).toBeVisible();
    }
  }

  /**
   * リリース行の取得
   */
  async getReleaseRows(): Promise<Locator[]> {
    const rows = this.page.locator(this.releaseRows);
    const count = await rows.count();
    const result = [];
    
    for (let i = 0; i < count; i++) {
      result.push(rows.nth(i));
    }
    
    return result;
  }

  /**
   * 特定のリリースの詳細確認
   */
  async verifyReleaseDetails(rowIndex: number, expectedData: {
    title: string;
    type: string;
    platform: string;
    date: string;
  }): Promise<void> {
    const rows = await this.getReleaseRows();
    expect(rows.length).toBeGreaterThan(rowIndex);
    
    const row = rows[rowIndex];
    
    // タイトルの確認
    const titleCell = row.locator(this.releaseTitle);
    await expect(titleCell).toContainText(expectedData.title);
    
    // 種別の確認
    const typeCell = row.locator(this.releaseType);
    await expect(typeCell).toContainText(expectedData.type);
    
    // プラットフォームの確認
    const platformCell = row.locator(this.releasePlatform);
    await expect(platformCell).toContainText(expectedData.platform);
    
    // 日付の確認
    const dateCell = row.locator(this.releaseDate);
    await expect(dateCell).toContainText(expectedData.date);
  }

  /**
   * 種別フィルターの適用
   */
  async filterByType(type: string): Promise<void> {
    await this.helpers.selectOption(this.typeFilter, type);
    await this.applyFilter();
  }

  /**
   * プラットフォームフィルターの適用
   */
  async filterByPlatform(platform: string): Promise<void> {
    await this.helpers.selectOption(this.platformFilter, platform);
    await this.applyFilter();
  }

  /**
   * 日付範囲フィルターの適用
   */
  async filterByDateRange(fromDate: string, toDate: string): Promise<void> {
    await this.page.fill(this.dateFromInput, fromDate);
    await this.page.fill(this.dateToInput, toDate);
    await this.applyFilter();
  }

  /**
   * キーワード検索の実行
   */
  async searchByKeyword(keyword: string): Promise<void> {
    await this.page.fill(this.searchInput, keyword);
    await this.applyFilter();
  }

  /**
   * フィルターの適用
   */
  async applyFilter(): Promise<void> {
    const applyButton = this.page.locator(this.applyFilterButton);
    await applyButton.click();
    await this.waitForLoadingToFinish();
  }

  /**
   * フィルターのクリア
   */
  async clearFilter(): Promise<void> {
    const clearButton = this.page.locator(this.clearFilterButton);
    if (await clearButton.count() > 0) {
      await clearButton.click();
      await this.waitForLoadingToFinish();
    }
  }

  /**
   * ソート機能のテスト
   */
  async testSorting(columnHeader: string): Promise<void> {
    const header = this.page.locator(`th:has-text("${columnHeader}")`);
    await expect(header).toBeVisible();
    
    // 最初のクリック（昇順）
    await header.click();
    await this.waitForLoadingToFinish();
    
    // ソート状態の確認
    const sortIndicator = header.locator(this.sortIndicator);
    await expect(sortIndicator).toBeVisible();
    
    // 2回目のクリック（降順）
    await header.click();
    await this.waitForLoadingToFinish();
  }

  /**
   * ページネーションのテスト
   */
  async testPagination(): Promise<void> {
    const pagination = this.page.locator(this.paginationNav);
    
    if (await pagination.count() > 0) {
      await expect(pagination).toBeVisible();
      
      // 次のページへ移動
      const nextButton = this.page.locator(this.nextPageButton);
      if (await nextButton.count() > 0 && await nextButton.isEnabled()) {
        await nextButton.click();
        await this.waitForLoadingToFinish();
        
        // ページが変更されたことを確認
        const currentPage = this.page.locator(this.currentPageInfo);
        await expect(currentPage).toContainText('2');
        
        // 前のページに戻る
        const prevButton = this.page.locator(this.prevPageButton);
        await prevButton.click();
        await this.waitForLoadingToFinish();
      }
    }
  }

  /**
   * リリース詳細の表示
   */
  async viewReleaseDetails(rowIndex: number): Promise<void> {
    const rows = await this.getReleaseRows();
    expect(rows.length).toBeGreaterThan(rowIndex);
    
    const row = rows[rowIndex];
    const detailsButton = row.locator(this.viewDetailsButtons);
    
    if (await detailsButton.count() > 0) {
      await detailsButton.click();
      await this.waitForLoadingToFinish();
    } else {
      // ボタンがない場合は行をクリック
      await row.click();
      await this.waitForLoadingToFinish();
    }
  }

  /**
   * ウォッチリストへの追加
   */
  async addToWatchlist(rowIndex: number): Promise<void> {
    const rows = await this.getReleaseRows();
    expect(rows.length).toBeGreaterThan(rowIndex);
    
    const row = rows[rowIndex];
    const watchlistButton = row.locator(this.addToWatchlistButtons);
    
    await expect(watchlistButton).toBeVisible();
    await watchlistButton.click();
    
    // 成功メッセージの確認
    await this.verifySuccessMessage('ウォッチリストに追加しました');
  }

  /**
   * 一括操作のテスト
   */
  async testBulkActions(): Promise<void> {
    const checkboxes = this.page.locator(this.bulkActionCheckboxes);
    const checkboxCount = await checkboxes.count();
    
    if (checkboxCount > 0) {
      // 複数の項目を選択
      const selectCount = Math.min(3, checkboxCount);
      for (let i = 0; i < selectCount; i++) {
        await checkboxes.nth(i).check();
      }
      
      // 一括操作ボタンが有効になることを確認
      const bulkButton = this.page.locator(this.bulkActionButton);
      await expect(bulkButton).toBeEnabled();
      
      // 一括操作の実行（例：一括削除）
      await bulkButton.click();
      
      // 確認ダイアログの処理
      this.helpers.handleModal('accept');
      
      await this.waitForLoadingToFinish();
    }
  }

  /**
   * フィルター結果の統計情報確認
   */
  async verifyFilterStatistics(): Promise<void> {
    const totalInfo = this.page.locator(this.totalCountInfo);
    const filteredInfo = this.page.locator(this.filteredCountInfo);
    
    if (await totalInfo.count() > 0) {
      await expect(totalInfo).toBeVisible();
      
      const totalText = await totalInfo.textContent();
      expect(totalText).toMatch(/\d+/); // 数値が含まれていることを確認
    }
    
    if (await filteredInfo.count() > 0) {
      await expect(filteredInfo).toBeVisible();
      
      const filteredText = await filteredInfo.textContent();
      expect(filteredText).toMatch(/\d+/); // 数値が含まれていることを確認
    }
  }

  /**
   * 空の検索結果の確認
   */
  async verifyEmptyResults(): Promise<void> {
    // 存在しないキーワードで検索
    await this.searchByKeyword('存在しないタイトル12345');
    
    // 空状態の表示確認
    const emptyState = this.page.locator('.empty-results, .no-data, .empty-state');
    await expect(emptyState).toBeVisible();
    
    const emptyMessage = await emptyState.textContent();
    expect(emptyMessage).toContain('結果が見つかりません');
  }

  /**
   * 複合フィルターの適用テスト
   */
  async testComplexFiltering(): Promise<void> {
    // 複数のフィルターを組み合わせて適用
    await this.filterByType('anime');
    await this.filterByPlatform('Netflix');
    await this.searchByKeyword('アニメ');
    
    // フィルター結果の確認
    const rows = await this.getReleaseRows();
    
    // 結果がフィルター条件に合致することを確認
    for (const row of rows) {
      const typeCell = row.locator(this.releaseType);
      const platformCell = row.locator(this.releasePlatform);
      const titleCell = row.locator(this.releaseTitle);
      
      await expect(typeCell).toContainText('anime');
      await expect(platformCell).toContainText('Netflix');
      await expect(titleCell).toContainText('アニメ');
    }
  }

  /**
   * リリース一覧の完全な機能テスト
   */
  async performCompleteReleasesWorkflow(): Promise<void> {
    await this.verifyReleasesTable();
    await this.testSorting('タイトル');
    await this.testSorting('リリース日');
    await this.testPagination();
    await this.filterByType('anime');
    await this.clearFilter();
    await this.searchByKeyword('テスト');
    await this.verifyFilterStatistics();
    await this.testComplexFiltering();
  }
}