// Single source of truth for query keys. Used by both the query factories in
// queries.ts and by invalidateQueries calls, so the two can never drift. All
// ids are normalized with Number() to match across string/number callers.
// Ids accept undefined (e.g. raw useParams values) the same way the previous
// inline `Number(requestId)` calls did.
type Id = string | number | undefined;

export const queryKeys = {
  request: (requestId: Id) => ['requests', Number(requestId)],
  requestComments: (requestId: Id) => [
    'requests',
    Number(requestId),
    'comments',
  ],
  requestCrew: (requestId: Id) => ['requests', Number(requestId), 'crew'],
  requestHistory: (requestId: Id) => ['requests', Number(requestId), 'history'],
  requestTodos: (requestId: Id) => ['requests', Number(requestId), 'todos'],
  requestVideos: (requestId: Id) => ['requests', Number(requestId), 'videos'],
  requests: () => ['requests'],
  requestsBySemester: (
    afterDate: string | undefined,
    beforeDate: string | undefined,
  ) => ['requests', `${afterDate}/${beforeDate}`],
  todo: (todoId: Id) => ['todos', `id:${Number(todoId)}`],
  todos: () => ['todos'],
  user: (userId: Id) => ['users', Number(userId)],
  users: () => ['users'],
  usersStaff: () => ['users', 'staff'],
  video: (requestId: Id, videoId: Id) => [
    'requests',
    Number(requestId),
    'videos',
    Number(videoId),
  ],
  videoHistory: (requestId: Id, videoId: Id) => [
    'requests',
    Number(requestId),
    'videos',
    Number(videoId),
    'history',
  ],
  videoRating: (requestId: Id, videoId: Id, ratingId: Id) => [
    'requests',
    Number(requestId),
    'videos',
    Number(videoId),
    'ratings',
    Number(ratingId),
  ],
  videoRatingOwn: (requestId: Id, videoId: Id) => [
    'requests',
    Number(requestId),
    'videos',
    Number(videoId),
    'ratings',
    'own',
  ],
  videoRatings: (requestId: Id, videoId: Id) => [
    'requests',
    Number(requestId),
    'videos',
    Number(videoId),
    'ratings',
  ],
  videoTodos: (requestId: Id, videoId: Id) => [
    'requests',
    Number(requestId),
    'videos',
    Number(videoId),
    'todos',
  ],
};
