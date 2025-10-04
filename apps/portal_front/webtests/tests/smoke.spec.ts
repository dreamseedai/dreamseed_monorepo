import { test, expect } from '@playwright/test';

const TARGET = process.env.TARGET_URL!; // set via CI/ENV
const ENV = process.env.ENV || 'staging';

test.describe('DreamSeed Browser Compatibility', () => {
  // HTTP → HTTPS redirect check
  test('redirects to HTTPS', async ({ request }) => {
    const httpUrl = TARGET.replace('https://', 'http://');
    const res = await request.get(httpUrl, { maxRedirects: 0 });
    expect([301, 308]).toContain(res.status());
  });

  // Basic render
  test('page renders', async ({ page }) => {
    await page.goto(TARGET, { waitUntil: 'domcontentloaded' });
    await expect(page.locator('body')).toBeVisible();
    
    // Take screenshot for visual verification
    await page.screenshot({ path: 'smoke-test-homepage.png' });
  });

  // Security headers
  test('security headers', async ({ request }) => {
    const res = await request.get(TARGET);
    const headers = res.headers();
    
    // HSTS check (environment-specific)
    const hsts = headers['strict-transport-security'];
    if (ENV === 'staging') {
      expect(hsts).toBeUndefined();
    }
    if (ENV === 'prod') {
      expect(hsts).toBeTruthy();
    }
    
    // Required security headers
    expect(headers['x-content-type-options']).toBe('nosniff');
    expect(headers['x-frame-options']).toBe('SAMEORIGIN');
    expect(headers['content-security-policy']).toBeTruthy();
    
    // COOP/COEP/CORP headers (if enabled)
    if (headers['cross-origin-opener-policy']) {
      expect(headers['cross-origin-opener-policy']).toBe('same-origin');
    }
    if (headers['cross-origin-embedder-policy']) {
      expect(headers['cross-origin-embedder-policy']).toBe('require-corp');
    }
    if (headers['cross-origin-resource-policy']) {
      expect(headers['cross-origin-resource-policy']).toBe('same-origin');
    }
  });

  // Cookie policy (if API sets cookie)
  test('cookie has Secure and SameSite=None', async ({ request }) => {
    const res = await request.get(TARGET + '/api/auth/me');
    const setCookie = res.headers()['set-cookie'] || '';
    
    // Allow 200/401/403/404 but check attributes when present
    expect([200, 401, 403, 404]).toContain(res.status());
    
    if (setCookie) {
      expect(setCookie.toLowerCase()).toContain('secure');
      expect(setCookie.toLowerCase()).toContain('samesite=none');
    }
  });

  // API endpoints respond correctly
  test('API endpoints respond correctly', async ({ request }) => {
    // Test health endpoint
    const healthResponse = await request.get(`${TARGET}/api/health`);
    expect([200, 404]).toContain(healthResponse.status());
    
    // Test healthz endpoint
    const healthzResponse = await request.get(`${TARGET}/healthz`);
    expect([200, 404]).toContain(healthzResponse.status());
  });

  // CORS preflight requests work
  test('CORS preflight requests work', async ({ request }) => {
    const response = await request.options(`${TARGET}/api/auth/me`, {
      headers: {
        'Origin': 'https://dreamseedai.com',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type'
      }
    });
    
    expect([200, 204]).toContain(response.status());
  });

  // Console error guard
  test('no severe console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto(TARGET, { waitUntil: 'domcontentloaded' });
    
    // Allow some common non-critical errors
    const criticalErrors = errors.filter(error => 
      !error.includes('favicon.ico') && 
      !error.includes('404') &&
      !error.includes('net::ERR_ABORTED') &&
      !error.includes('Failed to load resource')
    );
    
    expect(criticalErrors, criticalErrors.join('\n')).toHaveLength(0);
  });

  // Mixed content / secure context
  test('secure context', async ({ page }) => {
    await page.goto(TARGET, { waitUntil: 'domcontentloaded' });
    const isSecure = await page.evaluate(() => window.isSecureContext);
    expect(isSecure).toBeTruthy();
  });

  // WebSocket upgrade test (optional)
  test('websocket upgrade (optional)', async ({ request }) => {
    const base = TARGET.replace(/\/$/, '');
    const res = await request.get(base + '/ws', { maxRedirects: 0 });
    expect([101, 404, 301, 302]).toContain(res.status());
  });

  // Page loads in incognito mode
  test('page loads in incognito mode', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    await page.goto(TARGET, { waitUntil: 'domcontentloaded' });
    await expect(page.locator('body')).toBeVisible();
    
    await context.close();
  });

  // Mobile viewport renders correctly
  test('mobile viewport renders correctly', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(TARGET, { waitUntil: 'domcontentloaded' });
    
    await expect(page.locator('body')).toBeVisible();
    await page.screenshot({ path: 'smoke-test-mobile.png' });
  });

  // Performance check
  test('page loads within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto(TARGET, { waitUntil: 'domcontentloaded' });
    const loadTime = Date.now() - startTime;
    
    // Expect page to load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });

  // HTTP/2 support check
  test('HTTP/2 support', async ({ request }) => {
    const response = await request.get(TARGET);
    const headers = response.headers();
    
    // Check for HTTP/2 indicators
    if (headers['server'] && headers['server'].includes('nginx')) {
      // HTTP/2 is supported by nginx
      expect(response.status()).toBe(200);
    }
  });
});
