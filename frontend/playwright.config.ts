import path from 'path';

import { defineConfig, devices } from '@playwright/test';

const port = 8010;
const authDir = path.join(import.meta.dirname, 'e2e', '.auth');

export default defineConfig({
  forbidOnly: !!process.env.CI,
  fullyParallel: false,
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  retries: 0,
  testDir: 'e2e',
  use: {
    baseURL: `http://localhost:${port}`,
    locale: 'hu-HU',
    screenshot: 'only-on-failure',
    serviceWorkers: 'block',
    timezoneId: 'Europe/Budapest',
    trace: 'retain-on-failure',
  },
  webServer: {
    // e2e_server recreates and seeds the database, so every run starts fresh.
    command: `pnpm --dir ../frontend exec vite build --mode e2e && poetry run python manage.py e2e_server localhost:${port} --storage-state-dir "${authDir}"`,
    cwd: path.join(import.meta.dirname, '..', 'backend'),
    env: {
      DJANGO_SETTINGS_MODULE: 'core.settings.e2e',
      PYTHONUNBUFFERED: '1',
    },
    reuseExistingServer: false,
    stdout: 'pipe',
    timeout: 300_000,
    url: `http://localhost:${port}/`,
  },
  workers: 1,
});
