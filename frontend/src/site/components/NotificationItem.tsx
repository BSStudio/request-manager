import { cn } from 'cn';
import { Link } from 'react-router';

import type { Notification as ApiNotification } from 'api/models';
import { isAdminPath } from 'helpers/isAdminPath';
import { formatMessageTime } from 'site/lib/dates';

export const loadErrorText = 'Nem sikerült betölteni az értesítéseidet.';

export const noNotificationsText =
  'Itt látod majd, ha üzenetet írunk neked, vagy változik valami a felkéréseddel.';

type NotificationItemProps = {
  notification: ApiNotification;
  onOpen?: () => void;
};

export default function NotificationItem({
  notification,
  onOpen,
}: NotificationItemProps) {
  const unread = !notification.read_at;
  const className =
    'flex items-start gap-3 px-4 py-3 transition-colors outline-none hover:bg-muted/40 focus-visible:bg-muted/40 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:ring-inset sm:px-5';
  const content = (
    <>
      <span
        aria-hidden
        className={cn(
          'mt-2 size-2 shrink-0 rounded-full',
          unread && 'bg-primary',
        )}
      />
      <span className="min-w-0 flex-1">
        <span
          className={cn(
            'block',
            unread ? 'font-semibold' : 'text-muted-foreground',
          )}
        >
          {notification.title}
        </span>
        <span className="mt-0.5 line-clamp-2 text-sm text-muted-foreground">
          {notification.body}
        </span>
      </span>
      <time
        className="shrink-0 pt-0.5 text-xs text-muted-foreground"
        dateTime={notification.created}
      >
        {formatMessageTime(new Date(notification.created))}
      </time>
    </>
  );

  return isAdminPath(notification.url) ? (
    <a className={className} href={notification.url} onClick={onOpen}>
      {content}
    </a>
  ) : (
    <Link className={className} onClick={onOpen} to={notification.url}>
      {content}
    </Link>
  );
}
