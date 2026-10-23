import type { Locator, Page } from '@playwright/test';
import {
  addDays,
  differenceInCalendarMonths,
  format,
  setHours,
  startOfDay,
} from 'date-fns';
import { hu } from 'date-fns/locale';

import { expect } from './fixtures';

export async function pickDay(page: Page, label: string, day: Date) {
  await page.getByRole('button', { name: new RegExp(`^${label}`) }).click();
  const months = differenceInCalendarMonths(day, new Date());
  for (let month = 0; month < months; month++) {
    await page
      .getByRole('button', { name: 'Ugrás a következő hónapra' })
      .click();
  }
  // Day buttons are named like "2026. október 26., hétfő".
  await page
    .getByRole('button', { name: format(day, 'PPPP', { locale: hu }) })
    .click();
}

// The options open at the end of the page, outside any dialog.
export async function pick(page: Page, field: Locator, option: string) {
  await field.fill(option.split(' ')[0]);
  await page.getByRole('option').filter({ hasText: option }).click();
}

// Through the API: the admin's request list only shows the current semester.
export async function adminRequestPath(page: Page, title: string) {
  const response = await page.request.get('/api/v1/admin/requests', {
    params: { search: title },
  });
  await expect(response).toBeOK();
  const { results } = (await response.json()) as {
    results: { id: number; title: string }[];
  };
  const request = results.find((request) => request.title === title);
  if (!request) throw new Error(`The seed has no request called ${title}.`);
  return `/admin/requests/${request.id}`;
}

// Matched exactly: some seeded titles also appear inside longer ones.
export function requestLink(page: Page, title: string) {
  return page
    .getByRole('link')
    .filter({ has: page.getByText(title, { exact: true }) });
}

// Seeded data is relative to today, so tests build their dates the same way.
export function inDays(days: number, hour = 0) {
  return setHours(startOfDay(addDays(new Date(), days)), hour);
}

// PrimeReact's masked Calendar takes typed text and parses it on blur.
export async function fillDateTime(page: Page, label: string, date: Date) {
  const input = page.getByLabel(label, { exact: true });
  await input.fill(format(date, 'yyyy.MM.dd HH:mm'));
  await input.press('Tab');
}
