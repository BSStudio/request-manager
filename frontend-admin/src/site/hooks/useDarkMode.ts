import { useSyncExternalStore } from 'react';

import { getDarkMode, setDarkMode } from 'helpers/LocalStorageHelper';

const systemDarkMode = window.matchMedia('(prefers-color-scheme: dark)');
const listeners = new Set<() => void>();

function isDarkMode() {
  const saved = getDarkMode();
  return saved === null ? systemDarkMode.matches : saved === 'true';
}

function update() {
  document.documentElement.classList.toggle('dark', isDarkMode());
  listeners.forEach((listener) => listener());
}

systemDarkMode.addEventListener('change', update);
window.addEventListener('storage', (event) => {
  if (event.key === 'dark-mode') update();
});

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

// Shares the saved preference with the admin, which uses the same key.
export function useDarkMode() {
  const darkMode = useSyncExternalStore(subscribe, isDarkMode);

  const changeDarkMode = (value: boolean) => {
    setDarkMode(value);
    update();
  };

  return [darkMode, changeDarkMode] as const;
}
