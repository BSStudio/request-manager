import { expect, loginAs, test } from './fixtures';

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
});
