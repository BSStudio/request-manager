import type { ReactNode } from 'react';

import { Link } from 'react-router';

import type { Notification as ApiNotification } from 'api/models';
import { isAdminPath } from 'helpers/isAdminPath';
import { adminRouterPath } from 'helpers/notifications';

type NotificationLinkProps = {
  'aria-label'?: string;
  children: ReactNode;
  className?: string;
  notification: ApiNotification;
  onClick?: () => void;
};

const NotificationLink = ({
  children,
  notification,
  ...props
}: NotificationLinkProps) =>
  isAdminPath(notification.url) ? (
    <Link to={adminRouterPath(notification.url)} {...props}>
      {children}
    </Link>
  ) : (
    <a href={notification.url} {...props}>
      {children}
    </a>
  );

export default NotificationLink;
