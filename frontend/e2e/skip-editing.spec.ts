import { expect, loginAs, test } from './fixtures';
import { adminRequestPath, pick } from './helpers';

test.use({ storageState: loginAs('gyarto.gabor') });

// A new video of the seeded 'Kollégiumi kulturális est', whose material is
// already uploaded.
test('skipping the cut clears the editor and the cut', async ({ page }) => {
  const row = (label: string) =>
    page.getByRole('listitem').filter({ hasText: new RegExp(`^${label}`) });
  const editor = page.getByLabel('Vágó', { exact: true });
  const cut = page.getByRole('checkbox', { name: 'Megvágva' });

  await page.goto(
    `${await adminRequestPath(page, 'Kollégiumi kulturális est')}/videos/new`,
  );
  await page.getByLabel('Videó címe', { exact: true }).fill('Élő közvetítés');
  await pick(page, editor, 'Vágó Vilma');
  await cut.check();
  await page.getByRole('button', { exact: true, name: 'Mentés' }).click();
  await expect(page.getByText('Videó létrehozva')).toBeVisible();
  await expect(row('Vágó')).toContainText('Vágó Vilma');

  await page.getByRole('link', { name: 'Videó szerkesztése' }).click();
  await page.getByRole('checkbox', { name: 'Nem kell vágni' }).check();
  await expect(editor).toHaveValue('');
  await expect(editor).toBeDisabled();
  await expect(cut).not.toBeChecked();
  await expect(cut).toBeDisabled();
  await page.getByRole('button', { exact: true, name: 'Mentés' }).click();
  await expect(page).not.toHaveURL(/\/edit$/);

  await expect(row('Státusz')).toContainText('Megvágva');
  await expect(row('Vágó')).toContainText('Nem kell vágni');
  await expect(row('Megvágva')).toContainText('Nem kell vágni');
});
