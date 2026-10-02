import { useSyncExternalStore } from 'react';

import { isAxiosError } from 'axios';

import { logoutApi, meApi } from 'api/http';
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

// The cached user outlives the session when it expires on the server.
export async function revalidateSession() {
  if (!hasSession()) return;
  try {
    const { data } = await meApi.meRetrieve();
    setSession({
      avatar_url: data.profile.avatar_url,
      groups: data.groups,
      id: data.id,
      name: `${data.last_name ?? ''} ${data.first_name ?? ''}`.trim(),
      role: data.role,
    });
  } catch (error) {
    // The API client already clears the session on 401.
    if (isAxiosError(error) && error.response?.status === 403) clearSession();
  }
}

export async function signOut() {
  try {
    await logoutApi.logoutCreate({});
  } finally {
    clearSession();
  }
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
