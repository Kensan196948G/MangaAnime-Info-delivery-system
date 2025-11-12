import { FullConfig } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Playwright E2E テスト用グローバルセットアップ
 * 
 * テスト実行前の環境準備を行います：
 * - テスト用データベースの初期化
 * - テストレポートディレクトリの作成
 * - テスト用設定ファイルの準備
 */

async function globalSetup(config: FullConfig) {
  console.log('🚀 E2Eテストのグローバルセットアップを開始します...');
  
  const projectRoot = process.cwd();
  
  try {
    // テストレポートディレクトリの作成
    const reportDirs = [
      'tests/e2e/reports',
      'tests/e2e/reports/html',
      'tests/e2e/test-results',
      'tests/e2e/screenshots',
      'tests/e2e/videos'
    ];
    
    for (const dir of reportDirs) {
      const fullPath = path.join(projectRoot, dir);
      if (!fs.existsSync(fullPath)) {
        fs.mkdirSync(fullPath, { recursive: true });
        console.log(`✅ ディレクトリを作成: ${dir}`);
      }
    }
    
    // テスト用データベースファイルの削除（既存の場合）
    const testDbPath = path.join(projectRoot, 'test_e2e.db');
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
      console.log('🗑️  既存のテスト用データベースを削除しました');
    }
    
    // テスト用設定ファイルの作成
    const testConfig = {
      database_url: 'test_e2e.db',
      gmail: {
        enabled: false,  // テスト時は実際のメール送信を無効化
        user_email: 'test@example.com',
        app_password: 'test_password'
      },
      calendar: {
        enabled: false,  // テスト時は実際のカレンダー操作を無効化
        calendar_id: 'test_calendar'
      },
      filtering: {
        ng_keywords: ['テスト除外', 'NG_TEST']
      },
      collection: {
        auto_collection_enabled: true,
        collection_interval_hours: 1
      },
      notification: {
        test_mode: true  // テストモードを有効化
      }
    };
    
    const testConfigPath = path.join(projectRoot, 'test_config_e2e.json');
    fs.writeFileSync(testConfigPath, JSON.stringify(testConfig, null, 2));
    console.log('📝 テスト用設定ファイルを作成しました');
    
    // 環境変数の設定
    process.env.TESTING = 'true';
    process.env.CONFIG_FILE = testConfigPath;
    process.env.DATABASE_URL = testDbPath;
    
    console.log('✅ E2Eテストのグローバルセットアップが完了しました');
    
  } catch (error) {
    console.error('❌ グローバルセットアップでエラーが発生:', error);
    throw error;
  }
}

export default globalSetup;