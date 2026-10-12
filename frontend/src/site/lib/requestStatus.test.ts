import { describe, expect, it } from 'vitest';

import { RequestStatus, VideoStatus } from 'helpers/statuses';
import {
  getRequestStatus,
  getRequestStep,
  getStoppedNotice,
  getVideoStatus,
} from 'site/lib/requestStatus';

describe('getRequestStatus', () => {
  it.each(Object.entries(RequestStatus))('has a label for %s', (_, status) => {
    expect(getRequestStatus(status).label).not.toBe('Ismeretlen');
  });

  it('falls back for an unknown status', () => {
    expect(getRequestStatus(8)).toEqual({
      label: 'Ismeretlen',
      tone: 'inactive',
    });
  });
});

describe('getVideoStatus', () => {
  it.each(Object.entries(VideoStatus))('has a label for %s', (_, status) => {
    expect(getVideoStatus(status).label).not.toBe('Ismeretlen');
  });

  it('falls back for an unknown status', () => {
    expect(getVideoStatus(0).label).toBe('Ismeretlen');
  });
});

describe('getRequestStep', () => {
  it.each([
    ['REQUESTED', 0],
    ['ACCEPTED', 1],
    ['RECORDED', 2],
    ['UPLOADED', 2],
    ['EDITED', 3],
    ['ARCHIVED', 3],
    ['DONE', 3],
    ['DENIED', null],
    ['CANCELED', null],
    ['FAILED', null],
  ] as const)('puts %s at step %s', (status, step) => {
    expect(getRequestStep(RequestStatus[status])).toBe(step);
  });
});

describe('getStoppedNotice', () => {
  it.each([
    ['DENIED', 'Ezt a felkérést nem tudtuk elvállalni'],
    ['CANCELED', 'Lemondtátok a felkérést'],
    ['FAILED', 'A forgatás meghiúsult'],
  ] as const)('explains %s', (status, title) => {
    expect(getStoppedNotice(RequestStatus[status]).title).toBe(title);
  });
});
