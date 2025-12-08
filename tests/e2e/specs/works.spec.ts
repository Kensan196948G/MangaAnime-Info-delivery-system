import { test, expect } from '../fixtures/custom-fixtures';
import { PageHelper } from '../fixtures/custom-fixtures';
import { testWorks } from '../fixtures/test-data';

/**
 * 作品一覧ページE2Eテスト
 */
test.describe('作品一覧ページ', () => {
  test.beforeEach(async ({ page, testDataSetup }) => {
    await page.goto('/works');
  });

  test('作品一覧が表示される', async ({ page }) => {
    const helper = new PageHelper(page);

    // API応答待機
    await helper.waitForApiResponse('/api/works');

    // 作品カードが表示される
    const workCards = page.locator('.work-card');
    await expect(workCards).toHaveCountGreaterThan(0);
  });

  test('作品詳細モーダルが開く', async ({ page }) => {
    const helper = new PageHelper(page);

    // 最初の作品カードをクリック
    await page.click('.work-card:first-child');

    // モーダルが表示される
    const modal = page.locator('.work-detail-modal');
    await expect(modal).toBeVisible();

    // 詳細情報が表示される
    await expect(modal.locator('.work-title')).toBeVisible();
    await expect(modal.locator('.work-description')).toBeVisible();
    await expect(modal.locator('.work-official-url')).toBeVisible();
  });

  test('作品タイプでフィルタリング', async ({ page }) => {
    // アニメのみ表示
    await page.click('button[data-filter="anime"]');
    await page.waitForTimeout(500);

    const animeCards = page.locator('.work-card[data-type="anime"]');
    await expect(animeCards).toHaveCountGreaterThan(0);

    const mangaCards = page.locator('.work-card[data-type="manga"]');
    await expect(mangaCards).toHaveCount(0);

    // マンガのみ表示
    await page.click('button[data-filter="manga"]');
    await page.waitForTimeout(500);

    await expect(page.locator('.work-card[data-type="manga"]')).toHaveCountGreaterThan(0);
    await expect(page.locator('.work-card[data-type="anime"]')).toHaveCount(0);
  });

  test('ソート機能が動作する', async ({ page }) => {
    const helper = new PageHelper(page);

    // タイトル順
    await page.selectOption('select[name="sort"]', 'title_asc');
    await helper.waitForApiResponse('/api/works');

    let titles = await page.locator('.work-title').allTextContents();
    let sortedTitles = [...titles].sort();
    expect(titles).toEqual(sortedTitles);

    // 作成日順（新しい順）
    await page.selectOption('select[name="sort"]', 'created_desc');
    await helper.waitForApiResponse('/api/works');

    const firstCard = page.locator('.work-card').first();
    await expect(firstCard).toBeVisible();
  });

  test('検索機能が動作する', async ({ page }) => {
    const helper = new PageHelper(page);

    // 検索実行
    await page.fill('input[name="search"]', testWorks.anime.title);
    await page.click('button[type="submit"]');

    await helper.waitForApiResponse('/api/works/search');

    // 検索結果が表示される
    const searchResults = page.locator('.work-card');
    await expect(searchResults).toHaveCountGreaterThan(0);

    const firstResult = searchResults.first();
    await expect(firstResult.locator('.work-title')).toContainText(testWorks.anime.title);
  });

  test('お気に入り機能', async ({ page, authenticatedPage }) => {
    const helper = new PageHelper(authenticatedPage);

    // お気に入りボタンをクリック
    await authenticatedPage.click('.work-card:first-child .favorite-button');

    // API応答待機
    await helper.waitForApiResponse('/api/favorites');

    // お気に入り状態が反映される
    const favoriteButton = authenticatedPage.locator('.work-card:first-child .favorite-button');
    await expect(favoriteButton).toHaveClass(/favorited/);
  });

  test('無限スクロールが機能する', async ({ page }) => {
    const helper = new PageHelper(page);

    // 初期表示の作品数を取得
    const initialCount = await page.locator('.work-card').count();

    // ページ最下部までスクロール
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

    // 追加読み込み待機
    await helper.waitForApiResponse('/api/works');
    await page.waitForTimeout(1000);

    // 作品数が増加する
    const newCount = await page.locator('.work-card').count();
    expect(newCount).toBeGreaterThan(initialCount);
  });

  test('外部リンクが正しく開く', async ({ page, context }) => {
    // 新しいタブで開くリンク
    const [newPage] = await Promise.all([
      context.waitForEvent('page'),
      page.click('.work-card:first-child .official-link'),
    ]);

    // 外部サイトに遷移
    await newPage.waitForLoadState();
    expect(newPage.url()).toContain('http');

    await newPage.close();
  });

  test('作品情報の編集（管理者のみ）', async ({ page, authenticatedPage }) => {
    // 管理者としてログイン
    await authenticatedPage.goto('/admin/login');
    await authenticatedPage.fill('input[name="email"]', 'admin@example.com');
    await authenticatedPage.fill('input[name="password"]', 'Admin123!');
    await authenticatedPage.click('button[type="submit"]');

    await authenticatedPage.goto('/works');

    // 編集ボタンが表示される
    await expect(authenticatedPage.locator('.edit-button').first()).toBeVisible();

    // 編集モーダルを開く
    await authenticatedPage.click('.edit-button:first-child');

    const editModal = authenticatedPage.locator('.edit-modal');
    await expect(editModal).toBeVisible();

    // 作品情報を変更
    await authenticatedPage.fill('.edit-modal input[name="title"]', '変更後タイトル');
    await authenticatedPage.click('.edit-modal button[type="submit"]');

    const helper = new PageHelper(authenticatedPage);
    await helper.waitForApiResponse('/api/works');

    // 変更が反映される
    await expect(authenticatedPage.locator('.work-title').first()).toContainText('変更後タイトル');
  });

  test('エラーハンドリング', async ({ page }) => {
    // APIエラーシミュレート
    await page.route('**/api/works', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Database connection failed' }),
      });
    });

    await page.reload();

    // エラーメッセージ表示
    const errorMessage = page.locator('.error-message');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText('エラーが発生しました');

    // リトライボタンが表示される
    const retryButton = page.locator('.retry-button');
    await expect(retryButton).toBeVisible();
  });

  test('レスポンシブレイアウト', async ({ page }) => {
    // デスクトップ: グリッドレイアウト
    await page.setViewportSize({ width: 1280, height: 720 });
    const gridContainer = page.locator('.works-grid');
    await expect(gridContainer).toHaveCSS('display', /grid/);

    // タブレット: 2カラム
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(300);

    // モバイル: 1カラム
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(300);
  });

  test('キーボードナビゲーション', async ({ page }) => {
    // Tab キーで移動
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Enterキーでカード選択
    await page.keyboard.press('Enter');

    // モーダルが開く
    const modal = page.locator('.work-detail-modal');
    await expect(modal).toBeVisible();

    // Escapeキーでモーダルを閉じる
    await page.keyboard.press('Escape');
    await expect(modal).not.toBeVisible();
  });
});
