import { test, expect } from '../fixtures/custom-fixtures';
import { PageHelper } from '../fixtures/custom-fixtures';
import { testReleases } from '../fixtures/test-data';

/**
 * リリース情報ページE2Eテスト
 */
test.describe('リリース情報ページ', () => {
  test.beforeEach(async ({ page, testDataSetup }) => {
    await page.goto('/releases');
  });

  test('リリース一覧が表示される', async ({ page }) => {
    const helper = new PageHelper(page);

    // API応答待機
    await helper.waitForApiResponse('/api/releases');

    // リリースカードが表示される
    const releaseCards = page.locator('.release-card');
    await expect(releaseCards).toHaveCountGreaterThan(0);

    // 各カードに必要な情報が含まれる
    const firstCard = releaseCards.first();
    await expect(firstCard.locator('.release-title')).toBeVisible();
    await expect(firstCard.locator('.release-date')).toBeVisible();
    await expect(firstCard.locator('.release-platform')).toBeVisible();
    await expect(firstCard.locator('.release-type')).toBeVisible();
  });

  test('日付フィルターが機能する', async ({ page }) => {
    const helper = new PageHelper(page);

    // 日付範囲を設定
    await page.fill('input[name="start_date"]', '2025-12-01');
    await page.fill('input[name="end_date"]', '2025-12-31');
    await page.click('button[data-action="filter"]');

    await helper.waitForApiResponse('/api/releases');

    // フィルター結果が表示される
    const releaseCards = page.locator('.release-card');
    await expect(releaseCards).toHaveCountGreaterThan(0);
  });

  test('プラットフォームフィルターが機能する', async ({ page }) => {
    // プラットフォーム選択
    await page.click('button[data-platform="dアニメストア"]');
    await page.waitForTimeout(500);

    // 該当プラットフォームのみ表示
    const dAnimeCards = page.locator('.release-card[data-platform="dアニメストア"]');
    await expect(dAnimeCards).toHaveCountGreaterThan(0);

    const otherCards = page.locator('.release-card:not([data-platform="dアニメストア"])');
    await expect(otherCards).toHaveCount(0);
  });

  test('リリースタイプフィルターが機能する', async ({ page }) => {
    // エピソードのみ表示
    await page.click('input[type="checkbox"][value="episode"]');
    await page.waitForTimeout(500);

    const episodeCards = page.locator('.release-card[data-type="episode"]');
    await expect(episodeCards).toHaveCountGreaterThan(0);

    // ボリュームも追加
    await page.click('input[type="checkbox"][value="volume"]');
    await page.waitForTimeout(500);

    const volumeCards = page.locator('.release-card[data-type="volume"]');
    await expect(volumeCards).toHaveCountGreaterThan(0);
  });

  test('カレンダービューが表示される', async ({ page }) => {
    // カレンダービューに切り替え
    await page.click('button[data-view="calendar"]');
    await page.waitForTimeout(500);

    // カレンダーが表示される
    const calendar = page.locator('.calendar-view');
    await expect(calendar).toBeVisible();

    // 日付セルが表示される
    const dateCells = page.locator('.calendar-date');
    await expect(dateCells).toHaveCountGreaterThan(0);

    // リリースがある日付にマーカーが表示される
    const markedDates = page.locator('.calendar-date.has-releases');
    await expect(markedDates).toHaveCountGreaterThan(0);
  });

  test('リストビューとカレンダービューの切り替え', async ({ page }) => {
    // 初期はリストビュー
    await expect(page.locator('.list-view')).toBeVisible();
    await expect(page.locator('.calendar-view')).not.toBeVisible();

    // カレンダービューに切り替え
    await page.click('button[data-view="calendar"]');
    await page.waitForTimeout(300);

    await expect(page.locator('.calendar-view')).toBeVisible();
    await expect(page.locator('.list-view')).not.toBeVisible();

    // リストビューに戻す
    await page.click('button[data-view="list"]');
    await page.waitForTimeout(300);

    await expect(page.locator('.list-view')).toBeVisible();
    await expect(page.locator('.calendar-view')).not.toBeVisible();
  });

  test('リリース詳細が表示される', async ({ page }) => {
    // リリースカードをクリック
    await page.click('.release-card:first-child');

    // 詳細モーダルが開く
    const modal = page.locator('.release-detail-modal');
    await expect(modal).toBeVisible();

    // 詳細情報が表示される
    await expect(modal.locator('.work-info')).toBeVisible();
    await expect(modal.locator('.release-info')).toBeVisible();
    await expect(modal.locator('.source-link')).toBeVisible();
  });

  test('通知設定が機能する', async ({ page, authenticatedPage }) => {
    const helper = new PageHelper(authenticatedPage);

    // 通知ボタンをクリック
    await authenticatedPage.click('.release-card:first-child .notify-button');

    // API応答待機
    await helper.waitForApiResponse('/api/notifications');

    // 通知設定が保存される
    const notifyButton = authenticatedPage.locator('.release-card:first-child .notify-button');
    await expect(notifyButton).toHaveClass(/notified/);

    // 通知設定を解除
    await authenticatedPage.click('.release-card:first-child .notify-button');
    await helper.waitForApiResponse('/api/notifications');
    await expect(notifyButton).not.toHaveClass(/notified/);
  });

  test('GoogleカレンダーへのExport', async ({ page }) => {
    // カレンダーエクスポートボタンをクリック
    await page.click('.release-card:first-child .export-calendar');

    // 確認モーダルが表示される
    const confirmModal = page.locator('.confirm-modal');
    await expect(confirmModal).toBeVisible();

    // エクスポート実行
    await page.click('.confirm-modal button[data-action="confirm"]');

    const helper = new PageHelper(page);
    await helper.waitForApiResponse('/api/calendar/export');

    // 成功メッセージが表示される
    const successMessage = page.locator('.success-message');
    await expect(successMessage).toBeVisible();
    await expect(successMessage).toContainText('カレンダーに追加しました');
  });

  test('検索機能', async ({ page }) => {
    const helper = new PageHelper(page);

    // 作品名で検索
    await page.fill('input[name="search"]', 'テストアニメ');
    await page.click('button[type="submit"]');

    await helper.waitForApiResponse('/api/releases/search');

    // 検索結果が表示される
    const searchResults = page.locator('.release-card');
    await expect(searchResults).toHaveCountGreaterThan(0);

    // すべての結果に検索キーワードが含まれる
    const titles = await page.locator('.release-title').allTextContents();
    titles.forEach(title => {
      expect(title.toLowerCase()).toContain('テストアニメ'.toLowerCase());
    });
  });

  test('ソート機能', async ({ page }) => {
    const helper = new PageHelper(page);

    // 配信日順（近い順）
    await page.selectOption('select[name="sort"]', 'release_date_asc');
    await helper.waitForApiResponse('/api/releases');

    // 日付順に並んでいることを確認
    const dates = await page.locator('.release-date').allTextContents();
    const parsedDates = dates.map(d => new Date(d).getTime());

    for (let i = 0; i < parsedDates.length - 1; i++) {
      expect(parsedDates[i]).toBeLessThanOrEqual(parsedDates[i + 1]);
    }
  });

  test('ページネーション', async ({ page }) => {
    const helper = new PageHelper(page);

    // 2ページ目に移動
    await page.click('a[aria-label="2ページ目"]');
    await helper.waitForApiResponse('/api/releases');

    // URLが更新される
    expect(page.url()).toContain('page=2');

    // ページネーション状態が更新される
    const activePage = page.locator('.pagination .active');
    await expect(activePage).toContainText('2');
  });

  test('一括操作機能', async ({ page, authenticatedPage }) => {
    // 複数のリリースを選択
    await authenticatedPage.click('.release-card:nth-child(1) input[type="checkbox"]');
    await authenticatedPage.click('.release-card:nth-child(2) input[type="checkbox"]');
    await authenticatedPage.click('.release-card:nth-child(3) input[type="checkbox"]');

    // 一括操作メニューが表示される
    const bulkMenu = authenticatedPage.locator('.bulk-actions');
    await expect(bulkMenu).toBeVisible();

    // 一括通知設定
    await authenticatedPage.click('button[data-action="bulk-notify"]');

    const helper = new PageHelper(authenticatedPage);
    await helper.waitForApiResponse('/api/notifications/bulk');

    // 成功メッセージ
    const successMessage = authenticatedPage.locator('.success-message');
    await expect(successMessage).toBeVisible();
  });

  test('エクスポート機能（CSV）', async ({ page, context }) => {
    // CSVエクスポート
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('button[data-action="export-csv"]'),
    ]);

    // ダウンロードファイル名確認
    expect(download.suggestedFilename()).toMatch(/releases.*\.csv/);
  });

  test('エクスポート機能（iCal）', async ({ page, context }) => {
    // iCalエクスポート
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('button[data-action="export-ical"]'),
    ]);

    // ダウンロードファイル名確認
    expect(download.suggestedFilename()).toMatch(/releases.*\.ics/);
  });

  test('エラーハンドリング', async ({ page }) => {
    // APIエラーシミュレート
    await page.route('**/api/releases', route => {
      route.fulfill({
        status: 503,
        body: JSON.stringify({ error: 'Service Unavailable' }),
      });
    });

    await page.reload();

    // エラーメッセージ表示
    const errorMessage = page.locator('.error-message');
    await expect(errorMessage).toBeVisible();

    // リトライボタン
    await expect(page.locator('.retry-button')).toBeVisible();
  });

  test('リアルタイム更新', async ({ page }) => {
    const helper = new PageHelper(page);

    // 初期のリリース数を取得
    const initialCount = await page.locator('.release-card').count();

    // WebSocket接続シミュレート（新しいリリースが追加された通知）
    await page.evaluate(() => {
      window.dispatchEvent(
        new CustomEvent('new-release', {
          detail: { title: '新着リリース', date: '2025-12-25' },
        })
      );
    });

    await page.waitForTimeout(1000);

    // 通知バッジが表示される
    const notificationBadge = page.locator('.notification-badge');
    await expect(notificationBadge).toBeVisible();

    // 更新ボタンをクリック
    await page.click('button[data-action="refresh"]');
    await helper.waitForApiResponse('/api/releases');

    // リリース数が増加
    const newCount = await page.locator('.release-card').count();
    expect(newCount).toBeGreaterThanOrEqual(initialCount);
  });
});
