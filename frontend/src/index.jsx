import { StrictMode, useEffect } from 'react';

import { ThemeProvider, StyledEngineProvider } from '@mui/material/styles';
import {
  init as sentryInit,
  reactRouterBrowserTracingIntegration,
  showReportDialog,
} from '@sentry/react';
import { SnackbarProvider } from 'notistack';
import { createRoot } from 'react-dom/client';
import {
  createRoutesFromChildren,
  matchRoutes,
  useLocation,
  useNavigationType,
} from 'react-router';
import { RouterProvider } from 'react-router/dom';

import theme from 'assets/jss/theme';
import ServiceWorkerUpdate from 'components/ServiceWorkerUpdate';
import router from 'router';

import 'assets/scss/custom-icon-font.scss';
import 'assets/scss/material-kit-react.scss';

if (import.meta.env.PROD) {
  sentryInit({
    beforeSend(event) {
      // Check if it is an exception, and if so, show the report dialog
      if (event.exception) {
        showReportDialog({
          eventId: event.event_id,
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
    dsn: import.meta.env.VITE_SENTRY_URL,
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

const root = createRoot(document.getElementById('root'));
root.render(
  <StrictMode>
    <StyledEngineProvider injectFirst>
      <ThemeProvider theme={theme}>
        <SnackbarProvider
          maxSnack={3}
          preventDuplicate
          autoHideDuration={5000}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
        >
          <ServiceWorkerUpdate />
          <RouterProvider router={router} />
        </SnackbarProvider>
      </ThemeProvider>
    </StyledEngineProvider>
  </StrictMode>,
);
