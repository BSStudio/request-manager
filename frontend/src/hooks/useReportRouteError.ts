import { useEffect, useRef } from 'react';

import { captureException, isInitialized, sendFeedback } from '@sentry/react';
import { useMutation } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { isRouteErrorResponse } from 'react-router';

// The router catches errors thrown while loading or rendering a page, so
// Sentry would not see them. HTTP errors are not frontend bugs: a missing page
// is expected and the backend reports its own failures.
export function useReportRouteError(error: unknown) {
  const reported =
    isInitialized() &&
    !!error &&
    !isRouteErrorResponse(error) &&
    !isAxiosError(error);
  const eventId = useRef<string>(undefined);

  useEffect(() => {
    if (reported) eventId.current = captureException(error);
  }, [error, reported]);

  const feedback = useMutation({
    mutationFn: (message: string) =>
      sendFeedback({ associatedEventId: eventId.current, message }),
  });

  return { feedback, reported };
}
