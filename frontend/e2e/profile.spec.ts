import { expect, loginAs, test } from './fixtures';

test.describe('as a requester', () => {
  // Üres Péter is in no scenario, so changing his details affects no other test.
  test.use({ storageState: loginAs('ures.peter') });

  test('saves changed details', async ({ page }) => {
    await page.goto('/profile');
    await page.getByLabel('Keresztnév').fill('Pál');
    await page.getByLabel('Telefonszám').fill('06 20 555 1234');
    await page.getByRole('button', { name: 'Mentés' }).click();
    await expect(page.getByText('Elmentettük az adataidat.')).toBeVisible();

    await page.reload();
    await expect(page.getByLabel('Keresztnév')).toHaveValue('Pál');
    await expect(page.getByLabel('Telefonszám')).toHaveValue('+36 20 555 1234');
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(
      'Üres Pál',
    );
  });

  test('"Mégsem" restores the saved details', async ({ page }) => {
    await page.goto('/profile');
    const lastName = page.getByLabel('Vezetéknév');
    await expect(lastName).toHaveValue('Üres');

    await lastName.fill('Valaki');
    await page.getByRole('button', { name: 'Mégsem' }).click();

    await expect(lastName).toHaveValue('Üres');
    await expect(page.getByRole('button', { name: 'Mentés' })).toBeDisabled();
  });

  test('an invalid phone number is not saved', async ({ page }) => {
    await page.goto('/profile');
    const phone = page.getByLabel('Telefonszám');
    await expect(phone).not.toHaveValue('');

    await phone.fill('123');
    await page.getByRole('button', { name: 'Mentés' }).click();
    await expect(page.getByText('Érvénytelen telefonszám.')).toBeVisible();

    await page.reload();
    await expect(phone).not.toHaveValue('123');
  });

  test('"Összekapcsolás" sends you to the provider and back when cancelled', async ({
    page,
  }) => {
    await page.goto('/profile');
    await expect(page.getByText('Nincs összekapcsolva')).toHaveCount(3);
    // The fixture blocks the provider, so the request is only observed.
    const request = page.waitForRequest((request) =>
      request.url().startsWith('https://accounts.google.com/o/oauth2/v2/auth?'),
    );

    await page
      .getByRole('listitem')
      .filter({ hasText: 'Google' })
      .getByRole('button', { name: 'Összekapcsolás' })
      .click();

    const state = new URL((await request).url()).searchParams.get('state');
    expect(state).toBeTruthy();

    await page.goto(
      `/redirect?${new URLSearchParams({ error: 'access_denied', state: state ?? '' })}`,
    );
    await expect(page).toHaveURL(/\/profile$/);
    await expect(
      page.getByText('A fiók összekapcsolása megszakadt.'),
    ).toBeVisible();
  });
});

test.describe('as a crew member', () => {
  test.use({ storageState: loginAs('gyarto.gabor') });

  test('sees their details without a form', async ({ page }) => {
    await page.goto('/profile');

    await expect(
      page.getByText(
        'Az adataid a BSS címtárából jönnek, ott tudod módosítani őket.',
      ),
    ).toBeVisible();
    await expect(page.getByLabel('Keresztnév')).toHaveCount(0);
  });
});
