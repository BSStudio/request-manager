import { describe, expect, it } from 'vitest';
import type { z } from 'zod';

import type { User } from 'api/models';
import {
  emailSchema,
  getMissingProfileFields,
  nameSchema,
  phoneSchema,
} from 'site/lib/person';

function firstError(schema: z.ZodType, value: unknown) {
  return schema.safeParse(value).error?.issues[0].message;
}

describe('getMissingProfileFields', () => {
  const user = {
    email: 'minta.anna@example.com',
    first_name: 'Anna',
    last_name: 'Minta',
    phone_number: '+36301234567',
  } as User;

  it('returns nothing for a complete profile', () => {
    expect(getMissingProfileFields(user)).toEqual([]);
  });

  it('lists the missing fields in the order of the form', () => {
    expect(
      getMissingProfileFields({
        ...user,
        email: '',
        first_name: '',
        last_name: '',
        phone_number: '',
      }),
    ).toEqual(['vezetéknév', 'keresztnév', 'e-mail-cím', 'telefonszám']);
  });
});

describe('emailSchema', () => {
  it('accepts an e-mail address', () => {
    expect(firstError(emailSchema, 'minta.anna@example.com')).toBeUndefined();
  });

  it('rejects anything else', () => {
    expect(firstError(emailSchema, 'minta.anna')).toBe(
      'Érvényes e-mail-címet adj meg!',
    );
  });
});

describe('nameSchema', () => {
  const schema = nameSchema('Add meg a neved!');

  it('trims the name', () => {
    expect(schema.parse('  Anna ')).toBe('Anna');
  });

  it('requires a name', () => {
    expect(firstError(schema, '   ')).toBe('Add meg a neved!');
  });

  it('allows at most 150 characters', () => {
    expect(firstError(schema, 'a'.repeat(150))).toBeUndefined();
    expect(firstError(schema, 'a'.repeat(151))).toBe(
      'Legfeljebb 150 karakter lehet.',
    );
  });
});

describe('phoneSchema', () => {
  it('accepts a Hungarian number without a calling code', () => {
    expect(phoneSchema.parse(' 06 30 123 4567 ')).toBe('06 30 123 4567');
  });

  it('accepts a foreign number', () => {
    expect(firstError(phoneSchema, '+49 1512 3456789')).toBeUndefined();
  });

  it('requires a number', () => {
    expect(firstError(phoneSchema, '')).toBe('Add meg a telefonszámod!');
  });

  it('rejects an invalid number', () => {
    expect(firstError(phoneSchema, '123')).toBe('Érvénytelen telefonszám.');
  });
});
