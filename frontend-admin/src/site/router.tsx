import { wrapCreateBrowserRouter } from '@sentry/react';
import {
  createBrowserRouter,
  createRoutesFromElements,
  Route,
} from 'react-router';

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
