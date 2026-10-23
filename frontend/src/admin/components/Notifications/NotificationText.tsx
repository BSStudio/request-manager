import { classNames } from 'primereact/utils';

import TimeAgo from 'admin/helpers/TimeAgo';
import type { Notification as ApiNotification } from 'api/models';

export const noNotificationsText =
  'Itt látod majd az új felkéréseket, az üzeneteket és a hozzád rendelt feladatokat.';

const NotificationText = ({
  notification,
  oneLine = false,
}: {
  notification: ApiNotification;
  oneLine?: boolean;
}) => {
  const unread = !notification.read_at;

  return (
    <div className="align-items-start flex flex-1 gap-2 min-w-0">
      <span
        aria-hidden
        className={classNames(
          'border-circle flex-shrink-0 mt-2',
          unread && 'bg-primary',
        )}
        style={{ height: '0.5rem', width: '0.5rem' }}
      />
      <div className="flex-1 min-w-0">
        <div className={unread ? 'font-bold text-900' : 'text-600'}>
          {notification.title}
        </div>
        <div
          className={classNames(
            'mt-1 text-600 text-sm',
            oneLine &&
              'overflow-hidden text-overflow-ellipsis white-space-nowrap',
          )}
        >
          {notification.body}
        </div>
      </div>
      <TimeAgo
        className="flex-shrink-0 text-500 text-xs"
        datetime={notification.created}
        locale="hu_HU"
      />
    </div>
  );
};

export default NotificationText;
