import type { RequestAdminCreateRequest, UserNestedDetail } from 'api/models';
import { toE164 } from 'helpers/phone';

export type RequesterType = 'self' | 'search' | 'new';

export interface RequesterValues {
  requester: UserNestedDetail | null;
  requester_email: string;
  requester_first_name: string;
  requester_last_name: string;
  requester_mobile: string;
  requesterType: RequesterType;
}

export type RequesterPayload = Pick<
  RequestAdminCreateRequest,
  | 'requester'
  | 'requester_email'
  | 'requester_first_name'
  | 'requester_last_name'
  | 'requester_mobile'
>;

// Without a requester the API files the request under the logged-in user.
// Null: a search without a selected user.
export function requesterPayload(
  values: RequesterValues,
): RequesterPayload | null {
  switch (values.requesterType) {
    case 'self':
      return {};
    case 'search':
      return values.requester ? { requester: values.requester.id } : null;
    case 'new':
      return {
        requester_email: values.requester_email,
        requester_first_name: values.requester_first_name,
        requester_last_name: values.requester_last_name,
        requester_mobile: toE164(values.requester_mobile),
      };
  }
}
