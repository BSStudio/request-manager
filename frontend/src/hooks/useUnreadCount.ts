import { useEffect } from 'react';

import { useQuery } from '@tanstack/react-query';

import { unreadCountQuery } from 'helpers/notifications';
import { setAppBadge } from 'helpers/pwa';
import { useSessionUser } from 'helpers/session';

export function useUnreadCount() {
  const loggedIn = useSessionUser() !== null;
  const { data = 0 } = useQuery({ ...unreadCountQuery(), enabled: loggedIn });
  const count = loggedIn ? data : 0;

  useEffect(() => setAppBadge(count), [count]);

  return count;
}
