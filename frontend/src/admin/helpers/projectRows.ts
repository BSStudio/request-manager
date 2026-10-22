import { addDays, addWeeks, isAfter, startOfDay } from 'date-fns';

import type { RequesterPayload } from 'admin/helpers/requester';
import type { RequestAdminCreateRequest } from 'api/models';

export interface NewRequestRow {
  end_datetime: Date | null;
  place: string;
  start_datetime: Date | null;
  title: string;
  type: string;
}

type RowTimes = Pick<NewRequestRow, 'end_datetime' | 'start_datetime'>;

export const MAX_OCCURRENCES = 100;

// date-fns steps in local time, so a series keeps its wall-clock time across
// the daylight saving changes.
export function occurrences(
  firstStart: Date,
  firstEnd: Date,
  lastDay: Date,
  repeat: 'daily' | 'weekly',
): { end: Date; start: Date }[] {
  const step = repeat === 'daily' ? addDays : addWeeks;
  const series = [];
  for (let index = 0; index < MAX_OCCURRENCES; index++) {
    const start = step(firstStart, index);
    if (isAfter(startOfDay(start), startOfDay(lastDay))) break;
    series.push({ end: step(firstEnd, index), start });
  }
  return series;
}

export function nextRowTimes(last?: RowTimes): RowTimes {
  return {
    end_datetime: last?.end_datetime ? addDays(last.end_datetime, 1) : null,
    start_datetime: last?.start_datetime
      ? addDays(last.start_datetime, 1)
      : null,
  };
}

export function newRequestPayloads(
  rows: NewRequestRow[],
  shared: {
    accepted: boolean;
    name: string;
    place: string;
    requester: RequesterPayload;
    responsible: number | null;
    type: string;
  },
): RequestAdminCreateRequest[] {
  return rows.map((row) => ({
    ...shared.requester,
    ...(shared.accepted && { additional_data: { accepted: true } }),
    // The API names the cell of a missing time.
    end_datetime: row.end_datetime?.toISOString() ?? '',
    place: row.place.trim() || shared.place.trim(),
    responsible: shared.responsible,
    start_datetime: row.start_datetime?.toISOString() ?? '',
    title: row.title.trim() || shared.name.trim(),
    type: row.type.trim() || shared.type.trim(),
  }));
}

export function saveSummary(counts: {
  added: number;
  created: number;
  removed: number;
}): string | null {
  const parts = [
    counts.created && `${counts.created} új felkérés`,
    counts.added && `${counts.added} hozzáadva`,
    counts.removed && `${counts.removed} eltávolítva a projektből`,
  ].filter(Boolean);
  return parts.length ? `Mentéskor: ${parts.join(', ')}` : null;
}

const PROJECT_FIELDS = ['name', 'responsible'];
const ROW_FIELDS = ['end_datetime', 'place', 'start_datetime', 'title', 'type'];

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

function firstMessage(value: unknown): string | undefined {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return firstMessage(value[0]);
  return undefined;
}

// Messages without a cell in the editor, such as a requester field repeated on
// every row, are shown once.
export function projectSaveErrors(data: unknown): {
  fields: [path: string, message: string][];
  other: string[];
} {
  const fields: [string, string][] = [];
  const other = new Set<string>();
  if (!isRecord(data)) return { fields, other: [] };

  const addOther = (value: unknown) => {
    const message = firstMessage(value);
    if (message) other.add(message);
  };

  for (const [key, value] of Object.entries(data)) {
    if (PROJECT_FIELDS.includes(key)) {
      const message = firstMessage(value);
      if (message) fields.push([key, message]);
    } else if (key === 'new_requests' && Array.isArray(value)) {
      value.forEach((rowErrors: unknown, index) => {
        if (!isRecord(rowErrors)) return;
        for (const [field, messages] of Object.entries(rowErrors)) {
          const message = firstMessage(messages);
          if (!message) continue;
          if (ROW_FIELDS.includes(field)) {
            fields.push([`new_requests.${index}.${field}`, message]);
          } else {
            other.add(message);
          }
        }
      });
    } else {
      addOther(value);
    }
  }
  return { fields, other: [...other] };
}
