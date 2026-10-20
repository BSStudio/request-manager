import { isObject } from 'admin/helpers/pickDirtyFields';

// The API deep-merges additional_data and removes the keys sent as null, so a
// missing key and null mean the same.
export function diffAdditionalData(original: object, edited: object) {
  const before = original as Record<string, unknown>;
  const after = edited as Record<string, unknown>;
  const diff: Record<string, unknown> = {};
  for (const key of new Set([...Object.keys(before), ...Object.keys(after)])) {
    const was = before[key] ?? null;
    const is = after[key] ?? null;
    if (isObject(was) && isObject(is)) {
      const nested = diffAdditionalData(was, is);
      if (Object.keys(nested).length) diff[key] = nested;
    } else if (JSON.stringify(was) !== JSON.stringify(is)) {
      diff[key] = is;
    }
  }
  return diff;
}
