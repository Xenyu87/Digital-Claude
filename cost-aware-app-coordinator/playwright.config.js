// @ts-check
const { defineConfig, devices } = require('@playwright/test');
const path = require('path');

const visualFixture = path.join(__dirname, 'tests/fixtures/visual-blueprint-app');

module.exports = defineConfig({
  testDir: './tests/visual',
  timeout: 30000,
  expect: {
    timeout: 8000,
  },
  use: {
    baseURL: 'http://127.0.0.1:3102',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    viewport: { width: 1440, height: 950 },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: `python3 scripts/serve_dashboard.py --host 127.0.0.1 --port 3102 --interval 999 --project ${visualFixture} --no-open`,
    url: 'http://127.0.0.1:3102/reports/skill-dashboard.html',
    reuseExistingServer: false,
    timeout: 20000,
  },
});
