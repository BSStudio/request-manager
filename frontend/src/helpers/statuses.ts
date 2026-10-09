/* eslint-disable sort-keys -- In the order of the backend's Statuses choices, which the generated client only names NUMBER_0, NUMBER_1… */

export const RequestStatus = {
  DENIED: 0,
  REQUESTED: 1,
  ACCEPTED: 2,
  RECORDED: 3,
  UPLOADED: 4,
  EDITED: 5,
  ARCHIVED: 6,
  DONE: 7,
  CANCELED: 9,
  FAILED: 10,
} as const;

export const VideoStatus = {
  PENDING: 1,
  IN_PROGRESS: 2,
  EDITED: 3,
  CODED: 4,
  PUBLISHED: 5,
  DONE: 6,
} as const;

export const TodoStatus = {
  OPEN: 1,
  CLOSED: 2,
  DISCARDED: 3,
} as const;
