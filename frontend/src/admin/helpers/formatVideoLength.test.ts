import { describe, expect, it } from 'vitest';

import { formatVideoLength } from 'admin/helpers/formatVideoLength';

describe('formatVideoLength', () => {
  it('formats seconds as hh:mm:ss', () => {
    expect(formatVideoLength(0)).toBe('00:00:00');
    expect(formatVideoLength(3725)).toBe('01:02:05');
  });

  it('rounds to whole seconds', () => {
    expect(formatVideoLength(61.6)).toBe('00:01:02');
    expect(formatVideoLength(61.4)).toBe('00:01:01');
  });

  it('keeps counting hours past a day', () => {
    expect(formatVideoLength(93600)).toBe('26:00:00');
  });
});
