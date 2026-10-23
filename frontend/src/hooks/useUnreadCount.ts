import { useEffect } from 'react';

import { useQuery, useQueryClient } from '@tanstack/react-query';

import { notificationsQuery, unreadCountQuery } from 'helpers/notifications';
import { NOTIFICATION_MESSAGE } from 'helpers/pushWorker';
import { setAppBadge } from 'helpers/pwa';
import { useSessionUser } from 'helpers/session';

export function useUnreadCount() {
  const loggedIn = useSessionUser() !== null;
  const { data = 0 } = useQuery({ ...unreadCountQuery(), enabled: loggedIn });
  const count = loggedIn ? data : 0;

  useEffect(() => setAppBadge(count), [count]);

  const queryClient = useQueryClient();
  useEffect(() => {
    const refresh = (event: MessageEvent) => {
      if (
        (event.data as { type?: string } | null)?.type === NOTIFICATION_MESSAGE
      ) {
        void queryClient.invalidateQueries({
          queryKey: notificationsQuery().queryKey,
        });
      }
    };
    navigator.serviceWorker?.addEventListener('message', refresh);
    return () =>
      navigator.serviceWorker?.removeEventListener('message', refresh);
  }, [queryClient]);

  return count;
}
