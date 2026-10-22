import type { Page } from '@playwright/test';

import { expect, loginAs, test } from './fixtures';
import { adminRequestPath } from './helpers';

function projectRow(page: Page) {
  return page
    .getByRole('listitem')
    .filter({ has: page.getByText('Projekt', { exact: true }) });
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
