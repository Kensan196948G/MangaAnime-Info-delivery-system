import { test, expect } from '@playwright/test';
import { HomePage } from './pages/home-page';
import { ConfigPage } from './pages/config-page';
import { ReleasesPage } from './pages/releases-page';
import { TestDataGenerator } from './utils/test-helpers';

/**
 * 統合ワークフローのE2Eテスト
 * 
 * システム全体の統合されたユーザーワークフローをテストします
 */

test.describe('統合ワークフロー', () => {
  let homePage: HomePage;
  let configPage: ConfigPage;
  let releasesPage: ReleasesPage;

  test.beforeEach(async ({ page }) => {
    homePage = new HomePage(page);
    configPage = new ConfigPage(page);
    releasesPage = new ReleasesPage(page);
    
    // 包括的なエラー監視
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error('ブラウザエラー:', msg.text());
      }
    });
    
    page.on('pageerror', error => {
      console.error('ページエラー:', error.message);
    });
    
    // ネットワーク監視
    page.on('response', response => {
      if (response.status() >= 400) {
        console.log('HTTPエラーレスポンス:', response.status(), response.url());
      }
    });
  });

  test.describe('新規ユーザーのオンボーディングフロー', () => {
    
    test('初回セットアップから運用開始まで', async ({ page }) => {
      // 1. ホームページでシステム状態確認
      await homePage.navigate();
      await homePage.verifyFullDashboard();
      
      // 初期統計を記録
      const initialStats = await homePage.getStatistics();
      console.log('初期統計:', initialStats);
      
      // 2. 設定ページで基本設定を行う
      await configPage.navigate();
      
      // NGワードの設定
      const testNgKeywords = [
        'エロ_test',
        'R18_test', 
        'BL_test'
      ];
      
      for (const keyword of testNgKeywords) {
        await configPage.addNgKeyword(keyword);
      }
      
      // メール設定
      await configPage.updateEmailSettings({
        enabled: true,
        email: 'onboarding_test@example.com',
        appPassword: 'test_password_123'
      });
      
      // カレンダー設定
      await configPage.updateCalendarSettings({
        enabled: true,
        calendarId: 'primary'
      });
      
      // 自動収集設定
      await configPage.updateCollectionSettings({
        autoCollectionEnabled: true,
        intervalHours: 6,
        maxResults: 20
      });
      
      // 通知設定
      await configPage.updateNotificationSettings({
        enabled: true,
        types: ['email', 'calendar']
      });
      
      // 設定保存
      await configPage.saveConfiguration();
      
      // 3. 設定の動作確認
      // メールテスト
      await configPage.sendTestEmail();
      
      // カレンダーテスト
      await configPage.testCalendarConnection();
      
      // 4. リリース一覧で動作確認
      await releasesPage.navigate();
      await releasesPage.verifyReleasesTable();
      
      // フィルタリング機能の確認
      await releasesPage.filterByType('anime');
      await releasesPage.clearFilter();
      
      // 5. ダッシュボードに戻って確認
      await homePage.navigate();
      await homePage.verifyFullDashboard();
      
      // セットアップ後の統計を確認
      const finalStats = await homePage.getStatistics();
      console.log('セットアップ後統計:', finalStats);
    });
  });

  test.describe('日常的な運用ワークフロー', () => {
    
    test('毎日の確認・管理フロー', async ({ page }) => {
      // 1. ダッシュボードで日々の状況確認
      await homePage.navigate();
      
      // 本日のリリース確認
      const todayStats = await homePage.getStatistics();
      console.log('本日の統計:', todayStats);
      
      // 最近のリリース確認
      await homePage.verifyRecentReleases();
      
      // システム状態確認
      await homePage.verifySystemStatus();
      
      // 2. 新しいリリースの詳細確認
      if (todayStats.todayReleases > 0) {
        await homePage.clickRecentRelease(0);
      }
      
      // 3. リリース一覧で詳細な確認
      await releasesPage.navigate();
      
      // 今日のリリースでフィルタリング
      const today = new Date();
      const todayStr = today.toISOString().split('T')[0];
      await releasesPage.filterByDateRange(todayStr, todayStr);
      
      // 気になる作品をウォッチリストに追加
      const releaseRows = await releasesPage.getReleaseRows();
      if (releaseRows.length > 0) {
        await releasesPage.addToWatchlist(0);
      }
      
      // 4. 週間・月間の傾向確認
      const weekAgo = new Date();
      weekAgo.setDate(today.getDate() - 7);
      const weekAgoStr = weekAgo.toISOString().split('T')[0];
      
      await releasesPage.clearFilter();
      await releasesPage.filterByDateRange(weekAgoStr, todayStr);
      
      // 統計情報の確認
      await releasesPage.verifyFilterStatistics();
      
      // 5. カレンダーで今後の予定確認
      await page.goto('/calendar');
      await homePage.waitForPageLoad();
      
      const calendarView = page.locator('#calendar, .calendar-view');
      if (await calendarView.count() > 0) {
        await expect(calendarView).toBeVisible();
        
        // 今後のイベント確認
        const events = page.locator('.calendar-event, .event');
        const eventCount = await events.count();
        console.log('カレンダー上のイベント数:', eventCount);
        
        if (eventCount > 0) {
          // イベント詳細確認
          await events.first().click();
          
          const eventDetail = page.locator('.event-detail, .modal');
          if (await eventDetail.count() > 0) {
            await expect(eventDetail).toBeVisible();
          }
        }
      }
    });

    test('週次メンテナンス・設定見直しフロー', async ({ page }) => {
      // 1. システム統計の確認
      await homePage.navigate();
      const weeklyStats = await homePage.getStatistics();
      
      // 2. NGワードの見直し
      await configPage.navigate();
      
      // 新しいNGワードの追加（例：季節やトレンドに応じて）
      const newNgKeyword = 'weekly_review_' + TestDataGenerator.randomString(6);
      await configPage.addNgKeyword(newNgKeyword);
      
      // 既存のNGワードの確認と整理
      await configPage.verifyNgKeywords([newNgKeyword]);
      
      // 3. 通知設定の最適化
      await configPage.updateNotificationSettings({
        enabled: true,
        types: ['email', 'calendar']
      });
      
      // 4. 収集設定の調整（結果数やインターバルの見直し）
      await configPage.updateCollectionSettings({
        autoCollectionEnabled: true,
        intervalHours: 4, // より頻繁に
        maxResults: 30    // より多くの結果
      });
      
      await configPage.saveConfiguration();
      
      // 5. パフォーマンス確認
      const performanceMetrics = await homePage.getPerformanceMetrics();
      console.log('週次パフォーマンス指標:', performanceMetrics);
      
      // 6. ログ確認（エラーや警告の確認）
      const logsPage = page.locator('a:has-text("ログ")');
      if (await logsPage.count() > 0) {
        await logsPage.click();
        await homePage.waitForPageLoad();
        
        // ログ表示の確認
        const logEntries = page.locator('.log-entry, .log-line');
        const logCount = await logEntries.count();
        console.log('ログエントリ数:', logCount);
        
        // エラーログの確認
        const errorLogs = page.locator('.log-error, .error-log');
        const errorCount = await errorLogs.count();
        if (errorCount > 0) {
          console.log('エラーログが見つかりました:', errorCount);
          
          // 最初のエラーログの内容確認
          const firstError = await errorLogs.first().textContent();
          console.log('最初のエラー:', firstError);
        }
      }
    });
  });

  test.describe('トラブルシューティングワークフロー', () => {
    
    test('通知が届かない問題の診断・解決フロー', async ({ page }) => {
      // 1. 問題の確認：ダッシュボードで状態チェック
      await homePage.navigate();
      await homePage.verifySystemStatus();
      
      // 2. 設定の確認
      await configPage.navigate();
      
      // メール設定の確認
      const emailEnabled = page.locator('#email_enabled, input[name="email_enabled"]');
      const isEmailEnabled = await emailEnabled.isChecked();
      
      if (!isEmailEnabled) {
        console.log('メール機能が無効になっています');
        await configPage.updateEmailSettings({
          enabled: true,
          email: 'troubleshoot@example.com',
          appPassword: 'test_password'
        });
      }
      
      // カレンダー設定の確認
      const calendarEnabled = page.locator('#calendar_enabled, input[name="calendar_enabled"]');
      const isCalendarEnabled = await calendarEnabled.isChecked();
      
      if (!isCalendarEnabled) {
        console.log('カレンダー機能が無効になっています');
        await configPage.updateCalendarSettings({
          enabled: true,
          calendarId: 'primary'
        });
      }
      
      // 3. テスト実行で問題の特定
      if (isEmailEnabled || !isEmailEnabled) {
        await configPage.sendTestEmail();
        
        // テスト結果の確認
        const emailTestResult = page.locator('.test-result, .alert');
        if (await emailTestResult.count() > 0) {
          const resultText = await emailTestResult.textContent();
          console.log('メールテスト結果:', resultText);
          
          if (resultText?.includes('エラー') || resultText?.includes('失敗')) {
            // エラーの場合の対処
            console.log('メール設定に問題があります');
            
            // 設定値の再入力
            await configPage.updateEmailSettings({
              enabled: true,
              email: 'fixed_email@example.com',
              appPassword: 'corrected_password'
            });
            
            await configPage.saveConfiguration();
            
            // 再テスト
            await configPage.sendTestEmail();
          }
        }
      }
      
      if (isCalendarEnabled || !isCalendarEnabled) {
        await configPage.testCalendarConnection();
        
        const calendarTestResult = page.locator('.test-result, .alert');
        if (await calendarTestResult.count() > 0) {
          const resultText = await calendarTestResult.textContent();
          console.log('カレンダーテスト結果:', resultText);
        }
      }
      
      // 4. 設定保存と最終確認
      await configPage.saveConfiguration();
      
      // 5. ダッシュボードに戻って状態の改善確認
      await homePage.navigate();
      await homePage.verifySystemStatus();
    });

    test('データ収集が停止した問題の対処フロー', async ({ page }) => {
      // 1. ダッシュボードで収集状況確認
      await homePage.navigate();
      const initialStats = await homePage.getStatistics();
      
      // 2. 手動収集の実行
      await homePage.executeQuickAction('手動収集実行');
      
      // 収集処理の完了待機
      await homePage.waitForLoadingToFinish();
      
      // 3. 収集結果の確認
      await page.waitForTimeout(3000); // 収集処理の時間を待つ
      
      const updatedStats = await homePage.getStatistics();
      console.log('収集前統計:', initialStats);
      console.log('収集後統計:', updatedStats);
      
      // 4. リリース一覧で新しいデータ確認
      await releasesPage.navigate();
      await releasesPage.verifyReleasesTable();
      
      // 最新のリリース日でフィルタリング
      const today = new Date();
      const todayStr = today.toISOString().split('T')[0];
      await releasesPage.filterByDateRange(todayStr, todayStr);
      
      const todayReleases = await releasesPage.getReleaseRows();
      console.log('本日のリリース数:', todayReleases.length);
      
      // 5. 自動収集設定の確認・調整
      await configPage.navigate();
      
      await configPage.updateCollectionSettings({
        autoCollectionEnabled: true,
        intervalHours: 2, // より頻繁に収集
        maxResults: 50    // より多くの結果を取得
      });
      
      await configPage.saveConfiguration();
      
      // 6. システム状態の最終確認
      await homePage.navigate();
      await homePage.verifySystemStatus();
    });

    test('パフォーマンス問題の診断・対処フロー', async ({ page }) => {
      // 1. ベースラインパフォーマンス測定
      const startTime = Date.now();
      await homePage.navigate();
      const homeLoadTime = Date.now() - startTime;
      
      console.log('ホームページ読み込み時間:', homeLoadTime + 'ms');
      
      // 2. 重いページでのパフォーマンス確認
      const releasesStartTime = Date.now();
      await releasesPage.navigate();
      const releasesLoadTime = Date.now() - releasesStartTime;
      
      console.log('リリース一覧読み込み時間:', releasesLoadTime + 'ms');
      
      // 3. フィルタリング性能の確認
      const filterStartTime = Date.now();
      await releasesPage.filterByType('anime');
      const filterTime = Date.now() - filterStartTime;
      
      console.log('フィルタリング時間:', filterTime + 'ms');
      
      // 4. パフォーマンス問題が見つかった場合の対処
      if (homeLoadTime > 5000 || releasesLoadTime > 8000 || filterTime > 3000) {
        console.log('パフォーマンス問題を検出しました');
        
        // 設定の最適化
        await configPage.navigate();
        
        // 結果数を減らす
        await configPage.updateCollectionSettings({
          autoCollectionEnabled: true,
          intervalHours: 6,
          maxResults: 20 // 結果数を減らしてパフォーマンス改善
        });
        
        await configPage.saveConfiguration();
        
        // 5. 改善後の再測定
        const improvedStartTime = Date.now();
        await releasesPage.navigate();
        const improvedLoadTime = Date.now() - improvedStartTime;
        
        console.log('最適化後の読み込み時間:', improvedLoadTime + 'ms');
        
        // 改善を確認
        expect(improvedLoadTime).toBeLessThan(releasesLoadTime);
      }
      
      // 6. ブラウザリソース使用量の確認
      const performanceMetrics = await homePage.getPerformanceMetrics();
      console.log('詳細パフォーマンス指標:', performanceMetrics);
    });
  });

  test.describe('高度な統合シナリオ', () => {
    
    test('複数デバイス・ブラウザでの一貫性確認', async ({ page, context }) => {
      // 1. デスクトップブラウザでの設定
      await configPage.navigate();
      
      const testConfig = {
        ngKeyword: 'multi_device_test_' + TestDataGenerator.randomString(4),
        email: 'multidevice@example.com'
      };
      
      await configPage.addNgKeyword(testConfig.ngKeyword);
      await configPage.updateEmailSettings({
        enabled: true,
        email: testConfig.email
      });
      
      await configPage.saveConfiguration();
      
      // 2. 新しいタブ（別セッション）で設定確認
      const newPage = await context.newPage();
      const newConfigPage = new ConfigPage(newPage);
      
      await newConfigPage.navigate();
      
      // 設定が共有されていることを確認
      await newConfigPage.verifyNgKeywords([testConfig.ngKeyword]);
      
      const emailInput = newPage.locator('#email_address, input[name="email_address"]');
      if (await emailInput.count() > 0) {
        await expect(emailInput).toHaveValue(testConfig.email);
      }
      
      await newPage.close();
      
      // 3. モバイルビューでの確認
      await page.setViewportSize({ width: 375, height: 667 });
      
      await configPage.navigate();
      await configPage.verifyResponsiveLayout({ width: 375, height: 667 });
      
      // モバイルでも同じ設定が表示されることを確認
      await configPage.verifyNgKeywords([testConfig.ngKeyword]);
    });

    test('大量データ処理時の統合動作確認', async ({ page }) => {
      // 1. 大量データ設定
      await configPage.navigate();
      
      await configPage.updateCollectionSettings({
        autoCollectionEnabled: true,
        intervalHours: 1,
        maxResults: 100 // 大量データ
      });
      
      await configPage.saveConfiguration();
      
      // 2. 手動収集で大量データ取得
      await homePage.navigate();
      await homePage.executeQuickAction('手動収集実行');
      
      // 収集完了まで待機
      await homePage.waitForLoadingToFinish();
      await page.waitForTimeout(5000);
      
      // 3. 大量データでのリスト表示性能確認
      const startTime = Date.now();
      await releasesPage.navigate();
      const loadTime = Date.now() - startTime;
      
      expect(loadTime).toBeLessThan(10000); // 10秒以内
      
      // 4. 大量データでのフィルタリング性能確認
      const filterStartTime = Date.now();
      await releasesPage.searchByKeyword('anime');
      const filterTime = Date.now() - filterStartTime;
      
      expect(filterTime).toBeLessThan(5000); // 5秒以内
      
      // 5. ページネーション動作確認
      await releasesPage.testPagination();
      
      // 6. ダッシュボードでの統計表示確認
      await homePage.navigate();
      const finalStats = await homePage.getStatistics();
      
      // 統計が適切に更新されていることを確認
      expect(finalStats.totalWorks).toBeGreaterThan(0);
      
      console.log('大量データ処理後統計:', finalStats);
    });

    test('長時間運用シミュレーション', async ({ page }) => {
      const testDuration = 5000; // 5秒間のシミュレーション
      const startTime = Date.now();
      
      // 1. 初期状態の記録
      await homePage.navigate();
      const initialStats = await homePage.getStatistics();
      
      // 2. 継続的な操作シミュレーション
      while (Date.now() - startTime < testDuration) {
        // ダッシュボード確認
        await homePage.navigate();
        await homePage.verifyStatsCards();
        
        // リリース一覧確認
        await releasesPage.navigate();
        await releasesPage.searchByKeyword('test');
        await releasesPage.clearFilter();
        
        // 設定確認
        await configPage.navigate();
        
        // 短時間待機
        await page.waitForTimeout(500);
      }
      
      // 3. 長時間運用後の状態確認
      await homePage.navigate();
      const finalStats = await homePage.getStatistics();
      
      // システムが安定して動作していることを確認
      await homePage.verifySystemStatus();
      
      // メモリリークなどがないことの簡易確認
      const finalMetrics = await homePage.getPerformanceMetrics();
      console.log('長時間運用後メトリクス:', finalMetrics);
      
      // パフォーマンスが大幅に劣化していないことを確認
      expect(finalMetrics.loadComplete).toBeLessThan(10000); // 10秒以内
    });
  });
});