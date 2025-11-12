import { test, expect } from '@playwright/test';
import { ReleasesPage } from './pages/releases-page';
import { TestDataGenerator } from './utils/test-helpers';

/**
 * リリース一覧とフィルタリング機能のE2Eテスト
 * 
 * 作品リストの表示、検索、フィルタリング、ソート機能をテストします
 */

test.describe('リリース一覧とフィルタリング機能', () => {
  let releasesPage: ReleasesPage;

  test.beforeEach(async ({ page }) => {
    releasesPage = new ReleasesPage(page);
    await releasesPage.navigate();
    
    // コンソールエラーの監視
    releasesPage.enableConsoleErrorTracking();
    
    // ネットワークリクエストの監視
    await releasesPage.monitorNetworkRequests();
  });

  test.describe('基本表示機能', () => {
    
    test('リリース一覧テーブルが正常に表示される', async ({ page }) => {
      await releasesPage.verifyReleasesTable();
      
      // テーブルにデータが含まれているか確認
      const releaseRows = await releasesPage.getReleaseRows();
      
      if (releaseRows.length > 0) {
        // 最初の行の詳細を確認
        const firstRow = releaseRows[0];
        const titleCell = firstRow.locator('.release-title, td:first-child');
        const dateCell = firstRow.locator('.release-date, .date');
        const platformCell = firstRow.locator('.release-platform, .platform');
        
        await expect(titleCell).toBeVisible();
        await expect(titleCell).not.toBeEmpty();
        await expect(dateCell).toBeVisible();
        await expect(platformCell).toBeVisible();
      } else {
        // データがない場合の空状態表示を確認
        const emptyState = page.locator('.empty-state, .no-data, .empty-results');
        if (await emptyState.count() > 0) {
          await expect(emptyState).toBeVisible();
        }
      }
    });

    test('ページネーションが正常に動作する', async ({ page }) => {
      await releasesPage.testPagination();
    });

    test('統計情報が表示される', async ({ page }) => {
      await releasesPage.verifyFilterStatistics();
    });
  });

  test.describe('ソート機能', () => {
    
    test('タイトル順ソートが動作する', async ({ page }) => {
      await releasesPage.testSorting('タイトル');
      
      // ソート結果を検証
      const releaseRows = await releasesPage.getReleaseRows();
      if (releaseRows.length >= 2) {
        const firstTitle = await releaseRows[0].locator('.release-title, td:first-child').textContent();
        const secondTitle = await releaseRows[1].locator('.release-title, td:first-child').textContent();
        
        // アルファベット順またはあいうえお順になっていることを確認
        if (firstTitle && secondTitle) {
          expect(firstTitle.localeCompare(secondTitle, 'ja')).toBeLessThanOrEqual(0);
        }
      }
    });

    test('日付順ソートが動作する', async ({ page }) => {
      await releasesPage.testSorting('リリース日');
      
      // 日付ソート結果を検証
      const releaseRows = await releasesPage.getReleaseRows();
      if (releaseRows.length >= 2) {
        const firstDate = await releaseRows[0].locator('.release-date, .date').textContent();
        const secondDate = await releaseRows[1].locator('.release-date, .date').textContent();
        
        if (firstDate && secondDate) {
          const date1 = new Date(firstDate);
          const date2 = new Date(secondDate);
          
          // 日付が有効で、順序が正しいことを確認
          if (!isNaN(date1.getTime()) && !isNaN(date2.getTime())) {
            expect(date1.getTime()).toBeLessThanOrEqual(date2.getTime());
          }
        }
      }
    });

    test('複数回ソートで昇順・降順が切り替わる', async ({ page }) => {
      const titleHeader = page.locator('th:has-text("タイトル")');
      
      if (await titleHeader.count() > 0) {
        // 初期状態の確認
        await titleHeader.click();
        await releasesPage.waitForLoadingToFinish();
        
        let sortIndicator = titleHeader.locator('.sort-indicator, .sort-arrow');
        let sortClass = await sortIndicator.getAttribute('class');
        
        // 2回目のクリック（逆順）
        await titleHeader.click();
        await releasesPage.waitForLoadingToFinish();
        
        sortIndicator = titleHeader.locator('.sort-indicator, .sort-arrow');
        const newSortClass = await sortIndicator.getAttribute('class');
        
        // ソート状態が変化していることを確認
        expect(newSortClass).not.toBe(sortClass);
      }
    });
  });

  test.describe('フィルタリング機能', () => {
    
    test('種別フィルターが動作する', async ({ page }) => {
      // アニメでフィルタリング
      await releasesPage.filterByType('anime');
      
      // フィルター結果の確認
      const releaseRows = await releasesPage.getReleaseRows();
      for (const row of releaseRows) {
        const typeCell = row.locator('.release-type, .type');
        if (await typeCell.count() > 0) {
          await expect(typeCell).toContainText('anime');
        }
      }
      
      // マンガでフィルタリング
      await releasesPage.filterByType('manga');
      
      // フィルター結果の確認
      const mangaRows = await releasesPage.getReleaseRows();
      for (const row of mangaRows) {
        const typeCell = row.locator('.release-type, .type');
        if (await typeCell.count() > 0) {
          await expect(typeCell).toContainText('manga');
        }
      }
    });

    test('プラットフォームフィルターが動作する', async ({ page }) => {
      // 利用可能なプラットフォームを確認
      const platformSelect = page.locator('#platform-filter, select[name="platform"]');
      
      if (await platformSelect.count() > 0) {
        // 最初のオプション（空でない）を選択
        const options = platformSelect.locator('option');
        const optionCount = await options.count();
        
        if (optionCount > 1) {
          const firstOption = await options.nth(1).getAttribute('value');
          if (firstOption) {
            await releasesPage.filterByPlatform(firstOption);
            
            // フィルター結果の確認
            const releaseRows = await releasesPage.getReleaseRows();
            for (const row of releaseRows.slice(0, 5)) { // 最初の5行をチェック
              const platformCell = row.locator('.release-platform, .platform');
              if (await platformCell.count() > 0) {
                await expect(platformCell).toContainText(firstOption);
              }
            }
          }
        }
      }
    });

    test('日付範囲フィルターが動作する', async ({ page }) => {
      const today = new Date();
      const fromDate = new Date(today);
      fromDate.setDate(today.getDate() - 30); // 30日前
      const toDate = new Date(today);
      toDate.setDate(today.getDate() + 30); // 30日後
      
      const fromDateStr = fromDate.toISOString().split('T')[0];
      const toDateStr = toDate.toISOString().split('T')[0];
      
      await releasesPage.filterByDateRange(fromDateStr, toDateStr);
      
      // フィルター結果の確認
      const releaseRows = await releasesPage.getReleaseRows();
      for (const row of releaseRows.slice(0, 3)) { // 最初の3行をチェック
        const dateCell = row.locator('.release-date, .date');
        if (await dateCell.count() > 0) {
          const dateText = await dateCell.textContent();
          if (dateText) {
            const releaseDate = new Date(dateText);
            if (!isNaN(releaseDate.getTime())) {
              expect(releaseDate.getTime()).toBeGreaterThanOrEqual(fromDate.getTime());
              expect(releaseDate.getTime()).toBeLessThanOrEqual(toDate.getTime());
            }
          }
        }
      }
    });

    test('キーワード検索が動作する', async ({ page }) => {
      // まず、検索可能なタイトルを取得
      const releaseRows = await releasesPage.getReleaseRows();
      
      if (releaseRows.length > 0) {
        const firstTitleElement = releaseRows[0].locator('.release-title, td:first-child');
        const firstTitle = await firstTitleElement.textContent();
        
        if (firstTitle && firstTitle.length > 2) {
          // タイトルの一部で検索
          const searchKeyword = firstTitle.substring(0, 3);
          await releasesPage.searchByKeyword(searchKeyword);
          
          // 検索結果の確認
          const filteredRows = await releasesPage.getReleaseRows();
          for (const row of filteredRows) {
            const titleCell = row.locator('.release-title, td:first-child');
            if (await titleCell.count() > 0) {
              await expect(titleCell).toContainText(searchKeyword);
            }
          }
        }
      }
    });

    test('複合フィルターが動作する', async ({ page }) => {
      await releasesPage.testComplexFiltering();
    });

    test('フィルタークリア機能が動作する', async ({ page }) => {
      // フィルターを適用
      await releasesPage.filterByType('anime');
      await releasesPage.searchByKeyword('テスト');
      
      // 初期状態の行数を記録
      const initialRows = await releasesPage.getReleaseRows();
      const initialCount = initialRows.length;
      
      // フィルターをクリア
      await releasesPage.clearFilter();
      
      // クリア後の行数を確認
      const clearedRows = await releasesPage.getReleaseRows();
      const clearedCount = clearedRows.length;
      
      // クリア後の方が多いか同じ行数であることを確認
      expect(clearedCount).toBeGreaterThanOrEqual(initialCount);
    });
  });

  test.describe('検索機能詳細', () => {
    
    test('部分一致検索が動作する', async ({ page }) => {
      await releasesPage.searchByKeyword('アニメ');
      
      const releaseRows = await releasesPage.getReleaseRows();
      for (const row of releaseRows) {
        const titleCell = row.locator('.release-title, td:first-child');
        if (await titleCell.count() > 0) {
          const titleText = await titleCell.textContent();
          if (titleText) {
            expect(titleText.toLowerCase()).toContain('アニメ'.toLowerCase());
          }
        }
      }
    });

    test('大文字小文字を区別しない検索', async ({ page }) => {
      await releasesPage.searchByKeyword('ANIME');
      
      const releaseRows = await releasesPage.getReleaseRows();
      if (releaseRows.length > 0) {
        // 結果があれば検索が機能していることを確認
        const titleCell = releaseRows[0].locator('.release-title, td:first-child');
        await expect(titleCell).toBeVisible();
      }
    });

    test('空の検索結果の表示', async ({ page }) => {
      await releasesPage.verifyEmptyResults();
    });

    test('特殊文字を含む検索', async ({ page }) => {
      await releasesPage.searchByKeyword('Re:ゼロ');
      
      // 特殊文字が含まれていてもエラーが発生しないことを確認
      const errorMessage = page.locator('.error, .alert-danger');
      if (await errorMessage.count() > 0) {
        expect(await errorMessage.isVisible()).toBeFalsy();
      }
    });
  });

  test.describe('アクション機能', () => {
    
    test('リリース詳細表示が動作する', async ({ page }) => {
      const releaseRows = await releasesPage.getReleaseRows();
      
      if (releaseRows.length > 0) {
        await releasesPage.viewReleaseDetails(0);
        
        // 詳細ページまたはモーダルが表示されることを確認
        const detailModal = page.locator('.modal, .detail-modal');
        const detailPage = page.locator('.release-detail, #release-detail');
        
        const modalVisible = await detailModal.count() > 0 && await detailModal.isVisible();
        const pageVisible = await detailPage.count() > 0 && await detailPage.isVisible();
        const urlChanged = page.url().includes('detail') || page.url().includes('release');
        
        expect(modalVisible || pageVisible || urlChanged).toBeTruthy();
      }
    });

    test('ウォッチリスト追加機能', async ({ page }) => {
      const releaseRows = await releasesPage.getReleaseRows();
      
      if (releaseRows.length > 0) {
        const watchlistButton = releaseRows[0].locator('.add-watchlist, button:has-text("ウォッチリスト")');
        
        if (await watchlistButton.count() > 0) {
          await releasesPage.addToWatchlist(0);
          
          // 成功メッセージまたはボタン状態の変化を確認
          const successMessage = page.locator('.alert-success, .success');
          const buttonText = await watchlistButton.textContent();
          
          const hasSuccessMessage = await successMessage.count() > 0 && await successMessage.isVisible();
          const buttonChanged = buttonText?.includes('追加済') || buttonText?.includes('削除');
          
          expect(hasSuccessMessage || buttonChanged).toBeTruthy();
        }
      }
    });

    test('一括操作機能', async ({ page }) => {
      await releasesPage.testBulkActions();
    });
  });

  test.describe('レスポンシブ対応', () => {
    
    test('モバイル表示でのリリース一覧', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      await releasesPage.navigate();
      
      // モバイルでもテーブルまたはカードレイアウトが表示されることを確認
      const table = page.locator('.releases-table, #releases-table');
      const cardLayout = page.locator('.releases-cards, .card-layout');
      
      const tableVisible = await table.count() > 0 && await table.isVisible();
      const cardVisible = await cardLayout.count() > 0 && await cardLayout.isVisible();
      
      expect(tableVisible || cardVisible).toBeTruthy();
      
      // フィルター機能がモバイルでも動作することを確認
      await releasesPage.searchByKeyword('テスト');
    });

    test('タブレット表示でのリリース一覧', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      
      await releasesPage.navigate();
      await releasesPage.verifyReleasesTable();
      
      // タブレットでの基本操作確認
      await releasesPage.testSorting('タイトル');
      await releasesPage.searchByKeyword('アニメ');
    });
  });

  test.describe('パフォーマンステスト', () => {
    
    test('大量データの表示性能', async ({ page }) => {
      const startTime = Date.now();
      
      await releasesPage.navigate();
      await releasesPage.waitForPageLoad();
      
      const loadTime = Date.now() - startTime;
      
      // 5秒以内に読み込まれることを確認
      expect(loadTime).toBeLessThan(5000);
      
      console.log('リリース一覧ページ読み込み時間:', loadTime + 'ms');
    });

    test('フィルタリングの応答性能', async ({ page }) => {
      const startTime = Date.now();
      
      await releasesPage.filterByType('anime');
      
      const filterTime = Date.now() - startTime;
      
      // 3秒以内にフィルタリングが完了することを確認
      expect(filterTime).toBeLessThan(3000);
      
      console.log('フィルタリング処理時間:', filterTime + 'ms');
    });

    test('検索の応答性能', async ({ page }) => {
      const startTime = Date.now();
      
      await releasesPage.searchByKeyword('アニメ');
      
      const searchTime = Date.now() - startTime;
      
      // 2秒以内に検索が完了することを確認
      expect(searchTime).toBeLessThan(2000);
      
      console.log('検索処理時間:', searchTime + 'ms');
    });
  });

  test.describe('アクセシビリティ', () => {
    
    test('キーボードナビゲーション', async ({ page }) => {
      // Tabキーでテーブル要素をナビゲート
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      
      const focusedElement = page.locator(':focus');
      await expect(focusedElement).toBeVisible();
    });

    test('スクリーンリーダー対応', async ({ page }) => {
      // テーブルにaria-labelやrole属性があることを確認
      const table = page.locator('.releases-table, #releases-table');
      
      if (await table.count() > 0) {
        const ariaLabel = await table.getAttribute('aria-label');
        const role = await table.getAttribute('role');
        
        expect(ariaLabel || role).toBeTruthy();
      }
    });
  });
});