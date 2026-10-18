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

test('reads the length of a dropped video file', async ({ page }) => {
  await openNewVideo(page);
  const length = page.getByLabel('Videó hossza');
  const dataTransfer = await page.evaluateHandle(
    (bytes) => {
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(new File([new Uint8Array(bytes)], 'video.mp4'));
      return dataTransfer;
    },
    [...readFileSync(mp4)],
  );

  await length.dispatchEvent('drop', { dataTransfer });
  await expect(length).toHaveValue('00:01:02');
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
