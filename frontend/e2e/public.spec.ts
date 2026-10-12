import { expect, test } from './fixtures';

test('the home page loads', async ({ page }) => {
  await page.goto('/');

  await expect(
    page.getByRole('heading', { level: 1, name: /mi megörökítjük/ }),
  ).toBeVisible();
});

const providers = [
  ['Belépés AuthSCH-val', 'https://auth.sch.bme.hu/site/login'],
  ['Belépés Google-fiókkal', 'https://accounts.google.com/o/oauth2/v2/auth'],
  [
    'Belépés Microsoft-fiókkal',
    'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
  ],
  ['Belépés BSS-fiókkal', 'https://login.bsstudio.hu/application/o/authorize/'],
];

for (const [label, url] of providers) {
  test(`"${label}" sends you to the provider`, async ({ page }) => {
    await page.goto('/login');
    // The fixture blocks the provider, so the request is only observed.
    const request = page.waitForRequest((request) =>
      request.url().startsWith(`${url}?`),
    );

    await page.getByRole('button', { name: label }).click();

    const params = new URL((await request).url()).searchParams;
    expect(params.get('client_id')).toBeTruthy();
  });
}

test('the legal pages load', async ({ page }) => {
  await page.goto('/privacy');
  await expect(
    page.getByRole('heading', { level: 1, name: 'Adatvédelmi irányelvek' }),
  ).toBeVisible();

  await page.goto('/terms');
  await expect(
    page.getByRole('heading', { level: 1, name: 'Szolgáltatási feltételek' }),
  ).toBeVisible();
});

test('an unknown page shows the 404 page', async ({ page }) => {
  await page.goto('/nincs-ilyen-oldal');

  await expect(page.getByRole('heading', { name: 'Adásszünet' })).toBeVisible();
});
