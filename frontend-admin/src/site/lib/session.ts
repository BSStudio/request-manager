import { useSyncExternalStore } from 'react';

import { isAxiosError } from 'axios';

import { loginApi, logoutApi } from 'api/http';
import type { User } from 'api/models';
import {
  clearSession,
  getAvatar,
  getName,
  getUserId,
  hasSession,
  isPrivileged,
  SESSION_CHANGE_EVENT,
  setSession,
} from 'helpers/LocalStorageHelper';
import type { OAuthProvider } from 'site/lib/oauth';
import { formatName } from 'site/lib/person';
import { meQuery, queryClient } from 'site/lib/queries';

export type SessionUser = {
  avatar?: string;
  id: number;
  isPrivileged: boolean;
  name: string;
};

function readUser(): SessionUser | null {
  if (!hasSession()) return null;
  return {
    avatar: getAvatar(),
    id: getUserId(),
    isPrivileged: isPrivileged(),
    name: getName(),
  };
}

let user = readUser();
const listeners = new Set<() => void>();

function update() {
  user = readUser();
  listeners.forEach((listener) => listener());
}

window.addEventListener(SESSION_CHANGE_EVENT, update);
// Logging in or out in another tab.
window.addEventListener('storage', update);

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useSessionUser() {
  return useSyncExternalStore(subscribe, () => user);
}

export function cacheUser(data: User) {
  queryClient.setQueryData(meQuery().queryKey, data);
  setSession({
    avatar_url: data.profile.avatar_url,
    groups: data.groups,
    id: data.id,
    name: formatName(data.last_name, data.first_name),
    role: data.role,
  });
}

let sessionCheck = Promise.resolve();

// The cached user outlives the session when it expires on the server.
export function revalidateSession() {
  sessionCheck = (async () => {
    if (!hasSession()) return;
    try {
      cacheUser(await queryClient.query(meQuery()));
    } catch (error) {
      // The API client already clears the session on 401.
      if (isAxiosError(error) && error.response?.status === 403) {
        clearSession();
      }
    }
  })();
  return sessionCheck;
}

// Settles once the cached user is confirmed or cleared.
export function whenSessionChecked() {
  return sessionCheck;
}

export async function signIn(provider: OAuthProvider, code: string) {
  // The check's 401 for an expired session would clear the new one.
  await sessionCheck;
  const { data } = await loginApi.loginSocialCreate({ code, provider });
  setSession(data);
  queryClient.removeQueries({ queryKey: meQuery().queryKey });
  return data;
}

export async function signOut() {
  try {
    await logoutApi.logoutCreate({});
  } catch (error) {
    // Only a 401 means the server has no session left to end.
    if (!isAxiosError(error) || error.response?.status !== 401) throw error;
  }
  clearSession();
  queryClient.clear();
}

export function getInitials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase();
}
