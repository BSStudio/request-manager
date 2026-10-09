import { RequestStatus, TodoStatus, VideoStatus } from 'helpers/statuses';

import { Status, StatusStyle } from './StatusTagTypes';

export const FALLBACK_STATUS: StatusStyle = {
  color: 'orange',
  icon: 'bi bi-question-lg',
  text: 'Nem definiált állapot',
};

export const REQUEST_STATUSES: Status = {
  [RequestStatus.DENIED]: {
    color: 'pink',
    icon: 'bi bi-hand-thumbs-down-fill',
    text: 'Elutasítva',
  },
  [RequestStatus.REQUESTED]: {
    color: 'blue',
    icon: 'bi bi-envelope-fill',
    text: 'Felkérés',
  },
  [RequestStatus.ACCEPTED]: {
    color: 'teal',
    icon: 'bi bi-hand-thumbs-up-fill',
    text: 'Elvállalva',
  },
  [RequestStatus.RECORDED]: {
    color: 'cyan',
    icon: 'bi bi-camera-reels-fill',
    text: 'Leforgatva',
  },
  [RequestStatus.UPLOADED]: {
    color: 'purple',
    icon: 'bi bi-pencil-fill',
    text: 'Beírva',
  },
  [RequestStatus.EDITED]: {
    color: 'indigo',
    icon: 'bi bi-scissors',
    text: 'Megvágva',
  },
  [RequestStatus.ARCHIVED]: {
    color: 'yellow',
    icon: 'bi bi-archive-fill',
    text: 'Archiválva',
  },
  [RequestStatus.DONE]: {
    color: 'green',
    icon: 'bi bi-rocket-takeoff-fill',
    text: 'Lezárva',
  },
  [RequestStatus.CANCELED]: {
    color: 'bluegray',
    icon: 'bi bi-person-fill-x',
    text: 'Szervezők által lemondva',
  },
  [RequestStatus.FAILED]: {
    color: 'red',
    icon: 'bi bi-fire',
    text: 'Meghiúsult',
  },
};

export const TODO_STATUSES: Status = {
  [TodoStatus.OPEN]: {
    color: 'blue',
    icon: 'bi bi-clipboard2',
    text: 'Nyitva',
  },
  [TodoStatus.CLOSED]: {
    color: 'green',
    icon: 'bi bi-clipboard2-check',
    text: 'Lezárva',
  },
  [TodoStatus.DISCARDED]: {
    color: 'bluegray',
    icon: 'bi bi-clipboard2-x',
    text: 'Elvetve',
  },
};

export const VIDEO_STATUSES: Status = {
  [VideoStatus.PENDING]: {
    color: 'blue',
    icon: 'bi bi-hourglass-split',
    text: 'Vágásra vár',
  },
  [VideoStatus.IN_PROGRESS]: {
    color: 'teal',
    icon: 'bi bi-sliders',
    text: 'Vágás alatt',
  },
  [VideoStatus.EDITED]: {
    color: 'indigo',
    icon: 'bi bi-scissors',
    text: 'Megvágva',
  },
  [VideoStatus.CODED]: {
    color: 'yellow',
    icon: 'bi bi-file-earmark-play',
    text: 'Kikódolva',
  },
  [VideoStatus.PUBLISHED]: {
    color: 'purple',
    icon: 'bi bi-cloud-upload',
    text: 'Közzétéve',
  },
  [VideoStatus.DONE]: {
    color: 'green',
    icon: 'bi bi-rocket-takeoff-fill',
    text: 'Lezárva',
  },
};
