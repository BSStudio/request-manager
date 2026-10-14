import { createHash } from 'crypto';
import { readFile } from 'fs/promises';

import type { BrowserContext, Page } from '@playwright/test';

import { expect, loginAs, test } from './fixtures';
import { requestLink } from './helpers';

type StorageState = Awaited<ReturnType<BrowserContext['storageState']>>;

const isLogin = (url: URL) => url.pathname === '/api/v1/login/social';

// The fixture blocks the provider, so what it would get is only observed.
async function startLogin(page: Page) {
  const authorization = page.waitForRequest((request) =>
    request
      .url()
      .startsWith('https://login.bsstudio.hu/application/o/authorize/?'),
  );
  await page.getByRole('button', { name: 'Belépés BSS-fiókkal' }).click();
  const params = new URL((await authorization).url()).searchParams;
  const state = params.get('state');
  if (!state) throw new Error('The login sent no state to the provider.');
  return { hashedNonce: params.get('nonce'), state };
}

test('my requests ask for a login and open after it', async ({
  context,
  page,
}) => {
  // Anna's session without her cached user, so the app takes her for a
  // visitor. No provider can redeem a code here, so the login is faked.
  const { cookies } = JSON.parse(
    await readFile(loginAs('minta.anna'), 'utf8'),
  ) as StorageState;
  await context.addCookies(cookies);
  const me = await page.request.get('/api/v1/me');
  await expect(me).toBeOK();
  const { id } = (await me.json()) as { id: number };
  await page.route(isLogin, (route) =>
    route.fulfill({
      json: {
        avatar_url: null,
        groups: [],
        id,
        name: 'Minta Anna',
        role: 'user',
      },
    }),
  );

  await page.goto('/my-requests');
  await expect(page).toHaveURL(/\/login$/);
  const { hashedNonce, state } = await startLogin(page);

  const login = page.waitForRequest((request) =>
    isLogin(new URL(request.url())),
  );
  await page.goto(
    `/redirect?${new URLSearchParams({ code: 'teszt-kod', state })}`,
  );
  const body = (await login).postDataJSON() as Record<string, string>;
  expect(body).toMatchObject({ code: 'teszt-kod', provider: 'bss-login' });
  // The provider only saw the hash of the nonce the backend gets.
  expect(createHash('sha256').update(body.nonce).digest('hex')).toBe(
    hashedNonce,
  );
  await expect(page).toHaveURL(/\/my-requests$/);
  await expect(requestLink(page, 'Őszi szakmai konferencia')).toBeVisible();
});

test('a cancelled login goes back to the login page', async ({ page }) => {
  await page.goto('/login');
  const { state } = await startLogin(page);

  await page.goto(
    `/redirect?${new URLSearchParams({ error: 'access_denied', state })}`,
  );
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByText('A bejelentkezés megszakadt.')).toBeVisible();
});
