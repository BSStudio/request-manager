// Falls back to the raw text, so one unreadable value can't break the whole page.
export function formatJson(value: string) {
  try {
    return JSON.stringify(JSON.parse(value), null, 2);
  } catch {
    return value;
  }
}
