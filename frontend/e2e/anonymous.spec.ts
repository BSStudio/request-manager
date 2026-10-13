import { randomUUID } from 'crypto';

import { addDays } from 'date-fns';

import { expect, test } from './fixtures';
import { pickDay } from './helpers';

test('submits a request without logging in', async ({ page }) => {
  const suffix = randomUUID().slice(0, 8);

  await page.goto('/new-request');
  await page.getByLabel('Vezetéknév').fill('Vendég');
  await page.getByLabel('Keresztnév').fill('Vilmos');
  await page.getByLabel('E-mail-cím').fill(`vendeg.${suffix}@example.com`);
  await page.getByLabel('Telefonszám').fill('06 70 123 4567');
  await page.getByRole('button', { name: 'Tovább' }).click();

  await page.getByLabel('Az esemény neve').fill(`Vendégest ${suffix}`);
  await pickDay(page, 'Kezdés', addDays(new Date(), 20));
  await page
    .getByRole('textbox', { exact: true, name: 'Kezdés' })
    .fill('19:00');
  await page
    .getByRole('textbox', { exact: true, name: 'Várható befejezés' })
    .fill('23:00');
  await page.getByLabel('Helyszín').fill('Schönherz Kollégium, Qpa');
  await page.getByRole('radio', { name: 'Zenés hangulatvideó' }).check();
  await page.getByRole('button', { name: 'Tovább' }).click();
  await page.getByRole('button', { name: 'Tovább' }).click();
  await page.getByRole('button', { exact: true, name: 'Beküldés' }).click();

  // A test gets here faster than a person, often before Turnstile has finished.
  await expect(
    page.getByRole('heading', { name: 'Megkaptuk a felkérésed!' }),
  ).toBeVisible({ timeout: 15_000 });
  await expect(
    page.getByRole('link', { name: 'Felkérés megtekintése' }),
  ).toHaveCount(0);
});

test('sends a message through the contact form', async ({ page }) => {
  await page.goto('/');
  const name = page.getByLabel('Név', { exact: true });

  await name.fill('Vendég Vilmos');
  await page.getByLabel('E-mail-cím').fill('vendeg.vilmos@example.com');
  await page
    .getByLabel('Üzenet', { exact: true })
    .fill('Szia! Forgattok esküvőt is?');
  await page.getByRole('button', { name: 'Üzenet küldése' }).click();

  await expect(
    page.getByText('Köszönjük, megkaptuk az üzeneted!'),
  ).toBeVisible();
  await expect(name).toHaveValue('');
});
