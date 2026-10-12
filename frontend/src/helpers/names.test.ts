import { describe, expect, it } from 'vitest';

import { formatName } from 'helpers/names';

describe('formatName', () => {
  it('puts the last name first', () => {
    expect(formatName('Minta', 'Anna')).toBe('Minta Anna');
  });

  it('leaves out a missing part', () => {
    expect(formatName('Minta', null)).toBe('Minta');
    expect(formatName(undefined, 'Anna')).toBe('Anna');
    expect(formatName(null, undefined)).toBe('');
  });
});
