import {
  BanIcon,
  CircleXIcon,
  type LucideIcon,
  TriangleAlertIcon,
} from 'lucide-react';

import { RequestStatus, VideoStatus } from 'helpers/statuses';

export type StatusTone = 'active' | 'done' | 'failed' | 'inactive' | 'pending';

export type StatusInfo = { label: string; tone: StatusTone };

const requestStatuses: Record<number, StatusInfo> = {
  [RequestStatus.DENIED]: { label: 'Elutasítva', tone: 'failed' },
  [RequestStatus.REQUESTED]: { label: 'Elbírálás alatt', tone: 'pending' },
  [RequestStatus.ACCEPTED]: { label: 'Elvállalva', tone: 'active' },
  [RequestStatus.RECORDED]: { label: 'Leforgatva', tone: 'active' },
  [RequestStatus.UPLOADED]: { label: 'Leforgatva', tone: 'active' },
  [RequestStatus.EDITED]: { label: 'Elkészült', tone: 'done' },
  [RequestStatus.ARCHIVED]: { label: 'Elkészült', tone: 'done' },
  [RequestStatus.DONE]: { label: 'Elkészült', tone: 'done' },
  [RequestStatus.CANCELED]: { label: 'Lemondva', tone: 'inactive' },
  [RequestStatus.FAILED]: { label: 'Meghiúsult', tone: 'inactive' },
};

const videoStatuses: Record<number, StatusInfo> = {
  [VideoStatus.PENDING]: { label: 'Vágásra vár', tone: 'pending' },
  [VideoStatus.IN_PROGRESS]: { label: 'Vágás alatt', tone: 'active' },
  [VideoStatus.EDITED]: { label: 'Közzétételre vár', tone: 'active' },
  [VideoStatus.CODED]: { label: 'Közzétételre vár', tone: 'active' },
  [VideoStatus.PUBLISHED]: { label: 'Közzétéve', tone: 'done' },
  [VideoStatus.DONE]: { label: 'Közzétéve', tone: 'done' },
};

const unknownStatus: StatusInfo = { label: 'Ismeretlen', tone: 'inactive' };

export function getRequestStatus(status: number) {
  return requestStatuses[status] ?? unknownStatus;
}

export function getVideoStatus(status: number) {
  return videoStatuses[status] ?? unknownStatus;
}

// The same four steps as "Így működik" on the home page.
export const requestSteps = [
  {
    text: 'Megkaptuk a felkérésed. A hétfői gyűlésünkön döntünk róla, utána jelentkezünk.',
    title: 'Beküldve',
  },
  {
    text: 'Elvállaltuk, stábunk ott lesz az eseményeden.',
    title: 'Elvállalva',
  },
  {
    text: 'Leforgattuk az eseményt, most készülnek a videók.',
    title: 'Leforgatva',
  },
  {
    text: 'Elkészültek a videók. Amelyiket már közzétettük, lent meg is nézheted.',
    title: 'Elkészült',
  },
];

// The last step reached, null when the request stopped before it was done.
export function getRequestStep(status: number) {
  if (status === RequestStatus.REQUESTED) return 0;
  if (status === RequestStatus.ACCEPTED) return 1;
  if (status === RequestStatus.RECORDED || status === RequestStatus.UPLOADED)
    return 2;
  if (status >= RequestStatus.EDITED && status <= RequestStatus.DONE) return 3;
  return null;
}

type StoppedNotice = { icon: LucideIcon; text: string; title: string };

const stoppedNotices: Record<number, StoppedNotice> = {
  [RequestStatus.DENIED]: {
    icon: CircleXIcon,
    text: 'Sajnos most nem tudunk ott lenni az eseményeden. Reméljük, legközelebb összejön!',
    title: 'Ezt a felkérést nem tudtuk elvállalni',
  },
  [RequestStatus.CANCELED]: {
    icon: BanIcon,
    text: 'Ha mégis szükségetek lenne ránk, küldj be egy új felkérést!',
    title: 'Lemondtátok a felkérést',
  },
  [RequestStatus.FAILED]: {
    icon: TriangleAlertIcon,
    text: 'Valami közbejött, és nem sikerült rögzítenünk az eseményt. Sajnáljuk!',
    title: 'A forgatás meghiúsult',
  },
};

export function getStoppedNotice(status: number) {
  return stoppedNotices[status] ?? stoppedNotices[RequestStatus.DENIED];
}
