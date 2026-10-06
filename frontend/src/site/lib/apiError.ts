import { isAxiosError } from 'axios';

// Flattens DRF's error shapes: a plain string, { detail } or { field: [messages] }.
function firstMessage(data: unknown): string | undefined {
  if (typeof data === 'string') return data || undefined;
  if (Array.isArray(data)) return firstMessage(data[0]);
  if (data && typeof data === 'object') {
    const record = data as Record<string, unknown>;
    return firstMessage(record.detail ?? Object.values(record)[0]);
  }
  return undefined;
}

export function getApiErrorMessage(error: unknown) {
  if (!isAxiosError(error)) return undefined;
  if (!error.response) return 'Nem sikerült elérni a szervert.';
  return firstMessage(error.response.data);
}

export function isNotFound(error: unknown) {
  return isAxiosError(error) && error.response?.status === 404;
}

export function isRateLimited(error: unknown) {
  return isAxiosError(error) && error.response?.status === 429;
}
