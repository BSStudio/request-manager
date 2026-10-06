import { Semester } from 'helpers/SemesterHelper';

import { AdminTodosListStatusEnum } from './endpoints/admin-api';
import { adminApi } from './http';
import { queryKeys } from './queryKeys';

export const requestCommentsListQuery = (requestId: string | number) => ({
  queryFn: async () => {
    const comments = await adminApi.adminRequestsCommentsList(
      Number(requestId),
      'created',
    );
    return comments.data;
  },
  queryKey: queryKeys.requestComments(requestId),
  refetchInterval: 1000 * 30,
});

export const requestCrewListQuery = (requestId: string | number) => ({
  queryFn: async () => {
    const crew = await adminApi.adminRequestsCrewList(Number(requestId));
    return crew.data.sort((a, b) => a.id - b.id);
  },
  queryKey: queryKeys.requestCrew(requestId),
  refetchInterval: 1000 * 30,
});

export const requestHistoryListQuery = (requestId: string | number) => ({
  queryFn: async () => {
    const history = await adminApi.adminRequestsHistoryList(Number(requestId));
    return history.data;
  },
  queryKey: queryKeys.requestHistory(requestId),
});

export const requestRetrieveQuery = (requestId: string | number) => ({
  queryFn: async () => {
    const request = await adminApi.adminRequestsRetrieve(Number(requestId));
    return request.data;
  },
  queryKey: queryKeys.request(requestId),
  refetchInterval: 1000 * 60 * 5,
});

export const requestTodosListQuery = (requestId: string | number) => ({
  queryFn: async () => {
    const todos = await adminApi.adminRequestsTodosList(Number(requestId));
    return todos.data;
  },
  queryKey: queryKeys.requestTodos(requestId),
  refetchInterval: 1000 * 30,
});

export const requestVideoHistoryListQuery = (
  requestId: string | number,
  videoId: string | number,
) => ({
  queryFn: async () => {
    const history = await adminApi.adminRequestsVideosHistoryList(
      Number(videoId),
      Number(requestId),
    );
    return history.data;
  },
  queryKey: queryKeys.videoHistory(requestId, videoId),
});

export const requestVideosListQuery = (requestId: string | number) => ({
  queryFn: async () => {
    const videos = await adminApi.adminRequestsVideosList(Number(requestId));
    return videos.data;
  },
  queryKey: queryKeys.requestVideos(requestId),
  refetchInterval: 1000 * 30,
});

export const requestVideoRatingRetrieveOwnQuery = (
  requestId: string | number,
  videoId: string | number,
) => ({
  queryFn: async () => {
    const rating = await adminApi.adminRequestsVideosRatingsOwnRetrieve(
      Number(requestId),
      Number(videoId),
    );
    return rating.data;
  },
  queryKey: queryKeys.videoRatingOwn(requestId, videoId),
});

export const requestVideoRatingRetrieveQuery = (
  requestId: string | number,
  videoId: string | number,
  ratingId: string | number,
) => ({
  queryFn: async () => {
    const rating = await adminApi.adminRequestsVideosRatingsRetrieve(
      Number(ratingId),
      Number(requestId),
      Number(videoId),
    );
    return rating.data;
  },
  queryKey: queryKeys.videoRating(requestId, videoId, ratingId),
});

export const requestVideoRatingsListQuery = (
  requestId: string | number,
  videoId: string | number,
) => ({
  queryFn: async () => {
    const ratings = await adminApi.adminRequestsVideosRatingsList(
      Number(requestId),
      Number(videoId),
    );
    return ratings.data;
  },
  queryKey: queryKeys.videoRatings(requestId, videoId),
  refetchInterval: 1000 * 30,
});

export const requestVideoRetrieveQuery = (
  requestId: string | number,
  videoId: string | number,
) => ({
  queryFn: async () => {
    const video = await adminApi.adminRequestsVideosRetrieve(
      Number(videoId),
      Number(requestId),
    );
    return video.data;
  },
  queryKey: queryKeys.video(requestId, videoId),
  refetchInterval: 1000 * 60 * 5,
});

export const requestVideoTodosListQuery = (
  requestId: string | number,
  videoId: string | number,
) => ({
  queryFn: async () => {
    const todos = await adminApi.adminRequestsVideosTodosList(
      Number(requestId),
      Number(videoId),
    );
    return todos.data;
  },
  queryKey: queryKeys.videoTodos(requestId, videoId),
  refetchInterval: 1000 * 30,
});

export const requestsListQuery = (semester: Semester | null) => {
  const afterDate = semester?.afterDate.toISOString().split('T')[0];
  const beforeDate = semester?.beforeDate.toISOString().split('T')[0];

  return {
    queryFn: async () => {
      const requests = await adminApi.adminRequestsList(
        undefined,
        undefined,
        undefined,
        undefined,
        semester ? 200 : 10000,
        undefined,
        undefined,
        afterDate,
        beforeDate,
      );
      return requests.data.results || [];
    },
    queryKey: semester
      ? queryKeys.requestsBySemester(afterDate, beforeDate)
      : queryKeys.requests(),
    refetchInterval: 1000 * 30,
  };
};

export const todosListQuery = (
  assignees: Array<number>,
  ordering: string,
  status: Array<number>,
) => ({
  queryFn: async () => {
    const todos = await adminApi.adminTodosList(
      assignees,
      ordering,
      undefined,
      10000,
      undefined,
      status as AdminTodosListStatusEnum[],
    );
    return todos.data.results || [];
  },
  queryKey: ['todos', assignees, ordering, status],
  refetchInterval: 1000 * 30,
});

export const todoRetrieveQuery = (todoId: string | number) => ({
  queryFn: async () => {
    const todo = await adminApi.adminTodosRetrieve(Number(todoId));
    return todo.data;
  },
  queryKey: queryKeys.todo(todoId),
  refetchInterval: 1000 * 60 * 5,
});

export const usersListQuery = () => ({
  queryFn: async () => {
    const users = await adminApi.adminUsersList(
      undefined,
      undefined,
      undefined,
      undefined,
      10000,
    );
    return users.data.results || [];
  },
  queryKey: queryKeys.users(),
  refetchInterval: 1000 * 30,
});

export const usersRetrieveQuery = (userId: string | number) => ({
  queryFn: async () => {
    const user = await adminApi.adminUsersRetrieve(Number(userId));
    return user.data;
  },
  queryKey: queryKeys.user(userId),
  refetchInterval: 1000 * 60 * 5,
});

export const usersStaffListQuery = () => ({
  gcTime: 1000 * 60 * 60,
  queryFn: async () => {
    const usersStaff = await adminApi.adminUsersList(
      undefined,
      true,
      'full_name',
      undefined,
      10000,
    );
    return usersStaff.data.results || [];
  },
  queryKey: queryKeys.usersStaff(),
});
