import { isObject } from 'admin/helpers/pickDirtyFields';

// A missing key and null mean the same: the API removes the keys sent as null
// and deep-merges the rest. Anything but an object goes as it is, for the API
// to reject.
export function diffAdditionalData(original: object, edited: object): object {
  if (!isObject(edited)) return edited;
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
