import { useSyncExternalStore } from 'react';

import { logoutApi } from 'api/http';
import {
  clearSession,
  getAccessToken,
  getAvatar,
  getName,
  getRefreshToken,
  getUserId,
  isPrivileged,
  isRefreshTokenExpired,
} from 'helpers/LocalStorageHelper';

export type SessionUser = {
  avatar?: string;
  id: number;
  isPrivileged: boolean;
  name: string;
};

function readUser(): SessionUser | null {
  if (!getAccessToken() || isRefreshTokenExpired()) return null;
  return {
    avatar: getAvatar(),
    id: getUserId(),
    isPrivileged: isPrivileged(),
    name: getName(),
  };
}

let user = readUser();
const listeners = new Set<() => void>();

export function notifySessionChange() {
  user = readUser();
  listeners.forEach((listener) => listener());
}

// Logging in or out in another tab.
window.addEventListener('storage', notifySessionChange);

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useSessionUser() {
  return useSyncExternalStore(subscribe, () => user);
}

export async function signOut() {
  try {
    await logoutApi.logoutCreate({ refresh: getRefreshToken() });
  } finally {
    clearSession();
    notifySessionChange();
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
