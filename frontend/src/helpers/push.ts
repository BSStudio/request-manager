import { queryOptions } from '@tanstack/react-query';

import { isNotFound } from 'api/errors';
import { meApi } from 'api/http';
import type { PushSubscriptionRequest } from 'api/models';
import { queryClient } from 'api/queryClient';
import {
  getPushUserId,
  getUserId,
  setPushUserId,
} from 'helpers/LocalStorageHelper';
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
  try {
    const pushManager = await getPushManager();
    if (!pushManager) {
      return isAppleMobile() && !isStandalone() ? 'ios-install' : 'unsupported';
    }
    if (Notification.permission === 'denied') return 'denied';
    return (await pushManager.getSubscription()) ? 'on' : 'off';
  } catch {
    // Service workers blocked along with site data, or no Notification API.
    return 'unsupported';
  }
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
  try {
    await saveSubscription(subscription);
  } catch (error) {
    // Otherwise the switch would show on while the server knows nothing of it.
    await subscription.unsubscribe();
    throw error;
  }
  setPushUserId(getUserId());
  return 'on';
}

// Only in this browser: the server drops the endpoint once the push service
// answers 410 for it.
export async function forgetPushSubscription() {
  // First, so a failed unsubscribe is retried at the next login.
  setPushUserId(null);
  const subscription = await (await getPushManager())?.getSubscription();
  await subscription?.unsubscribe();
}

export async function disablePush() {
  const subscription = await (await getPushManager())?.getSubscription();
  if (!subscription) return;
  try {
    await meApi.mePushSubscriptionsRemoveCreate({
      pushSubscriptionRemoveRequest: { endpoint: subscription.endpoint },
    });
  } finally {
    // Even when the server was not told.
    await forgetPushSubscription();
  }
}

// Runs whenever a session starts or is confirmed. Someone else's subscription
// is dropped, so nobody gets another user's pushes. The user's own is handed
// over again: the browser may have renewed it, or the server dropped it.
export async function syncPushSubscription(userId: number) {
  try {
    const subscription = await (await getPushManager())?.getSubscription();
    if (!subscription) return;
    if (getPushUserId() === userId) {
      await saveSubscription(subscription);
    } else {
      await forgetPushSubscription();
      await queryClient.invalidateQueries({
        queryKey: pushStateQuery().queryKey,
      });
    }
  } catch {
    // The next load tries again.
  }
}
