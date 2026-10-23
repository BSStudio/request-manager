// The service worker imports this module, so it must not pull in the API
// client or anything else that needs a window.
import { isAdminPath } from 'helpers/isAdminPath';

// Posted to open windows when a push arrives, so their bells refresh.
export const NOTIFICATION_MESSAGE = 'NOTIFICATION';

export type PushPayload = {
  body: string;
  tag: string;
  title: string;
  unreadCount: number;
  url: string;
};

export function base64UrlToUint8Array(value: string) {
  const base64 = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=');
  return Uint8Array.from(atob(padded), (char) => char.charCodeAt(0));
}

export function windowFor<T extends { url: string }>(
  clients: readonly T[],
  target: string,
) {
  const admin = isAdminPath(target);
  return clients.find(
    (client) => isAdminPath(new URL(client.url).pathname) === admin,
  );
}
