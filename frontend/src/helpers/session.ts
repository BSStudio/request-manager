import { useSyncExternalStore } from 'react';

import { queryOptions } from '@tanstack/react-query';
import { isAxiosError } from 'axios';

import { loginApi, logoutApi, meApi } from 'api/http';
import type { User } from 'api/models';
import { queryClient } from 'api/queryClient';
import {
  clearSession,
  getAvatar,
  getGroups,
  getName,
  getUserId,
  hasSession,
  isPrivileged,
  SESSION_CHANGE_EVENT,
  setSession,
} from 'helpers/LocalStorageHelper';
import { formatName } from 'helpers/names';

export type CurrentUser = {
  avatar?: string;
  groups: string[];
  id: number;
  isPrivileged: boolean;
  name: string;
};

function readUser(): CurrentUser | null {
  if (!hasSession()) return null;
  return {
    avatar: getAvatar(),
    groups: getGroups(),
    id: getUserId(),
    isPrivileged: isPrivileged(),
    name: getName(),
  };
}

export const meQuery = () =>
  queryOptions({
    queryFn: async () => (await meApi.meRetrieve()).data,
    queryKey: ['me'],
  });

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

export async function signIn(provider: string, code: string, nonce: string) {
  // The check's 401 for an expired session would clear the new one.
  await sessionCheck;
  const { data } = await loginApi.loginSocialCreate({ code, nonce, provider });
  setSession(data);
  queryClient.removeQueries({ queryKey: meQuery().queryKey });
  return data;
}

export async function signOut() {
  try {
    await logoutApi.logoutCreate();
  } catch (error) {
    // Only a 401 means the server has no session left to end.
    if (!isAxiosError(error) || error.response?.status !== 401) throw error;
  }
  clearSession();
  queryClient.clear();
}
