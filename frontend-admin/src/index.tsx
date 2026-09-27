import { StrictMode, useEffect } from 'react';

import {
  init as sentryInit,
  reactRouterBrowserTracingIntegration,
  showReportDialog,
} from '@sentry/react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import * as locales from 'primelocale/hu.json';
import { PrimeReactProvider, addLocale } from 'primereact/api';
import { createRoot } from 'react-dom/client';
import {
  createRoutesFromChildren,
  matchRoutes,
  useLocation,
  useNavigationType,
} from 'react-router';
import { RouterProvider } from 'react-router/dom';
import { register } from 'timeago.js';
import huLocal from 'timeago.js/esm/lang/hu';

import { getName } from 'helpers/LocalStorageHelper';
import { ThemeProvider } from 'providers/ThemeProvider';
import { ToastProvider } from 'providers/ToastProvider';
import router, { queryClient } from 'router';

import 'bootstrap-icons/font/bootstrap-icons.css';
import 'primeicons/primeicons.css';
import 'primeflex/primeflex.css';

import 'index.css';

if (import.meta.env.PROD) {
  sentryInit({
    beforeSend(event) {
      // Check if it is an exception, and if so, show the report dialog
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
        request: { deny: ['forwarded', '-ip', 'remote-', 'via', '-user'] },
        response: { deny: ['forwarded', '-ip', 'remote-', 'via', '-user'] },
      },
      urlQueryParams: { deny: ['forwarded', '-ip', 'remote-', 'via', '-user'] },
      userInfo: false,
    },
    dsn: import.meta.env.VITE_SENTRY_URL_ADMIN,
    integrations: [
      reactRouterBrowserTracingIntegration({
        createRoutesFromChildren,
        matchRoutes,
        useEffect,
        useLocation,
        useNavigationType,
      }),
    ],
  });
}

addLocale('hu', locales['hu']);

register('hu_HU', huLocal);

const primeReactSettings = {
  locale: 'hu',
  ripple: true,
};

const root = createRoot(document.getElementById('root') as HTMLElement);
root.render(
  <StrictMode>
    <PrimeReactProvider value={primeReactSettings}>
      <ThemeProvider>
        <ToastProvider>
          <QueryClientProvider client={queryClient}>
            <RouterProvider router={router} />
            <ReactQueryDevtools />
          </QueryClientProvider>
        </ToastProvider>
      </ThemeProvider>
    </PrimeReactProvider>
  </StrictMode>,
);
