import { useEffect, useMemo } from 'react';

import { captureException, isEnabled } from '@sentry/react';
import { isAxiosError } from 'axios';
import { isRouteErrorResponse } from 'react-router';

// The router catches errors thrown while loading or rendering a page, so
// Sentry would not see them. HTTP errors are not frontend bugs: a missing page
// is expected and the backend reports its own failures.
export function useReportRouteError(error: unknown) {
  // A new ID for each error, so feedback about the last one starts over.
  const eventId = useMemo(() => {
    const reported =
      isEnabled() &&
      !!error &&
      !isRouteErrorResponse(error) &&
      !isAxiosError(error);
    return reported ? crypto.randomUUID().replaceAll('-', '') : undefined;
  }, [error]);

  useEffect(() => {
    if (eventId) captureException(error, { event_id: eventId });
  }, [error, eventId]);

  return eventId;
}
