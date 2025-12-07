const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('http://192.168.3.135:3030/collection-settings');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);

  console.log('=== 接続ステータス確認 ===');

  // Get all status badges
  const statuses = await page.evaluate(() => {
    const badges = Array.from(document.querySelectorAll('.connection-status'));
    return badges.slice(0, 6).map((badge, idx) => {
      const cardTitle = badge.closest('.source-config-card')?.querySelector('h5')?.textContent;
      return {
        card: cardTitle || 'Unknown',
        status: badge.textContent.trim(),
        class: badge.className
      };
    });
  });

  statuses.forEach((item, idx) => {
    console.log(`\nカード${idx + 1}: ${item.card}`);
    console.log(`ステータス: ${item.status}`);
    console.log(`クラス: ${item.class}`);
  });

  await browser.close();
})();
