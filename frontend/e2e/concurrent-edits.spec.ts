import type { Page } from '@playwright/test';
import { format } from 'date-fns';

import { expect, loginAs, test } from './fixtures';
import { adminRequestPath, pick } from './helpers';

test.use({ storageState: loginAs('admin.aladar') });

// The seeded 'Sportnap' and its video, which only this spec changes.
async function save(page: Page, toast: string) {
  await page.getByRole('button', { exact: true, name: 'Mentés' }).click();
  await expect(page.getByText(toast)).toBeVisible();
}

async function savedFields(page: Page, save: () => Promise<void>) {
  const response = page.waitForResponse(
    (response) => response.request().method() === 'PATCH',
  );
  await save();
  expect((await response).ok()).toBe(true);
  return (await response).request().postDataJSON() as unknown;
}

async function openTab(page: Page, tab: string) {
  await page.goto(await adminRequestPath(page, 'Sportnap'));
  await page.getByRole('tab', { name: tab }).click();
  return page.getByRole('tabpanel');
}

test('keeps a request change saved while another form was open', async ({
  context,
  page,
}) => {
  const requestPath = await adminRequestPath(page, 'Sportnap');
  const other = await context.newPage();
  await page.goto(`${requestPath}/edit`);
  await other.goto(`${requestPath}/edit`);

  await other.getByLabel('Helyszín').fill('BME sportcsarnok');
  await save(other, 'Felkérés módosítva');

  const deadline = new Date();
  await page.getByLabel('Határidő').fill(format(deadline, 'yyyy.MM.dd'));
  await page.getByLabel('Határidő').press('Tab');
  await save(page, 'Felkérés módosítva');

  const response = await page.request.get(`/api/v1${requestPath}`);
  await expect(response).toBeOK();
  expect(await response.json()).toMatchObject({
    deadline: format(deadline, 'yyyy-MM-dd'),
    place: 'BME sportcsarnok',
  });
});

test('keeps a video change saved while another form was open', async ({
  context,
  page,
}) => {
  await page.goto(await adminRequestPath(page, 'Sportnap'));
  await page.getByRole('tab', { name: 'Videók' }).click();
  await page.getByRole('link', { name: 'Ugrás a videóhoz' }).click();
  await expect(page).toHaveURL(/\/videos\/\d+$/);
  const videoPath = new URL(page.url()).pathname;
  const other = await context.newPage();
  await page.goto(`${videoPath}/edit`);
  await other.goto(`${videoPath}/edit`);

  const url = 'https://example.com/videok/sportnap';
  await other.getByLabel('Videó elérési útja').fill(url);
  await save(other, 'Videó módosítva');

  await page.getByLabel('Videó címe').fill('Sportnap 2026');
  await save(page, 'Videó módosítva');

  const response = await page.request.get(`/api/v1${videoPath}`);
  await expect(response).toBeOK();
  expect(await response.json()).toMatchObject({
    additional_data: { publishing: { website: url } },
    title: 'Sportnap 2026',
  });
});

test('a todo edit sends only the changed field', async ({ page }) => {
  const todos = await openTab(page, 'Feladatok');
  await todos.getByRole('button', { name: 'Új feladat' }).click();
  const created = page.getByRole('dialog', { name: 'Feladat létrehozása' });
  await created.getByLabel('Leírás').fill('Bakik összevágása');
  await created.getByRole('button', { name: 'Mentés' }).click();
  await expect(created).toBeHidden();

  await todos.getByRole('button', { name: 'Szerkesztés' }).click();
  const dialog = page.getByRole('dialog', { name: 'Feladat módosítása' });
  await expect(dialog.getByLabel('Leírás')).toHaveValue('Bakik összevágása');
  await dialog.getByLabel('Leírás').fill('Bakik összevágása a stábbulira');
  expect(
    await savedFields(page, () =>
      dialog.getByRole('button', { name: 'Mentés' }).click(),
    ),
  ).toEqual({ description: 'Bakik összevágása a stábbulira' });
  await expect(todos.getByText('Bakik összevágása a stábbulira')).toBeVisible();
});

test('a crew edit sends only the changed field', async ({ page }) => {
  const crew = await openTab(page, 'Stáb');
  await crew.getByRole('button', { name: 'Új stábtag' }).click();
  const dialog = page.getByRole('dialog', { name: 'Új stábtag hozzáadása' });
  await pick(
    page,
    dialog.getByLabel('Stábtag', { exact: true }),
    'Kamera Károly',
  );
  await pick(page, dialog.getByLabel('Pozíció', { exact: true }), 'Operatőr');
  await dialog.getByRole('button', { exact: true, name: 'Mentés' }).click();
  const row = crew.getByRole('row').filter({ hasText: 'Kamera Károly' });
  await expect(row).toContainText('Operatőr');

  await row.getByRole('button', { name: 'Sor szerkesztése' }).click();
  // While edited, the row's names are in its fields, not its text.
  await pick(page, crew.getByRole('combobox', { name: 'Pozíció' }), 'Rendező');
  expect(
    await savedFields(page, () =>
      crew.getByRole('button', { name: 'Szerkesztés mentése' }).click(),
    ),
  ).toEqual({ position: 'Rendező' });
  await expect(row).toContainText('Rendező');
});

test('a message edit sends only the changed field', async ({ page }) => {
  const thread = await openTab(page, 'Hozzászólások');
  await thread.getByRole('textbox').fill('Felkerült a honlapra.');
  await thread.getByRole('button', { name: 'Küldés' }).click();
  await thread.getByRole('button', { name: 'Szerkesztés' }).click();

  const edit = thread
    .locator('form')
    .filter({ has: page.getByRole('button', { name: 'Mégsem' }) });
  await edit.getByRole('textbox').fill('Felkerült a honlapra és a YouTube-ra.');
  expect(
    await savedFields(page, () =>
      edit.getByRole('button', { name: 'Mentés' }).click(),
    ),
  ).toEqual({ text: 'Felkerült a honlapra és a YouTube-ra.' });
  await expect(
    thread.getByText('Felkerült a honlapra és a YouTube-ra.'),
  ).toBeVisible();
});

test('a rating edit sends only the changed field', async ({ page }) => {
  const videos = await openTab(page, 'Videók');
  await videos.getByRole('link', { name: 'Ugrás a videóhoz' }).click();
  await page.getByRole('tab', { name: 'Értékelések' }).click();
  await page.getByRole('button', { name: 'Értékelés írása' }).click();
  const dialog = page.getByRole('dialog', { name: 'Értékelés' });
  // PrimeReact's stars have no role or name.
  await dialog.locator('.p-rating-item').nth(3).click();
  await dialog.getByRole('textbox').fill('Jól sikerült.');
  await dialog.getByRole('button', { name: 'Mentés' }).click();
  await expect(page.getByText('1 Értékelés')).toBeVisible();

  await dialog.getByRole('textbox').fill('Jól sikerült, csak kicsit hosszú.');
  expect(
    await savedFields(page, () =>
      dialog.getByRole('button', { name: 'Mentés' }).click(),
    ),
  ).toEqual({ review: 'Jól sikerült, csak kicsit hosszú.' });
});

test('a decision on the request sends only the changed field', async ({
  page,
}) => {
  await page.goto(await adminRequestPath(page, 'Sportnap'));
  await page.getByRole('button', { name: 'Felkérés elbírálása' }).click();
  const dialog = page.getByRole('dialog', { name: 'Felkérés elfogadása' });
  await dialog
    .getByRole('checkbox', { name: 'Szervezők által lemondva' })
    .check();
  expect(
    await savedFields(page, () =>
      dialog.getByRole('button', { exact: true, name: 'Mentés' }).click(),
    ),
  ).toEqual({ additional_data: { canceled: true } });
});

test('a recording edit sends only the changed field', async ({ page }) => {
  await page.goto(await adminRequestPath(page, 'Sportnap'));
  const recording = page.getByRole('listitem').filter({ hasText: /^Nyersek/ });
  await recording.getByRole('button', { name: 'Szerkesztés' }).click();
  await recording.getByPlaceholder('Elérési út').fill('/Felvetelek/Sportnap');
  expect(
    await savedFields(page, () =>
      recording.getByRole('button', { name: 'Mentés' }).click(),
    ),
  ).toEqual({
    additional_data: { recording: { path: '/Felvetelek/Sportnap' } },
  });
});

async function editAdditionalData(
  page: Page,
  apiPath: string,
  edit: (data: Record<string, unknown>) => void,
) {
  const response = await page.request.get(apiPath);
  await expect(response).toBeOK();
  const { additional_data } = (await response.json()) as {
    additional_data: Record<string, unknown>;
  };
  edit(additional_data);

  await page
    .getByRole('button', { name: 'További adatok szerkesztése' })
    .click();
  const dialog = page.getByRole('dialog', {
    name: 'További adatok szerkesztése',
  });
  await dialog.getByRole('textbox').fill(JSON.stringify(additional_data));
  return savedFields(page, () =>
    dialog.getByRole('button', { exact: true, name: 'Mentés' }).click(),
  );
}

test("the request's data editor sends only what changed", async ({ page }) => {
  const requestPath = await adminRequestPath(page, 'Sportnap');
  await page.goto(requestPath);
  expect(
    await editAdditionalData(page, `/api/v1${requestPath}`, (data) => {
      delete data.accepted;
      (data.recording as Record<string, unknown>).copied_to_gdrive = false;
    }),
  ).toEqual({
    additional_data: { accepted: null, recording: { copied_to_gdrive: false } },
  });

  const response = await page.request.get(`/api/v1${requestPath}`);
  const { additional_data } = (await response.json()) as {
    additional_data: object;
  };
  expect(additional_data).not.toHaveProperty('accepted');
  expect(additional_data).toHaveProperty('recording.copied_to_gdrive', false);
});

test("the video's data editor sends only what changed", async ({ page }) => {
  const videos = await openTab(page, 'Videók');
  await videos.getByRole('link', { name: 'Ugrás a videóhoz' }).click();
  await expect(page).toHaveURL(/\/videos\/\d+$/);
  const videoPath = new URL(page.url()).pathname;
  expect(
    await editAdditionalData(page, `/api/v1${videoPath}`, (data) => {
      data.length = 90;
    }),
  ).toEqual({ additional_data: { length: 90 } });
});
