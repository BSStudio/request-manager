import { afterEach, describe, expect, it, vi } from 'vitest';

import { loginApi, logoutApi } from 'api/http';
import { hasSession, setSession } from 'helpers/LocalStorageHelper';
import { forgetPushSubscription, syncPushSubscription } from 'helpers/push';
import { signIn, signOut } from 'helpers/session';

vi.mock('api/http', () => ({
  loginApi: { loginSocialCreate: vi.fn() },
  logoutApi: { logoutCreate: vi.fn() },
}));
vi.mock('helpers/push', () => ({
  forgetPushSubscription: vi.fn(() => Promise.resolve()),
  syncPushSubscription: vi.fn(() => Promise.resolve()),
}));

const sessionUser = {
  avatar_url: '',
  groups: [],
  id: 42,
  name: 'Minta Anna',
  role: 'user',
};

afterEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
});

describe('signIn', () => {
  it('drops push someone else turned on in this browser', async () => {
    vi.mocked(loginApi.loginSocialCreate).mockResolvedValueOnce({
      data: sessionUser,
    } as never);

    await signIn('google-oauth2', 'code', 'nonce');

    expect(syncPushSubscription).toHaveBeenCalledExactlyOnceWith(42);
  });
});

describe('signOut', () => {
  it('turns push off in this browser after logging out', async () => {
    setSession(sessionUser);

    await signOut();

    expect(logoutApi.logoutCreate).toHaveBeenCalledOnce();
    expect(forgetPushSubscription).toHaveBeenCalledOnce();
    expect(hasSession()).toBe(false);
  });

  it('logs out even when the browser cannot be unsubscribed', async () => {
    setSession(sessionUser);
    vi.mocked(forgetPushSubscription).mockRejectedValueOnce(
      new Error('push service'),
    );

    await signOut();

    expect(hasSession()).toBe(false);
  });

  it('keeps push on when logging out fails', async () => {
    setSession(sessionUser);
    vi.mocked(logoutApi.logoutCreate).mockRejectedValueOnce(
      new Error('offline'),
    );

    await expect(signOut()).rejects.toThrow('offline');
    expect(forgetPushSubscription).not.toHaveBeenCalled();
    expect(hasSession()).toBe(true);
  });
});
