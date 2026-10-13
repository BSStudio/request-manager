import type { Page } from '@playwright/test';
import { format, subDays } from 'date-fns';

import { expect, loginAs, test } from './fixtures';
import { requestLink } from './helpers';

// One request taken from submitted to closed; every step builds on the last.
test.describe.configure({ mode: 'serial' });

const videoUrl = 'https://example.com/videok/kari-golyabal-aftermovie';
let requestPath: string;

// The hidden status help also has list items with these words.
function detailsRow(page: Page, label: string) {
  return page
    .getByRole('listitem')
    .filter({ has: page.getByText(label, { exact: true }) });
}

function status(page: Page) {
  return detailsRow(page, 'Státusz');
}

function recording(page: Page) {
  return detailsRow(page, 'Nyersek');
}

async function pickStaff(page: Page, label: string, name: string) {
  const field = page.getByLabel(label, { exact: true });
  const option = page.getByRole('option').filter({ hasText: name });
  // The AutoComplete only searches while typed into, and finds nobody until
  // the staff list has loaded in the background.
  await expect(async () => {
    await field.clear();
    await field.pressSequentially(name.split(' ')[0]);
    await expect(option).toBeVisible({ timeout: 1000 });
  }).toPass();
  await option.click();
}

async function editVideo(page: Page, change: () => Promise<void>) {
  await page.getByRole('link', { name: 'Videó szerkesztése' }).click();
  await change();
  await page.getByRole('button', { exact: true, name: 'Mentés' }).click();
  await expect(page).not.toHaveURL(/\/edit$/);
}

test.describe('as an admin', () => {
  test.use({ storageState: loginAs('admin.aladar') });

  test('accepts the request', async ({ page }) => {
    await page.goto('/admin');
    await page
      .getByRole('row')
      .filter({ hasText: 'Kari gólyabál' })
      .getByRole('link', { name: 'Ugrás a felkéréshez' })
      .click();
    await expect(page).toHaveURL(/\/admin\/requests\/\d+$/);
    requestPath = new URL(page.url()).pathname;
    await expect(status(page)).toContainText('Felkérés');

    await page.getByRole('button', { name: 'Felkérés elbírálása' }).click();
    const dialog = page.getByRole('dialog', { name: 'Felkérés elfogadása' });
    await dialog.getByRole('button', { name: 'Elfogadva' }).click();
    await dialog.getByRole('button', { exact: true, name: 'Mentés' }).click();

    await expect(status(page)).toContainText('Elvállalva');
  });
});

test.describe('as a crew member', () => {
  test.use({ storageState: loginAs('gyarto.gabor') });

  test('takes the request on and enters the recording', async ({ page }) => {
    // Only an event that is over can be recorded, and nothing moves the clock.
    const day = format(subDays(new Date(), 2), 'yyyy.MM.dd');

    await page.goto(requestPath);
    await page.getByRole('link', { name: 'Felkérés szerkesztése' }).click();
    await pickStaff(page, 'Felelős', 'Gyártó Gábor');
    await page.getByLabel('Kezdés időpontja').fill(`${day} 18:00`);
    await page.getByLabel('Kezdés időpontja').press('Tab');
    await page.getByLabel('Befejezés időpontja').fill(`${day} 22:00`);
    await page.getByLabel('Befejezés időpontja').press('Tab');
    await page.getByRole('button', { exact: true, name: 'Mentés' }).click();
    await expect(page.getByText('Felkérés módosítva')).toBeVisible();
    await expect(status(page)).toContainText('Leforgatva');

    await page.getByRole('tab', { name: 'Stáb' }).click();
    await page.getByRole('button', { name: 'Új stábtag' }).click();
    const crew = page.getByRole('dialog', { name: 'Új stábtag hozzáadása' });
    await pickStaff(page, 'Stábtag', 'Kamera Károly');
    await crew.getByLabel('Pozíció', { exact: true }).fill('Operatőr');
    await crew.getByRole('button', { exact: true, name: 'Mentés' }).click();
    await expect(
      page.getByRole('row').filter({ hasText: 'Kamera Károly' }),
    ).toContainText('Operatőr');

    await recording(page).getByRole('button', { name: 'Szerkesztés' }).click();
    await recording(page)
      .getByPlaceholder('Elérési út')
      .fill('/Felvetelek/Kari golyabal');
    await recording(page).getByRole('button', { name: 'Mentés' }).click();
    await expect(status(page)).toContainText('Beírva');
  });

  test('finishes the video', async ({ page }) => {
    await page.goto(requestPath);
    await page.getByRole('tab', { name: 'Videók' }).click();
    await page.getByRole('link', { name: 'Új videó' }).click();
    await page.getByLabel('Videó címe', { exact: true }).fill('Aftermovie');
    await pickStaff(page, 'Vágó', 'Vágó Vilma');
    await page.getByRole('button', { exact: true, name: 'Mentés' }).click();
    await expect(page.getByText('Videó létrehozva')).toBeVisible();
    await expect(status(page)).toContainText('Vágás alatt');

    await editVideo(page, () =>
      page.getByRole('checkbox', { name: 'Megvágva' }).check(),
    );
    await expect(status(page)).toContainText('Megvágva');

    await editVideo(page, async () => {
      await page.getByRole('checkbox', { name: 'Kikódolva' }).check();
      await page.getByLabel('Videó elérési útja').fill(videoUrl);
    });
    await expect(status(page)).toContainText('Közzétéve');
    await page.getByRole('tab', { name: 'Feladatok' }).click();
    await expect(
      page.getByText('Megosztás közösségi platformokon'),
    ).toBeVisible();

    await editVideo(page, () =>
      page.getByRole('checkbox', { name: 'Archiválva' }).check(),
    );
    await expect(status(page)).toContainText('Lezárva');
  });

  test('archives the recording and closes the request', async ({ page }) => {
    await page.goto(requestPath);
    await expect(status(page)).toContainText('Megvágva');

    await recording(page).getByRole('button', { name: 'Szerkesztés' }).click();
    await recording(page)
      .getByText('Nincsenek felmásolva Google Driveba')
      .click();
    await recording(page).getByRole('button', { name: 'Mentés' }).click();
    await expect(status(page)).toContainText('Archiválva');

    await recording(page).getByRole('button', { name: 'Szerkesztés' }).click();
    await recording(page).getByText('Nincsenek törölve').click();
    await recording(page).getByRole('button', { name: 'Mentés' }).click();
    await expect(status(page)).toContainText('Lezárva');
  });
});

test.describe('as the requester', () => {
  test.use({ storageState: loginAs('minta.anna') });

  test('sees the finished request and its video', async ({ page }) => {
    await page.goto('/my-requests');
    await requestLink(page, 'Kari gólyabál').click();

    await expect(page.getByText('Elkészült').first()).toBeVisible();
    const video = page.getByRole('listitem').filter({ hasText: 'Aftermovie' });
    await expect(video).toContainText('Közzétéve');
    await expect(video.getByRole('link', { name: 'Megnézem' })).toHaveAttribute(
      'href',
      videoUrl,
    );
  });
});
