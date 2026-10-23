import { describe, expect, it } from 'vitest';

import type { Notification as ApiNotification } from 'api/models';
import {
  adminRouterPath,
  groupByDay,
  unreadLabel,
} from 'helpers/notifications';

const at = (created: string) =>
  ({
    body: '',
    created,
    id: 1,
    kind: 'studio_message',
    read_at: null,
    request: 1,
    title: '',
    url: '/my-requests/1',
  }) as ApiNotification;

describe('groupByDay', () => {
  const now = new Date('2026-10-20T10:00:00+02:00');

  it('splits into today, yesterday and earlier, dropping empty groups', () => {
    const today = at('2026-10-20T08:00:00+02:00');
    const yesterday = at('2026-10-19T23:30:00+02:00');
    const older = at('2026-10-12T12:00:00+02:00');

    expect(groupByDay([today, yesterday, older], now)).toEqual([
      { label: 'Ma', notifications: [today] },
      { label: 'Tegnap', notifications: [yesterday] },
      { label: 'Korábban', notifications: [older] },
    ]);
    expect(groupByDay([older], now)).toEqual([
      { label: 'Korábban', notifications: [older] },
    ]);
  });

  it('counts days in Budapest, not UTC', () => {
    const justAfterMidnight = at('2026-10-19T22:30:00Z');

    expect(groupByDay([justAfterMidnight], now)[0].label).toBe('Ma');
  });
});

describe('adminRouterPath', () => {
  it('drops the prefix the admin router adds as its basename', () => {
    expect(adminRouterPath('/admin/requests/5')).toBe('/requests/5');
  });
});

describe('unreadLabel', () => {
  it('says how many are unread', () => {
    expect(unreadLabel(0)).toBe('Értesítések');
    expect(unreadLabel(2)).toBe('Értesítések, 2 olvasatlan');
  });
});
