import { useEffect } from 'react';

import { captureException } from '@sentry/react';
import { isAxiosError } from 'axios';
import { isRouteErrorResponse } from 'react-router';

// The router catches errors thrown while loading or rendering a page, so
// Sentry would not see them. HTTP errors are not frontend bugs: a missing page
// is expected and the backend reports its own failures.
export function useReportRouteError(error: unknown) {
  useEffect(() => {
    if (!error || isRouteErrorResponse(error) || isAxiosError(error)) return;
    captureException(error);
  }, [error]);
}
