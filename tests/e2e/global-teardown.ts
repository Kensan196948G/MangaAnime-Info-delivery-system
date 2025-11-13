import { FullConfig } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Playwright E2E テスト用グローバルティアダウン
 * 
 * テスト実行後のクリーンアップを行います：
 * - テスト用データベースのクリーンアップ
 * - 一時ファイルの削除
 * - テスト結果のサマリー出力
 */

async function globalTeardown(config: FullConfig) {
  console.log('🧹 E2Eテストのグローバルティアダウンを開始します...');
  
  const projectRoot = process.cwd();
  
  try {
    // テスト用データベースの削除
    const testDbPath = path.join(projectRoot, 'test_e2e.db');
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
      console.log('🗑️  テスト用データベースを削除しました');
    }
    
    // テスト用設定ファイルの削除
    const testConfigPath = path.join(projectRoot, 'test_config_e2e.json');
    if (fs.existsSync(testConfigPath)) {
      fs.unlinkSync(testConfigPath);
      console.log('🗑️  テスト用設定ファイルを削除しました');
    }
    
    // テスト結果のサマリー生成
    const testResultsPath = path.join(projectRoot, 'tests/e2e/reports/test-results.json');
    if (fs.existsSync(testResultsPath)) {
      try {
        const results = JSON.parse(fs.readFileSync(testResultsPath, 'utf-8'));
        const summary = {
          timestamp: new Date().toISOString(),
          total_tests: results.stats?.total || 0,
          passed: results.stats?.passed || 0,
          failed: results.stats?.failed || 0,
          skipped: results.stats?.skipped || 0,
          duration: results.stats?.duration || 0,
          success_rate: results.stats?.total > 0 ? 
            ((results.stats?.passed || 0) / results.stats.total * 100).toFixed(2) + '%' : 
            '0%'
        };
        
        const summaryPath = path.join(projectRoot, 'tests/e2e/reports/test-summary.json');
        fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
        
        console.log('📊 テスト結果サマリー:');
        console.log(`   合計テスト数: ${summary.total_tests}`);
        console.log(`   成功: ${summary.passed}`);
        console.log(`   失敗: ${summary.failed}`);
        console.log(`   スキップ: ${summary.skipped}`);
        console.log(`   成功率: ${summary.success_rate}`);
        console.log(`   実行時間: ${(summary.duration / 1000).toFixed(2)}秒`);
      } catch (error) {
        console.warn('⚠️  テスト結果の解析でエラーが発生:', error.message);
      }
    }
    
    // 環境変数のクリーンアップ
    delete process.env.TESTING;
    delete process.env.CONFIG_FILE;
    delete process.env.DATABASE_URL;
    
    console.log('✅ E2Eテストのグローバルティアダウンが完了しました');
    
  } catch (error) {
    console.error('❌ グローバルティアダウンでエラーが発生:', error);
    // ティアダウンではエラーを投げずに警告として扱う
  }
}

export default globalTeardown;