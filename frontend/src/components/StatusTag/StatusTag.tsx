import React, { forwardRef } from 'react';

import { Tag } from 'primereact/tag';
import { classNames } from 'primereact/utils';

import {
  FALLBACK_STATUS,
  REQUEST_STATUSES,
  TODO_STATUSES,
  VIDEO_STATUSES,
} from './statusTagConsts';
import {
  RequestStatusTagProps,
  StatusTagProps,
  TodoStatusTagProps,
  VideoStatusTagProps,
} from './StatusTagTypes';

export const StatusTag = forwardRef<React.Ref<HTMLSpanElement>, StatusTagProps>(
  ({ className, modified = false, status, ...props }, ref) => {
    return (
      <Tag
        {...props}
        {...ref}
        className={classNames(
          `p-tag-${status.color} white-space-nowrap`,
          className,
        )}
        icon={status.icon}
        value={status.text.concat(modified ? '*' : '')}
      />
    );
  },
);

StatusTag.displayName = 'StatusTag';

export const RequestStatusTag = forwardRef<
  React.Ref<HTMLSpanElement>,
  RequestStatusTagProps
>(({ statusNum, ...props }, ref) => {
  return (
    <StatusTag
      {...props}
      {...ref}
      status={REQUEST_STATUSES[statusNum] || FALLBACK_STATUS}
    />
  );
});

RequestStatusTag.displayName = 'RequestStatusTag';

export const TodoStatusTag = forwardRef<
  React.Ref<HTMLSpanElement>,
  TodoStatusTagProps
>(({ statusNum, ...props }, ref) => {
  return (
    <StatusTag
      {...props}
      {...ref}
      modified={false}
      status={TODO_STATUSES[statusNum] || FALLBACK_STATUS}
    />
  );
});

TodoStatusTag.displayName = 'TodoStatusTag';

export const VideoStatusTag = forwardRef<
  React.Ref<HTMLSpanElement>,
  VideoStatusTagProps
>(({ statusNum, ...props }, ref) => {
  return (
    <StatusTag
      {...props}
      {...ref}
      status={VIDEO_STATUSES[statusNum] || FALLBACK_STATUS}
    />
  );
});

VideoStatusTag.displayName = 'VideoStatusTag';
