import { StrictMode } from 'react';

import { QueryClientProvider } from '@tanstack/react-query';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router/dom';

import { initSentry } from 'helpers/initSentry';
import { Toaster } from 'site/components/ui/sonner';
import { queryClient } from 'site/lib/queries';
import { revalidateSession } from 'site/lib/session';
import router from 'site/router';

import 'site/index.css';

if (import.meta.env.PROD) {
  initSentry(import.meta.env.VITE_SENTRY_URL);
}

void revalidateSession();

const root = createRoot(document.getElementById('root') as HTMLElement);
root.render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <Toaster position="bottom-center" />
    </QueryClientProvider>
  </StrictMode>,
);
