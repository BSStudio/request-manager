import type { Page } from '@playwright/test';
import { differenceInCalendarMonths, format } from 'date-fns';
import { hu } from 'date-fns/locale';

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

// Through the API: the admin's request list only shows the current semester.
export async function adminRequestPath(page: Page, title: string) {
  const response = await page.request.get('/api/v1/admin/requests', {
    params: { search: title },
  });
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
