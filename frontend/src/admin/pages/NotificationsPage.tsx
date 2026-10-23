import { useMutation, useQuery } from '@tanstack/react-query';
import { Button } from 'primereact/button';
import { ProgressBar } from 'primereact/progressbar';
import { Ripple } from 'primereact/ripple';
import { href } from 'react-router';

import LinkButton from 'admin/components/LinkButton/LinkButton';
import NotificationLink from 'admin/components/Notifications/NotificationLink';
import NotificationText, {
  noNotificationsText,
} from 'admin/components/Notifications/NotificationText';
import { showErrorToast } from 'admin/helpers/showErrorToast';
import { getUserId } from 'helpers/LocalStorageHelper';
import {
  groupByDay,
  markNotificationsRead,
  notificationsQuery,
} from 'helpers/notifications';
import { pushPageHint } from 'helpers/push';
import { usePushOffered } from 'hooks/usePushSubscription';
import { useUnreadCount } from 'hooks/useUnreadCount';

const NotificationsPage = () => {
  const count = useUnreadCount();
  const pushOffered = usePushOffered();
  const { data, isError, isLoading, isRefetching, refetch } =
    useQuery(notificationsQuery());
  const markAll = useMutation({
    mutationFn: () => markNotificationsRead(),
    onError: (error) => showErrorToast(error),
  });

  return (
    <div className="p-3 sm:p-5 surface-ground">
      <div className="align-items-center flex flex-wrap gap-2 justify-content-between mb-3">
        <div className="font-medium text-900 text-xl">Értesítések</div>
        <Button
          disabled={!count || markAll.isPending}
          icon="pi pi-check-square"
          label="Mindet elolvastam"
          onClick={() => markAll.mutate()}
          outlined
        />
      </div>
      {pushOffered && (
        <div className="align-items-center flex flex-wrap gap-2 mb-3 text-600">
          <i className="pi pi-bell" />
          <span>{pushPageHint}</span>
          <LinkButton
            buttonProps={{
              className: 'p-button-sm p-button-text px-1 py-0',
              icon: 'pi pi-angle-right',
              label: 'Ugrás',
            }}
            linkProps={{
              to: `${href('/users/:userId', { userId: getUserId().toString() })}?section=notifications`,
            }}
          />
        </div>
      )}
      <div className="border-round p-3 shadow-2 sm:p-4 surface-card">
        {isLoading && <ProgressBar mode="indeterminate" />}
        {isError && (
          <div className="align-items-center flex flex-wrap gap-3">
            <span className="text-600">
              Nem sikerült betölteni az értesítéseket.
            </span>
            <Button
              label="Újratöltés"
              loading={isRefetching}
              onClick={() => void refetch()}
              outlined
              size="small"
            />
          </div>
        )}
        {data?.length === 0 && (
          <p className="m-0 text-600">{noNotificationsText}</p>
        )}
        {groupByDay(data ?? []).map((group) => (
          <section className="mb-3" key={group.label}>
            <h2 className="font-medium m-0 mb-2 text-500 text-sm uppercase">
              {group.label}
            </h2>
            <ul className="list-none m-0 p-0">
              {group.notifications.map((notification) => (
                <li
                  className="align-items-center border-top-1 flex gap-3 py-3 surface-border"
                  key={notification.id}
                >
                  <NotificationText notification={notification} />
                  <NotificationLink
                    aria-label="Ugrás a felkéréshez"
                    className="no-underline p-button p-button-icon-only p-button-outlined p-component p-ripple"
                    notification={notification}
                  >
                    <span className="p-button-icon p-c pi pi-sign-in" />
                    <span className="p-button-label p-c">&nbsp;</span>
                    <Ripple />
                  </NotificationLink>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
};

export { NotificationsPage as Component };
