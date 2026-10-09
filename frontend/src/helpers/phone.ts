import { parsePhoneNumberFromString } from 'libphonenumber-js';

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
