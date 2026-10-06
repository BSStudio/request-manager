import {
  BanIcon,
  CircleXIcon,
  type LucideIcon,
  TriangleAlertIcon,
} from 'lucide-react';

export type StatusTone = 'active' | 'done' | 'failed' | 'inactive' | 'pending';

export type StatusInfo = { label: string; tone: StatusTone };

const requestStatuses: Record<number, StatusInfo> = {
  0: { label: 'Elutasítva', tone: 'failed' },
  1: { label: 'Elbírálás alatt', tone: 'pending' },
  2: { label: 'Elvállalva', tone: 'active' },
  3: { label: 'Leforgatva', tone: 'active' },
  4: { label: 'Leforgatva', tone: 'active' },
  5: { label: 'Elkészült', tone: 'done' },
  6: { label: 'Elkészült', tone: 'done' },
  7: { label: 'Elkészült', tone: 'done' },
  9: { label: 'Lemondva', tone: 'inactive' },
  10: { label: 'Meghiúsult', tone: 'inactive' },
};

const videoStatuses: Record<number, StatusInfo> = {
  1: { label: 'Vágásra vár', tone: 'pending' },
  2: { label: 'Vágás alatt', tone: 'active' },
  3: { label: 'Közzétételre vár', tone: 'active' },
  4: { label: 'Közzétételre vár', tone: 'active' },
  5: { label: 'Közzétéve', tone: 'done' },
  6: { label: 'Közzétéve', tone: 'done' },
};

// The API rejects ratings for videos below this status.
export const VIDEO_PUBLISHED = 5;

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
  if (status === 1) return 0;
  if (status === 2) return 1;
  if (status === 3 || status === 4) return 2;
  if (status >= 5 && status <= 7) return 3;
  return null;
}

type StoppedNotice = { icon: LucideIcon; text: string; title: string };

const stoppedNotices: Record<number, StoppedNotice> = {
  0: {
    icon: CircleXIcon,
    text: 'Sajnos most nem tudunk ott lenni az eseményeden. Reméljük, legközelebb összejön!',
    title: 'Ezt a felkérést nem tudtuk elvállalni',
  },
  9: {
    icon: BanIcon,
    text: 'Ha mégis szükségetek lenne ránk, küldj be egy új felkérést!',
    title: 'Lemondtátok a felkérést',
  },
  10: {
    icon: TriangleAlertIcon,
    text: 'Valami közbejött, és nem sikerült rögzítenünk az eseményt. Sajnáljuk!',
    title: 'A forgatás meghiúsult',
  },
};

export function getStoppedNotice(status: number) {
  return stoppedNotices[status] ?? stoppedNotices[0];
}
