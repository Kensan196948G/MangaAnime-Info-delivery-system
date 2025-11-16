const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  console.log('📡 収集設定ページを開いています...');
  await page.goto('http://192.168.3.135:3030/collection-settings');
  
  // ページが完全に読み込まれるまで待機
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);
  
  console.log('\n=== DOM値の確認 ===');
  const apiTotal = await page.textContent('#api-total-items');
  const apiSuccess = await page.textContent('#api-avg-success');
  const apiResponse = await page.textContent('#api-avg-response');
  const rssTotal = await page.textContent('#rss-total-items');
  const rssSuccess = await page.textContent('#rss-avg-success');
  
  console.log('API総取得数:', apiTotal);
  console.log('API平均成功率:', apiSuccess);
  console.log('API平均レスポンス:', apiResponse);
  console.log('RSS総取得数:', rssTotal);
  console.log('RSS平均成功率:', rssSuccess);
  
  console.log('\n=== JavaScriptファイルの確認 ===');
  const scripts = await page.evaluate(() => {
    const scripts = Array.from(document.querySelectorAll('script[src*="collection-settings"]'));
    return scripts.map(s => s.src);
  });
  console.log('JavaScript URL:', scripts[0]);
  
  console.log('\n=== HTMLソースの確認 ===');
  const htmlSource = await page.evaluate(() => {
    const span = document.getElementById('api-total-items');
    return span ? span.outerHTML : 'not found';
  });
  console.log('HTMLソース:', htmlSource);
  
  console.log('\n=== 問題診断 ===');
  if (apiTotal.includes('0件') || apiTotal === '0') {
    console.log('❌ 問題確認: DOM値が「0件」です');
    console.log('   原因: JavaScriptが古いバージョンをキャッシュしている');
    console.log('   HTMLソースは正しいが、JavaScriptが値を上書きしています');
  } else if (apiTotal.includes('12690件') || apiTotal.includes('12690')) {
    console.log('✅ 正常: 統計が正しく表示されています！');
    console.log('   API総取得数: 12690件 ✓');
  } else {
    console.log('⚠️  予期しない値:', apiTotal);
  }
  
  // スクリーンショットを保存
  await page.screenshot({ path: '/tmp/collection-settings-screenshot.png', fullPage: true });
  console.log('\n📸 スクリーンショット保存: /tmp/collection-settings-screenshot.png');
  
  await browser.close();
  
  console.log('\n✅ 診断完了');
})();
