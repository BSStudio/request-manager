import { StrictMode } from 'react';

import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import * as locales from 'primelocale/hu.json';
import { PrimeReactProvider, addLocale } from 'primereact/api';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router/dom';
import { register } from 'timeago.js';
import huLocal from 'timeago.js/esm/lang/hu';

import { initSentry } from 'helpers/initSentry';
import { ThemeProvider } from 'providers/ThemeProvider';
import { ToastProvider } from 'providers/ToastProvider';
import router, { queryClient } from 'router';

import 'bootstrap-icons/font/bootstrap-icons.css';
import 'primeicons/primeicons.css';
import 'primeflex/primeflex.css';

import 'index.css';

if (import.meta.env.PROD) {
  initSentry(import.meta.env.VITE_SENTRY_URL_ADMIN);
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
