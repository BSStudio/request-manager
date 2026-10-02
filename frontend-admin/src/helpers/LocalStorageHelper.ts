const sessionKeys = [
  'access_token',
  'avatar',
  'groups',
  'name',
  'refresh_exp',
  'refresh_token',
  'role',
  'user_id',
];

export function clearSession() {
  sessionKeys.forEach((key) => localStorage.removeItem(key));
}

export function getAccessToken() {
  return localStorage.getItem('access_token') || '';
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

export function getRefreshToken() {
  return localStorage.getItem('refresh_token') || '';
}

export function getRefreshTokenExpirationTime() {
  return localStorage.getItem('refresh_exp');
}

export function getRole() {
  return localStorage.getItem('role') || '';
}

export function getUserId() {
  return Number(localStorage.getItem('user_id'));
}

export function isAdmin() {
  return getRole() === 'admin';
}

export function isPrivileged() {
  return ['admin', 'staff'].includes(getRole());
}

export function isRefreshTokenExpired() {
  const expirationTime = Number(getRefreshTokenExpirationTime());
  return isNaN(expirationTime) || expirationTime < Date.now() / 1000;
}

export function setAccessToken(accessToken: string) {
  localStorage.setItem('access_token', accessToken);
}

export function setDarkMode(darkMode: boolean) {
  localStorage.setItem('dark-mode', JSON.stringify(darkMode));
}

export function setRedirectedFrom(redirectedFrom: string) {
  localStorage.setItem('redirectedFrom', redirectedFrom);
}

export function setRefreshToken(refreshToken: string) {
  localStorage.setItem('refresh_token', refreshToken);
}

export function setRefreshTokenExpirationTime(refreshTokenExpTime?: number) {
  return localStorage.setItem('refresh_exp', String(refreshTokenExpTime));
}
