import { format } from 'date-fns';
import { describe, expect, it } from 'vitest';

import {
  MAX_OCCURRENCES,
  type NewRequestRow,
  newRequestPayloads,
  nextRowTimes,
  occurrences,
  projectSaveErrors,
  saveSummary,
} from 'admin/helpers/projectRows';

function row(overrides: Partial<NewRequestRow> = {}): NewRequestRow {
  return {
    end_datetime: new Date(2026, 10, 3, 12),
    place: '',
    start_datetime: new Date(2026, 10, 3, 10, 15),
    title: '',
    type: '',
    ...overrides,
  };
}

function shared(
  overrides: Partial<Parameters<typeof newRequestPayloads>[1]> = {},
): Parameters<typeof newRequestPayloads>[1] {
  return {
    accepted: false,
    name: 'Fizika 1 előadások',
    place: 'F épület, előadóterem',
    requester: {},
    responsible: null,
    type: 'Élő közvetítés',
    ...overrides,
  };
}

describe('occurrences', () => {
  it('keeps the wall-clock time of a weekly series across the switch to winter time', () => {
    const series = occurrences(
      new Date(2026, 9, 13, 10, 15),
      new Date(2026, 9, 13, 12),
      new Date(2026, 10, 3),
      'weekly',
    );

    expect(series.map(({ start }) => format(start, 'MM-dd HH:mm'))).toEqual([
      '10-13 10:15',
      '10-20 10:15',
      '10-27 10:15',
      '11-03 10:15',
    ]);
    expect(series.every(({ end }) => format(end, 'HH:mm') === '12:00')).toBe(
      true,
    );
  });

  it('adds a row for each day up to and including the last one', () => {
    const series = occurrences(
      new Date(2026, 8, 1, 18),
      new Date(2026, 8, 1, 20),
      new Date(2026, 8, 7, 0, 0),
      'daily',
    );

    expect(series).toHaveLength(7);
    expect(format(series[6].start, 'MM-dd HH:mm')).toBe('09-07 18:00');
  });

  it('adds nothing when the last day is before the first', () => {
    expect(
      occurrences(
        new Date(2026, 8, 7, 18),
        new Date(2026, 8, 7, 20),
        new Date(2026, 8, 6),
        'daily',
      ),
    ).toEqual([]);
  });

  it(`stops at ${MAX_OCCURRENCES}`, () => {
    expect(
      occurrences(
        new Date(2026, 0, 1, 18),
        new Date(2026, 0, 1, 20),
        new Date(2026, 11, 31),
        'daily',
      ),
    ).toHaveLength(MAX_OCCURRENCES);
  });
});

describe('nextRowTimes', () => {
  it('moves the next row a day later with the same times', () => {
    // 25 October is the day of the switch to winter time.
    expect(
      nextRowTimes({
        end_datetime: new Date(2026, 9, 24, 20),
        start_datetime: new Date(2026, 9, 24, 18),
      }),
    ).toEqual({
      end_datetime: new Date(2026, 9, 25, 20),
      start_datetime: new Date(2026, 9, 25, 18),
    });
  });

  it('keeps a missing time missing', () => {
    expect(nextRowTimes({ end_datetime: null, start_datetime: null })).toEqual({
      end_datetime: null,
      start_datetime: null,
    });
  });

  it('starts the first row empty', () => {
    expect(nextRowTimes()).toEqual({
      end_datetime: null,
      start_datetime: null,
    });
  });
});

describe('newRequestPayloads', () => {
  it('fills empty cells from the project name and the shared values', () => {
    const [payload] = newRequestPayloads(
      [row({ place: '', title: ' ', type: '' })],
      shared(),
    );

    expect(payload).toMatchObject({
      place: 'F épület, előadóterem',
      title: 'Fizika 1 előadások',
      type: 'Élő közvetítés',
    });
  });

  it('keeps a value typed into a row', () => {
    const [payload] = newRequestPayloads(
      [row({ place: 'Aula', title: 'Megnyitó', type: 'Promóciós videó' })],
      shared(),
    );

    expect(payload).toMatchObject({
      place: 'Aula',
      title: 'Megnyitó',
      type: 'Promóciós videó',
    });
  });

  it('sends the times as ISO strings', () => {
    const [payload] = newRequestPayloads([row()], shared());

    expect(payload.start_datetime).toBe(
      new Date(2026, 10, 3, 10, 15).toISOString(),
    );
    expect(payload.end_datetime).toBe(new Date(2026, 10, 3, 12).toISOString());
  });

  it('accepts the new requests only when asked', () => {
    const [plain] = newRequestPayloads([row()], shared());
    const [accepted] = newRequestPayloads([row()], shared({ accepted: true }));

    expect(plain).not.toHaveProperty('additional_data');
    expect(accepted.additional_data).toEqual({ accepted: true });
  });

  it('gives every new request the project responsible and the requester', () => {
    const payloads = newRequestPayloads(
      [row(), row()],
      shared({ requester: { requester: 7 }, responsible: 5 }),
    );

    expect(payloads).toHaveLength(2);
    for (const payload of payloads) {
      expect(payload).toMatchObject({ requester: 7, responsible: 5 });
    }
  });
});

describe('saveSummary', () => {
  it('summarises only what the save changes', () => {
    expect(saveSummary({ added: 1, created: 2, removed: 0 })).toBe(
      'Mentéskor: 2 új felkérés, 1 hozzáadva',
    );
    expect(saveSummary({ added: 0, created: 0, removed: 3 })).toBe(
      'Mentéskor: 3 eltávolítva a projektből',
    );
  });

  it('says nothing when nothing changes', () => {
    expect(saveSummary({ added: 0, created: 0, removed: 0 })).toBeNull();
  });
});

describe('projectSaveErrors', () => {
  it('puts row errors under their cell and the rest aside', () => {
    expect(
      projectSaveErrors({
        add_requests: ['Megnyitó egy másik projekthez tartozik.'],
        name: ['Kötelező.'],
        new_requests: [
          {},
          {
            end_datetime: ['Későbbinek kell lennie mint az esemény kezdése.'],
            requester_email: ['Hibás e-mail.'],
          },
          { requester_email: ['Hibás e-mail.'] },
        ],
      }),
    ).toEqual({
      fields: [
        ['name', 'Kötelező.'],
        [
          'new_requests.1.end_datetime',
          'Későbbinek kell lennie mint az esemény kezdése.',
        ],
      ],
      other: ['Megnyitó egy másik projekthez tartozik.', 'Hibás e-mail.'],
    });
  });

  it('keeps a detail message', () => {
    expect(projectSaveErrors({ detail: 'Nincs jogosultságod.' })).toEqual({
      fields: [],
      other: ['Nincs jogosultságod.'],
    });
  });
});
