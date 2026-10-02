import React from 'react';

import { isAdminPath } from 'helpers/isAdminPath';
import { hasSession, setRedirectedFrom } from 'helpers/LocalStorageHelper';

type AuthenticationProviderProps = {
  children: React.JSX.Element;
};

export const AuthenticationProvider = ({
  children,
}: AuthenticationProviderProps) => {
  if (!hasSession() && isAdminPath(window.location.pathname)) {
    setRedirectedFrom(window.location.pathname);
    window.location.replace('/login');
    return;
  }

  return children;
};
