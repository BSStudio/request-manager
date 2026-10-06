import React from 'react';

import { isAdminPath } from 'helpers/isAdminPath';
import {
  hasSession,
  isPrivileged,
  setRedirectedFrom,
} from 'helpers/LocalStorageHelper';

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

  if (!isPrivileged() && isAdminPath(window.location.pathname)) {
    window.location.replace('/');
    return;
  }

  return children;
};
