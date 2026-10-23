import { useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import { cn } from 'cn';
import { BellIcon, RefreshCwIcon } from 'lucide-react';
import { Link } from 'react-router';

import { notificationsQuery, unreadLabel } from 'helpers/notifications';
import { useUnreadCount } from 'hooks/useUnreadCount';
import NotificationItem, {
  loadErrorText,
  noNotificationsText,
} from 'site/components/NotificationItem';
import { Button } from 'site/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from 'site/components/ui/popover';
import { Skeleton } from 'site/components/ui/skeleton';

const latest = 5;

export default function NotificationBell({
  className,
}: {
  className?: string;
}) {
  const count = useUnreadCount();
  const [open, setOpen] = useState(false);
  const { data, isError, isRefetching, refetch } = useQuery({
    ...notificationsQuery(),
    enabled: open,
  });
  const close = () => setOpen(false);

  return (
    <Popover onOpenChange={setOpen} open={open}>
      <PopoverTrigger asChild>
        <Button
          aria-label={unreadLabel(count)}
          className={cn('relative', className)}
          size="icon"
          variant="ghost"
        >
          <BellIcon />
          {count > 0 && (
            <span
              aria-hidden
              className="absolute top-0.5 right-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-[oklch(0.64_0.17_24)] px-1 text-[0.625rem] leading-none font-semibold text-white"
            >
              {count}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent
        align="end"
        className="w-[min(22rem,calc(100vw-2rem))] p-0"
        collisionPadding={16}
      >
        <p className="border-b px-4 py-3 font-semibold sm:px-5">Értesítések</p>
        {isError && (
          <div className="px-4 py-4 text-sm sm:px-5">
            <p className="text-muted-foreground">{loadErrorText}</p>
            <Button
              className="mt-3"
              disabled={isRefetching}
              onClick={() => void refetch()}
              size="sm"
              variant="outline"
            >
              <RefreshCwIcon
                className={isRefetching ? 'animate-spin' : undefined}
                data-icon="inline-start"
              />
              Újrapróbálom
            </Button>
          </div>
        )}
        {!data && !isError && (
          <div aria-busy className="space-y-2 px-4 py-4 sm:px-5">
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        )}
        {data?.length === 0 && (
          <p className="px-4 py-6 text-sm text-muted-foreground sm:px-5">
            {noNotificationsText}
          </p>
        )}
        {!!data?.length && (
          <ul className="divide-y">
            {data.slice(0, latest).map((notification) => (
              <li key={notification.id}>
                <NotificationItem notification={notification} onOpen={close} />
              </li>
            ))}
          </ul>
        )}
        <Link
          className="block border-t px-4 py-3 text-center text-sm font-medium text-primary transition-colors hover:bg-muted/40"
          onClick={close}
          to="/notifications"
        >
          Összes értesítés
        </Link>
      </PopoverContent>
    </Popover>
  );
}
