import { defineConfig } from '@playwright/test';
const allowSelfSigned = process.env.ALLOW_SELF_SIGNED === 'true';
export default defineConfig({
  timeout: 45_000,
  use: {
    headless: true,
    ignoreHTTPSErrors: allowSelfSigned, // only set true for simulation (8443/self-signed)
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list']
  ],
});

