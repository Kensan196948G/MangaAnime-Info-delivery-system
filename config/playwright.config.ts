import { defineConfig, devices } from '@playwright/test';

/**
 * MangaAnime-Info-delivery-system E2E Test Configuration
 * 
 * Playwrightを使用したEnd-to-Endテストの設定ファイル
 * Web UIの主要機能をテストします
 */

export default defineConfig({
  // テストディレクトリを指定
  testDir: './tests/e2e',
  
  // テスト実行タイムアウト（30秒）
  timeout: 30 * 1000,
  
  // テスト間での状態の完全分離
  fullyParallel: true,
  
  // CI環境では失敗時に再試行を無効化
  forbidOnly: !!process.env.CI,
  
  // CI環境での再試行回数
  retries: process.env.CI ? 2 : 0,
  
  // 並列実行ワーカー数（CI環境では1、ローカルでは半分）
  workers: process.env.CI ? 1 : undefined,
  
  // レポート設定
  reporter: [
    ['html', { outputFolder: 'tests/e2e/reports/html' }],
    ['json', { outputFile: 'tests/e2e/reports/test-results.json' }],
    ['junit', { outputFile: 'tests/e2e/reports/junit.xml' }],
    ['list']
  ],
  
  // 全テスト共通設定
  use: {
    // ベースURL（テスト対象のローカルサーバー）
    baseURL: 'http://127.0.0.1:3033',
    
    // トレース記録（失敗時のみ）
    trace: 'on-first-retry',
    
    // スクリーンショット（失敗時のみ）
    screenshot: 'only-on-failure',
    
    // ビデオ録画（失敗時のみ）
    video: 'retain-on-failure',
    
    // アクションタイムアウト
    actionTimeout: 10 * 1000,
    
    // ナビゲーションタイムアウト
    navigationTimeout: 15 * 1000,
  },

  // プロジェクト設定（異なるブラウザ・環境でのテスト）
  projects: [
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
    
    // モバイルブラウザテスト
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  // テストサーバーの設定
  webServer: {
    command: 'python3 web_app.py',
    port: 3033,
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
    env: {
      'FLASK_ENV': 'testing',
      'TESTING': 'true',
      'DATABASE_URL': 'sqlite:///test_e2e.db'
    }
  },

  // 出力ディレクトリ
  outputDir: 'tests/e2e/test-results/',
  
  // グローバルセットアップ・ティアダウン
  globalSetup: require.resolve('./tests/e2e/global-setup.ts'),
  globalTeardown: require.resolve('./tests/e2e/global-teardown.ts'),
});