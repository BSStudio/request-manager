import { useMutation, useQuery } from '@tanstack/react-query';
import { Button } from 'primereact/button';
import { ProgressBar } from 'primereact/progressbar';

import LinkButton from 'admin/components/LinkButton/LinkButton';
import NotificationText, {
  noNotificationsText,
} from 'admin/components/Notifications/NotificationText';
import { showErrorToast } from 'admin/helpers/showErrorToast';
import type { Notification as ApiNotification } from 'api/models';
import { isAdminPath } from 'helpers/isAdminPath';
import {
  adminRouterPath,
  groupByDay,
  markNotificationsRead,
  notificationsQuery,
} from 'helpers/notifications';
import { useUnreadCount } from 'hooks/useUnreadCount';

const jumpLabel = 'Ugrás a felkéréshez';
const jumpClassName = 'p-button-outlined';
const jumpIcon = 'pi pi-sign-in';

const JumpButton = ({ notification }: { notification: ApiNotification }) =>
  isAdminPath(notification.url) ? (
    <LinkButton
      buttonProps={{
        'aria-label': jumpLabel,
        className: jumpClassName,
        icon: jumpIcon,
      }}
      linkProps={{ to: adminRouterPath(notification.url) }}
    />
  ) : (
    // The site is the other app, so its links load the page.
    <a
      aria-label={jumpLabel}
      className={`no-underline p-button p-button-icon-only p-component ${jumpClassName}`}
      href={notification.url}
    >
      <span className={`p-button-icon ${jumpIcon}`} />
    </a>
  );

const NotificationsPage = () => {
  const count = useUnreadCount();
  const { data, isLoading } = useQuery(notificationsQuery());
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
      <div className="border-round p-3 shadow-2 sm:p-4 surface-card">
        {isLoading && <ProgressBar mode="indeterminate" />}
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
                  <JumpButton notification={notification} />
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
