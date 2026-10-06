import { Status, StatusStyle } from './StatusTagTypes';

export const FALLBACK_STATUS: StatusStyle = {
  color: 'orange',
  icon: 'bi bi-question-lg',
  text: 'Nem definiált állapot',
};

export const REQUEST_STATUSES: Status = {
  0: {
    color: 'pink',
    icon: 'bi bi-hand-thumbs-down-fill',
    text: 'Elutasítva',
  },
  1: {
    color: 'blue',
    icon: 'bi bi-envelope-fill',
    text: 'Felkérés',
  },
  2: {
    color: 'teal',
    icon: 'bi bi-hand-thumbs-up-fill',
    text: 'Elvállalva',
  },
  3: {
    color: 'cyan',
    icon: 'bi bi-camera-reels-fill',
    text: 'Leforgatva',
  },
  4: {
    color: 'purple',
    icon: 'bi bi-pencil-fill',
    text: 'Beírva',
  },
  5: {
    color: 'indigo',
    icon: 'bi bi-scissors',
    text: 'Megvágva',
  },
  6: {
    color: 'yellow',
    icon: 'bi bi-archive-fill',
    text: 'Archiválva',
  },
  7: {
    color: 'green',
    icon: 'bi bi-rocket-takeoff-fill',
    text: 'Lezárva',
  },
  9: {
    color: 'bluegray',
    icon: 'bi bi-person-fill-x',
    text: 'Szervezők által lemondva',
  },
  10: {
    color: 'red',
    icon: 'bi bi-fire',
    text: 'Meghiúsult',
  },
};

export const TODO_STATUSES: Status = {
  1: {
    color: 'blue',
    icon: 'bi bi-clipboard2',
    text: 'Nyitva',
  },
  2: {
    color: 'green',
    icon: 'bi bi-clipboard2-check',
    text: 'Lezárva',
  },
  3: {
    color: 'bluegray',
    icon: 'bi bi-clipboard2-x',
    text: 'Elvetve',
  },
};

export const VIDEO_STATUSES: Status = {
  1: {
    color: 'blue',
    icon: 'bi bi-hourglass-split',
    text: 'Vágásra vár',
  },
  2: {
    color: 'teal',
    icon: 'bi bi-sliders',
    text: 'Vágás alatt',
  },
  3: {
    color: 'indigo',
    icon: 'bi bi-scissors',
    text: 'Megvágva',
  },
  4: {
    color: 'yellow',
    icon: 'bi bi-file-earmark-play',
    text: 'Kikódolva',
  },
  5: {
    color: 'purple',
    icon: 'bi bi-cloud-upload',
    text: 'Közzétéve',
  },
  6: {
    color: 'green',
    icon: 'bi bi-rocket-takeoff-fill',
    text: 'Lezárva',
  },
};
