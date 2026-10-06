import { useSyncExternalStore } from 'react';

type BeforeInstallPromptEvent = Event & { prompt: () => Promise<void> };

let installPrompt: BeforeInstallPromptEvent | null = null;
const listeners = new Set<() => void>();

function setInstallPrompt(event: BeforeInstallPromptEvent | null) {
  installPrompt = event;
  listeners.forEach((listener) => listener());
}

// The browser fires this once, early, so it is caught before an app loads.
window.addEventListener('beforeinstallprompt', (event) => {
  // Keeps the browser's own banner away, the menus offer installing instead.
  event.preventDefault();
  setInstallPrompt(event as BeforeInstallPromptEvent);
});
window.addEventListener('appinstalled', () => setInstallPrompt(null));

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useCanInstall() {
  return useSyncExternalStore(subscribe, () => installPrompt !== null);
}

export async function promptInstall() {
  const event = installPrompt;
  // A prompt can only be shown once.
  setInstallPrompt(null);
  await event?.prompt();
}
