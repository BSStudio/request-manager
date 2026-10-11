import { AxiosError, AxiosHeaders } from 'axios';
import { describe, expect, it, vi } from 'vitest';

import {
  getApiErrorMessage,
  isNotFound,
  isRateLimited,
  setFieldErrors,
} from 'api/errors';

function apiError(status: number, data: unknown) {
  return new AxiosError('Request failed', undefined, undefined, undefined, {
    config: { headers: new AxiosHeaders() },
    data,
    headers: {},
    status,
    statusText: '',
  });
}

describe('getApiErrorMessage', () => {
  it.each([
    ['a plain string list', ['Hiba történt.']],
    ['a detail', { detail: 'Hiba történt.' }],
    ['a field error', { title: ['Hiba történt.', 'Másik hiba.'] }],
    ['a nested field error', { requester: { email: ['Hiba történt.'] } }],
    ['a non-field error', { non_field_errors: ['Hiba történt.'] }],
  ])('reads %s', (_, data) => {
    expect(getApiErrorMessage(apiError(400, data))).toBe('Hiba történt.');
  });

  it('says when the server could not be reached', () => {
    expect(getApiErrorMessage(new AxiosError('Network Error'))).toBe(
      'Nem sikerült elérni a szervert.',
    );
  });

  it('ignores an error page', () => {
    expect(
      getApiErrorMessage(apiError(502, '<html>Bad Gateway</html>')),
    ).toBeUndefined();
  });

  it('ignores errors that are not from the API', () => {
    expect(getApiErrorMessage(new Error('Hiba történt.'))).toBeUndefined();
  });
});

describe('isNotFound and isRateLimited', () => {
  it('tell the status apart', () => {
    expect(isNotFound(apiError(404, {}))).toBe(true);
    expect(isNotFound(apiError(429, {}))).toBe(false);
    expect(isRateLimited(apiError(429, {}))).toBe(true);
    expect(isRateLimited(new Error())).toBe(false);
  });
});

describe('setFieldErrors', () => {
  it('sets the messages on their fields, nested ones too', () => {
    const setError = vi.fn();
    const error = apiError(400, {
      requester: { email: ['Érvénytelen e-mail-cím.'] },
      title: ['Túl hosszú.'],
    });

    expect(setFieldErrors(error, setError)).toBe(true);
    expect(setError.mock.calls).toEqual([
      [
        'requester.email',
        { message: 'Érvénytelen e-mail-cím.', type: 'backend' },
      ],
      ['title', { message: 'Túl hosszú.', type: 'backend' }],
    ]);
  });

  it('leaves messages that belong to no field to the caller', () => {
    const setError = vi.fn();
    const error = apiError(400, {
      detail: 'Hiba történt.',
      non_field_errors: ['Hiba történt.'],
    });

    expect(setFieldErrors(error, setError)).toBe(false);
    expect(setError).not.toHaveBeenCalled();
  });

  it('only handles validation errors', () => {
    const setError = vi.fn();

    expect(setFieldErrors(apiError(403, { title: ['Hiba.'] }), setError)).toBe(
      false,
    );
    expect(setFieldErrors(new Error(), setError)).toBe(false);
    expect(setError).not.toHaveBeenCalled();
  });
});
