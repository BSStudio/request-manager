const isObject = (value: unknown): value is object =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

// Nested objects keep only their dirty keys: the API deep-merges
// additional_data.
export function pickDirtyFields<T extends object>(
  values: T,
  dirtyFields: object,
): Partial<T> {
  const picked: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(values)) {
    const dirty: unknown = (dirtyFields as Record<string, unknown>)[key];
    if (!dirty) continue;
    picked[key] =
      isObject(dirty) && isObject(value)
        ? pickDirtyFields(value, dirty)
        : value;
  }
  return picked as Partial<T>;
}
