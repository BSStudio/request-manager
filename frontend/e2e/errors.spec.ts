import { expect, loginAs, test } from './fixtures';
import { requestLink } from './helpers';

test.use({ storageState: loginAs('minta.anna') });

function isRequestList(url: URL) {
  return url.pathname === '/api/v1/requests';
}

test('shows an error when the requests fail to load', async ({ page }) => {
  await page.route(isRequestList, (route) =>
    route.fulfill({ body: 'Server Error', status: 500 }),
  );
  await page.goto('/my-requests');
  await expect(
    page.getByText('Nem sikerült betölteni a felkéréseidet.'),
  ).toBeVisible();

  await page.unroute(isRequestList);
  await page.getByRole('button', { name: 'Újrapróbálom' }).click();
  await expect(requestLink(page, 'Őszi szakmai konferencia')).toBeVisible();
});

test('shows an error when the server cannot be reached', async ({ page }) => {
  await page.route(isRequestList, (route) => route.abort('connectionrefused'));
  await page.goto('/my-requests');

  await expect(
    page.getByText('Nem sikerült betölteni a felkéréseidet.'),
  ).toBeVisible();
  await expect(
    page.getByText('Ellenőrizd az internetkapcsolatodat, és próbáld újra!'),
  ).toBeVisible();
});

test('tells when the connection is lost', async ({ context, page }) => {
  await page.goto('/my-requests');
  await expect(requestLink(page, 'Őszi szakmai konferencia')).toBeVisible();
  const offline = page
    .getByRole('status')
    .filter({ hasText: 'Nincs internetkapcsolat' });

  await context.setOffline(true);
  await expect(offline).toBeVisible();

  await context.setOffline(false);
  await expect(offline).toBeHidden();
});

test('shows the 404 page for a request that does not exist', async ({
  page,
}) => {
  await page.goto('/my-requests/999999');

  await expect(page.getByRole('heading', { name: 'Adásszünet' })).toBeVisible();
});

test('sends you to the login page when the session has expired', async ({
  context,
  page,
}) => {
  // The browser still remembers the user, but the server knows no session.
  await context.clearCookies();
  await page.goto('/my-requests');

  await expect(page).toHaveURL(/\/login$/);
  await expect(
    page.getByRole('heading', { name: 'Bejelentkezés' }),
  ).toBeVisible();
});
