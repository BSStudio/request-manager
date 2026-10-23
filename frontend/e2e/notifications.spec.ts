import { expect, loginAs, test } from './fixtures';

// The seeded notifications sit on requests no other test opens as their
// recipient, and these tests change them in order.
test.describe.configure({ mode: 'serial' });

test.describe('requester', () => {
  test.use({ storageState: loginAs('teszt.elek') });

  test('opening a notification marks its request read', async ({ page }) => {
    await page.goto('/my-requests');
    await page
      .getByRole('button', { name: 'Értesítések, 2 olvasatlan' })
      .click();
    await page
      .getByRole('link', { name: /Szülinapi buli a koliban: Sajnos/ })
      .click();

    await expect(page).toHaveURL(/\/my-requests\/\d+$/);
    await expect(
      page.getByRole('button', { name: 'Értesítések, 1 olvasatlan' }),
    ).toBeVisible();
  });

  test('marks everything read on the notifications page', async ({ page }) => {
    await page.goto('/notifications');
    await expect(page.getByRole('heading', { name: 'Tegnap' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Korábban' })).toBeVisible();

    await page.getByRole('button', { name: 'Mindet elolvastam' }).click();

    await expect(
      page.getByRole('button', { exact: true, name: 'Értesítések' }),
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Mindet elolvastam' }),
    ).toBeDisabled();
  });
});

test.describe('staff', () => {
  test.use({ storageState: loginAs('admin.aladar') });

  test('opening a notification marks its request read', async ({ page }) => {
    await page.goto('/admin');
    await page
      .getByRole('button', { name: 'Értesítések, 2 olvasatlan' })
      .click();
    await page
      .getByRole('link', { name: /Félévnyitó koncert · Minta Anna/ })
      .click();

    await expect(page).toHaveURL(/\/admin\/requests\/\d+$/);
    await expect(
      page.getByRole('button', { name: 'Értesítések, 1 olvasatlan' }),
    ).toBeVisible();
  });

  test('marks everything read on the notifications page', async ({ page }) => {
    await page.goto('/admin/notifications');
    // The menubar's closed dropdown holds the same row.
    await expect(
      page.getByText(/Éjszakai kosármeccs: Kár/).filter({ visible: true }),
    ).toBeVisible();

    await page.getByRole('button', { name: 'Mindet elolvastam' }).click();

    await expect(
      page.getByRole('button', { exact: true, name: 'Értesítések' }),
    ).toBeVisible();
  });
});
