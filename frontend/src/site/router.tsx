import { wrapCreateBrowserRouter } from '@sentry/react';
import { createBrowserRouter } from 'react-router';

import RequireLogin from 'site/components/RequireLogin';
import Layout, { type SiteRouteHandle } from 'site/Layout';
import ErrorPage from 'site/pages/ErrorPage';
import NotFoundPage from 'site/pages/NotFoundPage';

const overlayHeader: SiteRouteHandle = { overlayHeader: true };

function HydrateFallback() {
  return <div className="min-h-svh bg-background" />;
}

const sentryCreateBrowserRouter = wrapCreateBrowserRouter(createBrowserRouter);

const router = sentryCreateBrowserRouter([
  {
    path: '/',
    Component: Layout,
    ErrorBoundary: ErrorPage,
    HydrateFallback,
    children: [
      {
        // Keeps the header and footer around errors thrown by the pages.
        ErrorBoundary: ErrorPage,
        children: [
          {
            index: true,
            handle: overlayHeader,
            lazy: () => import('site/pages/HomePage'),
          },
          {
            path: 'login',
            handle: overlayHeader,
            lazy: () => import('site/pages/LoginPage'),
          },
          {
            path: 'new-request',
            handle: overlayHeader,
            lazy: () => import('site/pages/NewRequestPage'),
          },
          {
            path: 'privacy',
            handle: overlayHeader,
            lazy: () => import('site/pages/PrivacyPolicyPage'),
          },
          {
            path: 'redirect',
            lazy: () => import('site/pages/OAuthRedirectPage'),
          },
          {
            path: 'terms',
            handle: overlayHeader,
            lazy: () => import('site/pages/TermsOfServicePage'),
          },
          {
            Component: RequireLogin,
            children: [
              {
                path: 'my-requests',
                handle: overlayHeader,
                lazy: () => import('site/pages/MyRequestsPage'),
              },
              {
                path: 'my-requests/:id',
                handle: overlayHeader,
                lazy: () => import('site/pages/RequestDetailPage'),
              },
              {
                path: 'profile',
                handle: overlayHeader,
                lazy: () => import('site/pages/ProfilePage'),
              },
            ],
          },
          { path: '*', Component: NotFoundPage, handle: overlayHeader },
        ],
      },
    ],
  },
]);

if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    router.dispose();
  });
}

export default router;
