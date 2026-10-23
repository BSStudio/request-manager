import { afterEach, describe, expect, it, vi } from 'vitest';

import { setAppBadge } from 'helpers/pwa';

describe('setAppBadge', () => {
  afterEach(() => {
    delete (navigator as Partial<Navigator>).setAppBadge;
    delete (navigator as Partial<Navigator>).clearAppBadge;
  });

  it('shows the count, and clears it at zero', () => {
    const set = vi.fn(() => Promise.resolve());
    const clear = vi.fn(() => Promise.resolve());
    Object.assign(navigator, { clearAppBadge: clear, setAppBadge: set });

    setAppBadge(3);
    setAppBadge(0);

    expect(set).toHaveBeenCalledExactlyOnceWith(3);
    expect(clear).toHaveBeenCalledOnce();
  });

  it('ignores a browser that refuses to show it', async () => {
    const set = vi.fn(() =>
      Promise.reject(new DOMException('NotAllowedError')),
    );
    Object.assign(navigator, { clearAppBadge: vi.fn(), setAppBadge: set });

    expect(() => setAppBadge(3)).not.toThrow();
    await expect(set.mock.results[0].value).rejects.toThrow();
  });

  it('does nothing where the Badging API is missing', () => {
    expect(() => setAppBadge(3)).not.toThrow();
  });
});
