import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: false });
const context = await browser.newContext();
const page = await context.newPage();

// Enable console logging
page.on('console', msg => console.log('BROWSER:', msg.text()));
page.on('request', req => {
  if (req.url().includes('/sessions/') && req.method() === 'POST') {
    console.log('REQUEST:', req.method(), req.url());
  }
});
page.on('response', res => {
  if (res.url().includes('/sessions/') && res.request().method() === 'POST') {
    console.log('RESPONSE:', res.status(), res.url());
  }
});

// Navigate to login page
await page.goto('https://regen.gaiaai.xyz/registry-review');
await page.waitForTimeout(2000);

// Click test login button
const testLoginBtn = page.getByRole('button', { name: 'Test Login' });
if (await testLoginBtn.isVisible()) {
  await testLoginBtn.click();
  await page.waitForTimeout(2000);
}

// Click on a session
await page.click('text=Botany Farm');
await page.waitForTimeout(3000);

// Check if Extract Evidence button exists and click it
const extractBtn = page.getByRole('button', { name: /Extract Evidence/i });
if (await extractBtn.isVisible()) {
  console.log('Found Extract Evidence button, clicking...');
  await extractBtn.click();
  console.log('Clicked Extract Evidence, waiting for network requests...');
  await page.waitForTimeout(10000);
} else {
  console.log('Extract Evidence button not found');
}

await browser.close();
