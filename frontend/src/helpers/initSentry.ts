import { useEffect } from 'react';

import {
  init,
  reactRouterBrowserTracingIntegration,
  showReportDialog,
} from '@sentry/react';
import {
  createRoutesFromChildren,
  matchRoutes,
  useLocation,
  useNavigationType,
} from 'react-router';

import { getName } from 'helpers/LocalStorageHelper';

const privateHeaders = {
  deny: ['forwarded', '-ip', 'remote-', 'via', '-user'],
};

export function initSentry(app: 'admin' | 'site') {
  if (!import.meta.env.PROD) return;
  init({
    beforeSend(event) {
      if (event.exception) {
        showReportDialog({
          eventId: event.event_id,
          user: {
            name: getName(),
          },
        });
      }
      return event;
    },
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
