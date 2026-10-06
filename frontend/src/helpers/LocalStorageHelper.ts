import type { SessionUser } from 'api/models';

export const SESSION_CHANGE_EVENT = 'session-change';

// The session cookie decides who is logged in, these keys only cache who it is.
const sessionKeys = ['avatar', 'groups', 'name', 'role', 'user_id'];

export function clearSession() {
  sessionKeys.forEach((key) => localStorage.removeItem(key));
  window.dispatchEvent(new Event(SESSION_CHANGE_EVENT));
}

export function getAvatar() {
  return localStorage.getItem('avatar') || undefined;
}

export function getDarkMode() {
  return localStorage.getItem('dark-mode');
}

export function getGroups() {
  return JSON.parse(localStorage.getItem('groups') || '[]');
}

export function getName() {
  return localStorage.getItem('name') || '';
}

export function getRole() {
  return localStorage.getItem('role') || '';
}

export function getUserId() {
  return Number(localStorage.getItem('user_id'));
}

export function hasSession() {
  return localStorage.getItem('user_id') !== null;
}

export function isAdmin() {
  return getRole() === 'admin';
}

export function isPrivileged() {
  return ['admin', 'staff'].includes(getRole());
}

export function popRedirectedFrom() {
  const redirectedFrom = localStorage.getItem('redirectedFrom');
  localStorage.removeItem('redirectedFrom');
  return redirectedFrom;
}

export function setDarkMode(darkMode: boolean) {
  localStorage.setItem('dark-mode', JSON.stringify(darkMode));
}

export function setRedirectedFrom(redirectedFrom: string) {
  localStorage.setItem('redirectedFrom', redirectedFrom);
}

export function setSession({
  avatar_url,
  groups,
  id,
  name,
  role,
}: SessionUser) {
  if (avatar_url) {
    localStorage.setItem('avatar', avatar_url);
  } else {
    localStorage.removeItem('avatar');
  }
  localStorage.setItem('groups', JSON.stringify(groups));
  localStorage.setItem('name', name);
  localStorage.setItem('role', role);
  localStorage.setItem('user_id', String(id));
  window.dispatchEvent(new Event(SESSION_CHANGE_EVENT));
}
