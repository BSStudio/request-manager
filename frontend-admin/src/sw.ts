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
