import { adminApi } from '../../api/http';
import {
  BanUserRequest,
  CommentAdminCreateUpdateRequest,
  CrewMemberAdminCreateUpdateRequest,
  PatchedCommentAdminCreateUpdateRequest,
  PatchedCrewMemberAdminCreateUpdateRequest,
  PatchedRatingAdminCreateUpdateRequest,
  PatchedRequestAdminUpdateRequest,
  PatchedTodoAdminCreateUpdateRequest,
  PatchedUserAdminRetrieveUpdateRequest,
  PatchedVideoAdminCreateUpdateRequest,
  RatingAdminCreateUpdateRequest,
  RequestAdminCreateRequest,
  TodoAdminCreateUpdateRequest,
  VideoAdminCreateUpdateRequest,
} from '../../api/models';

export const requestCommentCreateMutation = (requestId: number) => ({
  mutationFn: (newComment: CommentAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsCommentsCreate({
      commentAdminCreateUpdateRequest: newComment,
      requestId,
    });
  },
});

export const requestCommentUpdateMutation = (
  requestId: number,
  commentId: number,
) => ({
  mutationFn: (updateComment: PatchedCommentAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsCommentsPartialUpdate({
      id: commentId,
      patchedCommentAdminCreateUpdateRequest: updateComment,
      requestId,
    });
  },
});

export const requestCreateMutation = () => ({
  mutationFn: (newRequest: RequestAdminCreateRequest) => {
    return adminApi.adminRequestsCreate({
      requestAdminCreateRequest: newRequest,
    });
  },
});

export const requestCrewCreateMutation = (requestId: number) => ({
  mutationFn: (newCrewMember: CrewMemberAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsCrewCreate({
      crewMemberAdminCreateUpdateRequest: newCrewMember,
      requestId,
    });
  },
});

export const requestTodoCreateMutation = (requestId: number) => ({
  mutationFn: (newTodo: TodoAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsTodosCreate({
      requestId,
      todoAdminCreateUpdateRequest: newTodo,
    });
  },
});

export const requestUpdateMutation = (requestId: number) => ({
  mutationFn: (updateRequest: PatchedRequestAdminUpdateRequest) => {
    return adminApi.adminRequestsPartialUpdate({
      id: requestId,
      patchedRequestAdminUpdateRequest: updateRequest,
    });
  },
});

export const requestVideoCreateMutation = (requestId: number) => ({
  mutationFn: (createVideo: VideoAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsVideosCreate({
      requestId,
      videoAdminCreateUpdateRequest: createVideo,
    });
  },
});

export const requestVideoRatingCreateMutation = (
  requestId: number,
  videoId: number,
) => ({
  mutationFn: (newRating: RatingAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsVideosRatingsCreate({
      ratingAdminCreateUpdateRequest: newRating,
      requestId,
      videoId,
    });
  },
});

export const requestVideoRatingUpdateMutation = (
  requestId: number,
  videoId: number,
  ratingId: number,
) => ({
  mutationFn: (updateRating: PatchedRatingAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsVideosRatingsPartialUpdate({
      id: ratingId,
      patchedRatingAdminCreateUpdateRequest: updateRating,
      requestId,
      videoId,
    });
  },
});

export const requestVideoTodoCreateMutation = (
  requestId: number,
  videoId: number,
) => ({
  mutationFn: (newTodo: TodoAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsVideosTodosCreate({
      requestId,
      todoAdminCreateUpdateRequest: newTodo,
      videoId,
    });
  },
});

export const requestVideoUpdateMutation = (
  requestId: number,
  videoId: number,
) => ({
  mutationFn: (updateVideo: PatchedVideoAdminCreateUpdateRequest) => {
    return adminApi.adminRequestsVideosPartialUpdate({
      id: videoId,
      patchedVideoAdminCreateUpdateRequest: updateVideo,
      requestId,
    });
  },
});

export const todoUpdateMutation = (todoId: number) => ({
  mutationFn: (updateTodo: PatchedTodoAdminCreateUpdateRequest) => {
    return adminApi.adminTodosPartialUpdate({
      id: todoId,
      patchedTodoAdminCreateUpdateRequest: updateTodo,
    });
  },
});

export const userUpdateMutation = (userId: number) => ({
  mutationFn: (updateUser: PatchedUserAdminRetrieveUpdateRequest) => {
    return adminApi.adminUsersPartialUpdate({
      id: userId,
      patchedUserAdminRetrieveUpdateRequest: updateUser,
    });
  },
});

export const requestDeleteMutation = (requestId: number) => ({
  mutationFn: () => {
    return adminApi.adminRequestsDestroy({ id: requestId });
  },
});

export const requestCommentDeleteMutation = (
  requestId: number,
  commentId: number,
) => ({
  mutationFn: () => {
    return adminApi.adminRequestsCommentsDestroy({ id: commentId, requestId });
  },
});

export const requestCrewDeleteMutation = (requestId: number) => ({
  mutationFn: (crewId: number) => {
    return adminApi.adminRequestsCrewDestroy({ id: crewId, requestId });
  },
});

export const requestCrewUpdateMutation = (requestId: number) => ({
  mutationFn: (variables: {
    crewId: number;
    crewMember: PatchedCrewMemberAdminCreateUpdateRequest;
  }) => {
    return adminApi.adminRequestsCrewPartialUpdate({
      id: variables.crewId,
      patchedCrewMemberAdminCreateUpdateRequest: variables.crewMember,
      requestId,
    });
  },
});

export const requestVideoDeleteMutation = (
  requestId: number,
  videoId: number,
) => ({
  mutationFn: () => {
    return adminApi.adminRequestsVideosDestroy({ id: videoId, requestId });
  },
});

export const requestVideoRatingDeleteMutation = (
  requestId: number,
  videoId: number,
  ratingId: number,
) => ({
  mutationFn: () => {
    return adminApi.adminRequestsVideosRatingsDestroy({
      id: ratingId,
      requestId,
      videoId,
    });
  },
});

export const todoDeleteMutation = (todoId: number) => ({
  mutationFn: () => {
    return adminApi.adminTodosDestroy({ id: todoId });
  },
});

export const userBanCreateMutation = (userId: number) => ({
  mutationFn: (ban: BanUserRequest) => {
    return adminApi.adminUsersBanCreate({ banUserRequest: ban, id: userId });
  },
});

export const userBanDeleteMutation = (userId: number) => ({
  mutationFn: () => {
    return adminApi.adminUsersBanDestroy({ id: userId });
  },
});
