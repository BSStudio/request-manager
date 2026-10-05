import { wrapCreateBrowserRouter } from '@sentry/react';
import {
  createBrowserRouter,
  createRoutesFromElements,
  Route,
} from 'react-router';

import RequireLogin from 'site/components/RequireLogin';
import Layout, { type SiteRouteHandle } from 'site/Layout';
import ErrorPage from 'site/pages/ErrorPage';
import NotFoundPage from 'site/pages/NotFoundPage';

const overlayHeader: SiteRouteHandle = { overlayHeader: true };

const sentryCreateBrowserRouter = wrapCreateBrowserRouter(createBrowserRouter);

const router = sentryCreateBrowserRouter(
  createRoutesFromElements(
    <Route
      element={<Layout />}
      errorElement={<ErrorPage />}
      hydrateFallbackElement={<div className="min-h-svh bg-background" />}
      path="/"
    >
      {/* Keeps the header and footer around errors thrown by the pages. */}
      <Route errorElement={<ErrorPage />}>
        <Route
          handle={overlayHeader}
          index
          lazy={() => import('site/pages/HomePage')}
        />
        <Route
          handle={overlayHeader}
          lazy={() => import('site/pages/LoginPage')}
          path="login"
        />
        <Route
          handle={overlayHeader}
          lazy={() => import('site/pages/NewRequestPage')}
          path="new-request"
        />
        <Route
          lazy={() => import('site/pages/OAuthRedirectPage')}
          path="redirect"
        />
        <Route element={<RequireLogin />}>
          <Route
            handle={overlayHeader}
            lazy={() => import('site/pages/MyRequestsPage')}
            path="my-requests"
          />
          <Route
            handle={overlayHeader}
            lazy={() => import('site/pages/RequestDetailPage')}
            path="my-requests/:id"
          />
          <Route
            handle={overlayHeader}
            lazy={() => import('site/pages/ProfilePage')}
            path="profile"
          />
        </Route>
        <Route element={<NotFoundPage />} handle={overlayHeader} path="*" />
      </Route>
    </Route>,
  ),
);

if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    router.dispose();
  });
}

export default router;
