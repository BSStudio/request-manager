import { describe, expect, it } from 'vitest';

import { formatPhone, toE164 } from 'helpers/phone';

describe('formatPhone', () => {
  it('takes a number without a calling code as Hungarian', () => {
    expect(formatPhone('06301234567')).toBe('+36 30 123 4567');
    expect(formatPhone('30 123 4567')).toBe('+36 30 123 4567');
  });

  it('keeps the calling code of a foreign number', () => {
    expect(formatPhone('+4915123456789')).toBe('+49 1512 3456789');
  });

  it('returns what it cannot parse as it is', () => {
    expect(formatPhone('nincs')).toBe('nincs');
  });
});

describe('toE164', () => {
  it('takes a number without a calling code as Hungarian', () => {
    expect(toE164('06 30 123 4567')).toBe('+36301234567');
  });

  it('keeps the calling code of a foreign number', () => {
    expect(toE164('+49 1512 3456789')).toBe('+4915123456789');
  });

  it('returns what it cannot parse as it is', () => {
    expect(toE164('nincs')).toBe('nincs');
  });
});
