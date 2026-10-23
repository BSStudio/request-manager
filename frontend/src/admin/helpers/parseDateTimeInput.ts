import { isValid, parse } from 'date-fns';

// For Calendar's parseDateTime with the mask 9999.99.99 99:99. Its own parser
// takes "2026.11.20 __:__" as midnight, fills the mask with it and leaves no
// room to type the time; a throw keeps the input as typed until it is whole.
export function parseDateTimeInput(text: string): Date {
  const date = parse(text, 'yyyy.MM.dd HH:mm', new Date());
  if (!isValid(date)) throw new Error('Incomplete date and time');
  return date;
}
