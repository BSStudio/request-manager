import { wrapCreateBrowserRouter } from '@sentry/react';
import { BlockUI } from 'primereact/blockui';
import { ProgressSpinner } from 'primereact/progressspinner';
import {
  createBrowserRouter,
  createRoutesFromElements,
  type LoaderFunctionArgs,
  Outlet,
  Route,
} from 'react-router';

import {
  requestRetrieveQuery,
  requestVideoRetrieveQuery,
} from 'admin/api/queries';
import Layout from 'admin/Layout';
import ErrorPage from 'admin/pages/ErrorPage';
import type { loaderData as userProfileLoaderData } from 'admin/pages/UserProfilePage';
import { queryClient } from 'api/queryClient';

export async function requestLoader({ params }: LoaderFunctionArgs) {
  if (!params.requestId) {
    throw new Error('No request ID provided');
  }
  const request = await queryClient.query({
    ...requestRetrieveQuery(params.requestId),
    staleTime: 'static',
  });
  return { requestId: params.requestId, requestTitle: request.title };
}

export async function videoLoader({ params }: LoaderFunctionArgs) {
  if (!params.requestId) {
    throw new Error('No request ID provided');
  }
  if (!params.videoId) {
    throw new Error('No video ID provided');
  }
  const video = await queryClient.query({
    ...requestVideoRetrieveQuery(params.requestId, params.videoId),
    staleTime: 'static',
  });
  return {
    requestId: params.requestId,
    videoId: params.videoId,
    videoTitle: video.title,
  };
}

export type requestLoaderData = Awaited<ReturnType<typeof requestLoader>>;
export type videoLoaderData = Awaited<ReturnType<typeof videoLoader>>;

const sentryCreateBrowserRouter = wrapCreateBrowserRouter(createBrowserRouter);

const router = sentryCreateBrowserRouter(
  createRoutesFromElements(
    <Route
      path="/"
      element={<Layout />}
      hydrateFallbackElement={
        <BlockUI blocked={true} fullScreen template={<ProgressSpinner />} />
      }
      errorElement={
        <Layout>
          <ErrorPage />
        </Layout>
      }
    >
      <Route index lazy={() => import('admin/pages/LandingPage')} />
      <Route
        path="requests"
        element={<Outlet />}
        handle={{
          crumb: () => 'Felkérések',
        }}
      >
        <Route index lazy={() => import('admin/pages/RequestsListPage')} />
        <Route
          path="new"
          lazy={() => import('admin/pages/RequestCreatorEditorPage')}
          handle={{
            crumb: () => 'Új',
          }}
        />
        <Route
          path=":requestId"
          loader={requestLoader}
          handle={{
            crumb: ({ requestTitle }: requestLoaderData) => requestTitle,
          }}
        >
          <Route index lazy={() => import('admin/pages/RequestDetailsPage')} />
          <Route
            path="edit"
            lazy={() => import('admin/pages/RequestCreatorEditorPage')}
            handle={{
              crumb: () => 'Szerkesztés',
            }}
          />
          <Route
            path="videos"
            handle={{
              crumb: () => 'Videók',
            }}
          >
            <Route index lazy={() => import('admin/pages/VideosListPage')} />
            <Route
              path="new"
              lazy={() => import('admin/pages/VideoCreatorEditorPage')}
              handle={{
                crumb: () => 'Új videó',
              }}
            />
            <Route
              path=":videoId"
              loader={videoLoader}
              handle={{
                crumb: ({ videoTitle }: videoLoaderData) => videoTitle,
              }}
            >
              <Route
                index
                lazy={() => import('admin/pages/VideoDetailsPage')}
              />
              <Route
                path="edit"
                lazy={() => import('admin/pages/VideoCreatorEditorPage')}
                handle={{
                  crumb: () => 'Szerkesztés',
                }}
              />
            </Route>
          </Route>
        </Route>
      </Route>
      <Route
        path="search"
        lazy={() => import('admin/pages/SearchPage')}
        handle={{
          crumb: () => 'Keresés',
        }}
      />
      <Route
        path="todos"
        lazy={() => import('admin/pages/TodosPage')}
        handle={{
          crumb: () => 'Feladatok',
        }}
      />
      <Route
        path="users"
        handle={{
          crumb: () => 'Felhasználók',
        }}
      >
        <Route index lazy={() => import('admin/pages/UsersListPage')} />
        <Route
          path=":userId"
          lazy={() => import('admin/pages/UserProfilePage')}
          handle={{
            crumb: ({ userFullName }: userProfileLoaderData) => userFullName,
          }}
        />
      </Route>
      <Route path="error" element={<ErrorPage />} />
    </Route>,
  ),
  {
    basename: '/admin',
  },
);

if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    router.dispose();
  });
}

export default router;
