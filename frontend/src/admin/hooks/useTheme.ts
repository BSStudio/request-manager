import { useEffect, useState } from 'react';

import {
  getDarkMode as getLocalStorageDarkMode,
  setDarkMode as setLocalStorageDarkMode,
} from 'helpers/LocalStorageHelper';

const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)');

export const useTheme = () => {
  const [darkMode, setDarkMode] = useState<boolean>(getDarkMode());

  // If no previous setting was saved we check the browser's preference.
  // Saved option always overrides browser's preference.
  function getDarkMode(): boolean {
    if (getLocalStorageDarkMode() === null) return prefersDarkMode.matches;
    return getLocalStorageDarkMode() === 'true';
  }

  useEffect(() => {
    // Save preferences on change if:
    // 1. User did not save previous preference and changes to
    //  something else than browser's preference.
    // 2. User has a saved preference but changes to other theme.
    function savePreference() {
      const darkModeSavedPref = getLocalStorageDarkMode();
      const darkModeSavedPrefBool = darkModeSavedPref === 'true';

      if (darkModeSavedPref === null) {
        if (prefersDarkMode.matches !== darkMode)
          setLocalStorageDarkMode(darkMode);
      } else {
        if (darkModeSavedPrefBool !== darkMode)
          setLocalStorageDarkMode(darkMode);
      }
    }

    const previousValue = getDarkMode();
    if (previousValue !== darkMode) {
      savePreference();
      window.location.reload();
    }
  }, [darkMode]);

  // Subscribe to brower's theme preference changes.
  // If the brower changes the preference and we don't have
  // any saved preferences, we update the theme accordingly.
  useEffect(() => {
    function handlePreferredThemeChange() {
      if (
        getLocalStorageDarkMode() === null &&
        darkMode !== prefersDarkMode.matches
      ) {
        setDarkMode(prefersDarkMode.matches);
        window.location.reload();
      }
    }

    prefersDarkMode.addEventListener('change', handlePreferredThemeChange);
    return () => {
      prefersDarkMode.removeEventListener('change', handlePreferredThemeChange);
    };
  }, [darkMode]);

  return [darkMode, setDarkMode] as const;
};
