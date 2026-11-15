// Loads the exported Web build in headless Chromium and waits for the check line.
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 360, height: 640 } });
  const logs = [];
  page.on('console', m => logs.push(m.text()));
  page.on('pageerror', e => logs.push('PAGEERROR ' + e.message));
  await page.goto(process.argv[2]);
  const t0 = Date.now();
  while (Date.now() - t0 < 90000 && !logs.some(l => l.includes('EXPORT_SMOKE_OK'))) await page.waitForTimeout(500);
  await browser.close();
  const hit = logs.find(l => l.includes('EXPORT_SMOKE_OK'));
  console.log(hit || logs.slice(0, 15).join('\n'));
  process.exit(hit ? 0 : 1);
})();
