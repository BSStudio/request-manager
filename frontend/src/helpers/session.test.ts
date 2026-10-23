import { describe, expect, it, vi } from 'vitest';

import { logoutApi } from 'api/http';
import { hasSession, setSession } from 'helpers/LocalStorageHelper';
import { disablePush } from 'helpers/push';
import { signOut } from 'helpers/session';

vi.mock('api/http', () => ({
  logoutApi: { logoutCreate: vi.fn() },
}));
vi.mock('helpers/push', () => ({ disablePush: vi.fn() }));

describe('signOut', () => {
  it('logs out even when the browser cannot be unsubscribed', async () => {
    setSession({
      avatar_url: '',
      groups: [],
      id: 42,
      name: 'Minta Anna',
      role: 'user',
    });
    vi.mocked(disablePush).mockRejectedValueOnce(new Error('offline'));

    await signOut();

    expect(logoutApi.logoutCreate).toHaveBeenCalledOnce();
    expect(hasSession()).toBe(false);
  });
});
