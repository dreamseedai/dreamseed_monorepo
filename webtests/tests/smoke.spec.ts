import { test, expect } from '@playwright/test';

const TARGET = process.env.TARGET_URL!; // set via CI/ENV
const ENV = process.env.ENV || 'staging';

// HTTP → HTTPS redirect check
test('redirects to HTTPS', async ({ request }) => {
  const HTTP_ORIGIN =
    process.env.HTTP_ORIGIN              // e.g., http://<IP>:8080 (simulation)
    || TARGET.replace(/^https:/, 'http:') // fallback: http same host
           .replace(/:8443\b/, ':8080')   // common sim: 8443→8080
           .replace(/:443\b/, '');        // default https→http(80)

  const res = await request.get(HTTP_ORIGIN, { maxRedirects: 0 });
  // Accept both 301 and 308 as valid permanent redirects
  expect([301, 308]).toContain(res.status());

  const loc = res.headers()['location'] || res.headers()['Location'];
  expect(loc, 'Location header must be present').toBeTruthy();

  // Normalize/parse Location and assert scheme/host correctness
  const redirected = new URL(loc!, HTTP_ORIGIN);
  const targetUrl = new URL(TARGET);

  expect(redirected.protocol).toBe('https:');
  // host includes hostname:port — we want host equality across environments
  expect(redirected.host).toBe(targetUrl.host);
});

// Basic render
test('page renders', async ({ page }) => {
  await page.goto(TARGET, { waitUntil: 'domcontentloaded' });
  await expect(page.locator('body')).toBeVisible();
});

// Security headers
test('security headers', async ({ request }) => {
  const res = await request.get(TARGET);
  const hsts = res.headers()['strict-transport-security'];
  if (ENV === 'staging') expect(hsts).toBeUndefined();
  if (ENV === 'prod') expect(hsts).toBeTruthy();
  expect(res.headers()['x-content-type-options']).toBe('nosniff');
  expect(res.headers()['content-security-policy']).toBeTruthy();
});

// Cookie policy (if API sets cookie)
test('cookie has Secure and SameSite=None', async ({ request }) => {
  const res = await request.get(TARGET + '/api/auth/me');
  const setCookie = res.headers()['set-cookie'] || '';
  // allow 200/401/403/404 but check attributes when present
  expect([200,401,403,404]).toContain(res.status());
  if (setCookie) {
    expect(setCookie.toLowerCase()).toContain('secure');
    expect(setCookie.toLowerCase()).toContain('samesite=none');
  }
});

// Console error guard
test('no severe console errors', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  await page.goto(process.env.TARGET_URL!, { waitUntil: 'domcontentloaded' });
  expect(errors, errors.join('\n')).toHaveLength(0);
});

// Mixed content / secure context
test('secure context', async ({ page }) => {
  await page.goto(process.env.TARGET_URL!, { waitUntil: 'domcontentloaded' });
  const isSecure = await page.evaluate(() => window.isSecureContext);
  expect(isSecure).toBeTruthy();
});

// (Optional) WebSocket upgrade check — only if /ws exists
// Skips gracefully when endpoint missing.
test('websocket upgrade (optional)', async ({ request }) => {
  const base = process.env.TARGET_URL!.replace(/\/$/, '');
  const res = await request.get(base + '/ws', { maxRedirects: 0 });
  expect([101, 404, 301, 302]).toContain(res.status());
});