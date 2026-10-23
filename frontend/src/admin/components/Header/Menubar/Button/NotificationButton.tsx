import { useRef, useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import { Badge } from 'primereact/badge';
import { Ripple } from 'primereact/ripple';
import { StyleClass } from 'primereact/styleclass';
import { Link } from 'react-router';

import NotificationLink from 'admin/components/Notifications/NotificationLink';
import NotificationText, {
  noNotificationsText,
} from 'admin/components/Notifications/NotificationText';
import { notificationsQuery, unreadLabel } from 'helpers/notifications';
import { useUnreadCount } from 'hooks/useUnreadCount';

const latest = 5;

const itemClassName =
  'block hover:surface-hover no-underline p-3 text-color transition-colors transition-duration-150';

const NotificationButton = () => {
  const btnRef = useRef(null);
  const count = useUnreadCount();
  // Loaded once the dropdown is first opened; StyleClass keeps no open state.
  const [opened, setOpened] = useState(false);
  const { data } = useQuery({ ...notificationsQuery(), enabled: opened });

  const close = () => (btnRef.current as HTMLAnchorElement | null)?.click();

  return (
    <li className="border-top-1 lg:border-top-none lg:relative surface-border">
      <StyleClass
        enterActiveClassName="scalein"
        enterFromClassName="hidden"
        hideOnOutsideClick
        leaveActiveClassName="fadeout"
        leaveToClassName="hidden"
        nodeRef={btnRef}
        selector="@next"
      >
        <a
          aria-label={unreadLabel(count)}
          className="align-items-center border-left-2 border-transparent cursor-pointer flex font-medium h-full hover:border-primary hover:text-900 lg:border-bottom-2 lg:border-left-none lg:px-3 lg:py-2 p-3 p-ripple px-6 text-600 transition-colors transition-duration-150"
          onClick={() => setOpened(true)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              event.currentTarget.click();
            }
          }}
          ref={btnRef}
          role="button"
          tabIndex={0}
        >
          <i className="lg:mr-0 lg:text-2xl mr-2 p-overlay-badge pi pi-bell text-base">
            {count > 0 && (
              <Badge
                className="hidden lg:inline-block"
                severity="danger"
                value={count}
              />
            )}
          </i>
          <span className="block font-medium lg:hidden">Értesítések</span>
          {count > 0 && (
            <Badge
              className="lg:hidden ml-auto"
              severity="danger"
              value={count}
            />
          )}
          <Ripple />
        </a>
      </StyleClass>

      <div className="border-50 border-round hidden lg:absolute lg:border-1 lg:px-0 lg:right-0 lg:shadow-2 lg:w-25rem m-0 origin-top px-6 shadow-0 surface-overlay w-full z-5">
        <div className="border-bottom-1 font-medium hidden lg:block p-3 surface-border text-900">
          Értesítések
        </div>
        {data?.length === 0 && (
          <p className="m-0 p-3 text-600">{noNotificationsText}</p>
        )}
        <ul className="list-none m-0 p-0">
          {data?.slice(0, latest).map((notification) => (
            <li
              className="border-bottom-1 surface-border"
              key={notification.id}
            >
              <NotificationLink
                className={itemClassName}
                notification={notification}
                onClick={close}
              >
                <NotificationText notification={notification} oneLine />
              </NotificationLink>
            </li>
          ))}
        </ul>
        <Link
          className="block font-medium no-underline p-3 text-center text-primary"
          onClick={close}
          to="/notifications"
        >
          Összes értesítés
        </Link>
      </div>
    </li>
  );
};

export default NotificationButton;
