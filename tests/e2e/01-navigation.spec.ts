import { test, expect } from '@playwright/test';
import { HomePage } from './pages/home-page';
import { ConfigPage } from './pages/config-page';
import { ReleasesPage } from './pages/releases-page';

/**
 * ナビゲーション機能のE2Eテスト
 * 
 * 基本的なページ遷移と表示を確認します
 */

test.describe('ナビゲーション機能', () => {
  
  test.beforeEach(async ({ page }) => {
    // コンソールエラーの監視を有効化
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error('ブラウザコンソールエラー:', msg.text());
      }
    });
    
    // ネットワークエラーの監視
    page.on('response', response => {
      if (response.status() >= 400) {
        console.error('HTTPエラー:', response.status(), response.url());
      }
    });
  });

  test('ホームページが正常に表示される', async ({ page }) => {
    const homePage = new HomePage(page);
    
    await homePage.navigate();
    
    // ページタイトルの確認
    await homePage.helpers.verifyPageTitle('MangaAnime Info Delivery System');
    
    // 基本要素の表示確認
    await homePage.verifyStatsCards();
    await homePage.verifyRecentReleases();
    await homePage.verifySystemStatus();
    
    // ナビゲーションメニューの表示確認
    const navMenu = page.locator('nav, .navbar');
    await expect(navMenu).toBeVisible();
    
    // 主要なナビゲーションリンクの存在確認
    const expectedNavLinks = ['ホーム', 'リリース一覧', '設定', 'ログ'];
    for (const linkText of expectedNavLinks) {
      const link = page.locator(`nav a:has-text("${linkText}"), .navbar a:has-text("${linkText}")`);
      await expect(link).toBeVisible();
    }
  });

  test('リリース一覧ページへの遷移', async ({ page }) => {
    const homePage = new HomePage(page);
    const releasesPage = new ReleasesPage(page);
    
    // ホームページから開始
    await homePage.navigate();
    
    // リリース一覧へのナビゲーション
    await homePage.clickNavLink('リリース一覧');
    
    // URLの確認
    await expect(page).toHaveURL(/.*\/releases/);
    
    // ページの表示確認
    await releasesPage.verifyReleasesTable();
    
    // ページタイトルの確認
    const pageTitle = await releasesPage.getPageTitle();
    expect(pageTitle).toContain('リリース一覧');
  });

  test('設定ページへの遷移', async ({ page }) => {
    const homePage = new HomePage(page);
    const configPage = new ConfigPage(page);
    
    // ホームページから開始
    await homePage.navigate();
    
    // 設定ページへのナビゲーション
    await homePage.clickNavLink('設定');
    
    // URLの確認
    await expect(page).toHaveURL(/.*\/config/);
    
    // 設定フォームの表示確認
    const configForm = page.locator('#config-form, form[name="config"]');
    await expect(configForm).toBeVisible();
    
    // ページタイトルの確認
    const pageTitle = await configPage.getPageTitle();
    expect(pageTitle).toContain('設定');
  });

  test('ブレッドクラムナビゲーション', async ({ page }) => {
    const homePage = new HomePage(page);
    const releasesPage = new ReleasesPage(page);
    
    await homePage.navigate();
    await homePage.clickNavLink('リリース一覧');
    
    // ブレッドクラムの表示確認
    const breadcrumb = page.locator('.breadcrumb, nav[aria-label="breadcrumb"]');
    if (await breadcrumb.count() > 0) {
      await expect(breadcrumb).toBeVisible();
      await expect(breadcrumb).toContainText('ホーム');
      await expect(breadcrumb).toContainText('リリース一覧');
    }
  });

  test('404エラーページの表示', async ({ page }) => {
    // 存在しないページにアクセス
    const response = await page.goto('/nonexistent-page');
    
    if (response && response.status() === 404) {
      // 404エラーページの表示確認
      const errorMessage = page.locator('.error-404, .not-found');
      if (await errorMessage.count() > 0) {
        await expect(errorMessage).toBeVisible();
      }
      
      // ホームへのリンクがあることを確認
      const homeLink = page.locator('a:has-text("ホーム"), a:has-text("トップ")');
      if (await homeLink.count() > 0) {
        await expect(homeLink).toBeVisible();
      }
    }
  });

  test('モバイル表示でのナビゲーション', async ({ page }) => {
    // モバイルビューポートに設定
    await page.setViewportSize({ width: 375, height: 667 });
    
    const homePage = new HomePage(page);
    await homePage.navigate();
    
    // モバイルメニューの確認
    const mobileMenuToggle = page.locator('.navbar-toggler, .mobile-menu-toggle, .hamburger');
    if (await mobileMenuToggle.count() > 0) {
      await expect(mobileMenuToggle).toBeVisible();
      
      // メニューを開く
      await mobileMenuToggle.click();
      
      // メニューが展開されることを確認
      const mobileMenu = page.locator('.navbar-collapse, .mobile-menu, .nav-menu');
      await expect(mobileMenu).toBeVisible();
      
      // ナビゲーションリンクの確認
      const navLink = mobileMenu.locator('a:has-text("リリース一覧")');
      await expect(navLink).toBeVisible();
      await navLink.click();
      
      // ページ遷移の確認
      await expect(page).toHaveURL(/.*\/releases/);
    }
  });

  test('タブレット表示でのナビゲーション', async ({ page }) => {
    // タブレットビューポートに設定
    await page.setViewportSize({ width: 768, height: 1024 });
    
    const homePage = new HomePage(page);
    await homePage.navigate();
    
    // レスポンシブレイアウトの確認
    await homePage.verifyResponsiveLayout({ width: 768, height: 1024 });
    
    // ナビゲーション機能の確認
    await homePage.clickNavLink('設定');
    await expect(page).toHaveURL(/.*\/config/);
  });

  test('キーボードナビゲーション', async ({ page }) => {
    const homePage = new HomePage(page);
    await homePage.navigate();
    
    // Tabキーでナビゲーション要素にフォーカス移動
    await page.keyboard.press('Tab');
    
    // フォーカスされた要素がナビゲーション内にあることを確認
    const focusedElement = page.locator(':focus');
    const isInNav = await focusedElement.locator('..').locator('nav, .navbar').count() > 0;
    
    if (isInNav) {
      // Enterキーでリンクをアクティベート
      await page.keyboard.press('Enter');
      await page.waitForLoadState('networkidle');
      
      // ページが遷移したことを確認
      const currentUrl = page.url();
      expect(currentUrl).not.toBe('http://127.0.0.1:3033/');
    }
  });

  test('アクティブページの視覚的インジケーター', async ({ page }) => {
    const homePage = new HomePage(page);
    
    // ホームページでアクティブ状態を確認
    await homePage.navigate();
    const homeNavLink = page.locator('nav a:has-text("ホーム"), .navbar a:has-text("ホーム")');
    if (await homeNavLink.count() > 0) {
      const homeClassList = await homeNavLink.getAttribute('class');
      // activeクラスまたは類似の視覚的インジケーターがあることを確認
      if (homeClassList) {
        expect(homeClassList).toMatch(/active|current|selected/);
      }
    }
    
    // リリース一覧ページでアクティブ状態を確認
    await homePage.clickNavLink('リリース一覧');
    const releasesNavLink = page.locator('nav a:has-text("リリース一覧"), .navbar a:has-text("リリース一覧")');
    if (await releasesNavLink.count() > 0) {
      const releasesClassList = await releasesNavLink.getAttribute('class');
      if (releasesClassList) {
        expect(releasesClassList).toMatch(/active|current|selected/);
      }
    }
  });

  test('ページ読み込み性能の確認', async ({ page }) => {
    const homePage = new HomePage(page);
    
    // パフォーマンス測定の開始
    await homePage.navigate();
    
    // パフォーマンスメトリクスの取得
    const metrics = await homePage.getPerformanceMetrics();
    
    // 基本的な性能要件の確認
    expect(metrics.domContentLoaded).toBeLessThan(3000); // 3秒以内
    expect(metrics.loadComplete).toBeLessThan(5000); // 5秒以内
    
    console.log('ページ読み込み性能:', metrics);
  });

  test('サイドバーナビゲーション（存在する場合）', async ({ page }) => {
    const homePage = new HomePage(page);
    await homePage.navigate();
    
    // サイドバーの存在確認
    const sidebar = page.locator('.sidebar, aside, .side-nav');
    if (await sidebar.count() > 0) {
      await expect(sidebar).toBeVisible();
      
      // サイドバー内のナビゲーションリンク確認
      const sidebarLinks = sidebar.locator('a');
      const linkCount = await sidebarLinks.count();
      
      if (linkCount > 0) {
        // 最初のリンクをテスト
        const firstLink = sidebarLinks.first();
        await firstLink.click();
        await page.waitForLoadState('networkidle');
        
        // ページが遷移したことを確認
        const newUrl = page.url();
        expect(newUrl).toContain('http://127.0.0.1:3033');
      }
    }
  });
});