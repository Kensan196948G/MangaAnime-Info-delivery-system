const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('http://192.168.3.135:3030/collection-settings');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  console.log('=== カード内の全テキスト確認 ===');
  const cardTexts = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.source-config-card'));
    return cards.slice(0, 2).map((card, idx) => {
      return {
        title: card.querySelector('h5')?.textContent,
        fullText: card.textContent.replace(/\s+/g, ' ').substring(0, 400)
      };
    });
  });
  
  cardTexts.forEach((card, idx) => {
    console.log('\nカード' + (idx + 1) + ': ' + card.title);
    console.log('内容:', card.fullText);
  });
  
  await browser.close();
})();
