import { endOfMonth, format, startOfMonth, subMonths } from 'date-fns';

import { expect, loginAs, test } from './fixtures';

test.use({
  permissions: ['clipboard-read', 'clipboard-write'],
  storageState: loginAs('gyarto.gabor'),
});

// A fixed report, so the test does not depend on which seeded events fall
// into last month.
const report = {
  requests: [
    { date: '2026-08-31', id: 1, title: 'Kari napok' },
    { date: '2026-09-04', id: 2, title: 'Kari gólyabál' },
  ],
  videos: [],
};

test('copies last month with and without dates', async ({ page }) => {
  const lastMonth = subMonths(new Date(), 1);
  let query: URLSearchParams | undefined;
  await page.route(
    (url) => url.pathname === '/api/v1/admin/report',
    async (route) => {
      query = new URL(route.request().url()).searchParams;
      await route.fulfill({ json: report });
    },
  );
  const requests = page.getByRole('region', { name: 'Felkérések' });
  // Windows hands the lines back with \r\n.
  const copied = async () =>
    (await page.evaluate(() => navigator.clipboard.readText())).replaceAll(
      '\r\n',
      '\n',
    );

  await page.goto('/admin/requests/report');

  await expect(requests).toContainText('Felkérések (2)');
  expect(query?.get('date_after')).toBe(
    format(startOfMonth(lastMonth), 'yyyy-MM-dd'),
  );
  expect(query?.get('date_before')).toBe(
    format(endOfMonth(lastMonth), 'yyyy-MM-dd'),
  );
  await requests.getByRole('button', { name: 'Másolás' }).click();
  await expect
    .poll(copied)
    .toBe('2026. 08. 31. Kari napok\n2026. 09. 04. Kari gólyabál');

  await page.getByText('Dátumok', { exact: true }).click();
  await requests.getByRole('button', { name: 'Másolás' }).click();
  await expect.poll(copied).toBe('Kari napok\nKari gólyabál');

  const videos = page.getByRole('region', { name: 'Vágások' });
  await expect(videos).toContainText('Ebben a hónapban nem volt vágás.');
  await expect(videos.getByRole('button', { name: 'Másolás' })).toBeDisabled();
});

test('tells when copying fails', async ({ page }) => {
  await page.route(
    (url) => url.pathname === '/api/v1/admin/report',
    (route) => route.fulfill({ json: report }),
  );
  await page.goto('/admin/requests/report');
  await page.evaluate(() => {
    navigator.clipboard.writeText = () => Promise.reject(new Error('Denied'));
  });

  await page
    .getByRole('region', { name: 'Felkérések' })
    .getByRole('button', { name: 'Másolás' })
    .click();

  await expect(
    page.getByText('Nem sikerült a vágólapra másolni.'),
  ).toBeVisible();
});
