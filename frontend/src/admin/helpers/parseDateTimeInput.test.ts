import { describe, expect, it } from 'vitest';

import { parseDateTimeInput } from 'admin/helpers/parseDateTimeInput';

describe('parseDateTimeInput', () => {
  it('reads a complete date and time', () => {
    expect(parseDateTimeInput('2026.11.20 18:30')).toEqual(
      new Date(2026, 10, 20, 18, 30),
    );
  });

  it('refuses a date whose time is still being typed', () => {
    expect(() => parseDateTimeInput('2026.11.20 __:__')).toThrow();
    expect(() => parseDateTimeInput('2026.11.20 1_:__')).toThrow();
  });

  it('refuses a date that does not exist', () => {
    expect(() => parseDateTimeInput('2026.13.40 18:30')).toThrow();
  });
});
