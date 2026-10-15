import type { Page } from '@playwright/test';

import { expect, loginAs, test } from './fixtures';
import { adminRequestPath } from './helpers';

test.use({ storageState: loginAs('admin.aladar') });

// Page titles list the breadcrumbs from the most specific one.
function crumbs(...names: string[]) {
  const escaped = names.map((name) => RegExp.escape(name));
  return new RegExp(`^${[...escaped, 'Admin'].join(' \\| ')} \\|`);
}

function crumb(page: Page, name: string) {
  return page.getByRole('banner').getByRole('link', { exact: true, name });
}

test('every page opens from the menu', async ({ page }) => {
  const menu = page.getByRole('banner').getByRole('list').first();
  await page.goto('/admin');

  await menu.getByText('Felkérések', { exact: true }).click();
  await menu.getByRole('link', { name: 'Lista' }).click();
  await expect(page).toHaveTitle(crumbs('Felkérések'));
  // The list shows the current half-year, which no seeded request is always in.
  await expect(
    page.getByRole('link', { name: 'Ugrás a felkéréshez' }).first(),
  ).toBeVisible();

  await menu.getByText('Felkérések', { exact: true }).click();
  await menu.getByRole('link', { name: 'Új' }).click();
  await expect(page).toHaveTitle(crumbs('Új', 'Felkérések'));
  await expect(page.getByLabel('Esemény neve')).toBeVisible();

  await menu.getByRole('link', { name: 'Feladatok' }).click();
  await expect(page).toHaveTitle(crumbs('Feladatok'));
  await expect(
    page.getByText('Zenék kiválasztása az aftermovie-hoz'),
  ).toBeVisible();

  await menu.getByRole('link', { name: 'Felhasználók' }).click();
  await expect(page).toHaveTitle(crumbs('Felhasználók'));
  await expect(
    page.getByRole('row').filter({ hasText: 'Admin Aladár' }),
  ).toBeVisible();

  await menu.getByRole('link', { name: 'Keresés' }).click();
  await expect(page).toHaveTitle(crumbs('Keresés'));
});

test('the breadcrumbs lead back from a video', async ({ page }) => {
  await page.goto(await adminRequestPath(page, 'Kollégiumi kulturális est'));
  await page.getByRole('tab', { name: 'Videók' }).click();
  await page
    .getByRole('row')
    .filter({ hasText: 'Fellépések egyben' })
    .getByRole('link', { name: 'Ugrás a videóhoz' })
    .click();
  await expect(page).toHaveTitle(
    crumbs(
      'Fellépések egyben',
      'Videók',
      'Kollégiumi kulturális est',
      'Felkérések',
    ),
  );

  await crumb(page, 'Videók').click();
  await expect(page).toHaveTitle(
    crumbs('Videók', 'Kollégiumi kulturális est', 'Felkérések'),
  );
  await expect(
    page.getByRole('row').filter({ hasText: 'Fellépések egyben' }),
  ).toBeVisible();

  await crumb(page, 'Kollégiumi kulturális est').click();
  await expect(page).toHaveTitle(
    crumbs('Kollégiumi kulturális est', 'Felkérések'),
  );

  await crumb(page, 'Felkérések').click();
  await expect(page).toHaveTitle(crumbs('Felkérések'));
});

// The seeded 'Diákköri konferencia' and its video, which only this test uses.
test('the breadcrumbs follow a renamed request and video', async ({ page }) => {
  await page.goto(await adminRequestPath(page, 'Diákköri konferencia'));
  await page.getByRole('link', { name: 'Felkérés szerkesztése' }).click();
  await page.getByLabel('Esemény neve').fill('Tavaszi diákköri konferencia');
  await page.getByRole('button', { exact: true, name: 'Mentés' }).click();
  await expect(page).toHaveTitle(
    crumbs('Tavaszi diákköri konferencia', 'Felkérések'),
  );

  await page.getByRole('tab', { name: 'Videók' }).click();
  await page
    .getByRole('row')
    .filter({ hasText: 'Díjátadó' })
    .getByRole('link', { name: 'Ugrás a videóhoz' })
    .click();
  await page.getByRole('link', { name: 'Videó szerkesztése' }).click();
  await page.getByLabel('Videó címe', { exact: true }).fill('Díjátadó gála');
  await page.getByRole('button', { exact: true, name: 'Mentés' }).click();
  await expect(page).toHaveTitle(
    crumbs(
      'Díjátadó gála',
      'Videók',
      'Tavaszi diákköri konferencia',
      'Felkérések',
    ),
  );
});

test("a user's open section is kept in the address", async ({ page }) => {
  await page.goto('/admin/users');
  await page.getByRole('textbox', { name: 'Keresés' }).fill('Tiltott');
  await page
    .getByRole('row')
    .filter({ hasText: 'Tiltott Tamás' })
    .getByRole('link', { name: 'Ugrás a profilra' })
    .click();
  await expect(page).toHaveTitle(crumbs('Tiltott Tamás', 'Felhasználók'));

  await page.getByRole('link', { name: 'Kitiltás' }).click();
  await expect(page).toHaveURL(/\?section=ban$/);
  await page.reload();
  await expect(page.getByLabel('Indoklás')).toHaveValue(
    'Többször küldött kamu felkérést',
  );
});

test('a request that does not exist shows the error page', async ({ page }) => {
  await page.goto('/admin/requests/999999');

  await expect(page.getByText('Az oldal nem található')).toBeVisible();
  await expect(page).toHaveTitle(/^Hiba történt \| Admin \|/);
  await expect(crumb(page, 'Felkérések')).toBeHidden();

  await page.getByRole('button', { name: 'Ugrás a kezdőlapra' }).click();
  await expect(page).toHaveURL(/\/admin$/);
});
