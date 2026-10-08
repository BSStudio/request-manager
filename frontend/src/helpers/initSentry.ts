import { useEffect } from 'react';

import { init, reactRouterBrowserTracingIntegration } from '@sentry/react';
import {
  createRoutesFromChildren,
  matchRoutes,
  useLocation,
  useNavigationType,
} from 'react-router';

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
      urlQueryParams: privateHeaders,
      userInfo: false,
    },
    dsn: import.meta.env.VITE_SENTRY_URL,
    initialScope: { tags: { app } },
    integrations: [
      reactRouterBrowserTracingIntegration({
        createRoutesFromChildren,
        matchRoutes,
        useEffect,
        useLocation,
        useNavigationType,
      }),
    ],
    tunnel: '/api/v1/misc/tunnel',
  });
}
