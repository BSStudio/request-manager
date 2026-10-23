/// <reference lib="webworker" />
import { CacheableResponsePlugin } from 'workbox-cacheable-response';
import { ExpirationPlugin } from 'workbox-expiration';
import {
  cleanupOutdatedCaches,
  createHandlerBoundToURL,
  precacheAndRoute,
} from 'workbox-precaching';
import { NavigationRoute, registerRoute } from 'workbox-routing';
import { CacheFirst } from 'workbox-strategies';

import {
  NOTIFICATION_MESSAGE,
  type PushPayload,
  windowFor,
} from 'helpers/pushWorker';

declare let self: ServiceWorkerGlobalScope;

// Every script and stylesheet of the build, so a tab left open on the old
// version can still load its lazy pages after a deploy removed them.
precacheAndRoute(self.__WB_MANIFEST);
cleanupOutdatedCaches();

// Both apps are the same index.html, the server answers everything else.
registerRoute(
  new NavigationRoute(createHandlerBoundToURL('/index.html'), {
    denylist: [
      /^\/api\//,
      /^\/django-admin\//,
      /^\/health/,
      /^\/livez$/,
      /^\/readyz$/,
      /^\/static\//,
      /\/[^/]+\.[^/]+$/,
    ],
  }),
);

// Fonts and images are cached once used. Their names carry a hash.
registerRoute(
  ({ request, url }) =>
    url.pathname.startsWith('/static/') &&
    (request.destination === 'font' || request.destination === 'image'),
  new CacheFirst({
    cacheName: 'assets',
    plugins: [
      new CacheableResponsePlugin({ statuses: [200] }),
      new ExpirationPlugin({
        maxAgeSeconds: 60 * 60 * 24 * 365,
        maxEntries: 100,
      }),
    ],
  }),
);

// Sent by the update prompt, also by the old app's, which still runs for
// returning visitors until this worker takes over.
self.addEventListener('message', (event) => {
  if ((event.data as { type?: string } | null)?.type === 'SKIP_WAITING') {
    void self.skipWaiting();
  }
});

async function showPush({ body, tag, title, unreadCount, url }: PushPayload) {
  if ('setAppBadge' in self.navigator) {
    await (
      unreadCount
        ? self.navigator.setAppBadge(unreadCount)
        : self.navigator.clearAppBadge()
    ).catch(() => {});
  }
  await self.registration.showNotification(title, {
    body,
    data: { url },
    icon: '/pwa-192x192.png',
    // A newer push about the same request replaces the older one and alerts again.
    renotify: true,
    tag,
  } as NotificationOptions);
  for (const client of await self.clients.matchAll({ type: 'window' })) {
    client.postMessage({ type: NOTIFICATION_MESSAGE });
  }
}

self.addEventListener('push', (event) => {
  if (event.data) {
    event.waitUntil(showPush(event.data.json() as PushPayload));
  }
});

async function openRequest(url: string) {
  const client = windowFor(
    await self.clients.matchAll({ type: 'window' }),
    url,
  );
  if (!client) {
    await self.clients.openWindow(url);
    return;
  }
  // Focus first, while the click still counts as the user's.
  await client.focus();
  await client.navigate(url);
}

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    openRequest((event.notification.data as { url: string }).url),
  );
});
