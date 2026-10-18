import { readFileSync } from 'fs';
import path from 'path';

import type { Page } from '@playwright/test';

import { expect, loginAs, test } from './fixtures';
import { adminRequestPath } from './helpers';

test.use({ storageState: loginAs('admin.aladar') });

// 61.6 seconds long.
const mp4 = path.join(import.meta.dirname, 'files', 'video.mp4');
// 2.6 seconds long.
const mxf = path.join(import.meta.dirname, 'files', 'video.mxf');

// A new video of the seeded 'Állásbörze', which is never saved.
async function openNewVideo(page: Page) {
  await page.goto(`${await adminRequestPath(page, 'Állásbörze')}/videos/new`);
}

async function pickFile(
  page: Page,
  file: Parameters<Page['setInputFiles']>[1],
) {
  const fileChooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Hossz kiolvasása fájlból' }).click();
  await (await fileChooser).setFiles(file);
}

test('reads the length of a picked video file', async ({ page }) => {
  await openNewVideo(page);
  const length = page.getByLabel('Videó hossza');

  await pickFile(page, mp4);
  await expect(length).toHaveValue('00:01:02');

  await pickFile(page, mxf);
  await expect(length).toHaveValue('00:00:03');
});

function dragMp4(page: Page) {
  return page.evaluateHandle(
    (bytes) => {
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(new File([new Uint8Array(bytes)], 'video.mp4'));
      return dataTransfer;
    },
    [...readFileSync(mp4)],
  );
}

test('reads the length of a video dropped anywhere on the page', async ({
  page,
}) => {
  await openNewVideo(page);
  const length = page.getByLabel('Videó hossza');
  const dropHint = page.getByText('Engedd el a videót a hossz kiolvasásához');
  const dataTransfer = await dragMp4(page);

  await page
    .getByText('Videó létrehozása')
    .dispatchEvent('dragenter', { dataTransfer });
  await expect(dropHint).toBeVisible();
  await dropHint.dispatchEvent('drop', { dataTransfer });
  await expect(dropHint).toBeHidden();
  await expect(length).toHaveValue('00:01:02');
});

test('hides the drop hint when the video is dragged away', async ({ page }) => {
  await openNewVideo(page);
  const dropHint = page.getByText('Engedd el a videót a hossz kiolvasásához');
  const dataTransfer = await dragMp4(page);

  await page
    .getByText('Videó létrehozása')
    .dispatchEvent('dragenter', { dataTransfer });
  await expect(dropHint).toBeVisible();
  await dropHint.dispatchEvent('dragleave', { dataTransfer });
  await expect(dropHint).toBeHidden();
});

test('shows the drop hint again when the video comes right back', async ({
  page,
}) => {
  await openNewVideo(page);
  const title = page.getByText('Videó létrehozása');
  const dropHint = page.getByText('Engedd el a videót a hossz kiolvasásához');
  const dataTransfer = await dragMp4(page);

  await title.dispatchEvent('dragenter', { dataTransfer });
  await expect(dropHint).toBeVisible();
  await dropHint.dispatchEvent('dragleave', { dataTransfer });
  await title.dispatchEvent('dragenter', { dataTransfer });
  // Longer than the overlay's fade-out.
  await page.waitForTimeout(500);
  await expect(dropHint).toBeVisible();
});

test('keeps a partly typed length while a video is dragged over', async ({
  page,
}) => {
  await openNewVideo(page);
  const length = page.getByLabel('Videó hossza');
  const dropHint = page.getByText('Engedd el a videót a hossz kiolvasásához');
  const dataTransfer = await dragMp4(page);

  await length.pressSequentially('012');
  await page
    .getByText('Videó létrehozása')
    .dispatchEvent('dragenter', { dataTransfer });
  await expect(dropHint).toBeVisible();
  await dropHint.dispatchEvent('dragleave', { dataTransfer });
  await expect(dropHint).toBeHidden();
  await expect(length).toHaveValue('01:2_:__');
});

test('tells when a file has no length', async ({ page }) => {
  await openNewVideo(page);
  const length = page.getByLabel('Videó hossza');

  await pickFile(page, {
    buffer: Buffer.from('Nem videó.'),
    mimeType: 'text/plain',
    name: 'jegyzet.txt',
  });
  await expect(
    page.getByText('Nem sikerült kiolvasni a videó hosszát.'),
  ).toBeVisible();
  await expect(length).toHaveValue('');
});
