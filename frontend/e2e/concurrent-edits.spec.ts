import type { Page } from '@playwright/test';
import { format } from 'date-fns';

import { expect, loginAs, test } from './fixtures';
import { adminRequestPath } from './helpers';

test.use({ storageState: loginAs('admin.aladar') });

// The seeded 'Sportnap' and its video, which only this spec changes.
async function save(page: Page, toast: string) {
  await page.getByRole('button', { exact: true, name: 'Mentés' }).click();
  await expect(page.getByText(toast)).toBeVisible();
}

test('keeps a request change saved while another form was open', async ({
  context,
  page,
}) => {
  const requestPath = await adminRequestPath(page, 'Sportnap');
  const other = await context.newPage();
  await page.goto(`${requestPath}/edit`);
  await other.goto(`${requestPath}/edit`);

  await other.getByLabel('Helyszín').fill('BME sportcsarnok');
  await save(other, 'Felkérés módosítva');

  const deadline = new Date();
  await page.getByLabel('Határidő').fill(format(deadline, 'yyyy.MM.dd'));
  await page.getByLabel('Határidő').press('Tab');
  await save(page, 'Felkérés módosítva');

  const response = await page.request.get(`/api/v1${requestPath}`);
  await expect(response).toBeOK();
  expect(await response.json()).toMatchObject({
    deadline: format(deadline, 'yyyy-MM-dd'),
    place: 'BME sportcsarnok',
  });
});

test('keeps a video change saved while another form was open', async ({
  context,
  page,
}) => {
  await page.goto(await adminRequestPath(page, 'Sportnap'));
  await page.getByRole('tab', { name: 'Videók' }).click();
  await page.getByRole('link', { name: 'Ugrás a videóhoz' }).click();
  await expect(page).toHaveURL(/\/videos\/\d+$/);
  const videoPath = new URL(page.url()).pathname;
  const other = await context.newPage();
  await page.goto(`${videoPath}/edit`);
  await other.goto(`${videoPath}/edit`);

  const url = 'https://example.com/videok/sportnap';
  await other.getByLabel('Videó elérési útja').fill(url);
  await save(other, 'Videó módosítva');

  await page.getByLabel('Videó címe').fill('Sportnap 2026');
  await save(page, 'Videó módosítva');

  const response = await page.request.get(`/api/v1${videoPath}`);
  await expect(response).toBeOK();
  expect(await response.json()).toMatchObject({
    additional_data: { publishing: { website: url } },
    title: 'Sportnap 2026',
  });
});
