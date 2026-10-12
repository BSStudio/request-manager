import { expect, loginAs, test } from './fixtures';
import { requestLink } from './helpers';

test.use({ storageState: loginAs('minta.anna') });

test('rates a video, changes and deletes the rating', async ({ page }) => {
  await page.goto('/my-requests');
  await requestLink(page, 'Tanszéki évzáró előadás').click();
  const video = page
    .getByRole('listitem')
    .filter({ hasText: 'Rövid összefoglaló' });
  const stars = video.getByRole('group', { name: 'Értékelés' });
  await expect(video.getByText('Hogy tetszett a videó?')).toBeVisible();

  await stars.getByRole('button', { name: '4 csillag' }).click();
  await video.getByLabel('Véleményed').fill('Jó lett, csak kicsit hosszú.');
  await video.getByRole('button', { name: 'Mentés' }).click();
  await expect(page.getByText('Köszönjük az értékelést!')).toBeVisible();

  await page.reload();
  await expect(video.getByText('Az értékelésed')).toBeVisible();
  await expect(video.getByText('„Jó lett, csak kicsit hosszú.”')).toBeVisible();
  await expect(
    stars.getByRole('button', { name: '4 csillag' }),
  ).toHaveAttribute('aria-pressed', 'true');

  await stars.getByRole('button', { name: '5 csillag' }).click();
  await video.getByLabel('Véleményed').fill('Tökéletes lett!');
  await video.getByRole('button', { name: 'Mentés' }).click();
  await expect(video.getByText('„Tökéletes lett!”')).toBeVisible();
  await expect(
    stars.getByRole('button', { name: '5 csillag' }),
  ).toHaveAttribute('aria-pressed', 'true');

  await video.getByRole('button', { name: 'Törlés' }).click();
  const dialog = page.getByRole('alertdialog', {
    name: 'Törlöd az értékelésed?',
  });
  await dialog.getByRole('button', { name: 'Törlés' }).click();
  await expect(video.getByText('Hogy tetszett a videó?')).toBeVisible();

  await page.reload();
  await expect(video.getByText('Hogy tetszett a videó?')).toBeVisible();
});
