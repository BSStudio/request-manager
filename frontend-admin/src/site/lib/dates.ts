import { format, isSameDay } from 'date-fns';
import { hu } from 'date-fns/locale';

export function formatDay(date: Date) {
  return format(date, 'yyyy. MMMM d., EEEE', { locale: hu });
}

export function formatTime(date: Date) {
  return format(date, 'HH:mm');
}

export function formatRange(start: Date, end: Date) {
  return isSameDay(start, end)
    ? `${formatDay(start)}, ${formatTime(start)}–${formatTime(end)}`
    : `${formatDay(start)} ${formatTime(start)} – ${formatDay(end)} ${formatTime(end)}`;
}
