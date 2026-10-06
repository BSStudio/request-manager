import { getApiErrorMessage } from 'api/errors';

export function getErrorMessage(error: unknown) {
  return getApiErrorMessage(error) ?? 'Ismeretlen hiba történt.';
}
