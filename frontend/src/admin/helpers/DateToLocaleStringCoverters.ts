export function dateTimeToLocaleString(date: Date, isMobile?: boolean) {
  if (isMobile) {
    return date.toLocaleString('hu-HU', {
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  }
  return date.toLocaleString('hu-HU', {
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    month: 'long',
    weekday: 'long',
    year: 'numeric',
  });
}

export function dateToLocaleString(date: Date, isMobile?: boolean) {
  if (isMobile) {
    return date.toLocaleDateString('hu-HU', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  }
  return date.toLocaleDateString('hu-HU', {
    day: '2-digit',
    month: 'long',
    weekday: 'long',
    year: 'numeric',
  });
}
