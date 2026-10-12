import path from 'path';

import { test as base, expect } from '@playwright/test';

// Turnstile's test key loads its script from Cloudflare; nothing else may leave.
const allowedHosts = ['localhost', 'challenges.cloudflare.com'];

export const test = base.extend({
  page: async ({ page }, use) => {
    const errors: Error[] = [];
    page.on('pageerror', (error) => errors.push(error));
    await page.route(
      (url) =>
        url.protocol.startsWith('http') && !allowedHosts.includes(url.hostname),
      (route) => route.abort(),
    );
    await use(page);
    expect(errors, 'uncaught errors on the page').toEqual([]);
  },
});

export { expect };

// Written by e2e_server for every seeded user before the tests start.
export function loginAs(username: string) {
  return path.join(import.meta.dirname, '.auth', `${username}.json`);
}
