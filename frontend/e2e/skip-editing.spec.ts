import { expect, loginAs, test } from './fixtures';
import { adminRequestPath } from './helpers';

test.use({ storageState: loginAs('gyarto.gabor') });

// A new video of the seeded 'Kollégiumi kulturális est', whose material is
// already uploaded.
test('a video that needs no cut is edited without an editor', async ({
  page,
}) => {
  await page.goto(
    `${await adminRequestPath(page, 'Kollégiumi kulturális est')}/videos/new`,
  );
  await page.getByLabel('Videó címe', { exact: true }).fill('Élő közvetítés');
  await page.getByRole('checkbox', { name: 'Nem kell vágni' }).check();
  await expect(page.getByLabel('Vágó', { exact: true })).toBeDisabled();
  await expect(page.getByRole('checkbox', { name: 'Megvágva' })).toBeDisabled();
  await page.getByRole('button', { exact: true, name: 'Mentés' }).click();
  await expect(page.getByText('Videó létrehozva')).toBeVisible();

  const row = (label: string) =>
    page.getByRole('listitem').filter({ hasText: new RegExp(`^${label}`) });
  await expect(row('Státusz')).toContainText('Megvágva');
  await expect(row('Vágó')).toContainText('Nem kell vágni');
  await expect(row('Megvágva')).toContainText('Nem kell vágni');
});
