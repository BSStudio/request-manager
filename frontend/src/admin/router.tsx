import { wrapCreateBrowserRouter } from '@sentry/react';
import { BlockUI } from 'primereact/blockui';
import { ProgressSpinner } from 'primereact/progressspinner';
import { createBrowserRouter, type LoaderFunctionArgs } from 'react-router';

import {
  projectRetrieveQuery,
  requestRetrieveQuery,
  requestVideoRetrieveQuery,
} from 'admin/api/queries';
import Layout from 'admin/Layout';
import ErrorPage from 'admin/pages/ErrorPage';
import type { loaderData as userProfileLoaderData } from 'admin/pages/UserProfilePage';
import { queryClient } from 'api/queryClient';

// These read the titles the breadcrumbs show. React Router reruns a loader only
// when its route's params change, so the editors revalidate after a save.
async function requestLoader({ params }: LoaderFunctionArgs) {
  if (!params.requestId) {
    throw new Error('No request ID provided');
  }
  const request = await queryClient.query({
    ...requestRetrieveQuery(params.requestId),
    staleTime: 'static',
  });
  return { requestId: params.requestId, requestTitle: request.title };
}

async function projectLoader({ params }: LoaderFunctionArgs) {
  if (!params.projectId) {
    throw new Error('No project ID provided');
  }
  const project = await queryClient.query({
    ...projectRetrieveQuery(params.projectId),
    staleTime: 'static',
  });
  return { projectId: params.projectId, projectName: project.name };
}

async function videoLoader({ params }: LoaderFunctionArgs) {
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

type projectLoaderData = Awaited<ReturnType<typeof projectLoader>>;
type requestLoaderData = Awaited<ReturnType<typeof requestLoader>>;
type videoLoaderData = Awaited<ReturnType<typeof videoLoader>>;

function LayoutErrorBoundary() {
  return (
    <Layout>
      <ErrorPage />
    </Layout>
  );
}

function HydrateFallback() {
  return <BlockUI blocked={true} fullScreen template={<ProgressSpinner />} />;
}

const sentryCreateBrowserRouter = wrapCreateBrowserRouter(createBrowserRouter);

const router = sentryCreateBrowserRouter(
  [
    {
      path: '/',
      Component: Layout,
      ErrorBoundary: LayoutErrorBoundary,
      HydrateFallback,
      children: [
        { index: true, lazy: () => import('admin/pages/LandingPage') },
        {
          path: 'requests',
          handle: { crumb: () => 'Felkérések' },
          children: [
            { index: true, lazy: () => import('admin/pages/RequestsListPage') },
            {
              path: 'new',
              handle: { crumb: () => 'Új' },
              lazy: () => import('admin/pages/RequestCreatorEditorPage'),
            },
            {
              path: 'report',
              handle: { crumb: () => 'Havi beszámoló' },
              lazy: () => import('admin/pages/MonthlyReportPage'),
            },
            {
              path: ':requestId',
              handle: {
                crumb: ({ requestTitle }: requestLoaderData) => requestTitle,
              },
              loader: requestLoader,
              children: [
                {
                  index: true,
                  lazy: () => import('admin/pages/RequestDetailsPage'),
                },
                {
                  path: 'edit',
                  handle: { crumb: () => 'Szerkesztés' },
                  lazy: () => import('admin/pages/RequestCreatorEditorPage'),
                },
                {
                  path: 'videos',
                  handle: { crumb: () => 'Videók' },
                  children: [
                    {
                      index: true,
                      lazy: () => import('admin/pages/VideosListPage'),
                    },
                    {
                      path: 'new',
                      handle: { crumb: () => 'Új videó' },
                      lazy: () => import('admin/pages/VideoCreatorEditorPage'),
                    },
                    {
                      path: ':videoId',
                      handle: {
                        crumb: ({ videoTitle }: videoLoaderData) => videoTitle,
                      },
                      loader: videoLoader,
                      children: [
                        {
                          index: true,
                          lazy: () => import('admin/pages/VideoDetailsPage'),
                        },
                        {
                          path: 'edit',
                          handle: { crumb: () => 'Szerkesztés' },
                          lazy: () =>
                            import('admin/pages/VideoCreatorEditorPage'),
                        },
                      ],
                    },
                  ],
                },
              ],
            },
          ],
        },
        {
          path: 'projects',
          handle: { crumb: () => 'Projektek' },
          children: [
            { index: true, lazy: () => import('admin/pages/ProjectsListPage') },
            {
              path: 'new',
              handle: { crumb: () => 'Új' },
              lazy: () => import('admin/pages/ProjectCreatorEditorPage'),
            },
            {
              path: ':projectId',
              handle: {
                crumb: ({ projectName }: projectLoaderData) => projectName,
              },
              loader: projectLoader,
              lazy: () => import('admin/pages/ProjectCreatorEditorPage'),
            },
          ],
        },
        {
          path: 'search',
          handle: { crumb: () => 'Keresés' },
          lazy: () => import('admin/pages/SearchPage'),
        },
        {
          path: 'todos',
          handle: { crumb: () => 'Feladatok' },
          lazy: () => import('admin/pages/TodosPage'),
        },
        {
          path: 'users',
          handle: { crumb: () => 'Felhasználók' },
          children: [
            { index: true, lazy: () => import('admin/pages/UsersListPage') },
            {
              path: ':userId',
              handle: {
                crumb: ({ userFullName }: userProfileLoaderData) =>
                  userFullName,
              },
              lazy: () => import('admin/pages/UserProfilePage'),
            },
          ],
        },
        { path: 'error', Component: ErrorPage },
      ],
    },
  ],
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
