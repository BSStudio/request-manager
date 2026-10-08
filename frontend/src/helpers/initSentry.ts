import { useEffect } from 'react';

import {
  addEventProcessor,
  init,
  reactRouterBrowserTracingIntegration,
} from '@sentry/react';
import {
  createRoutesFromChildren,
  matchRoutes,
  useLocation,
  useNavigationType,
} from 'react-router';

import { getUserId, hasSession } from 'helpers/LocalStorageHelper';

const privateHeaders = {
  deny: ['forwarded', '-ip', 'remote-', 'via', '-user'],
};

export function initSentry(app: 'admin' | 'site') {
  if (!import.meta.env.PROD) return;
  init({
    dataCollection: {
      cookies: false,
      databaseQueryData: false,
      genAI: { inputs: false, outputs: false },
      graphQL: { document: false, variables: false },
      httpBodies: [],
      httpHeaders: {
        request: privateHeaders,
        response: privateHeaders,
      },
      urlQueryParams: false,
      userInfo: false,
    },
    dsn: import.meta.env.VITE_SENTRY_URL,
    initialScope: { tags: { app } },
    integrations: (defaults) => [
      // A session on every page load would make the backend call Sentry each
      // time, for release health we do not use.
      ...defaults.filter(({ name }) => name !== 'BrowserSession'),
      reactRouterBrowserTracingIntegration({
        createRoutesFromChildren,
        // Named after the element, whose alt text or label can be a name.
        enableInp: false,
        matchRoutes,
        useEffect,
        useLocation,
        useNavigationType,
      }),
    ],
    // Clicked elements and visited URLs can carry personal data.
    maxBreadcrumbs: 0,
    tracesSampleRate: 0.15,
    tunnel: '/api/v1/misc/tunnel',
  });
  // Only the ID: personal data stays out of Sentry.
  addEventProcessor((event) =>
    hasSession() ? { ...event, user: { id: getUserId() } } : event,
  );
}
