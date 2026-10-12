import type { Page } from '@playwright/test';

import { expect, loginAs, test } from './fixtures';
import { requestLink } from './helpers';

// Teszt Elek's own message, which no other test reads.
const seeded = 'Sajnos elmarad a fórum, de köszönjük, hogy elvállaltátok!';
const edited = 'Sajnos elmarad a fórum, de tavasszal újra jelentkezünk!';

test.use({ storageState: loginAs('teszt.elek') });

async function openThread(page: Page) {
  await page.goto('/my-requests');
  await requestLink(page, 'Hallgatói fórum').click();
  return page.getByRole('list', { name: 'Üzenetek' });
}

test('edits their message', async ({ page }) => {
  const thread = await openThread(page);
  const message = thread.getByRole('listitem').filter({ hasText: seeded });
  const text = page.getByLabel('Üzenet szerkesztése');

  await message.getByRole('button', { name: 'Műveletek' }).click();
  await page.getByRole('menuitem', { name: 'Szerkesztés' }).click();
  await text.fill(edited);
  await page.getByRole('button', { name: 'Mégsem' }).click();
  await expect(thread).toContainText(seeded);

  await message.getByRole('button', { name: 'Műveletek' }).click();
  await page.getByRole('menuitem', { name: 'Szerkesztés' }).click();
  await text.fill(edited);
  await page.getByRole('button', { name: 'Mentés' }).click();
  await expect(thread).toContainText(edited);

  await page.reload();
  await expect(thread).toContainText(edited);
  await expect(thread).not.toContainText(seeded);
});

test('deletes their message', async ({ page }) => {
  const thread = await openThread(page);
  await expect(thread).toContainText(edited);

  await thread.getByRole('button', { name: 'Műveletek' }).click();
  await page.getByRole('menuitem', { name: 'Törlés' }).click();
  await page
    .getByRole('alertdialog', { name: 'Törlöd az üzenetet?' })
    .getByRole('button', { name: 'Törlés' })
    .click();
  await expect(
    page.getByText('Üzenetet írhatsz nekünk a felkérésedhez'),
  ).toBeVisible();

  await page.reload();
  await expect(
    page.getByText('Üzenetet írhatsz nekünk a felkérésedhez'),
  ).toBeVisible();
});
