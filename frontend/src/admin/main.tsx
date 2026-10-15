import { StrictMode } from 'react';

import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import * as locales from 'primelocale/hu.json';
import { PrimeReactProvider, addLocale } from 'primereact/api';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router/dom';
import { register } from 'timeago.js';
import huLocal from 'timeago.js/esm/lang/hu';

import { ThemeProvider } from 'admin/providers/ThemeProvider';
import { ToastProvider } from 'admin/providers/ToastProvider';
import router from 'admin/router';
import { queryClient } from 'api/queryClient';
import { revalidateSession } from 'helpers/session';

import 'bootstrap-icons/font/bootstrap-icons.css';
import 'primeicons/primeicons.css';
import 'primeflex/primeflex.css';

import 'admin/index.css';

void revalidateSession();

// The admin's date masks type 2026.10.14, which the locale's own 'yy. mm. dd.'
// would not parse.
addLocale('hu', { ...locales['hu'], dateFormat: 'yy.mm.dd' });

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
