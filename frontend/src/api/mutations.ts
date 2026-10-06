import { adminApi } from './http';
import {
  BanUserRequest,
  CommentAdminCreateUpdateRequest,
  CrewMemberAdminCreateUpdateRequest,
  PatchedCommentAdminCreateUpdateRequest,
  PatchedCrewMemberAdminCreateUpdateRequest,
  PatchedRatingAdminCreateUpdateRequest,
  PatchedRequestAdminUpdateRequest,
  PatchedVideoAdminCreateUpdateRequest,
  RatingAdminCreateUpdateRequest,
  RequestAdminCreateRequest,
  TodoAdminCreateUpdateRequest,
  UserAdminRetrieveUpdateRequest,
  VideoAdminCreateUpdateRequest,
} from './models';

export const requestCommentCreateMutation = (requestId: number) => ({
  mutationFn: (newComment: CommentAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsCommentsCreate(requestId, newComment);
  },
});

export const requestCommentUpdateMutation = (
  requestId: number,
  commentId: number,
) => ({
  mutationFn: (updateComment: PatchedCommentAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsCommentsPartialUpdate(
      commentId,
      requestId,
      updateComment,
    );
  },
});

export const requestCreateMutation = () => ({
  mutationFn: (newRequest: RequestAdminCreateRequest) => {
    return adminApi.adminRequestsCreate(newRequest);
  },
});

export const requestCrewCreateMutation = (requestId: number) => ({
  mutationFn: (newCrewMember: CrewMemberAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsCrewCreate(requestId, newCrewMember);
  },
});

export const requestTodoCreateMutation = (requestId: number) => ({
  mutationFn: (newTodo: TodoAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsTodosCreate(requestId, newTodo);
  },
});

export const requestUpdateMutation = (requestId: number) => ({
  mutationFn: (updateRequest: PatchedRequestAdminUpdateRequest) => {
    return adminApi.adminRequestsPartialUpdate(requestId, updateRequest);
  },
});

export const requestVideoCreateMutation = (requestId: number) => ({
  mutationFn: (createVideo: VideoAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsVideosCreate(requestId, createVideo);
  },
});

export const requestVideoRatingCreateMutation = (
  requestId: number,
  videoId: number,
) => ({
  mutationFn: (newRating: RatingAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsVideosRatingsCreate(
      requestId,
      videoId,
      newRating,
    );
  },
});

export const requestVideoRatingUpdateMutation = (
  requestId: number,
  videoId: number,
  ratingId: number,
) => ({
  mutationFn: (updateRating: PatchedRatingAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsVideosRatingsPartialUpdate(
      ratingId,
      requestId,
      videoId,
      updateRating,
    );
  },
});

export const requestVideoTodoCreateMutation = (
  requestId: number,
  videoId: number,
) => ({
  mutationFn: (newTodo: TodoAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsVideosTodosCreate(requestId, videoId, newTodo);
  },
});

export const requestVideoUpdateMutation = (
  requestId: number,
  videoId: number,
) => ({
  mutationFn: (updateVideo: PatchedVideoAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsVideosPartialUpdate(
      videoId,
      requestId,
      updateVideo,
    );
  },
});

export const todoUpdateMutation = (todoId: number) => ({
  mutationFn: (updateTodo: TodoAdminCreateUpdateRequest) => {
    return adminApi.adminTodosPartialUpdate(todoId, updateTodo);
  },
});

export const userUpdateMutation = (userId: number) => ({
  mutationFn: (updateUser: UserAdminRetrieveUpdateRequest) => {
    return adminApi.adminUsersPartialUpdate(userId, updateUser);
  },
});

export const requestDeleteMutation = (requestId: number) => ({
  mutationFn: () => {
    return adminApi.adminRequestsDestroy(requestId);
  },
});

export const requestCommentDeleteMutation = (
  requestId: number,
  commentId: number,
) => ({
  mutationFn: () => {
    return adminApi.adminRequestsCommentsDestroy(commentId, requestId);
  },
});

export const requestCrewDeleteMutation = (requestId: number) => ({
  mutationFn: (crewId: number) => {
    return adminApi.adminRequestsCrewDestroy(crewId, requestId);
  },
});

export const requestCrewUpdateMutation = (requestId: number) => ({
  mutationFn: (variables: {
    crewId: number;
    crewMember: PatchedCrewMemberAdminCreateUpdateRequest;
  }) => {
    return adminApi.adminRequestsCrewPartialUpdate(
      variables.crewId,
      requestId,
      variables.crewMember,
    );
  },
});

export const requestVideoDeleteMutation = (
  requestId: number,
  videoId: number,
) => ({
  mutationFn: () => {
    return adminApi.adminRequestsVideosDestroy(videoId, requestId);
  },
});

export const requestVideoRatingDeleteMutation = (
  requestId: number,
  videoId: number,
  ratingId: number,
) => ({
  mutationFn: () => {
    return adminApi.adminRequestsVideosRatingsDestroy(
      ratingId,
      requestId,
      videoId,
    );
  },
});

export const todoDeleteMutation = (todoId: number) => ({
  mutationFn: () => {
    return adminApi.adminTodosDestroy(todoId);
  },
});

export const userBanCreateMutation = (userId: number) => ({
  mutationFn: (ban: BanUserRequest) => {
    return adminApi.adminUsersBanCreate(userId, ban);
  },
});

export const userBanDeleteMutation = (userId: number) => ({
  mutationFn: () => {
    return adminApi.adminUsersBanDestroy(userId);
  },
});
