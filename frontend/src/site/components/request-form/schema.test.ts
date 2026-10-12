import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  emptyValues,
  eventSchema,
  OTHER_TYPE,
  parseTime,
  toDateTime,
} from 'site/components/request-form/schema';

describe('parseTime', () => {
  it.each([
    ['18:30', '18:30'],
    ['18.30', '18:30'],
    ['18,30', '18:30'],
    ['18 30', '18:30'],
    ['1830', '18:30'],
    ['930', '09:30'],
    ['8:30', '08:30'],
    ['18', '18:00'],
    ['7', '07:00'],
    [' 18:30 ', '18:30'],
  ])('reads %j as %s', (input, time) => {
    expect(parseTime(input)).toBe(time);
  });

  it.each(['', 'este', '24:00', '18:60', '18:3', '18-30', '183'])(
    'rejects %j',
    (input) => {
      expect(parseTime(input)).toBeNull();
    },
  );
});

describe('toDateTime', () => {
  it('joins the date and the time', () => {
    expect(toDateTime('2026-10-20', '1830')).toEqual(
      new Date(2026, 9, 20, 18, 30),
    );
  });

  it('needs both a date and a valid time', () => {
    expect(toDateTime('', '18:30')).toBeNull();
    expect(toDateTime('2026-10-20', 'este')).toBeNull();
  });
});

describe('eventSchema', () => {
  const event = {
    ...emptyValues,
    endDate: '2026-10-20',
    endTime: '20:00',
    place: 'Schönherz Kollégium',
    startDate: '2026-10-20',
    startTime: '18:00',
    title: 'Félévnyitó koncert',
    type: 'Élő közvetítés',
  };

  function errors(values: Partial<typeof event>) {
    const result = eventSchema.safeParse({ ...event, ...values });
    return result.error?.issues.map(({ message, path }) => [
      path.join('.'),
      message,
    ]);
  }

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 12, 12));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('accepts a complete event', () => {
    expect(errors({})).toBeUndefined();
  });

  it('requires the title and the place', () => {
    expect(errors({ place: ' ', title: ' ' })).toEqual([
      ['place', 'Add meg a helyszínt!'],
      ['title', 'Add meg az esemény nevét!'],
    ]);
  });

  it('asks what kind of video when the type is "other"', () => {
    expect(errors({ type: OTHER_TYPE })).toEqual([
      ['typeOther', 'Írd le, milyen videót szeretnél!'],
    ]);
    expect(errors({ type: OTHER_TYPE, typeOther: 'Interjú' })).toBeUndefined();
  });

  it('rejects a start in the past', () => {
    expect(errors({ startDate: '2026-10-12', startTime: '11:59' })).toEqual([
      ['startTime', 'A kezdés nem lehet a múltban.'],
    ]);
  });

  it('rejects an end that is not after the start', () => {
    expect(errors({ endTime: '18:00' })).toEqual([
      ['endTime', 'A befejezés legyen később, mint a kezdés.'],
    ]);
  });

  it('allows an event that ends the next day', () => {
    expect(errors({ endDate: '2026-10-21', endTime: '02:00' })).toBeUndefined();
  });
});
