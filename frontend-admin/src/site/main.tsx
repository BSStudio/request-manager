import { StrictMode } from 'react';

import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router/dom';

import { initSentry } from 'helpers/initSentry';
import { Toaster } from 'site/components/ui/sonner';
import { TooltipProvider } from 'site/components/ui/tooltip';
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
    <TooltipProvider>
      <RouterProvider router={router} />
      <Toaster position="bottom-center" />
    </TooltipProvider>
  </StrictMode>,
);
