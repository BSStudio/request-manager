import { Semester } from 'admin/helpers/SemesterHelper';

import { queryKeys } from './queryKeys';
import { AdminTodosListStatusEnum } from '../../api/endpoints/admin-api';
import { adminApi } from '../../api/http';

export const projectRequestsListQuery = (projectId: number) => ({
  queryFn: async () => {
    const requests = await adminApi.adminRequestsList({
      ordering: 'start_datetime',
      pageSize: 10000,
      project: projectId,
    });
    return requests.data.results ?? [];
  },
  queryKey: queryKeys.projectRequests(projectId),
});

export const projectRetrieveQuery = (projectId: string | number) => ({
  queryFn: async () => {
    const project = await adminApi.adminProjectsRetrieve({
      id: Number(projectId),
    });
    return project.data;
  },
  queryKey: queryKeys.project(projectId),
});

export const projectsListQuery = () => ({
  queryFn: async () => {
    const projects = await adminApi.adminProjectsList();
    return projects.data;
  },
  queryKey: queryKeys.projects(),
  refetchInterval: 1000 * 30,
});

export const reportQuery = (dateAfter: string, dateBefore: string) => ({
  queryFn: async () => {
    const report = await adminApi.adminReportRetrieve({
      dateAfter,
      dateBefore,
    });
    return report.data;
  },
  queryKey: queryKeys.report(dateAfter, dateBefore),
});

export const requestCommentsListQuery = (requestId: string | number) => ({
  queryFn: async () => {
    const comments = await adminApi.adminRequestsCommentsList({
      ordering: 'created',
      requestId: Number(requestId),
    });
    return comments.data;
  },
  queryKey: queryKeys.requestComments(requestId),
  refetchInterval: 1000 * 30,
});

export const requestCrewListQuery = (requestId: string | number) => ({
  queryFn: async () => {
    const crew = await adminApi.adminRequestsCrewList({
      requestId: Number(requestId),
    });
    return crew.data.sort((a, b) => a.id - b.id);
  },
  queryKey: queryKeys.requestCrew(requestId),
  refetchInterval: 1000 * 30,
});

export const requestHistoryListQuery = (requestId: string | number) => ({
  queryFn: async () => {
    const history = await adminApi.adminRequestsHistoryList({
      id: Number(requestId),
    });
    return history.data;
  },
  queryKey: queryKeys.requestHistory(requestId),
});

export const requestRetrieveQuery = (requestId: string | number) => ({
  queryFn: async () => {
    const request = await adminApi.adminRequestsRetrieve({
      id: Number(requestId),
    });
    return request.data;
  },
  queryKey: queryKeys.request(requestId),
  refetchInterval: 1000 * 60 * 5,
});

export const requestTodosListQuery = (requestId: string | number) => ({
  queryFn: async () => {
    const todos = await adminApi.adminRequestsTodosList({
      requestId: Number(requestId),
    });
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
    const history = await adminApi.adminRequestsVideosHistoryList({
      id: Number(videoId),
      requestId: Number(requestId),
    });
    return history.data;
  },
  queryKey: queryKeys.videoHistory(requestId, videoId),
});

export const requestVideosListQuery = (requestId: string | number) => ({
  queryFn: async () => {
    const videos = await adminApi.adminRequestsVideosList({
      requestId: Number(requestId),
    });
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
    const rating = await adminApi.adminRequestsVideosRatingsOwnRetrieve({
      requestId: Number(requestId),
      videoId: Number(videoId),
    });
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
    const rating = await adminApi.adminRequestsVideosRatingsRetrieve({
      id: Number(ratingId),
      requestId: Number(requestId),
      videoId: Number(videoId),
    });
    return rating.data;
  },
  queryKey: queryKeys.videoRating(requestId, videoId, ratingId),
});

export const requestVideoRatingsListQuery = (
  requestId: string | number,
  videoId: string | number,
) => ({
  queryFn: async () => {
    const ratings = await adminApi.adminRequestsVideosRatingsList({
      requestId: Number(requestId),
      videoId: Number(videoId),
    });
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
    const video = await adminApi.adminRequestsVideosRetrieve({
      id: Number(videoId),
      requestId: Number(requestId),
    });
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
    const todos = await adminApi.adminRequestsVideosTodosList({
      requestId: Number(requestId),
      videoId: Number(videoId),
    });
    return todos.data;
  },
  queryKey: queryKeys.videoTodos(requestId, videoId),
  refetchInterval: 1000 * 30,
});

export const requestsListQuery = (
  semester: Semester | null,
  page: number,
  pageSize: number,
  ordering: string,
) => {
  const afterDate = semester?.afterDate.toISOString().split('T')[0];
  const beforeDate = semester?.beforeDate.toISOString().split('T')[0];

  return {
    queryFn: async () => {
      const requests = await adminApi.adminRequestsList({
        ordering,
        page,
        pageSize,
        startDatetimeAfter: afterDate,
        startDatetimeBefore: beforeDate,
      });
      return requests.data;
    },
    queryKey: queryKeys.requestsList({
      afterDate,
      beforeDate,
      ordering,
      page,
      pageSize,
    }),
    refetchInterval: 1000 * 30,
  };
};

export const requestsWithoutProjectQuery = (search: string) => ({
  enabled: search.trim().length >= 2,
  queryFn: async () => {
    const requests = await adminApi.adminRequestsList({
      hasProject: false,
      ordering: '-start_datetime',
      pageSize: 50,
      search: search.trim(),
    });
    return requests.data.results ?? [];
  },
  queryKey: queryKeys.requestsWithoutProject(search.trim()),
});

export const todosListQuery = (
  assignees: Array<number>,
  ordering: string,
  status: Array<number>,
) => ({
  queryFn: async () => {
    const todos = await adminApi.adminTodosList({
      assignees,
      ordering,
      pageSize: 10000,
      status: status as AdminTodosListStatusEnum[],
    });
    return todos.data.results || [];
  },
  queryKey: ['todos', assignees, ordering, status],
  refetchInterval: 1000 * 30,
});

export const todoRetrieveQuery = (todoId: string | number) => ({
  queryFn: async () => {
    const todo = await adminApi.adminTodosRetrieve({ id: Number(todoId) });
    return todo.data;
  },
  queryKey: queryKeys.todo(todoId),
  refetchInterval: 1000 * 60 * 5,
});

export const usersListQuery = () => ({
  queryFn: async () => {
    const users = await adminApi.adminUsersList({ pageSize: 10000 });
    return users.data.results || [];
  },
  queryKey: queryKeys.users(),
  refetchInterval: 1000 * 30,
});

export const usersRetrieveQuery = (userId: string | number) => ({
  queryFn: async () => {
    const user = await adminApi.adminUsersRetrieve({ id: Number(userId) });
    return user.data;
  },
  queryKey: queryKeys.user(userId),
  refetchInterval: 1000 * 60 * 5,
});

export const usersStaffListQuery = () => ({
  gcTime: 1000 * 60 * 60,
  queryFn: async () => {
    const usersStaff = await adminApi.adminUsersList({
      isStaff: true,
      ordering: 'full_name',
      pageSize: 10000,
    });
    return usersStaff.data.results || [];
  },
  queryKey: queryKeys.usersStaff(),
});
