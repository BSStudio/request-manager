import { QueryClient, queryOptions } from '@tanstack/react-query';

import { meApi } from 'api/http';

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
