const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  console.log('📡 収集設定ページを開いています...');
  await page.goto('http://192.168.3.135:3030/collection-settings');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  console.log('\n=== セクションヘッダーの統計サマリー ===');
  const apiTotal = await page.textContent('#api-total-items');
  const apiSuccess = await page.textContent('#api-avg-success');
  const rssTotal = await page.textContent('#rss-total-items');
  const rssSuccess = await page.textContent('#rss-avg-success');
  
  console.log('✅ API総取得数:', apiTotal);
  console.log('✅ API平均成功率:', apiSuccess);
  console.log('✅ RSS総取得数:', rssTotal);
  console.log('✅ RSS平均成功率:', rssSuccess);
  
  console.log('\n=== 各カード内の統計表示確認 ===');
  const cardStats = await page.evaluate(() => {
    const statsLabels = Array.from(document.querySelectorAll('.form-label'));
    return statsLabels.filter(label => label.textContent.includes('収集統計')).length;
  });
  
  if (cardStats === 0) {
    console.log('✅ カード内の「収集統計」セクションが削除されました');
  } else {
    console.log('⚠️  まだカード内に「収集統計」が残っています:', cardStats, '個');
  }
  
  console.log('\n=== カード内の設定項目確認 ===');
  const cardLabels = await page.evaluate(() => {
    const labels = Array.from(document.querySelectorAll('.form-label'));
    return labels.map(l => l.textContent.trim()).filter(t => t && !t.includes('統計'));
  });
  console.log('カード内の項目:', cardLabels.slice(0, 10).join(', '), '...');
  
  await page.screenshot({ path: '/tmp/card-display-updated.png', fullPage: true });
  console.log('\n📸 スクリーンショット保存: /tmp/card-display-updated.png');
  
  await browser.close();
  console.log('\n✅ 確認完了');
})();
