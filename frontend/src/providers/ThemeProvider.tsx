import React, { lazy, Suspense } from 'react';

import { useTheme } from 'hooks/useTheme';

const DarkTheme = lazy(() => import('themes/dark/DarkTheme'));
const LightTheme = lazy(() => import('themes/light/LightTheme'));

type ThemeProviderProps = {
  children: React.JSX.Element;
};

export const ThemeProvider = ({ children }: ThemeProviderProps) => {
  const [darkMode] = useTheme();

  return (
    <Suspense fallback={<span />}>
      {darkMode ? <DarkTheme /> : <LightTheme />}
      {children}
    </Suspense>
  );
};
