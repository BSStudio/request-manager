import { useCallback } from 'react';

import { useRegisterSW } from 'virtual:pwa-register/react';

const UPDATE_CHECK_INTERVAL = 60 * 60 * 1000;

// Registers the service worker. A new deploy waits until the user reloads
// through update(), so an open page never mixes two versions.
export function useAppUpdate() {
  const {
    needRefresh: [needRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    // Tabs of the admin stay open for days.
    onRegisteredSW(_url, registration) {
      if (!registration) return;
      setInterval(() => void registration.update(), UPDATE_CHECK_INTERVAL);
    },
  });

  const update = useCallback(
    () => updateServiceWorker(true),
    [updateServiceWorker],
  );

  return { needRefresh, update };
}
