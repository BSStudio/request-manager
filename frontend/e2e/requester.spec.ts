import { randomUUID } from 'crypto';

import type { Page } from '@playwright/test';
import { addDays, format, isSameMonth } from 'date-fns';
import { hu } from 'date-fns/locale';

import { expect, loginAs, test } from './fixtures';

async function pickDay(page: Page, label: string, day: Date) {
  await page.getByRole('button', { name: new RegExp(`^${label}`) }).click();
  if (!isSameMonth(day, new Date())) {
    await page
      .getByRole('button', { name: 'Ugrás a következő hónapra' })
      .click();
  }
  // Day buttons are named like "2026. október 26., hétfő".
  await page
    .getByRole('button', { name: format(day, 'PPPP', { locale: hu }) })
    .click();
}

function requestLink(page: Page, title: string) {
  return page
    .getByRole('link')
    .filter({ has: page.getByText(title, { exact: true }) });
}

test.describe('as a requester', () => {
  test.use({ storageState: loginAs('minta.anna') });

  test('submits a request, finds it and messages the studio', async ({
    page,
  }) => {
    const title = `E2E felkérés ${randomUUID().slice(0, 8)}`;
    const message = 'Sziasztok! Kell áramot biztosítanunk a helyszínen?';

    await page.goto('/new-request');
    await page.getByLabel('Az esemény neve').fill(title);
    await pickDay(page, 'Kezdés', addDays(new Date(), 14));
    await page
      .getByRole('textbox', { exact: true, name: 'Kezdés' })
      .fill('18:00');
    await page
      .getByRole('textbox', { exact: true, name: 'Várható befejezés' })
      .fill('22:00');
    await page.getByLabel('Helyszín').fill('Schönherz Kollégium, 17. emelet');
    await page.getByRole('radio', { name: 'Élő közvetítés' }).check();
    await page.getByRole('button', { name: 'Tovább' }).click();
    await page.getByLabel('Megjegyzés').fill('A műsor 18:30-kor kezdődik.');
    await page.getByRole('button', { name: 'Tovább' }).click();
    await page.getByRole('button', { exact: true, name: 'Beküldés' }).click();
    await expect(
      page.getByRole('heading', { name: 'Megkaptuk a felkérésed!' }),
    ).toBeVisible();

    await page.goto('/my-requests');
    await requestLink(page, title).click();
    await expect(
      page.getByRole('heading', { level: 1, name: title }),
    ).toBeVisible();
    await expect(page.getByText('Elbírálás alatt').first()).toBeVisible();

    await page.getByLabel('Új üzenet').fill(message);
    await page.getByRole('button', { name: 'Küldés' }).click();
    await expect(page.getByRole('list', { name: 'Üzenetek' })).toContainText(
      message,
    );
  });

  test('sees who handles an accepted request', async ({ page }) => {
    await page.goto('/my-requests');
    await requestLink(page, 'Őszi szakmai konferencia').click();

    await expect(
      page.getByText('Elvállaltuk, stábunk ott lesz az eseményeden.'),
    ).toBeVisible();
    // Scoped to the sidebar: staff replies in the thread show names too.
    await expect(page.locator('aside').getByText('Gyártó Gábor')).toBeVisible();
    await expect(page.getByRole('list', { name: 'Üzenetek' })).toContainText(
      'Sziasztok! 9-kor kezdünk',
    );
  });
});

test.describe('as a requester without requests', () => {
  test.use({ storageState: loginAs('ures.peter') });

  test('sees the empty state', async ({ page }) => {
    await page.goto('/my-requests');

    await expect(
      page.getByRole('heading', { name: 'Még nem küldtél be felkérést' }),
    ).toBeVisible();
  });
});
