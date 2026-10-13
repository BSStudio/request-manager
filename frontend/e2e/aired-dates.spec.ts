import type { Page } from '@playwright/test';
import { format, setDate, subDays } from 'date-fns';

import { expect, loginAs, test } from './fixtures';

test.use({ storageState: loginAs('admin.aladar') });

const videoSave = /\/api\/v1\/admin\/requests\/\d+\/videos\/\d+$/;

// The seeded 'Állásbörze promóvideó', which only this spec changes. Found
// through the API: the request list only shows the current semester.
async function openVideo(page: Page) {
  const response = await page.request.get(
    '/api/v1/admin/requests?search=Állásbörze',
  );
  const { results } = (await response.json()) as {
    results: { id: number; title: string }[];
  };
  const request = results.find(({ title }) => title === 'Állásbörze');
  if (!request) throw new Error('The seed has no request called Állásbörze.');
  await page.goto(`/admin/requests/${request.id}`);
  await page.getByRole('tab', { name: 'Videók' }).click();
  await page.getByRole('link', { name: 'Ugrás a videóhoz' }).click();
}

test('adds and removes the days a video aired', async ({ page }) => {
  const seeded = [50, 45].map((days) =>
    format(subDays(new Date(), days), 'yyyy-MM-dd'),
  );
  const added = format(setDate(new Date(), 15), 'yyyy-MM-dd');
  await openVideo(page);
  const aired = page.getByRole('listitem').filter({
    has: page.getByText('Adásba került', { exact: true }),
  });
  const dialog = page.getByRole('dialog', {
    name: 'Adásba kerülés hozzáadása',
  });
  const save = dialog.getByRole('button', { name: 'Mentés' });

  async function addDay() {
    await aired.getByRole('button', { name: 'Hozzáadás' }).click();
    await expect(save).toBeDisabled();
    // The 15th is never one of the other months' days the calendar shows.
    await dialog.getByRole('gridcell').filter({ hasText: /^15$/ }).click();
    await save.click();
  }

  for (const day of seeded) await expect(aired).toContainText(day);

  await page.route(videoSave, (route) =>
    route.request().method() === 'PATCH'
      ? route.fulfill({ body: 'Server Error', status: 500 })
      : route.continue(),
  );
  await addDay();
  await expect(page.getByText('Hiba').first()).toBeVisible();
  await dialog.getByRole('button', { name: 'Mégsem' }).click();
  await expect(aired).not.toContainText(added);
  await page.unroute(videoSave);

  await addDay();
  await expect(dialog).toBeHidden();
  await addDay();
  await expect(dialog).toBeHidden();
  await page.reload();
  await expect(aired.getByText(added, { exact: true })).toHaveCount(1);

  for (const day of [...seeded, added]) {
    await aired.getByRole('button', { name: `${day} törlése` }).click();
    await expect(aired.getByText(day, { exact: true })).toHaveCount(0);
  }
  await expect(aired).toContainText('Nem került még adásba');
});
