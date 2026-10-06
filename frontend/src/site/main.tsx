import { StrictMode } from 'react';

import { QueryClientProvider } from '@tanstack/react-query';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router/dom';

import { queryClient } from 'api/queryClient';
import { initSentry } from 'helpers/initSentry';
import { revalidateSession } from 'helpers/session';
import { Toaster } from 'site/components/ui/sonner';
import router from 'site/router';

import 'site/index.css';

initSentry('site');

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
