export function formatName(
  lastName?: string | null,
  firstName?: string | null,
) {
  return `${lastName ?? ''} ${firstName ?? ''}`.trim();
}

export function getInitials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase();
}
