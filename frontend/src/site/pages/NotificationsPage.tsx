import { useMutation, useQuery } from '@tanstack/react-query';
import { BellIcon, CheckCheckIcon } from 'lucide-react';
import { toast } from 'sonner';

import { getApiErrorMessage } from 'api/errors';
import {
  groupByDay,
  markNotificationsRead,
  notificationsQuery,
} from 'helpers/notifications';
import { usePageTitle } from 'hooks/usePageTitle';
import { useUnreadCount } from 'hooks/useUnreadCount';
import LoadError from 'site/components/LoadError';
import NotificationItem, {
  loadErrorText,
  noNotificationsText,
} from 'site/components/NotificationItem';
import PageHero from 'site/components/PageHero';
import { Button } from 'site/components/ui/button';
import { Skeleton } from 'site/components/ui/skeleton';

function LoadingRows() {
  return (
    <div aria-busy className="divide-y pt-6">
      {[0, 1, 2].map((index) => (
        <div className="space-y-2 px-5 py-4 sm:px-6" key={index}>
          <Skeleton className="h-5 w-1/2 max-w-64" />
          <Skeleton className="h-4 w-3/4 max-w-96" />
        </div>
      ))}
    </div>
  );
}

function NotificationsPage() {
  usePageTitle('Értesítések');
  const count = useUnreadCount();
  const { data, isError, isPending, isRefetching, refetch } =
    useQuery(notificationsQuery());
  const markAll = useMutation({
    mutationFn: () => markNotificationsRead(),
    onError: (error) =>
      toast.error('Nem sikerült olvasottnak jelölni az értesítéseket.', {
        description: getApiErrorMessage(error),
      }),
  });

  return (
    <>
      <PageHero
        actions={
          <Button
            className="bg-white text-ink hover:bg-white/85"
            disabled={!count || markAll.isPending}
            onClick={() => markAll.mutate()}
            size="lg"
          >
            <CheckCheckIcon data-icon="inline-start" />
            Mindet elolvastam
          </Button>
        }
        kicker="Értesítések"
        title="Mi történt a felkéréseiddel?"
      >
        <p className="mt-4 max-w-xl text-lg text-white/70">
          {count
            ? `${count} olvasatlan értesítésed van.`
            : 'Mindet elolvastad.'}
        </p>
      </PageHero>
      <div className="relative z-10 mx-auto -mt-16 w-full max-w-6xl px-4 pb-24 sm:px-6">
        <div className="overflow-hidden rounded-3xl border bg-card shadow-sm">
          {isPending && <LoadingRows />}
          {isError && (
            <LoadError
              onRetry={() => void refetch()}
              retrying={isRefetching}
              title={loadErrorText}
            />
          )}
          {data?.length === 0 && (
            <div className="flex flex-col items-center px-6 py-20 text-center">
              <span className="grid size-16 place-items-center rounded-full bg-primary/10 text-primary">
                <BellIcon className="size-7" />
              </span>
              <p className="mt-6 max-w-sm text-muted-foreground">
                {noNotificationsText}
              </p>
            </div>
          )}
          {groupByDay(data ?? []).map((group) => (
            <section className="border-b last:border-b-0" key={group.label}>
              <h2 className="px-5 pt-6 pb-2 font-mono text-xs font-normal tracking-[0.2em] text-muted-foreground uppercase sm:px-6">
                {group.label}
              </h2>
              <ul className="divide-y">
                {group.notifications.map((notification) => (
                  <li key={notification.id}>
                    <NotificationItem notification={notification} />
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </div>
    </>
  );
}

export { NotificationsPage as Component };
