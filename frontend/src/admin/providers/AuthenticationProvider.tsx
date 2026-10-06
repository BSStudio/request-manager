import React from 'react';

import { setRedirectedFrom } from 'helpers/LocalStorageHelper';
import { useSessionUser } from 'helpers/session';

type AuthenticationProviderProps = {
  children: React.JSX.Element;
};

// Follows the session, so logging out in another tab or losing the staff role
// leaves the admin too.
export const AuthenticationProvider = ({
  children,
}: AuthenticationProviderProps) => {
  const user = useSessionUser();

  if (!user) {
    setRedirectedFrom(window.location.pathname);
    window.location.replace('/login');
    return;
  }

  if (!user.isPrivileged) {
    window.location.replace('/');
    return;
  }

  return children;
};
