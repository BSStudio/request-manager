export function formatVideoLength(seconds: number) {
  const total = Math.round(seconds);
  return [Math.floor(total / 3600), Math.floor(total / 60) % 60, total % 60]
    .map((part) => String(part).padStart(2, '0'))
    .join(':');
}
