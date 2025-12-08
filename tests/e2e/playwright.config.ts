import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2Eテスト設定
 * MangaAnime-Info-delivery-system用
 */
export default defineConfig({
  testDir: './specs',

  // テスト実行設定
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  // レポート設定
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list'],
  ],

  // タイムアウト設定
  timeout: 30 * 1000,
  expect: {
    timeout: 5000,
  },

  // テストオプション
  use: {
    // ベースURL
    baseURL: process.env.BASE_URL || 'http://localhost:5000',

    // トレース設定
    trace: 'on-first-retry',

    // スクリーンショット設定
    screenshot: 'only-on-failure',

    // ビデオ設定
    video: 'retain-on-failure',

    // 動作設定
    actionTimeout: 10 * 1000,
    navigationTimeout: 15 * 1000,

    // ロケール設定
    locale: 'ja-JP',
    timezoneId: 'Asia/Tokyo',

    // ビューポート設定
    viewport: { width: 1280, height: 720 },

    // ユーザーエージェント
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  },

  // プロジェクト設定（複数ブラウザ対応）
  projects: [
    // デスクトップ
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // モバイル
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },

    // タブレット
    {
      name: 'iPad',
      use: { ...devices['iPad Pro'] },
    },
  ],

  // Webサーバー設定（ローカルテスト用）
  webServer: {
    command: 'python app/app.py',
    url: 'http://localhost:5000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
    stdout: 'pipe',
    stderr: 'pipe',
    env: {
      FLASK_ENV: 'test',
      DATABASE_URL: 'sqlite:///test.db',
    },
  },

  // グローバル設定
  globalSetup: require.resolve('./global-setup.ts'),
  globalTeardown: require.resolve('./global-teardown.ts'),
});
