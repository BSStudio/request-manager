import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  formatDay,
  formatMessageTime,
  formatRange,
  formatTime,
} from 'site/lib/dates';

describe('formatDay', () => {
  it('writes the date out in Hungarian', () => {
    expect(formatDay(new Date(2026, 9, 12))).toBe('2026. október 12., hétfő');
  });
});

describe('formatTime', () => {
  it('uses Hungarian time', () => {
    expect(formatTime(new Date('2026-10-12T16:05:00Z'))).toBe('18:05');
  });
});

describe('formatMessageTime', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 12, 15));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('says "ma" for today', () => {
    expect(formatMessageTime(new Date(2026, 9, 12, 9, 5))).toBe('ma 09:05');
  });

  it('says "tegnap" for yesterday', () => {
    expect(formatMessageTime(new Date(2026, 9, 11, 23, 59))).toBe(
      'tegnap 23:59',
    );
  });

  it('leaves out the year within this year', () => {
    expect(formatMessageTime(new Date(2026, 2, 5, 14, 30))).toBe(
      'márc. 5. 14:30',
    );
  });

  it('leaves out the time in earlier years', () => {
    expect(formatMessageTime(new Date(2025, 11, 24, 18))).toBe(
      '2025. dec. 24.',
    );
  });
});

describe('formatRange', () => {
  it('writes the day once for a single day', () => {
    expect(
      formatRange(new Date(2026, 9, 12, 18), new Date(2026, 9, 12, 20, 30)),
    ).toBe('2026. október 12., hétfő, 18:00–20:30');
  });

  it('writes both days for several days', () => {
    expect(
      formatRange(new Date(2026, 9, 12, 18), new Date(2026, 9, 13, 2)),
    ).toBe('2026. október 12., hétfő 18:00 – 2026. október 13., kedd 02:00');
  });
});
