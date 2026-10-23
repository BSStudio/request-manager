import { afterEach, describe, expect, it, vi } from 'vitest';

import { meApi } from 'api/http';
import {
  disablePush,
  enablePush,
  readPushState,
  syncPushSubscription,
} from 'helpers/push';
import { isStandalone } from 'helpers/pwa';

vi.mock('api/http', () => ({
  meApi: {
    mePushSubscriptionsCreate: vi.fn(),
    mePushSubscriptionsRemoveCreate: vi.fn(),
  },
}));
vi.mock('helpers/pwa', () => ({ isStandalone: vi.fn(() => false) }));

const iPhone =
  'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1';

function fakeSubscription() {
  const json = {
    endpoint: 'https://fcm.googleapis.com/fcm/send/abc',
    keys: { auth: 'auth', p256dh: 'p256dh' },
  };
  return {
    endpoint: json.endpoint,
    toJSON: () => json,
    unsubscribe: vi.fn(() => Promise.resolve(true)),
  };
}

function stubBrowser({
  answer = 'default',
  permission = 'default',
  push = true,
  subscription = null,
  userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/141.0',
}: {
  answer?: NotificationPermission;
  permission?: NotificationPermission;
  push?: boolean;
  subscription?: ReturnType<typeof fakeSubscription> | null;
  userAgent?: string;
} = {}) {
  const pushManager = {
    getSubscription: vi.fn(() => Promise.resolve(subscription)),
    subscribe: vi.fn(() => Promise.resolve(fakeSubscription())),
  };
  const notification = {
    permission,
    requestPermission: vi.fn(() => {
      notification.permission = answer;
      return Promise.resolve(answer);
    }),
  };
  vi.stubGlobal('Notification', notification);
  vi.stubGlobal('navigator', {
    maxTouchPoints: 0,
    serviceWorker: {
      getRegistration: () =>
        Promise.resolve(push ? { pushManager } : undefined),
    },
    userAgent,
  });
  return { notification, pushManager };
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe('readPushState', () => {
  it('is unsupported without a service worker', async () => {
    stubBrowser({ push: false });
    expect(await readPushState()).toBe('unsupported');
  });

  it('asks iPhone users to add the page to the home screen', async () => {
    stubBrowser({ push: false, userAgent: iPhone });
    expect(await readPushState()).toBe('ios-install');

    vi.mocked(isStandalone).mockReturnValueOnce(true);
    expect(await readPushState()).toBe('unsupported');
  });

  it('reads the permission, then the subscription', async () => {
    stubBrowser({ permission: 'denied' });
    expect(await readPushState()).toBe('denied');

    stubBrowser({ permission: 'granted', subscription: fakeSubscription() });
    expect(await readPushState()).toBe('on');

    stubBrowser({ permission: 'granted' });
    expect(await readPushState()).toBe('off');
  });
});

describe('enablePush', () => {
  it('does not subscribe when the prompt is refused', async () => {
    const { pushManager } = stubBrowser({ answer: 'denied' });

    expect(await enablePush('-_8')).toBe('denied');
    expect(pushManager.subscribe).not.toHaveBeenCalled();
  });

  it('subscribes and hands the subscription to the server', async () => {
    const { pushManager } = stubBrowser({ answer: 'granted' });

    expect(await enablePush('-_8')).toBe('on');
    expect(pushManager.subscribe).toHaveBeenCalledExactlyOnceWith({
      applicationServerKey: new Uint8Array([251, 255]),
      userVisibleOnly: true,
    });
    expect(meApi.mePushSubscriptionsCreate).toHaveBeenCalledExactlyOnceWith({
      pushSubscriptionRequest: fakeSubscription().toJSON(),
    });
  });
});

describe('disablePush', () => {
  it('tells the server, then unsubscribes', async () => {
    const subscription = fakeSubscription();
    stubBrowser({ permission: 'granted', subscription });

    await disablePush();

    expect(
      meApi.mePushSubscriptionsRemoveCreate,
    ).toHaveBeenCalledExactlyOnceWith({
      pushSubscriptionRemoveRequest: { endpoint: subscription.endpoint },
    });
    expect(subscription.unsubscribe).toHaveBeenCalledOnce();
  });

  it('unsubscribes even when the server cannot be told', async () => {
    const subscription = fakeSubscription();
    stubBrowser({ permission: 'granted', subscription });
    vi.mocked(meApi.mePushSubscriptionsRemoveCreate).mockRejectedValueOnce(
      new Error('offline'),
    );

    await expect(disablePush()).rejects.toThrow('offline');
    expect(subscription.unsubscribe).toHaveBeenCalledOnce();
  });
});

describe('syncPushSubscription', () => {
  it('hands an existing subscription over again, quietly', async () => {
    stubBrowser({ permission: 'granted', subscription: fakeSubscription() });
    vi.mocked(meApi.mePushSubscriptionsCreate).mockRejectedValueOnce(
      new Error('offline'),
    );

    await expect(syncPushSubscription()).resolves.toBeUndefined();
    expect(meApi.mePushSubscriptionsCreate).toHaveBeenCalledOnce();
  });
});
