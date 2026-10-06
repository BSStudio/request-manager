import { QueryClient, queryOptions } from '@tanstack/react-query';

import { meApi, requestsApi } from 'api/http';
import type { RequestList } from 'api/models';
import { isNotFound } from 'site/lib/apiError';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 1000 * 30,
    },
  },
});

export const meQuery = () =>
  queryOptions({
    queryFn: async () => (await meApi.meRetrieve()).data,
    queryKey: ['me'],
  });

export const myRequestsQuery = () =>
  queryOptions({
    queryFn: async () =>
      // Without pagination the API returns a plain list, the generated type
      // only knows the paginated shape.
      (
        await requestsApi.requestsList(
          '-start_datetime',
          undefined,
          undefined,
          false,
        )
      ).data as unknown as RequestList[],
    queryKey: ['requests'],
  });

export const requestQuery = (id: number) =>
  queryOptions({
    queryFn: async () => (await requestsApi.requestsRetrieve(id)).data,
    queryKey: ['requests', id],
    retry: (failureCount, error) => !isNotFound(error) && failureCount < 1,
  });

export const requestCommentsQuery = (id: number) =>
  queryOptions({
    queryFn: async () => (await requestsApi.requestsCommentsList(id)).data,
    queryKey: ['requests', id, 'comments'],
  });

export const requestVideosQuery = (id: number) =>
  queryOptions({
    queryFn: async () => (await requestsApi.requestsVideosList(id)).data,
    queryKey: ['requests', id, 'videos'],
  });
