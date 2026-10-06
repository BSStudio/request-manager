import { isAxiosError } from 'axios';
import type { FieldValues, Path, UseFormSetError } from 'react-hook-form';

function isRecord(data: unknown): data is Record<string, unknown> {
  return !!data && typeof data === 'object' && !Array.isArray(data);
}

// Flattens DRF's error shapes: a plain string, { detail } or { field: [messages] }.
function firstMessage(data: unknown): string | undefined {
  if (typeof data === 'string') return data || undefined;
  if (Array.isArray(data)) return firstMessage(data[0]);
  if (isRecord(data)) {
    return firstMessage(data.detail ?? Object.values(data)[0]);
  }
  return undefined;
}

export function getApiErrorMessage(error: unknown) {
  if (!isAxiosError(error)) return undefined;
  if (!error.response) return 'Nem sikerült elérni a szervert.';
  const { data } = error.response;
  // DRF answers with JSON, so text is an error page of the server or a proxy.
  return typeof data === 'string' ? undefined : firstMessage(data);
}

export function isNotFound(error: unknown) {
  return isAxiosError(error) && error.response?.status === 404;
}

export function isRateLimited(error: unknown) {
  return isAxiosError(error) && error.response?.status === 429;
}

// Shows the messages of a 400 under the form fields they belong to, nested
// serializers included. Returns false for any other error.
export function setFieldErrors<T extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<T>,
) {
  if (!isAxiosError(error) || error.response?.status !== 400) return false;
  const { data } = error.response;
  if (!isRecord(data)) return false;

  const setErrors = (errors: Record<string, unknown>, prefix: string) => {
    Object.entries(errors).forEach(([field, value]) => {
      if (isRecord(value)) {
        setErrors(value, `${prefix}${field}.`);
      } else {
        setError(`${prefix}${field}` as Path<T>, {
          message: firstMessage(value),
          type: 'backend',
        });
      }
    });
  };
  setErrors(data, '');
  return true;
}
