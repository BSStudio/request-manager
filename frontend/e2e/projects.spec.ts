import type { Page } from '@playwright/test';
import { format } from 'date-fns';

import { expect, loginAs, test } from './fixtures';
import { adminRequestPath, fillDateTime, inDays } from './helpers';

function projectRow(page: Page) {
  return page
    .getByRole('listitem')
    .filter({ has: page.getByText('Projekt', { exact: true }) });
}

// An editable Dropdown labels both its read-only focus target and the input
// one types into.
function videoType(page: Page, label: string) {
  return page
    .getByLabel(label, { exact: true })
    .and(page.locator(':not([readonly])'));
}

// The labelled input of PrimeReact's Dropdown is its hidden focus target, and
// the options with their filter open at the end of the page.
async function chooseProject(page: Page, name: string) {
  await page.getByLabel('Projekt', { exact: true }).focus();
  await page.keyboard.press('Enter');
  await page.locator('.p-dropdown-filter').fill(name);
  await page.getByRole('option', { exact: true, name }).click();
}

test.describe('as a crew member', () => {
  test.use({ storageState: loginAs('gyarto.gabor') });

  test('lists the projects and their requests', async ({ page }) => {
    await page.goto('/admin/projects');
    const week = page.getByRole('row').filter({ hasText: 'Kollégiumi hét' });
    await expect(week).toContainText('3');

    await week.getByRole('button', { name: /^Kiterjed/ }).click();
    await expect(
      page.getByText('Kollégiumi hét – Vetélkedő', { exact: true }),
    ).toBeVisible();

    await page
      .getByPlaceholder('Keresés név vagy felelős szerint')
      .fill('fizika');
    await expect(
      page.getByRole('row').filter({ hasText: 'Fizika 1 előadások' }),
    ).toBeVisible();
    await expect(
      page.getByRole('row').filter({ hasText: 'Kollégiumi hét' }),
    ).toHaveCount(0);
  });

  test('moves a request into a project and out again', async ({ page }) => {
    await page.goto(await adminRequestPath(page, 'Kari gólyabál'));
    await page.getByRole('link', { name: 'Felkérés szerkesztése' }).click();
    await chooseProject(page, 'Kollégiumi hét');
    await page.getByRole('button', { exact: true, name: 'Mentés' }).click();

    await expect(page).toHaveURL(/\/admin\/requests\/\d+$/);
    await expect(projectRow(page)).toContainText('Kollégiumi hét');
    await expect(
      projectRow(page).getByRole('link', { name: 'Ugrás' }),
    ).toHaveAttribute('href', /\/admin\/projects\/\d+$/);
    await page.getByRole('tab', { name: 'Előzmények' }).click();
    const history = page.getByRole('tabpanel', { name: 'Előzmények' });
    await expect(history.getByText('Projekt', { exact: true })).toBeVisible();
    await expect(history.getByText('Kollégiumi hét')).toBeVisible();

    await page.getByRole('link', { name: 'Felkérés szerkesztése' }).click();
    await page.locator('.p-dropdown-clear-icon').click();
    await page.getByRole('button', { exact: true, name: 'Mentés' }).click();

    await expect(page).toHaveURL(/\/admin\/requests\/\d+$/);
    await expect(projectRow(page)).toHaveCount(0);
  });
});

test.describe('as an admin', () => {
  test.use({ storageState: loginAs('admin.aladar') });

  test('creates a week of different events in one go', async ({ page }) => {
    await page.goto('/admin/projects/new');
    await page.getByLabel('Projekt neve').fill('Próbahét');
    await videoType(page, 'Videó típusa').fill('Zenés hangulatvideó');
    await page.getByLabel('Helyszín', { exact: true }).fill('Sportcsarnok');

    await page.getByRole('button', { name: 'Új felkérés' }).click();
    await page.getByLabel('Esemény neve, 1. új felkérés').fill('Megnyitó');
    await fillDateTime(page, 'Kezdés, 1. új felkérés', inDays(30, 18));
    await fillDateTime(page, 'Befejezés, 1. új felkérés', inDays(30, 20));
    // A day later, with the same times.
    await page.getByRole('button', { name: 'Új felkérés' }).click();
    await page.getByLabel('Helyszín, 2. új felkérés').fill('Uszoda');
    await expect(page.getByText('Mentéskor: 2 új felkérés')).toBeVisible();
    await page.getByRole('button', { exact: true, name: 'Mentés' }).click();

    await expect(page).toHaveURL(/\/admin\/projects$/);
    const project = page.getByRole('row').filter({ hasText: 'Próbahét' });
    await expect(project).toContainText('2');
    await project.getByRole('button', { name: /^Kiterjed/ }).click();
    await expect(page.getByText('Megnyitó', { exact: true })).toBeVisible();
    // The project and its second request, which took the project name.
    await expect(
      page.getByRole('cell', { exact: true, name: 'Próbahét' }),
    ).toHaveCount(2);
  });

  test('takes a date and time typed key by key', async ({ page }) => {
    await page.goto('/admin/projects/new');
    await page.getByRole('button', { name: 'Új felkérés' }).click();
    const start = page.getByLabel('Kezdés, 1. új felkérés', { exact: true });
    await start.click();
    await page.keyboard.type('202611201830');
    await start.press('Tab');

    await expect(start).toHaveValue('2026.11.20 18:30');
  });

  test('a failed save keeps the rows and saves nothing', async ({ page }) => {
    await page.goto('/admin/projects/new');
    await page.getByLabel('Projekt neve').fill('Hibás hét');
    await page.getByRole('button', { name: 'Új felkérés' }).click();
    await page.getByLabel('Esemény neve, 1. új felkérés').fill('Fordított');
    await fillDateTime(page, 'Kezdés, 1. új felkérés', inDays(30, 20));
    await fillDateTime(page, 'Befejezés, 1. új felkérés', inDays(30, 18));
    await videoType(page, 'Videó típusa, 1. új felkérés').fill(
      'Élő közvetítés',
    );
    await page.getByLabel('Helyszín, 1. új felkérés').fill('Aula');
    await page.getByRole('button', { exact: true, name: 'Mentés' }).click();

    await expect(
      page.getByLabel('Befejezés, 1. új felkérés', { exact: true }),
    ).toHaveAttribute('aria-invalid', 'true');
    await expect(page.getByLabel('Esemény neve, 1. új felkérés')).toHaveValue(
      'Fordított',
    );
    await expect(page).toHaveURL(/\/admin\/projects\/new$/);

    await page.goto('/admin/projects');
    await expect(
      page.getByRole('row').filter({ hasText: 'Hibás hét' }),
    ).toHaveCount(0);
  });

  test('opens a request of the project in a new tab', async ({ page }) => {
    await page.goto('/admin/projects');
    await page
      .getByRole('row')
      .filter({ hasText: 'Kollégiumi hét' })
      .getByRole('link', { name: 'Projekt szerkesztése' })
      .click();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'Kollégiumi hét – Megnyitó' })
        .getByRole('link', { name: 'Ugrás a felkéréshez' }),
    ).toHaveAttribute('target', '_blank');
  });

  test('deletes a project and keeps its requests', async ({ page }) => {
    await page.goto('/admin/projects/new');
    await page.getByLabel('Projekt neve').fill('Törlendő');
    await videoType(page, 'Videó típusa').fill('Élő közvetítés');
    await page.getByLabel('Helyszín', { exact: true }).fill('Aula');
    await page.getByRole('button', { name: 'Új felkérés' }).click();
    await page.getByLabel('Esemény neve, 1. új felkérés').fill('Megmaradó');
    await fillDateTime(page, 'Kezdés, 1. új felkérés', inDays(40, 18));
    await fillDateTime(page, 'Befejezés, 1. új felkérés', inDays(40, 20));
    await page.getByRole('button', { exact: true, name: 'Mentés' }).click();
    await expect(page).toHaveURL(/\/admin\/projects$/);

    await page
      .getByRole('row')
      .filter({ hasText: 'Törlendő' })
      .getByRole('link', { name: 'Projekt szerkesztése' })
      .click();
    await page.getByRole('button', { name: 'Projekt törlése' }).click();
    await page.getByRole('button', { exact: true, name: 'Igen' }).click();

    await expect(page).toHaveURL(/\/admin\/projects$/);
    await expect(
      page.getByRole('row').filter({ hasText: 'Törlendő' }),
    ).toHaveCount(0);
    await page.goto(await adminRequestPath(page, 'Megmaradó'));
    await expect(projectRow(page)).toHaveCount(0);
  });

  test('creates a weekly lecture series, accepted', async ({ page }) => {
    await page.goto('/admin/projects/new');
    await page.getByLabel('Projekt neve').fill('Analízis 1 előadások');
    await videoType(page, 'Videó típusa').fill('Élő közvetítés');
    await page.getByLabel('Helyszín', { exact: true }).fill('Q épület');

    await page.getByRole('button', { name: 'Ismétlődő alkalmak…' }).click();
    const series = page.getByRole('dialog', { name: 'Ismétlődő alkalmak' });
    await fillDateTime(page, 'Első alkalom kezdete', inDays(14, 10));
    await fillDateTime(page, 'Első alkalom vége', inDays(14, 12));
    const lastDay = series.getByLabel('Utolsó alkalom napja', { exact: true });
    await lastDay.fill(format(inDays(35), 'yyyy.MM.dd'));
    await lastDay.press('Tab');
    await expect(series).toContainText('4 alkalom');
    await series.getByRole('button', { name: 'Alkalmak hozzáadása' }).click();

    await expect(
      page.getByLabel('Kezdés, 4. új felkérés', { exact: true }),
    ).toBeVisible();
    await page.getByLabel('Új felkérések elfogadása').check();
    await page.getByRole('button', { exact: true, name: 'Mentés' }).click();

    await expect(page).toHaveURL(/\/admin\/projects$/);
    await page
      .getByRole('row')
      .filter({ hasText: 'Analízis 1 előadások' })
      .getByRole('button', { name: /^Kiterjed/ })
      .click();
    await expect(page.getByText('Elvállalva', { exact: true })).toHaveCount(4);
  });

  test('adds an existing request and removes another', async ({ page }) => {
    await page.goto('/admin/projects');
    await page
      .getByRole('row')
      .filter({ hasText: 'Fizika 1 előadások' })
      .getByRole('link', { name: 'Projekt szerkesztése' })
      .click();

    await page
      .getByRole('button', { name: 'Meglévő felkérések hozzáadása…' })
      .click();
    const dialog = page.getByRole('dialog', {
      name: 'Meglévő felkérések hozzáadása',
    });
    const search = dialog.getByPlaceholder('Keresés a felkérések címében');
    // Requests of a project are not offered.
    await search.fill('Fizika 1');
    await expect(
      dialog.getByText('Nincs projekt nélküli felkérés ezzel a címmel.'),
    ).toBeVisible();
    await search.fill('Kari gólyabál');
    await dialog.getByLabel('Kari gólyabál', { exact: true }).check();
    await dialog.getByRole('button', { name: 'Hozzáadás' }).click();

    const added = page.getByRole('row').filter({ hasText: 'Kari gólyabál' });
    await expect(added).toContainText('Hozzáadva');
    // Its details were loaded, as for the other rows.
    await expect(added).toContainText('Schönherz Kollégium');

    // Already in the table, so not offered again.
    await page
      .getByRole('button', { name: 'Meglévő felkérések hozzáadása…' })
      .click();
    await search.fill('Kari gólyabál');
    await expect(
      dialog.getByText('Nincs projekt nélküli felkérés ezzel a címmel.'),
    ).toBeVisible();
    await dialog.getByRole('button', { name: 'Mégsem' }).click();

    await page
      .getByRole('row')
      .filter({ hasText: 'Fizika 1 előadás' })
      .first()
      .getByRole('button', { name: 'Eltávolítás a projektből' })
      .click();
    await expect(
      page.getByText('Mentéskor: 1 hozzáadva, 1 eltávolítva a projektből'),
    ).toBeVisible();
    await page.getByRole('button', { exact: true, name: 'Mentés' }).click();

    await expect(page).toHaveURL(/\/admin\/projects$/);
    await page
      .getByRole('row')
      .filter({ hasText: 'Fizika 1 előadások' })
      .getByRole('button', { name: /^Kiterjed/ })
      .click();
    await expect(
      page.getByText('Kari gólyabál', { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole('cell', { exact: true, name: 'Fizika 1 előadás' }),
    ).toHaveCount(3);
  });
});
