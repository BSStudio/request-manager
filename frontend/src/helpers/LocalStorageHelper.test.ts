import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  clearSession,
  getAvatar,
  getGroups,
  getName,
  getUserId,
  hasSession,
  isAdmin,
  isPrivileged,
  popRedirectedFrom,
  SESSION_CHANGE_EVENT,
  setDarkMode,
  setRedirectedFrom,
  setSession,
} from 'helpers/LocalStorageHelper';

const sessionUser = {
  avatar_url: 'https://example.com/avatar.png',
  groups: ['Stáb'],
  id: 42,
  name: 'Minta Anna',
  role: 'staff',
};

describe('session', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('has no session before one is set', () => {
    expect(hasSession()).toBe(false);
    expect(getGroups()).toEqual([]);
    expect(getName()).toBe('');
  });

  it('reads back the user it was set with', () => {
    setSession(sessionUser);

    expect(hasSession()).toBe(true);
    expect(getAvatar()).toBe(sessionUser.avatar_url);
    expect(getGroups()).toEqual(['Stáb']);
    expect(getName()).toBe('Minta Anna');
    expect(getUserId()).toBe(42);
  });

  it('drops the avatar of an earlier user without one', () => {
    setSession(sessionUser);
    setSession({ ...sessionUser, avatar_url: null });

    expect(getAvatar()).toBeUndefined();
  });

  it.each([
    ['admin', true, true],
    ['staff', false, true],
    ['user', false, false],
  ])('a %s is admin: %s, privileged: %s', (role, admin, privileged) => {
    setSession({ ...sessionUser, role });

    expect(isAdmin()).toBe(admin);
    expect(isPrivileged()).toBe(privileged);
  });

  it('clears the session but keeps other settings', () => {
    setSession(sessionUser);
    setDarkMode(true);
    clearSession();

    expect(hasSession()).toBe(false);
    expect(getAvatar()).toBeUndefined();
    expect(localStorage.getItem('dark-mode')).toBe('true');
  });

  it('tells the app when the session changes', () => {
    const listener = vi.fn();
    window.addEventListener(SESSION_CHANGE_EVENT, listener);

    setSession(sessionUser);
    clearSession();

    expect(listener).toHaveBeenCalledTimes(2);
    window.removeEventListener(SESSION_CHANGE_EVENT, listener);
  });
});

describe('popRedirectedFrom', () => {
  it('returns the saved path once', () => {
    setRedirectedFrom('/my-requests');

    expect(popRedirectedFrom()).toBe('/my-requests');
    expect(popRedirectedFrom()).toBeNull();
  });
});
