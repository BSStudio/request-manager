export function formatName(
  lastName?: string | null,
  firstName?: string | null,
) {
  return `${lastName ?? ''} ${firstName ?? ''}`.trim();
}
