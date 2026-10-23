import { describe, expect, it } from 'vitest';

import {
  type RequesterValues,
  requesterPayload,
} from 'admin/helpers/requester';
import type { UserNestedDetail } from 'api/models';

function values(overrides: Partial<RequesterValues>): RequesterValues {
  return {
    requester: null,
    requester_email: '',
    requester_first_name: '',
    requester_last_name: '',
    requester_mobile: '',
    requesterType: 'self',
    ...overrides,
  };
}

function user(id: number): UserNestedDetail {
  return {
    avatar_url: '',
    email: 'minta.anna@example.com',
    full_name: 'Minta Anna',
    id,
    is_staff: false,
    phone_number: '',
  };
}

describe('requesterPayload', () => {
  it('sends nothing for the logged-in user', () => {
    expect(requesterPayload(values({ requesterType: 'self' }))).toEqual({});
  });

  it('sends the id of a found user', () => {
    expect(
      requesterPayload(values({ requester: user(7), requesterType: 'search' })),
    ).toEqual({ requester: 7 });
  });

  it('refuses a search without a selected user', () => {
    expect(requesterPayload(values({ requesterType: 'search' }))).toBeNull();
  });

  it('sends the details of a new user with an E.164 phone number', () => {
    expect(
      requesterPayload(
        values({
          requester_email: 'a@example.com',
          requester_first_name: 'Anna',
          requester_last_name: 'Minta',
          requester_mobile: '06 30 123 4567',
          requesterType: 'new',
        }),
      ),
    ).toEqual({
      requester_email: 'a@example.com',
      requester_first_name: 'Anna',
      requester_last_name: 'Minta',
      requester_mobile: '+36301234567',
    });
  });
});
