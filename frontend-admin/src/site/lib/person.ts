import {
  isValidPhoneNumber,
  parsePhoneNumberFromString,
} from 'libphonenumber-js';
import { z } from 'zod';

import type { User } from 'api/models';

export function formatName(
  lastName?: string | null,
  firstName?: string | null,
) {
  return `${lastName ?? ''} ${firstName ?? ''}`.trim();
}

// Any country works with its calling code, a number typed without one is
// taken as Hungarian.
export function formatPhone(phone: string) {
  return (
    parsePhoneNumberFromString(phone, 'HU')?.formatInternational() ?? phone
  );
}

// The API stores numbers in E.164.
export function toE164(phone: string) {
  return parsePhoneNumberFromString(phone, 'HU')?.number ?? phone;
}

// Requests are made in the user's name, so the request form needs all of
// these and sends the user to their profile otherwise.
export function getMissingProfileFields(user: User) {
  return [
    !user.last_name && 'vezetéknév',
    !user.first_name && 'keresztnév',
    !user.email && 'e-mail-cím',
    !user.profile.phone_number && 'telefonszám',
  ].filter((field) => field !== false);
}

export const emailSchema = z.email('Érvényes e-mail-címet adj meg!');

export const nameSchema = (requiredMessage: string) =>
  z
    .string()
    .trim()
    .min(1, requiredMessage)
    .max(150, 'Legfeljebb 150 karakter lehet.');

export const phoneSchema = z
  .string()
  .trim()
  .min(1, 'Add meg a telefonszámod!')
  .refine((value) => isValidPhoneNumber(value, 'HU'), {
    message: 'Érvénytelen telefonszám.',
  });
