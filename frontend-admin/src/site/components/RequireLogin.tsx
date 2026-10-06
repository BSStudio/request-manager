import { Navigate, Outlet, useLocation } from 'react-router';

import { useSessionUser } from 'site/lib/session';

export default function RequireLogin() {
  const user = useSessionUser();
  const location = useLocation();

  if (!user) {
    return <Navigate replace state={{ from: location.pathname }} to="/login" />;
  }
  return <Outlet />;
}
