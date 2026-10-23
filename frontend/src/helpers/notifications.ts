import { queryOptions } from '@tanstack/react-query';
import { isSameDay, subDays } from 'date-fns';

import { meApi } from 'api/http';
import type { Notification as ApiNotification } from 'api/models';
import { queryClient } from 'api/queryClient';

const notificationsKey = ['notifications'];

export const notificationsQuery = () =>
  queryOptions({
    queryFn: async () =>
      // Without pagination the API returns a plain list, the generated type
      // only knows the paginated shape.
      (await meApi.meNotificationsList({ pagination: false }))
        .data as unknown as ApiNotification[],
    queryKey: notificationsKey,
  });

export const unreadCountQuery = () =>
  queryOptions({
    queryFn: async () =>
      (await meApi.meNotificationsUnreadCountRetrieve()).data.count,
    queryKey: [...notificationsKey, 'unread-count'],
  });

export async function markNotificationsRead(request?: number) {
  await meApi.meNotificationsReadCreate({
    markNotificationsReadRequest: request === undefined ? {} : { request },
  });
  await queryClient.invalidateQueries({ queryKey: notificationsKey });
}

// For opening a request's page: not worth an error for the reader, the next
// visit tries again.
export function markRequestRead(request: number) {
  markNotificationsRead(request).catch(() => {});
}

type DayLabel = 'Korábban' | 'Ma' | 'Tegnap';

export function groupByDay(notifications: ApiNotification[], now = new Date()) {
  const label = ({ created }: ApiNotification): DayLabel => {
    if (isSameDay(created, now)) return 'Ma';
    if (isSameDay(created, subDays(now, 1))) return 'Tegnap';
    return 'Korábban';
  };
  return (['Ma', 'Tegnap', 'Korábban'] as const)
    .map((day) => ({
      label: day,
      notifications: notifications.filter((item) => label(item) === day),
    }))
    .filter((group) => group.notifications.length > 0);
}

export function adminRouterPath(url: string) {
  return url.replace(/^\/admin/, '');
}

export function unreadLabel(count: number) {
  return count ? `Értesítések, ${count} olvasatlan` : 'Értesítések';
}
