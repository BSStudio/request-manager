import { afterEach, describe, expect, it } from 'vitest';

import { getAvatarStyle, getInitials } from 'helpers/avatar';

describe('getInitials', () => {
  it('takes the first letter of the first two names', () => {
    expect(getInitials('Minta Anna Mária')).toBe('MA');
  });

  it('ignores extra spaces and capitalizes', () => {
    expect(getInitials('  ádám   éva ')).toBe('ÁÉ');
  });

  it('returns nothing for an empty name', () => {
    expect(getInitials('')).toBe('');
  });
});

describe('getAvatarStyle', () => {
  afterEach(() => {
    document.documentElement.classList.remove('dark');
  });

  it('gives a name the same color however it is spaced or cased', () => {
    expect(getAvatarStyle(' minta  ANNA ')).toEqual(
      getAvatarStyle('Minta Anna'),
    );
  });

  it('spreads names over several colors', () => {
    const names = ['Minta Anna', 'Teszt Elek', 'Próba Béla', 'Kiss Virág'];
    const colors = new Set(
      names.map((name) => getAvatarStyle(name).backgroundColor),
    );
    expect(colors.size).toBeGreaterThan(1);
  });

  it('mixes the text color with black on the light theme', () => {
    expect(getAvatarStyle('Minta Anna').color).toMatch(/ black\)$/);
  });

  it('mixes the text color with white on the dark theme', () => {
    document.documentElement.classList.add('dark');
    expect(getAvatarStyle('Minta Anna').color).toMatch(/ white\)$/);
  });
});
