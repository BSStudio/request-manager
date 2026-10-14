import { readFile } from 'fs/promises';

import type { BrowserContext } from '@playwright/test';

import { expect, loginAs, test } from './fixtures';
import { requestLink } from './helpers';

type StorageState = Awaited<ReturnType<BrowserContext['storageState']>>;

const provider = 'https://login.bsstudio.hu/application/o/authorize/';

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
  const { id } = (await (await page.request.get('/api/v1/me')).json()) as {
    id: number;
  };
  const isLogin = (url: URL) => url.pathname === '/api/v1/login/social';
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

  const authorization = page.waitForRequest((request) =>
    request.url().startsWith(`${provider}?`),
  );
  await page.getByRole('button', { name: 'Belépés BSS-fiókkal' }).click();
  const state = new URL((await authorization).url()).searchParams.get('state');

  const login = page.waitForRequest((request) =>
    isLogin(new URL(request.url())),
  );
  await page.goto(
    `/redirect?${new URLSearchParams({ code: 'teszt-kod', state: state ?? '' })}`,
  );
  expect((await login).postDataJSON()).toMatchObject({
    code: 'teszt-kod',
    provider: 'bss-login',
  });
  await expect(page).toHaveURL(/\/my-requests$/);
  await expect(requestLink(page, 'Őszi szakmai konferencia')).toBeVisible();
});

test('a cancelled login goes back to the login page', async ({ page }) => {
  await page.goto('/redirect?error=access_denied');

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByText('A bejelentkezés megszakadt.')).toBeVisible();
});
