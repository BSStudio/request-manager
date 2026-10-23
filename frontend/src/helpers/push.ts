import { queryOptions } from '@tanstack/react-query';

import { isNotFound } from 'api/errors';
import { meApi } from 'api/http';
import type { PushSubscriptionRequest } from 'api/models';
import { base64UrlToUint8Array } from 'helpers/pushWorker';
import { getPushManager, isStandalone } from 'helpers/pwa';

export type PushState = 'denied' | 'ios-install' | 'off' | 'on' | 'unsupported';

export const pushHints: Partial<Record<PushState, string>> = {
  denied:
    'Letiltottad a push értesítéseket. A böngésző beállításaiban engedélyezheted újra.',
  'ios-install':
    'iPhone-on akkor kapsz push értesítést, ha a Megosztás menüben a Főképernyőhöz adod az oldalt.',
  unsupported: 'Ez a böngésző nem tud push értesítést fogadni.',
};

export const pushDescriptions = {
  admin:
    'Push értesítést kapsz ezen az eszközön az új felkérésekről, az üzenetekről és a hozzád rendelt feladatokról.',
  site: 'Push értesítést kapsz ezen az eszközön, ha üzenetet írunk neked, elvállaljuk a felkérésed vagy közzétesszük a videót.',
};

export const pushPageHint =
  'Ha push értesítést is szeretnél ezen az eszközön, kapcsold be a profilodban.';

export const pushErrors = {
  disable: 'Nem sikerült kikapcsolni a push értesítéseket.',
  enable: 'Nem sikerült bekapcsolni a push értesítéseket.',
};

export const pushKeyQuery = () =>
  queryOptions({
    queryFn: async () => {
      try {
        return (await meApi.mePushSubscriptionsKeyRetrieve()).data.public_key;
      } catch (error) {
        // Push is turned off on the server.
        if (isNotFound(error)) return null;
        throw error;
      }
    },
    queryKey: ['push', 'key'],
  });

export const pushStateQuery = () =>
  queryOptions({ queryFn: readPushState, queryKey: ['push', 'state'] });

function isAppleMobile() {
  return (
    /iPhone|iPad|iPod/.test(navigator.userAgent) ||
    // iPadOS Safari reports itself as a Mac.
    (navigator.userAgent.includes('Macintosh') && navigator.maxTouchPoints > 1)
  );
}

export async function readPushState(): Promise<PushState> {
  const pushManager = await getPushManager();
  if (!pushManager) {
    return isAppleMobile() && !isStandalone() ? 'ios-install' : 'unsupported';
  }
  if (Notification.permission === 'denied') return 'denied';
  return (await pushManager.getSubscription()) ? 'on' : 'off';
}

function saveSubscription(subscription: PushSubscription) {
  return meApi.mePushSubscriptionsCreate({
    // Typed with optional fields, a push subscription always has them.
    pushSubscriptionRequest:
      subscription.toJSON() as unknown as PushSubscriptionRequest,
  });
}

export async function enablePush(publicKey: string): Promise<PushState> {
  // First, while still in the tap: Safari may refuse a prompt after an await.
  const permission = await Notification.requestPermission();
  const pushManager = await getPushManager();
  if (permission !== 'granted' || !pushManager) return readPushState();
  const subscription = await pushManager.subscribe({
    applicationServerKey: base64UrlToUint8Array(publicKey),
    userVisibleOnly: true,
  });
  await saveSubscription(subscription);
  return 'on';
}

export async function disablePush() {
  const subscription = await (await getPushManager())?.getSubscription();
  if (!subscription) return;
  try {
    await meApi.mePushSubscriptionsRemoveCreate({
      pushSubscriptionRemoveRequest: { endpoint: subscription.endpoint },
    });
  } finally {
    // Even when the server was not told, like unsubscribePush.
    await subscription.unsubscribe();
  }
}

// The browser may renew its subscription, and the server drops one the push
// service refused, so each load hands the current one over again.
export async function syncPushSubscription() {
  try {
    const subscription = await (await getPushManager())?.getSubscription();
    if (subscription) await saveSubscription(subscription);
  } catch {
    // The next load tries again.
  }
}
