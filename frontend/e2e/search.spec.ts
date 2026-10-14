import { format } from 'date-fns';

import { expect, loginAs, test } from './fixtures';

test.use({ storageState: loginAs('admin.aladar') });

test('a typed day reaches the request search as that day', async ({ page }) => {
  const today = new Date();
  await page.goto('/admin/search');
  const after = page.getByLabel('Kezdés időpontja későbbi mint', {
    exact: true,
  });
  await after.click();
  await after.pressSequentially(format(today, 'yyyyMMdd'));
  await after.press('Tab');
  await expect(after).toHaveValue(format(today, 'yyyy.MM.dd'));

  const request = page.waitForRequest((request) =>
    request.url().includes('start_datetime_after='),
  );
  await page.getByRole('button', { exact: true, name: 'Keresés' }).click();

  const params = new URL((await request).url()).searchParams;
  expect(params.get('start_datetime_after')).toBe(format(today, 'yyyy-MM-dd'));
});
