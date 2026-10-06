import type { TagProps } from 'primereact/tag';
import type { IconType } from 'primereact/utils';

export type Status = {
  [key: number]: StatusStyle;
};

export type StatusStyle = {
  color:
    | 'blue'
    | 'bluegray'
    | 'cyan'
    | 'green'
    | 'indigo'
    | 'orange'
    | 'pink'
    | 'purple'
    | 'red'
    | 'teal'
    | 'yellow';
  icon: IconType<TagProps>;
  text: string;
};

export interface RequestStatusTagProps extends TagProps {
  modified?: boolean;
  statusNum: number;
}

export interface StatusTagProps extends TagProps {
  modified?: boolean;
  status: StatusStyle;
}

export interface TodoStatusTagProps extends TagProps {
  statusNum: number;
}

export interface VideoStatusTagProps extends TagProps {
  modified?: boolean;
  statusNum: number;
}
